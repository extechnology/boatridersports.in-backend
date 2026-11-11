from django_filters import rest_framework as filters
from django.db.models import Q, OuterRef, Subquery
from .product_models import BikeModel, AccessoriesModel

class BikeFilter(filters.FilterSet):

    min_price = filters.NumberFilter(method="filter_min_price")
    max_price = filters.NumberFilter(method="filter_max_price")

    brand = filters.CharFilter(method="filter_brand")
    category = filters.CharFilter(method="filter_category")
    special_tag = filters.CharFilter(method="filter_special_tag")

    wheel_size = filters.CharFilter(method="filter_wheel_size")
    material = filters.CharFilter(method="filter_material")
    suspension = filters.CharFilter(method="filter_suspension")
    rear_suspension_travel = filters.CharFilter(method="filter_rear_suspension_travel")

    color = filters.CharFilter(method="filter_color")
    size = filters.CharFilter(method="filter_size")

    # ---------- FK FILTERS ----------

    def filter_brand(self, queryset, name, value):
        brands = self.request.GET.getlist("brand") if self.request else []
        if brands:
            queryset = queryset.filter(brand__brand_name__in=brands)
        return queryset

    def filter_category(self, queryset, name, value):
        categories = self.request.GET.getlist("category") if self.request else []
        if categories:
            queryset = queryset.filter(category__category_name__in=categories)
        return queryset

    def filter_special_tag(self, queryset, name, value):
        tags = self.request.GET.getlist("special_tag") if self.request else []
        if tags:
            queryset = queryset.filter(special_tag__tag_name__in=tags)
        return queryset

    # ---------- MANY TO MANY FILTERS ----------

    def filter_wheel_size(self, queryset, name, value):
        sizes = self.request.GET.getlist("wheel_size") if self.request else []
        if sizes:
            queryset = queryset.filter(wheel_size__wheel_size__in=sizes)
        return queryset

    def filter_material(self, queryset, name, value):
        materials = self.request.GET.getlist("material") if self.request else []
        if materials:
            queryset = queryset.filter(material__material__in=materials)
        return queryset

    def filter_suspension(self, queryset, name, value):
        suspensions = self.request.GET.getlist("suspension") if self.request else []
        if suspensions:
            queryset = queryset.filter(suspension__suspension__in=suspensions)
        return queryset

    def filter_rear_suspension_travel(self, queryset, name, value):
        travels = self.request.GET.getlist("rear_suspension_travel") if self.request else []
        if travels:
            queryset = queryset.filter(
                rear_suspension_travel__rear_suspension_travel__in=travels
            )
        return queryset

    def filter_color(self, queryset, name, value):
        colors = self.request.GET.getlist("color") if self.request else []
        if colors:
            queryset = queryset.filter(
                bike_colors__color__color_name__in=colors
            )
        return queryset

    def filter_size(self, queryset, name, value):
        sizes = self.request.GET.getlist("size") if self.request else []
        if sizes:
            queryset = queryset.filter(
                bike_sizes__bike_size__size__in=sizes
            )
        return queryset

    # ---------- PRICE FILTERS ----------
    is_discount = filters.BooleanFilter(field_name="is_discount")
    def filter_min_price(self, queryset, name, value):
        return queryset.filter(
            Q(is_discount=True, discount_price__gte=value) |
            Q(is_discount=False, price__gte=value)
        )

    def filter_max_price(self, queryset, name, value):
        return queryset.filter(
            Q(is_discount=True, discount_price__lte=value) |
            Q(is_discount=False, price__lte=value)
        )

    class Meta:
        model = BikeModel
        fields = [
            "brand",
            "category",
            "special_tag",
            "wheel_size",
            "material",
            "suspension",
            "rear_suspension_travel",
            "color",
            "size",
            "min_price",
            "max_price",
        ]


class AccessoriesFilter(filters.FilterSet):

    # 🔹 Price filters (considering discount_price if active)
    min_price = filters.NumberFilter(method="filter_min_price")
    max_price = filters.NumberFilter(method="filter_max_price")

    def filter_min_price(self, queryset, name, value):
        return queryset.filter(
            Q(is_discount=True, discount_price__gte=value) |
            Q(is_discount=False, price__gte=value)
        )

    def filter_max_price(self, queryset, name, value):
        return queryset.filter(
            Q(is_discount=True, discount_price__lte=value) |
            Q(is_discount=False, price__lte=value)
        )

    # 🔹 Text search
    name = filters.CharFilter(method="filter_search_name")
    def filter_search_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(model_name__icontains=value) |
            Q(model_no__icontains=value)
        )

    description = filters.CharFilter(
        field_name="description",
        lookup_expr="icontains"
    )

    # 🔹 Category / Sub Category / Brand filters (support getlist multi-select)
    category = filters.CharFilter(method="filter_category")
    sub_category = filters.CharFilter(method="filter_sub_category")
    brand = filters.CharFilter(method="filter_brand")
    special_tag = filters.CharFilter(method="filter_special_tag")

    def filter_category(self, queryset, name, value):
        categories = self.request.GET.getlist("category") if self.request else []
        if categories:
            return queryset.filter(sub_category__category__name__in=categories)
        return queryset.filter(sub_category__category__name__icontains=value)

    def filter_sub_category(self, queryset, name, value):
        sub_categories = self.request.GET.getlist("sub_category") if self.request else []
        if sub_categories:
            return queryset.filter(sub_category__name__in=sub_categories)
        return queryset.filter(sub_category__name__icontains=value)

    def filter_brand(self, queryset, name, value):
        brands = self.request.GET.getlist("brand") if self.request else []
        if brands:
            return queryset.filter(brand__brand_name__in=brands)
        return queryset.filter(brand__brand_name__icontains=value)

    def filter_special_tag(self, queryset, name, value):
        tags = self.request.GET.getlist("special_tag") if self.request else []
        if tags:
            return queryset.filter(special_tag__tag_name__in=tags)
        return queryset.filter(special_tag__tag_name__icontains=value)

    # 🔹 Specification Filter Attributes
    model_no = filters.CharFilter(method="filter_model_no")
    model_name = filters.CharFilter(method="filter_model_name")
    speed = filters.CharFilter(method="filter_speed")
    tire_type = filters.CharFilter(method="filter_tire_type")
    hub_width = filters.CharFilter(method="filter_hub_width")
    valve_type = filters.CharFilter(method="filter_valve_type")
    size = filters.CharFilter(method="filter_size")
    ml = filters.CharFilter(method="filter_ml")
    color = filters.CharFilter(method="filter_color")
    bike_mounted_type = filters.CharFilter(method="filter_bike_mounted_type")
    material = filters.CharFilter(method="filter_material")
    warranty = filters.CharFilter(method="filter_warranty")

    def filter_model_no(self, queryset, name, value):
        vals = self.request.GET.getlist("model_no") if self.request else []
        if vals:
            return queryset.filter(model_no__in=vals)
        return queryset.filter(model_no__icontains=value)

    def filter_model_name(self, queryset, name, value):
        vals = self.request.GET.getlist("model_name") if self.request else []
        if vals:
            return queryset.filter(model_name__in=vals)
        return queryset.filter(model_name__icontains=value)

    def filter_speed(self, queryset, name, value):
        vals = self.request.GET.getlist("speed") if self.request else []
        if vals:
            return queryset.filter(speed__in=vals)
        return queryset.filter(speed__icontains=value)

    def filter_tire_type(self, queryset, name, value):
        vals = self.request.GET.getlist("tire_type") if self.request else []
        if vals:
            return queryset.filter(tire_type__in=vals)
        return queryset.filter(tire_type__icontains=value)

    def filter_hub_width(self, queryset, name, value):
        vals = self.request.GET.getlist("hub_width") if self.request else []
        if vals:
            return queryset.filter(hub_width__in=vals)
        return queryset.filter(hub_width__icontains=value)

    def filter_valve_type(self, queryset, name, value):
        vals = self.request.GET.getlist("valve_type") if self.request else []
        if vals:
            return queryset.filter(valve_type__in=vals)
        return queryset.filter(valve_type__icontains=value)

    def filter_size(self, queryset, name, value):
        vals = self.request.GET.getlist("size") if self.request else []
        if vals:
            return queryset.filter(size__in=vals)
        return queryset.filter(size__icontains=value)

    def filter_ml(self, queryset, name, value):
        vals = self.request.GET.getlist("ml") if self.request else []
        if vals:
            return queryset.filter(ml__in=vals)
        return queryset.filter(ml__icontains=value)

    def filter_color(self, queryset, name, value):
        vals = self.request.GET.getlist("color") if self.request else []
        if vals:
            return queryset.filter(color__in=vals)
        return queryset.filter(color__icontains=value)

    def filter_bike_mounted_type(self, queryset, name, value):
        vals = self.request.GET.getlist("bike_mounted_type") if self.request else []
        if vals:
            return queryset.filter(bike_mounted_type__in=vals)
        return queryset.filter(bike_mounted_type__icontains=value)

    def filter_material(self, queryset, name, value):
        vals = self.request.GET.getlist("material") if self.request else []
        if vals:
            return queryset.filter(material__in=vals)
        return queryset.filter(material__icontains=value)

    def filter_warranty(self, queryset, name, value):
        vals = self.request.GET.getlist("warranty") if self.request else []
        if vals:
            return queryset.filter(warranty__in=vals)
        return queryset.filter(warranty__icontains=value)

    class Meta:
        model = AccessoriesModel
        fields = [
            "name",
            "model_name",
            "model_no",
            "description",
            "category",
            "sub_category",
            "brand",
            "speed",
            "tire_type",
            "hub_width",
            "valve_type",
            "size",
            "ml",
            "color",
            "bike_mounted_type",
            "material",
            "warranty",
            "special_tag",
            "min_price",
            "max_price",
        ]



def bike_filters(request):
    name = request.GET.get('name')
    brand = request.GET.getlist('brand')
    category = request.GET.getlist('category')
    special_tag = request.GET.getlist('special_tag')
    wheel_size = request.GET.getlist('wheel_size')
    material = request.GET.getlist('material')
    suspension = request.GET.getlist('suspension')
    rear_suspension_travel = request.GET.getlist('rear_suspension_travel')
    color = request.GET.getlist('color')
    size = request.GET.getlist('size')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    qs = BikeModel.objects.all()

    if name:
        qs = qs.filter(name__icontains=name)

    if brand:
        qs = qs.filter(brand__brand_name__in=brand)

    if category:
        qs = qs.filter(category__category_name__in=category)

    if special_tag:
        qs = qs.filter(special_tag__tag_name__in=special_tag)

    if wheel_size:
        qs = qs.filter(wheel_size__wheel_size__in=wheel_size)

    if material:
        qs = qs.filter(material__material__in=material)

    if suspension:
        qs = qs.filter(suspension__suspension__in=suspension)

    if rear_suspension_travel:
        qs = qs.filter(
            rear_suspension_travel__rear_suspension_travel__in=rear_suspension_travel
        )

    if color:
        qs = qs.filter(bike_colors__color__color_name__in=color)

    if size:
        qs = qs.filter(bike_sizes__bike_size__size__in=size)

    if min_price:
        qs = qs.filter(price__gte=min_price)

    if max_price:
        qs = qs.filter(price__lte=max_price)

    # ✅ HARD DEDUPLICATION BY BIKE ID
    qs = qs.filter(
        id__in=Subquery(
            qs.values('id').distinct()
        )
    )

    return qs


def accessories_filters(request):
    name = request.GET.get('name')
    brand = request.GET.getlist('brand')
    category = request.GET.getlist('category')
    sub_category = request.GET.getlist('sub_category')
    special_tag = request.GET.getlist('special_tag')

    # Specification Filter Attributes
    model_no = request.GET.getlist('model_no') or ([request.GET.get('model_no')] if request.GET.get('model_no') else [])
    model_name = request.GET.getlist('model_name') or ([request.GET.get('model_name')] if request.GET.get('model_name') else [])
    speed = request.GET.getlist('speed')
    tire_type = request.GET.getlist('tire_type')
    hub_width = request.GET.getlist('hub_width')
    valve_type = request.GET.getlist('valve_type')
    size = request.GET.getlist('size')
    ml = request.GET.getlist('ml')
    color = request.GET.getlist('color')
    bike_mounted_type = request.GET.getlist('bike_mounted_type')
    material = request.GET.getlist('material')
    warranty = request.GET.getlist('warranty')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    queryset = AccessoriesModel.objects.all().order_by('-created')

    if name:
        queryset = queryset.filter(
            Q(name__icontains=name) |
            Q(model_name__icontains=name) |
            Q(model_no__icontains=name) |
            Q(description__icontains=name)
        )

    if brand:
        queryset = queryset.filter(brand__brand_name__in=brand)

    if category:
        queryset = queryset.filter(
            sub_category__category__name__in=category
        )

    if sub_category:
        queryset = queryset.filter(
            sub_category__name__in=sub_category
        )

    if model_no:
        queryset = queryset.filter(model_no__in=model_no)

    if model_name:
        queryset = queryset.filter(model_name__in=model_name)

    if speed:
        queryset = queryset.filter(speed__in=speed)

    if tire_type:
        queryset = queryset.filter(tire_type__in=tire_type)

    if hub_width:
        queryset = queryset.filter(hub_width__in=hub_width)

    if valve_type:
        queryset = queryset.filter(valve_type__in=valve_type)

    if size:
        queryset = queryset.filter(size__in=size)

    if ml:
        queryset = queryset.filter(ml__in=ml)

    if color:
        queryset = queryset.filter(color__in=color)

    if bike_mounted_type:
        queryset = queryset.filter(bike_mounted_type__in=bike_mounted_type)

    if material:
        queryset = queryset.filter(material__in=material)

    if warranty:
        queryset = queryset.filter(warranty__in=warranty)

    if special_tag:
        queryset = queryset.filter(special_tag__tag_name__in=special_tag)

    if min_price:
        queryset = queryset.filter(
            Q(is_discount=True, discount_price__gte=min_price) |
            Q(is_discount=False, price__gte=min_price)
        )

    if max_price:
        queryset = queryset.filter(
            Q(is_discount=True, discount_price__lte=max_price) |
            Q(is_discount=False, price__lte=max_price)
        )

    return queryset
