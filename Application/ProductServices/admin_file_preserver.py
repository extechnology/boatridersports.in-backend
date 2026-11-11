import os
import uuid
import logging
from datetime import timedelta
from django import forms
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

TEMP_UPLOAD_DIR = 'temp_admin_uploads'
SIGNER_SALT = 'preserved_admin_file_upload'
signer = TimestampSigner(salt=SIGNER_SALT)


class PreservedUploadedFile(File):
    """
    A File wrapper around an uploaded file that was temporarily preserved
    during a form validation failure.
    """
    is_preserved = True

    def __init__(self, file_obj, name, size=None, content_type=None, temp_rel_path=None, token=None):
        super().__init__(file_obj, name=name)
        self.size = size if size is not None else getattr(file_obj, 'size', 0)
        self.content_type = content_type or getattr(file_obj, 'content_type', 'application/octet-stream')
        self.temp_rel_path = temp_rel_path
        self.token = token
        if temp_rel_path:
            try:
                self._url = default_storage.url(temp_rel_path)
            except Exception:
                self._url = None
        else:
            self._url = getattr(file_obj, 'url', None)

    @property
    def url(self):
        return self._url

    def __str__(self):
        return self.name


def save_temp_file(uploaded_file):
    """
    Saves an UploadedFile to temporary storage and returns (token, temp_rel_path).
    Resets the file pointer so downstream operations can still read it.
    """
    subfolder = uuid.uuid4().hex
    safe_name = os.path.basename(uploaded_file.name or 'upload')
    temp_rel_path = f"{TEMP_UPLOAD_DIR}/{subfolder}/{safe_name}"

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    saved_path = default_storage.save(temp_rel_path, uploaded_file)

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    token = signer.sign(saved_path)
    return token, saved_path


def load_temp_file(token):
    """
    Validates a token and returns a PreservedUploadedFile from temporary storage,
    or None if invalid, expired, or missing.
    """
    if not token or not isinstance(token, str):
        return None

    try:
        # Max age: 24 hours (86400 seconds)
        path = signer.unsign(token, max_age=86400)
    except (BadSignature, SignatureExpired):
        return None

    # Security check: ensure path is inside TEMP_UPLOAD_DIR
    clean_path = os.path.normpath(path).replace('\\', '/')
    if not clean_path.startswith(TEMP_UPLOAD_DIR):
        return None

    if default_storage.exists(clean_path):
        try:
            f = default_storage.open(clean_path)
            name = os.path.basename(clean_path)
            return PreservedUploadedFile(
                f,
                name=name,
                size=f.size,
                temp_rel_path=clean_path,
                token=token
            )
        except Exception as e:
            logger.warning(f"Failed to load preserved temp file {clean_path}: {e}")
            return None
    return None


def delete_temp_file(token_or_path):
    """
    Deletes the temporary file and attempts to remove its parent folder.
    """
    if not token_or_path:
        return

    path = token_or_path
    if ':' in token_or_path:
        try:
            path = signer.unsign(token_or_path)
        except Exception:
            return

    clean_path = os.path.normpath(path).replace('\\', '/')
    if not clean_path.startswith(TEMP_UPLOAD_DIR):
        return

    try:
        if default_storage.exists(clean_path):
            default_storage.delete(clean_path)
            # Try to remove parent folder if supported by storage
            parent_dir = os.path.dirname(clean_path)
            if hasattr(default_storage, 'path'):
                full_parent = os.path.join(default_storage.path(''), parent_dir)
                if os.path.isdir(full_parent) and not os.listdir(full_parent):
                    try:
                        os.rmdir(full_parent)
                    except Exception:
                        pass
    except Exception as e:
        logger.debug(f"Could not delete temp file {clean_path}: {e}")


def cleanup_expired_temp_files(max_age_hours=24):
    """
    Deletes temporary admin upload files older than max_age_hours.
    """
    try:
        if not hasattr(default_storage, 'path'):
            return
        temp_dir = os.path.join(default_storage.path(''), TEMP_UPLOAD_DIR)
        if not os.path.isdir(temp_dir):
            return

        now = timezone.now().timestamp()
        max_age_seconds = max_age_hours * 3600

        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    if now - mtime > max_age_seconds:
                        os.remove(filepath)
                except Exception:
                    pass
            # Remove empty directory
            if not os.listdir(root) and root != temp_dir:
                try:
                    os.rmdir(root)
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Error during expired temp files cleanup: {e}")


class PreservedAdminFileWidget(AdminFileWidget):
    """
    Enhanced AdminFileWidget that:
    1. Preserves uploaded files to temporary storage when form validation fails.
    2. Displays a clear preview notice showing the preserved file and thumbnail.
    3. Seamlessly restores the preserved file on subsequent submissions.
    4. Displays an image preview for existing saved images in edit mode.
    """
    is_image = False

    def value_from_datadict(self, data, files, name):
        upload = files.get(name)
        token_name = f"{name}-temp-token"
        existing_token = data.get(token_name)
        clear_checkbox = self.clear_checkbox_name(name)

        # 1. User clicked "Clear"
        if not self.is_required and clear_checkbox in data:
            if existing_token:
                delete_temp_file(existing_token)
            return False

        # 2. User uploaded a new file in request.FILES
        if upload:
            try:
                token, rel_path = save_temp_file(upload)
                # If there was a previous temp token, delete the older one
                if existing_token and existing_token != token:
                    delete_temp_file(existing_token)
                return PreservedUploadedFile(
                    upload,
                    name=upload.name,
                    size=upload.size,
                    content_type=getattr(upload, 'content_type', None),
                    temp_rel_path=rel_path,
                    token=token
                )
            except Exception as e:
                logger.error(f"Error preserving uploaded file {upload.name}: {e}")
                return upload

        # 3. No new file uploaded, but temp token is present in POST data
        if existing_token:
            preserved = load_temp_file(existing_token)
            if preserved:
                return preserved

        # 4. "Save as new" support: carry over existing saved file to new instance
        existing_file_path = data.get(f"{name}-existing-file")
        if '_saveasnew' in data and not upload and not existing_token and existing_file_path:
            if default_storage.exists(existing_file_path):
                try:
                    f = default_storage.open(existing_file_path)
                    return PreservedUploadedFile(
                        f,
                        name=os.path.basename(existing_file_path),
                        size=getattr(f, 'size', 0),
                        temp_rel_path=None
                    )
                except Exception as e:
                    logger.warning(f"Could not load existing file {existing_file_path} for save_as_new: {e}")

        # 5. Standard fallback (e.g. existing model instance or None)
        return super().value_from_datadict(data, files, name)

    def render(self, name, value, attrs=None, renderer=None):
        token_val = getattr(value, 'token', None)
        token_name = f"{name}-temp-token"

        # Check if value is a PreservedUploadedFile
        is_temp_preserved = bool(token_val and getattr(value, 'is_preserved', False))

        # Standard widget render
        base_html = super().render(name, value, attrs=attrs, renderer=renderer)

        existing_hidden = ''
        if value and getattr(value, 'name', None):
            existing_hidden = format_html(
                '<input type="hidden" name="{}" value="{}">',
                f"{name}-existing-file",
                str(value.name)
            )

        # Extra UI for preserved temp file
        if is_temp_preserved:
            hidden_input = format_html(
                '<input type="hidden" name="{}" value="{}">',
                token_name,
                token_val
            )

            file_url = getattr(value, 'url', None) or '#'
            file_name = str(value)

            preview_thumbnail = ''
            if self.is_image and file_url and file_url != '#':
                preview_thumbnail = format_html(
                    '<div style="margin-top: 6px;">'
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-height: 90px; max-width: 160px; object-fit: contain; '
                    'border-radius: 4px; border: 1px solid #c8e6c9; background: #fff; padding: 2px;" '
                    'title="Click to view full image" />'
                    '</a>'
                    '</div>',
                    file_url,
                    file_url
                )

            notice_html = format_html(
                '<div style="margin: 6px 0 10px 0; padding: 8px 12px; background: #f0fdf4; '
                'border: 1px solid #86efac; border-radius: 6px; display: inline-block; max-width: 100%;">'
                '<div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">'
                '<span style="display: inline-flex; align-items: center; justify-content: center; '
                'width: 18px; height: 18px; background: #16a34a; color: #fff; border-radius: 50%; '
                'font-size: 11px; font-weight: bold;">✓</span>'
                '<strong style="color: #166534; font-size: 12px;">Uploaded file preserved:</strong>'
                '<a href="{}" target="_blank" style="color: #15803d; font-weight: 600; font-size: 12px; '
                'text-decoration: underline;">{}</a>'
                '</div>'
                '{}'
                '<div style="color: #4b5563; font-size: 11px; margin-top: 4px;">'
                'This file is safely retained and will be saved when you submit. Choose a file below only to replace it.'
                '</div>'
                '</div><br>',
                file_url,
                file_name,
                mark_safe(preview_thumbnail)
            )

            return mark_safe(f"{notice_html}{hidden_input}{existing_hidden}{base_html}")

        # If it's an existing saved image in DB (change mode), add a thumbnail preview above "Currently:"
        if self.is_image and value and getattr(value, 'url', None):
            existing_thumb = format_html(
                '<div style="margin: 4px 0 8px 0;">'
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-height: 80px; max-width: 140px; object-fit: contain; '
                'border-radius: 4px; border: 1px solid #ddd; background: #fff; padding: 2px;" '
                'title="Current Image Preview" />'
                '</a>'
                '</div>',
                value.url,
                value.url
            )
            return mark_safe(f"{existing_hidden}{existing_thumb}{base_html}")

        return mark_safe(f"{existing_hidden}{base_html}")


class PreservedAdminImageWidget(PreservedAdminFileWidget):
    """
    Preserved admin widget configured specifically for ImageField.
    """
    is_image = True


class PreservedFileField(forms.FileField):
    """
    A form FileField that does NOT discard bound uploaded files during validation errors.
    """
    widget = PreservedAdminFileWidget

    def bound_data(self, data, initial):
        if data:
            return data
        return initial


class PreservedImageField(forms.ImageField):
    """
    A form ImageField that does NOT discard bound uploaded files during validation errors.
    """
    widget = PreservedAdminImageWidget

    def bound_data(self, data, initial):
        if data:
            return data
        return initial


class PreserveFilesAdminMixin:
    """
    ModelAdmin and InlineModelAdmin mixin that:
    1. Overrides formfields for ImageField and FileField to use Preserved form fields and widgets.
    2. Automatically cleans up temporary files after successful model and formset saves.
    """
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.ImageField):
            kwargs.setdefault('form_class', PreservedImageField)
            kwargs.setdefault('widget', PreservedAdminImageWidget)
        elif isinstance(db_field, models.FileField):
            kwargs.setdefault('form_class', PreservedFileField)
            kwargs.setdefault('widget', PreservedAdminFileWidget)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._cleanup_form_temp_files(request, form)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        self._cleanup_formset_temp_files(request, formset)

    def _cleanup_form_temp_files(self, request, form):
        """
        Cleans up temporary files saved for fields on the main form.
        """
        if not form:
            return
        for field_name in form.fields:
            token_name = f"{field_name}-temp-token"
            token = request.POST.get(token_name)
            if token:
                # Close the file handle if open so Windows doesn't block deletion
                val = getattr(obj_or_val := form.cleaned_data.get(field_name), 'file', None)
                if val and hasattr(val, 'close'):
                    try:
                        val.close()
                    except Exception:
                        pass
                delete_temp_file(token)

    def _cleanup_formset_temp_files(self, request, formset):
        """
        Cleans up temporary files saved for fields on inline formsets.
        """
        if not formset:
            return
        for f in formset.forms:
            for field_name in f.fields:
                prefix = f.prefix
                token_name = f"{prefix}-{field_name}-temp-token"
                token = request.POST.get(token_name)
                if token:
                    val = getattr(f.cleaned_data.get(field_name), 'file', None)
                    if val and hasattr(val, 'close'):
                        try:
                            val.close()
                        except Exception:
                            pass
                    delete_temp_file(token)

