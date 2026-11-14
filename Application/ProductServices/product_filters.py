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


def _normalize_filter_values(raw_values):
    """
    Takes a list of values (or single value), splits by comma if needed,
    and returns a clean list of non-empty stripped strings.
    """
    if not raw_values:
        return []
    if isinstance(raw_values, str):
        raw_values = [raw_values]
    result = []
    for item in raw_values:
        if not item:
            continue
        s = str(item).strip()
        if not s:
            continue
        if ',' in s:
            result.extend([p.strip() for p in s.split(',') if p.strip()])
        else:
            result.append(s)
    return result


def _get_filter_word_variants(term):
    """
    Produces clean, singular/plural variants for robust e-commerce matching.
    e.g. 'Gear' -> {'Gear', 'Gears'}, 'Gears' -> {'Gears', 'Gear'},
         'Accessories' -> {'Accessories', 'Accessory'}
    """
    clean = term.strip()
    variants = {clean}
    lower = clean.lower()
    if lower.endswith('ies') and len(clean) > 4:
        variants.add(clean[:-3] + 'y')
        variants.add(clean[:-3] + 'Y')
    elif lower.endswith('es') and len(clean) > 4:
        variants.add(clean[:-2])
    elif lower.endswith('s') and len(clean) > 3:
        variants.add(clean[:-1])
    else:
        variants.add(clean + 's')
        if lower.endswith('y'):
            variants.add(clean[:-1] + 'ies')
    return variants


def _build_smart_category_q(terms):
    """
    Builds a Q object for category / sub_category matching that:
    1. Checks sub_category__category__name (exact & icontains)
    2. Checks sub_category__name (exact & icontains)
    3. Handles singular/plural variants (Gear <-> Gears, Saddle <-> Saddles)
    4. Matches product name and model_name for specific category names
    """
    term_list = _normalize_filter_values(terms)
    if not term_list:
        return Q()

    combined_q = Q()
    for term in term_list:
        variants = _get_filter_word_variants(term)
        term_q = Q()
        for v in variants:
            term_q |= Q(sub_category__category__name__iexact=v)
            term_q |= Q(sub_category__name__iexact=v)
            term_q |= Q(sub_category__category__name__icontains=v)
            term_q |= Q(sub_category__name__icontains=v)
            if len(v) >= 4 and v.lower() not in ['spare', 'spares', 'accessory', 'accessories']:
                term_q |= Q(name__icontains=v)
                term_q |= Q(model_name__icontains=v)
        combined_q |= term_q
    return combined_q


def _build_smart_spec_q(field_name, values):
    """
    Builds a case-insensitive, partial-tolerant Q object for product specifications.
    Handles 'Tubeless Ready', '500ml', '500', '11 Speed', etc.
    """
    val_list = _normalize_filter_values(values)
    if not val_list:
        return Q()

    combined_q = Q()
    for val in val_list:
        combined_q |= Q(**{f"{field_name}__iexact": val})
        combined_q |= Q(**{f"{field_name}__icontains": val})
    return combined_q


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
        if not categories and value:
            categories = [value]
        q = _build_smart_category_q(categories)
        return queryset.filter(q) if q else queryset

    def filter_sub_category(self, queryset, name, value):
        sub_categories = self.request.GET.getlist("sub_category") if self.request else []
        if not sub_categories and value:
            sub_categories = [value]
        q = _build_smart_category_q(sub_categories)
        return queryset.filter(q) if q else queryset

    def filter_brand(self, queryset, name, value):
        brands = self.request.GET.getlist("brand") if self.request else []
        if not brands and value:
            brands = [value]
        brands = _normalize_filter_values(brands)
        if brands:
            brand_q = Q()
            for b in brands:
                brand_q |= Q(brand__brand_name__iexact=b) | Q(brand__brand_name__icontains=b)
            return queryset.filter(brand_q)
        return queryset

    def filter_special_tag(self, queryset, name, value):
        tags = self.request.GET.getlist("special_tag") if self.request else []
        if not tags and value:
            tags = [value]
        tags = _normalize_filter_values(tags)
        if tags:
            tag_q = Q()
            for t in tags:
                tag_q |= Q(special_tag__tag_name__iexact=t)
            return queryset.filter(tag_q)
        return queryset

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
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("model_no", vals)
        return queryset.filter(q) if q else queryset

    def filter_model_name(self, queryset, name, value):
        vals = self.request.GET.getlist("model_name") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("model_name", vals)
        return queryset.filter(q) if q else queryset

    def filter_speed(self, queryset, name, value):
        vals = self.request.GET.getlist("speed") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("speed", vals)
        return queryset.filter(q) if q else queryset

    def filter_tire_type(self, queryset, name, value):
        vals = self.request.GET.getlist("tire_type") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("tire_type", vals)
        return queryset.filter(q) if q else queryset

    def filter_hub_width(self, queryset, name, value):
        vals = self.request.GET.getlist("hub_width") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("hub_width", vals)
        return queryset.filter(q) if q else queryset

    def filter_valve_type(self, queryset, name, value):
        vals = self.request.GET.getlist("valve_type") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("valve_type", vals)
        return queryset.filter(q) if q else queryset

    def filter_size(self, queryset, name, value):
        vals = self.request.GET.getlist("size") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("size", vals)
        return queryset.filter(q) if q else queryset

    def filter_ml(self, queryset, name, value):
        vals = self.request.GET.getlist("ml") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("ml", vals)
        return queryset.filter(q) if q else queryset

    def filter_color(self, queryset, name, value):
        vals = self.request.GET.getlist("color") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("color", vals)
        return queryset.filter(q) if q else queryset

    def filter_bike_mounted_type(self, queryset, name, value):
        vals = self.request.GET.getlist("bike_mounted_type") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("bike_mounted_type", vals)
        return queryset.filter(q) if q else queryset

    def filter_material(self, queryset, name, value):
        vals = self.request.GET.getlist("material") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("material", vals)
        return queryset.filter(q) if q else queryset

    def filter_warranty(self, queryset, name, value):
        vals = self.request.GET.getlist("warranty") if self.request else []
        if not vals and value:
            vals = [value]
        q = _build_smart_spec_q("warranty", vals)
        return queryset.filter(q) if q else queryset

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
    brand = _normalize_filter_values(request.GET.getlist('brand') or request.GET.get('brand'))
    category = _normalize_filter_values(request.GET.getlist('category') or request.GET.get('category'))
    special_tag = _normalize_filter_values(request.GET.getlist('special_tag') or request.GET.get('special_tag'))
    wheel_size = _normalize_filter_values(request.GET.getlist('wheel_size') or request.GET.get('wheel_size'))
    material = _normalize_filter_values(request.GET.getlist('material') or request.GET.get('material'))
    suspension = _normalize_filter_values(request.GET.getlist('suspension') or request.GET.get('suspension'))
    rear_suspension_travel = _normalize_filter_values(request.GET.getlist('rear_suspension_travel') or request.GET.get('rear_suspension_travel'))
    color = _normalize_filter_values(request.GET.getlist('color') or request.GET.get('color'))
    size = _normalize_filter_values(request.GET.getlist('size') or request.GET.get('size'))
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    qs = BikeModel.objects.all()

    if name:
        qs = qs.filter(name__icontains=name)

    if brand:
        brand_q = Q()
        for b in brand:
            brand_q |= Q(brand__brand_name__iexact=b)
        qs = qs.filter(brand_q)

    if category:
        cat_q = Q()
        for c in category:
            cat_q |= Q(category__category_name__iexact=c)
        qs = qs.filter(cat_q)

    if special_tag:
        tag_q = Q()
        for t in special_tag:
            tag_q |= Q(special_tag__tag_name__iexact=t)
        qs = qs.filter(tag_q)

    if wheel_size:
        ws_q = Q()
        for ws in wheel_size:
            ws_q |= Q(wheel_size__wheel_size__iexact=ws)
        qs = qs.filter(ws_q)

    if material:
        mat_q = Q()
        for m in material:
            mat_q |= Q(material__material__iexact=m)
        qs = qs.filter(mat_q)

    if suspension:
        susp_q = Q()
        for s in suspension:
            susp_q |= Q(suspension__suspension__iexact=s)
        qs = qs.filter(susp_q)

    if rear_suspension_travel:
        rst_q = Q()
        for r in rear_suspension_travel:
            rst_q |= Q(rear_suspension_travel__rear_suspension_travel__iexact=r)
        qs = qs.filter(rst_q)

    if color:
        col_q = Q()
        for c in color:
            col_q |= Q(bike_colors__color__color_name__iexact=c)
        qs = qs.filter(col_q)

    if size:
        size_q = Q()
        for s in size:
            size_q |= Q(bike_sizes__bike_size__size__iexact=s) | Q(sizes__size__iexact=s)
        qs = qs.filter(size_q)

    if min_price:
        try:
            val = float(min_price)
            qs = qs.filter(
                Q(is_discount=True, discount_price__gte=val) |
                Q(is_discount=False, price__gte=val)
            )
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            val = float(max_price)
            qs = qs.filter(
                Q(is_discount=True, discount_price__lte=val) |
                Q(is_discount=False, price__lte=val)
            )
        except (ValueError, TypeError):
            pass

    # ✅ HARD DEDUPLICATION BY BIKE ID
    qs = qs.filter(
        id__in=Subquery(
            qs.values('id').distinct()
        )
    )

    return qs


def accessories_filters(request):
    name = request.GET.get('name')
    brand = _normalize_filter_values(request.GET.getlist('brand') or request.GET.get('brand'))
    category = _normalize_filter_values(request.GET.getlist('category') or request.GET.get('category'))
    sub_category = _normalize_filter_values(request.GET.getlist('sub_category') or request.GET.get('sub_category'))
    special_tag = _normalize_filter_values(request.GET.getlist('special_tag') or request.GET.get('special_tag'))

    # Specification Filter Attributes
    model_no = _normalize_filter_values(request.GET.getlist('model_no') or request.GET.get('model_no'))
    model_name = _normalize_filter_values(request.GET.getlist('model_name') or request.GET.get('model_name'))
    speed = _normalize_filter_values(request.GET.getlist('speed') or request.GET.get('speed'))
    tire_type = _normalize_filter_values(request.GET.getlist('tire_type') or request.GET.get('tire_type'))
    hub_width = _normalize_filter_values(request.GET.getlist('hub_width') or request.GET.get('hub_width'))
    valve_type = _normalize_filter_values(request.GET.getlist('valve_type') or request.GET.get('valve_type'))
    size = _normalize_filter_values(request.GET.getlist('size') or request.GET.get('size'))
    ml = _normalize_filter_values(request.GET.getlist('ml') or request.GET.get('ml'))
    color = _normalize_filter_values(request.GET.getlist('color') or request.GET.get('color'))
    bike_mounted_type = _normalize_filter_values(request.GET.getlist('bike_mounted_type') or request.GET.get('bike_mounted_type'))
    material = _normalize_filter_values(request.GET.getlist('material') or request.GET.get('material'))
    warranty = _normalize_filter_values(request.GET.getlist('warranty') or request.GET.get('warranty'))

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
        brand_q = Q()
        for b in brand:
            brand_q |= Q(brand__brand_name__iexact=b) | Q(brand__brand_name__icontains=b)
        queryset = queryset.filter(brand_q)

    if category:
        cat_q = _build_smart_category_q(category)
        if cat_q:
            queryset = queryset.filter(cat_q)

    if sub_category:
        subcat_q = _build_smart_category_q(sub_category)
        if subcat_q:
            queryset = queryset.filter(subcat_q)

    if model_no:
        q = _build_smart_spec_q('model_no', model_no)
        if q:
            queryset = queryset.filter(q)

    if model_name:
        q = _build_smart_spec_q('model_name', model_name)
        if q:
            queryset = queryset.filter(q)

    if speed:
        q = _build_smart_spec_q('speed', speed)
        if q:
            queryset = queryset.filter(q)

    if tire_type:
        q = _build_smart_spec_q('tire_type', tire_type)
        if q:
            queryset = queryset.filter(q)

    if hub_width:
        q = _build_smart_spec_q('hub_width', hub_width)
        if q:
            queryset = queryset.filter(q)

    if valve_type:
        q = _build_smart_spec_q('valve_type', valve_type)
        if q:
            queryset = queryset.filter(q)

    if size:
        q = _build_smart_spec_q('size', size)
        if q:
            queryset = queryset.filter(q)

    if ml:
        q = _build_smart_spec_q('ml', ml)
        if q:
            queryset = queryset.filter(q)

    if color:
        q = _build_smart_spec_q('color', color)
        if q:
            queryset = queryset.filter(q)

    if bike_mounted_type:
        q = _build_smart_spec_q('bike_mounted_type', bike_mounted_type)
        if q:
            queryset = queryset.filter(q)

    if material:
        q = _build_smart_spec_q('material', material)
        if q:
            queryset = queryset.filter(q)

    if warranty:
        q = _build_smart_spec_q('warranty', warranty)
        if q:
            queryset = queryset.filter(q)

    if special_tag:
        tag_q = Q()
        for t in special_tag:
            tag_q |= Q(special_tag__tag_name__iexact=t)
        queryset = queryset.filter(tag_q)

    if min_price:
        try:
            val = float(min_price)
            queryset = queryset.filter(
                Q(is_discount=True, discount_price__gte=val) |
                Q(is_discount=False, price__gte=val)
            )
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            val = float(max_price)
            queryset = queryset.filter(
                Q(is_discount=True, discount_price__lte=val) |
                Q(is_discount=False, price__lte=val)
            )
        except (ValueError, TypeError):
            pass

    return queryset
