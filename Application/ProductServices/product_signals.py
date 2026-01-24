from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .product_tasks import build_bike_sidebar, build_accessory_sidebar
from .product_models import (
    BikeCategoryModel,
    BikeBrandModel,
    WheelSizeModel,
    MaterialModel,
    SuspensionModel,
    RearSuspensionTravelModel,
    ColorModel,
    SizeModel,
    SpecialTagModel,
    BikeModel,
    BikeSizesModel,
    BikeColorsModel,
    BikeImagesModel,
    AccessoryImagesModel,
    AccessoriesModel,
    AccessoriesSubCategoryModel,
    AccessoriesCategoryModel,
    GuideAndTrainerModel,
)

# ONE function – multiple senders
@receiver([post_save, post_delete], sender=BikeCategoryModel)
@receiver([post_save, post_delete], sender=BikeBrandModel)
@receiver([post_save, post_delete], sender=WheelSizeModel)
@receiver([post_save, post_delete], sender=MaterialModel)
@receiver([post_save, post_delete], sender=SuspensionModel)
@receiver([post_save, post_delete], sender=RearSuspensionTravelModel)
@receiver([post_save, post_delete], sender=ColorModel)
@receiver([post_save, post_delete], sender=SizeModel)
@receiver([post_save, post_delete], sender=SpecialTagModel)
@receiver([post_save, post_delete], sender=BikeModel)
@receiver([post_save, post_delete], sender=BikeSizesModel)
@receiver([post_save, post_delete], sender=BikeColorsModel)
@receiver([post_save, post_delete], sender=BikeImagesModel)
@receiver([post_save, post_delete], sender=GuideAndTrainerModel)
@receiver([post_save, post_delete], sender=AccessoryImagesModel)
@receiver([post_save, post_delete], sender=AccessoriesModel)
@receiver([post_save, post_delete], sender=AccessoriesSubCategoryModel)
@receiver([post_save, post_delete], sender=AccessoriesCategoryModel)
def refresh_sidebar(sender, **kwargs):
    build_bike_sidebar.delay()
    build_accessory_sidebar.delay()



