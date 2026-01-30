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

    # 🔹 Price filters
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")

    min_discount_price = filters.NumberFilter(
        field_name="discount_price", lookup_expr="gte"
    )
    max_discount_price = filters.NumberFilter(
        field_name="discount_price", lookup_expr="lte"
    )

    # 🔹 Text search
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains"
    )

    description = filters.CharFilter(
        field_name="description",
        lookup_expr="icontains"
    )

    # 🔹 Category filters (FK → FK)
    category = filters.CharFilter(
        field_name="sub_category__category__name",
        lookup_expr="icontains"
    )

    sub_category = filters.CharFilter(
        field_name="sub_category__name",
        lookup_expr="icontains"
    )

    # 🔹 Brand filter (ManyToMany)
    brand = filters.CharFilter(
        field_name="brand__brand_name",
        lookup_expr="icontains"
    )

    class Meta:
        model = AccessoriesModel
        fields = [
            "name",
            "description",
            "category",
            "sub_category",
            "brand",
            "min_price",
            "max_price",
            "min_discount_price",
            "max_discount_price",
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
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    special_tag = request.GET.getlist('special_tag')

    queryset = AccessoriesModel.objects.all()

    if name:
        queryset = queryset.filter(name__icontains=name)

    if brand:
        queryset = queryset.filter(brand__brand_name__in=brand)

    # ✅ FIX: go through sub_category → category → name
    if category:
        queryset = queryset.filter(
            sub_category__category__name__in=category
        )

    # ✅ FIX: correct field name
    if sub_category:
        queryset = queryset.filter(
            sub_category__name__in=sub_category
        )

    if special_tag:
        queryset = queryset.filter(special_tag__tag_name__in=special_tag)

    if min_price:
        queryset = queryset.filter(price__gte=min_price)

    if max_price:
        queryset = queryset.filter(price__lte=max_price)

    return queryset
