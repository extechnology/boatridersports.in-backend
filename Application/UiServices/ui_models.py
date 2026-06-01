from django.db import models
from django.core.cache import cache

class HomeSliderVideoModel(models.Model):
    desktop_video = models.FileField(upload_to='home_slider_videos/',null=True,blank=True,help_text="Upload home slider video")
    mobile_video = models.FileField(upload_to='home_slider_videos/',null=True,blank=True,help_text="Upload home slider video")
    title = models.CharField(max_length=100)
    sub_title = models.CharField(max_length=100)
    description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete("home_slider_video")
    
    def clean(self):
        if not self.pk and HomeSliderVideoModel.objects.exists():
            raise ValidationError("Only one Home Slider Video is allowed.")
