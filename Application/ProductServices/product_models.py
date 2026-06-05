from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from Application.AuthenticationServices.auth_models import User

# ==========================================================================
# Global Models
# ==========================================================================

# Store the bike category universal
class BikeCategoryModel(models.Model):
    category_name = models.CharField(max_length=255, unique=True)
    category_image = models.ImageField(upload_to='_images/',null=True, blank=True,help_text="Upload the category image for the category, this is requiered")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_name

# Store the bike brand universal
class BikeBrandModel(models.Model):
    brand_name = models.CharField(max_length=255, unique=True)
    brand_image = models.ImageField(upload_to='bike_brand_images/',help_text="Upload the brand image for the brand, this is requiered and add png files only")
    brand_description = models.TextField(null=True, blank=True)

    online_purchase_enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.brand_name

class WheelSizeModel(models.Model):
    wheel_size = models.CharField(max_length=255, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.wheel_size

class MaterialModel(models.Model):
    material = models.CharField(max_length=255, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.material

class SuspensionModel(models.Model):
    suspension = models.CharField(max_length=255, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.suspension

class RearSuspensionTravelModel(models.Model):
    rear_suspension_travel = models.CharField(max_length=255, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.rear_suspension_travel

# Store the bike color universal
class ColorModel(models.Model):
    color_name = models.CharField(max_length=255, unique=True)
    color_code = models.CharField(max_length=7,  help_text="Enter the first color code in hex format (e.g. #FF0000 for red)")
    color_code_2 = models.CharField(max_length=7, help_text="Enter the second color if its dual color",null=True, blank=True)
    color_image = models.ImageField(upload_to='bike_color_images/',null=True, blank=True,help_text="Upload the color image for the color")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.color_name

# Store the bike size universal
class SizeModel(models.Model):
    size = models.CharField(max_length=255, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.size

# Store the bike special tag universal
class SpecialTagModel(models.Model):
    tag_name = models.CharField(max_length=255, unique=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.tag_name

# ==========================================================================
# End Glonbal Models
# ==========================================================================

# ==========================================================================
# Bike Models
# ==========================================================================

# bike model
class BikeModel(models.Model):
    unique_id =  models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    special_tag = models.ForeignKey(SpecialTagModel, on_delete=models.CASCADE)

    brand = models.ForeignKey(BikeBrandModel, on_delete=models.CASCADE)
    
    category = models.ForeignKey(BikeCategoryModel, on_delete=models.CASCADE)

    product_type = models.CharField(max_length=255,default = 'bike',editable=False)
    wheel_size = models.ManyToManyField(WheelSizeModel,related_name='bike_wheel_sizes')
    sizes = models.ManyToManyField(SizeModel,related_name='bike_sizes', blank=True)
    material = models.ManyToManyField(MaterialModel,related_name='bake_materials')
    suspension = models.ManyToManyField(SuspensionModel,related_name='bike_suspensions',null=True, blank=True)
    rear_suspension_travel = models.ManyToManyField(RearSuspensionTravelModel,related_name='bike_rear_suspension_travels',null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    is_available = models.BooleanField(default=True)
    is_out_of_stock = models.BooleanField(default=False)

    is_discount = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2,default=0)

    background_color = models.CharField(max_length=255, help_text="Enter the background color in hex format (e.g. #FF0000 for red)",null=True, blank=True)
    text_color = models.CharField(max_length=255, help_text="Enter the text color in hex format (e.g. #FFFFFF for white)",null=True, blank=True)
    
    is_dark = models.BooleanField(default=False)
    
    is_featured = models.BooleanField(default=False, help_text="Set true if the bike is featured (e.g. home page)")
    featured_image = models.ImageField(upload_to='featured_images/', null=True, blank=True, help_text="Upload the featured image for the bike  if its featured")
    
    youtube_link = models.TextField(null=True, blank=True, help_text="Enter the youtube link for the bike")
    
    online_purchase_enabled = models.BooleanField(default=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2,default=0)


    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.stock == 0:
            self.is_out_of_stock = True
        else:
            self.is_out_of_stock = False
    
        if self.brand.online_purchase_enabled == False:
            self.online_purchase_enabled = False
            
        super().save(*args, **kwargs)

# bike sizes
class BikeSizesModel(models.Model):
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_sizes')
    bike_size = models.ForeignKey(SizeModel, on_delete=models.CASCADE,help_text="select the size for the bike")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.bike_size.size

# bike colors
class BikeColorsModel(models.Model):
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_colors')
    color = models.ForeignKey(ColorModel, on_delete=models.CASCADE,help_text="select the color for the image",related_name='bike_colors')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.color.color_name

# bike images
class BikeImagesModel(models.Model):
    color = models.ForeignKey(BikeColorsModel, on_delete=models.CASCADE,related_name='bike_images')
    image = models.ImageField(upload_to='bike_images_colors/')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.color.color.color_name

# bike spec label
class BikeSpecLabelModel(models.Model):
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_spec_labels')
    label = models.CharField(max_length=255, help_text="Enter the label for the spec (e.g.frameset, component, etc)")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.label

# bike spec value
class BikeSpecValueModel(models.Model):
    bike_spec_label = models.ForeignKey(BikeSpecLabelModel, on_delete=models.CASCADE,related_name='bike_spec_values')
    name = models.CharField(max_length=255, help_text="Enter the name for the spec (e.g. front suspension, rear suspension, etc)")
    value = models.CharField(max_length=255, help_text="Enter the value for the spec (e.g. front suspension, rear suspension, etc)")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.value

# bike posters
class BikePostersModel(models.Model):
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_posters')
    poster = models.ImageField(upload_to='bike_posters/')
    title = models.CharField(max_length=255, help_text="Enter the title for the poster (e.g. Bike Poster, Bike Wallpaper, etc)")
    description = models.TextField(help_text="Enter the description for the poster")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

# bike downloads
class BikeDownloadsModel(models.Model):
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_downloads')

    file = models.FileField(upload_to='bike_downloads/')
    title = models.CharField(max_length=255, help_text="Enter the title for the download (e.g. Bike Manuel, Bike Brochure, etc)")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class BikeReviewsModel(models.Model):
    bike = models.ForeignKey(BikeModel, on_delete=models.CASCADE,related_name='bike_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='bike_reviews')
    review = models.TextField(help_text="Enter the review for the bike")
    rating = models.IntegerField(help_text="Enter the rating for the bike")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.review

# ==========================================================================
# End Bike Models
# ==========================================================================

# ==========================================================================
# Accessories Models
# ==========================================================================

class AccessoriesCategoryModel(models.Model):
    name = models.CharField(max_length=255, help_text="Enter the name for the category")
    image = models.ImageField(upload_to='accessory_category_images/',null=True, blank=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class AccessoriesSubCategoryModel(models.Model):
    category = models.ForeignKey(AccessoriesCategoryModel, on_delete=models.CASCADE,related_name='accessories')
    name = models.CharField(max_length=255, help_text="Enter the name for the accessory")
    # description = models.TextField(help_text="Enter the description for the accessory")

    def __str__(self):
        return self.name

class AccessoriesModel(models.Model):
    unique_id =  models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255, help_text="Enter the name for the accessory")
    description = models.TextField(help_text="Enter the description for the accessory")

    product_type = models.CharField(max_length=255,default = 'accessories',editable=False) 
    special_tag = models.ForeignKey(SpecialTagModel, on_delete=models.CASCADE,null = True, blank= True)
    is_dark = models.BooleanField(default=False, help_text="Set true if the accessory is dark")
    
    sub_category = models.ForeignKey(AccessoriesSubCategoryModel,on_delete=models.CASCADE,related_name='accessories')
    brand = models.ForeignKey(BikeBrandModel,related_name='accessories',on_delete=models.CASCADE,null=True,blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2,help_text="Enter the price for the accessory")
    stock = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_out_of_stock = models.BooleanField(default=False)
    is_discount = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2,default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    online_purchase_enabled = models.BooleanField(default=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2,default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.brand and self.brand.online_purchase_enabled == False:
            self.online_purchase_enabled = False
        super().save(*args, **kwargs)
    
    def get_discounted_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price

class AccessoryImagesModel(models.Model):
    accessory = models.ForeignKey(AccessoriesModel, on_delete=models.CASCADE,related_name='accessory_images')
    image = models.ImageField(upload_to='accessory_images/')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.accessory.name

class GuideAndTrainerModel(models.Model):
    name = models.CharField(max_length=255, help_text="Enter the name for the guide and trainer")
    description = models.TextField(help_text="Enter the description for the guide and trainer")
    
    CHOICES = (
        ('guide', 'Guide'),
        ('trainer', 'Trainer'),
    )
    type = models.CharField(max_length=10, choices=CHOICES, default='guide')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


# ==========================================================================
# End Accessories Models
# ==========================================================================



class ShippingChargeModel(models.Model):
    NAME_OPTIONS =(
        ('bike','bike'),
        ('accessory','accessory'),
    )
    name = models.CharField(max_length=255,choices=NAME_OPTIONS, default='bike', help_text="Enter the name for the shipping charge",unique = True)
    charge = models.DecimalField(max_digits=10, decimal_places=2, help_text="Enter the charge for the shipping")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name