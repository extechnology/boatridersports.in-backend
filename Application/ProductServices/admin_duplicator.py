"""
Duplication utility for Products in Django Admin.

Allows deep-cloning of BikeModel and AccessoriesModel instances along with:
- ManyToMany relationships (wheel sizes, materials, suspensions, sizes)
- Nested inlines (sizes & prices, colors & images, spec labels & values, posters, downloads)
- Fresh UUIDs and collision-free names (e.g. "Name (Copy)", "Name (Copy 2)")
"""

import os
import uuid
import logging
from django.db import transaction
from .product_models import (
    BikeModel, BikeSizesModel, BikeColorsModel, BikeImagesModel,
    BikeSpecLabelModel, BikeSpecValueModel, BikePostersModel, BikeDownloadsModel,
    AccessoriesModel, AccessoryImagesModel
)

logger = logging.getLogger(__name__)


def generate_copy_name(model_class, original_name, name_field='name'):
    """
    Generates a unique copy name to satisfy unique=True constraints.
    E.g. "Mountain Bike (Copy)", "Mountain Bike (Copy 2)", etc.
    """
    base_name = f"{original_name} (Copy)"
    if not model_class.objects.filter(**{name_field: base_name}).exists():
        return base_name

    counter = 2
    while True:
        candidate = f"{original_name} (Copy {counter})"
        if not model_class.objects.filter(**{name_field: candidate}).exists():
            return candidate
        counter += 1


def clone_bike(original_bike, new_name=None):
    """
    Creates a full deep clone of a BikeModel instance and all its related inlines.
    
    Copies:
    - All parent scalar fields
    - A fresh unique_id (UUID)
    - ManyToMany relationships (wheel_size, material, suspension, rear_suspension_travel, sizes)
    - BikeSizesModel (each size's price, stock, discount)
    - BikeColorsModel and child BikeImagesModel
    - BikeSpecLabelModel and child BikeSpecValueModel
    - BikePostersModel (poster image, title, description)
    - BikeDownloadsModel (file, title)
    
    Does NOT copy:
    - User reviews (BikeReviewsModel)
    """
    with transaction.atomic():
        if not new_name:
            new_name = generate_copy_name(BikeModel, original_bike.name)

        new_bike = BikeModel.objects.get(pk=original_bike.pk)
        new_bike.pk = None
        new_bike.id = None
        new_bike.unique_id = uuid.uuid4()
        new_bike.name = new_name
        new_bike.save()

        # 1. Copy ManyToMany relations
        if original_bike.wheel_size.exists():
            new_bike.wheel_size.set(original_bike.wheel_size.all())
        if original_bike.material.exists():
            new_bike.material.set(original_bike.material.all())
        if original_bike.suspension.exists():
            new_bike.suspension.set(original_bike.suspension.all())
        if original_bike.rear_suspension_travel.exists():
            new_bike.rear_suspension_travel.set(original_bike.rear_suspension_travel.all())
        if original_bike.sizes.exists():
            new_bike.sizes.set(original_bike.sizes.all())

        # 2. Deep-copy BikeSizesModel
        for bs in original_bike.bike_sizes.all():
            BikeSizesModel.objects.create(
                bike=new_bike,
                bike_size=bs.bike_size,
                price=bs.price,
                stock=bs.stock,
                is_available=bs.is_available,
                is_out_of_stock=bs.is_out_of_stock,
                is_discount=bs.is_discount,
                discount_price=bs.discount_price,
                discount_percentage=bs.discount_percentage,
            )

        # 3. Deep-copy BikeColorsModel and nested BikeImagesModel
        for color_obj in original_bike.bike_colors.all():
            new_color = BikeColorsModel.objects.create(
                bike=new_bike,
                color=color_obj.color,
            )
            for img_obj in color_obj.bike_images.all():
                if img_obj.image:
                    BikeImagesModel.objects.create(
                        color=new_color,
                        image=img_obj.image.name,
                    )

        # 4. Deep-copy BikeSpecLabelModel and nested BikeSpecValueModel
        for label_obj in original_bike.bike_spec_labels.all():
            new_label = BikeSpecLabelModel.objects.create(
                bike=new_bike,
                label=label_obj.label,
            )
            for val_obj in label_obj.bike_spec_values.all():
                BikeSpecValueModel.objects.create(
                    bike_spec_label=new_label,
                    name=val_obj.name,
                    value=val_obj.value,
                )

        # 5. Deep-copy BikePostersModel
        for poster_obj in original_bike.bike_posters.all():
            poster_name = poster_obj.poster.name if poster_obj.poster else ''
            BikePostersModel.objects.create(
                bike=new_bike,
                poster=poster_name,
                title=poster_obj.title,
                description=poster_obj.description,
            )

        # 6. Deep-copy BikeDownloadsModel
        for dl_obj in original_bike.bike_downloads.all():
            file_name = dl_obj.file.name if dl_obj.file else ''
            BikeDownloadsModel.objects.create(
                bike=new_bike,
                file=file_name,
                title=dl_obj.title,
            )

        logger.info(f"Successfully duplicated Bike {original_bike.id} ({original_bike.name}) to {new_bike.id} ({new_bike.name})")
        return new_bike


def clone_accessory(original_accessory, new_name=None):
    """
    Creates a full deep clone of an AccessoriesModel instance and all its related images.
    
    Copies:
    - All parent scalar fields
    - A fresh unique_id (UUID)
    - AccessoryImagesModel
    """
    with transaction.atomic():
        if not new_name:
            new_name = generate_copy_name(AccessoriesModel, original_accessory.name)

        new_acc = AccessoriesModel.objects.get(pk=original_accessory.pk)
        new_acc.pk = None
        new_acc.id = None
        new_acc.unique_id = uuid.uuid4()
        new_acc.name = new_name
        new_acc.save()

        # Deep-copy AccessoryImagesModel
        for img_obj in original_accessory.accessory_images.all():
            if img_obj.image:
                AccessoryImagesModel.objects.create(
                    accessory=new_acc,
                    image=img_obj.image.name,
                )

        logger.info(f"Successfully duplicated Accessory {original_accessory.id} ({original_accessory.name}) to {new_acc.id} ({new_acc.name})")
        return new_acc

