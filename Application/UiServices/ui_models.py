from django.db import models

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
    
