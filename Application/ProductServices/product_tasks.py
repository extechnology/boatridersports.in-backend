from celery import shared_task
from django.core.cache import cache
from .product_models import (
    BikeCategoryModel, BikeBrandModel, SizeModel,
    WheelSizeModel, MaterialModel, SuspensionModel,
    RearSuspensionTravelModel, ColorModel,
    AccessoriesCategoryModel, AccessoriesSubCategoryModel,
    AccessoriesModel, SpecialTagModel
)

@shared_task
def build_bike_sidebar():
    data = {
        "categories": list(BikeCategoryModel.objects.values_list("category_name", flat=True)),
        "brands": list(BikeBrandModel.objects.values_list("brand_name", flat=True)),
        "sizes": list(SizeModel.objects.values_list("size", flat=True)),
        "wheel_sizes": list(WheelSizeModel.objects.values_list("wheel_size", flat=True)),
        "materials": list(MaterialModel.objects.values_list("material", flat=True)),
        "suspensions": list(SuspensionModel.objects.values_list("suspension", flat=True)),
        "rearSuspensionTravel": list(
            RearSuspensionTravelModel.objects.values_list("rear_suspension_travel", flat=True)
        ),
        "colors": [
            {
                "name": c.color_name,
                "code": list(filter(None, [c.color_code, c.color_code_2]))
            }
            for c in ColorModel.objects.all()
        ],
         "product_type": "bike",
        "special_tags":list(SpecialTagModel.objects.values_list("tag_name", flat=True))

    }

    cache.set("sidebar_bike", data, timeout=60 * 60 * 24)  # 24 hours
    return data

@shared_task
def build_accessory_sidebar():
    data = {
        "categories": list(
            AccessoriesCategoryModel.objects.values_list("name", flat=True)
        ),
        "sub_categories": list(
            AccessoriesSubCategoryModel.objects.values_list("name", flat=True)
        ),
        "brands": list(
            BikeBrandModel.objects.values_list("brand_name", flat=True)
        ),
        "product_type": "accessories",  
        "special_tags": list(
            SpecialTagModel.objects.values_list("tag_name", flat=True)
        )
    }

    cache.set("sidebar_accessory", data, timeout=60 * 60 * 24)
    return data

