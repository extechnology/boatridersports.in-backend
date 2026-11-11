# Boatrider Sports — Frontend Integration Guide: Spares & Accessories Filter System

> **Instruction for Frontend Developer / Next.js AI Agent:**
> Implement the updated **Spares & Accessories Filter System** on `boatridersports.in`.
> The backend has been upgraded with **16 comprehensive filter segments** for spares and accessories, with dynamic filter discovery, multi-select filtering, price range sliding, and search matching.
>
> ⚠️ **Note on Field Optionality:** Not every accessory possesses all 16 fields (e.g., a tubeless sealant specifies `ml`, a chain specifies `speed`, a tire specifies `tire_type` and `size`, a light specifies `bike_mounted_type`). The filter sidebar dynamically surfaces only options that actually exist in the product catalog.

---

## 1. System Overview & Endpoints

- **Backend Base URL:** `https://server.boatridersports.in/api` (or local `http://localhost:8000/api`)
- **Key Endpoints:**
  1. **Get Filter Sidebar Options:**  
     `GET /api/product/products-filter-side-bar/?sidebar=accessories`
  2. **Get Filtered Accessories List (Paginated):**  
     `GET /api/product/products-filtered/?type=accessories&...`
  3. **Get Accessory Details:**  
     `GET /api/product/product-detail-page/accessories/<unique_id_or_id>/`

---

## 2. Filter Segments Specification (16 Segments)

| # | Filter Segment | Sidebar Response Key | Query Param Name | Type / UI Control | Example Values |
|---|---|---|---|---|---|
| 1 | **Brand** | `brands` | `brand` | Multi-select Checkboxes | `["Shimano", "SRAM", "Fox", "Maxxis"]` |
| 2 | **Category** | `categories` | `category` | Multi-select / Radio | `["Spares", "Accessories", "Apparel"]` |
| 3 | **Sub Category** | `sub_categories` | `sub_category` | Multi-select Checkboxes | `["Chains", "Cassettes", "Tires", "Pumps", "Bottles"]` |
| 4 | **Model No.** | `model_numbers` | `model_no` | Search / Dropdown | `["RD-M8100", "CN-M7100", "PD-M520"]` |
| 5 | **Model Name** | `model_names` | `model_name` | Dropdown / Checkboxes | `["Deore XT", "GX Eagle", "Minion DHF"]` |
| 6 | **Speed** | `speeds` | `speed` | Multi-select Pills / Checkboxes | `["12 Speed", "11 Speed", "10 Speed", "Single Speed"]` |
| 7 | **Tire Type** | `tire_types` | `tire_type` | Multi-select Checkboxes | `["Tubeless Ready", "Clincher", "Tubular", "Folding Bead"]` |
| 8 | **Hub Width** | `hub_widths` | `hub_width` | Multi-select Checkboxes | `["148mm Boost", "142mm", "135mm", "100mm", "110mm Boost"]` |
| 9 | **Valve Type** | `valve_types` | `valve_type` | Multi-select Pills | `["Presta", "Schrader", "Dunlop"]` |
| 10 | **Size** | `sizes` | `size` | Multi-select Pills / Badges | `["29x2.40", "700x28c", "S", "M", "L", "XL", "31.8mm"]` |
| 11 | **Ml** | `ml` | `ml` | Multi-select Pills | `["100ml", "120ml", "250ml", "500ml", "1L"]` |
| 12 | **Color** | `colors` | `color` | Color Swatches / Checkboxes | `["Black", "Red", "Silver", "Matte Grey"]` |
| 13 | **Bike Mounted Type** | `bike_mounted_types` | `bike_mounted_type` | Multi-select Checkboxes | `["Handlebar", "Frame", "Saddle", "Seatpost", "Fork"]` |
| 14 | **Material** | `materials` | `material` | Multi-select Checkboxes | `["Alloy", "Carbon", "Steel", "Plastic", "Silicone"]` |
| 15 | **Warranty** | `warranties` | `warranty` | Dropdown / Badges | `["6 Months", "1 Year", "2 Years", "Lifetime"]` |
| 16 | **MRP Range** | `mrp_range` | `min_price`, `max_price` | Dual Range Slider | `min_price=500&max_price=15000` |

---

## 3. API Contract & Payload Examples

### 3.1. Fetching Filter Sidebar (`GET /api/product/products-filter-side-bar/?sidebar=accessories`)

#### Response `200 OK`:
```json
{
  "product_type": "accessories",
  "brands": ["Fox", "Muc-Off", "Park Tool", "Shimano", "SRAM", "Stan's NoTubes"],
  "categories": ["Components & Spares", "Maintenance & Care", "Rider Accessories"],
  "sub_categories": ["Cassettes", "Chains", "Cleaners & Lubes", "Hydration", "Pedals", "Tires & Tubes"],
  "model_numbers": ["CN-M7100", "CN-M8100", "PD-M520", "RD-M8100-SGS", "ST0070"],
  "model_names": ["Deore XT", "GX Eagle", "Minion DHF", "Race Sealant"],
  "speeds": ["10 Speed", "11 Speed", "12 Speed", "Single Speed"],
  "tire_types": ["Clincher", "Folding Bead", "Tubeless Ready", "Wire Bead"],
  "hub_widths": ["100mm", "110mm Boost", "135mm", "142mm", "148mm Boost"],
  "valve_types": ["Dunlop", "Presta", "Schrader"],
  "sizes": ["126 Links", "27.5x2.35", "29x2.40", "700x28c", "EU 42", "L", "M", "S", "XL"],
  "ml": ["100ml", "120ml", "250ml", "500ml", "750ml", "1L"],
  "colors": ["Black", "Matte Grey", "Orange", "Red", "Silver", "White"],
  "bike_mounted_types": ["Direct Mount", "Fork", "Frame", "Handlebar", "Saddle", "Seatpost"],
  "materials": ["Alloy / Aluminium", "Carbon", "Composite", "Plastic", "Silicone", "Steel"],
  "warranties": ["6 Months", "1 Year", "2 Years", "3 Years", "Lifetime"],
  "mrp_range": {
    "min_price": 250.0,
    "max_price": 28500.0
  },
  "special_tags": ["Bestseller", "New Arrival", "Pro Choice"]
}
```

---

### 3.2. Fetching Filtered Accessories (`GET /api/product/products-filtered/?type=accessories&...`)

#### Query Parameter Rules:
- **Multiple Values for Same Key:** Send repeating query parameters:  
  `?type=accessories&brand=Shimano&brand=SRAM&speed=12+Speed&speed=11+Speed`
- **Text Search:** Filter by query string `name`:  
  `?type=accessories&name=Chain` (searches `name`, `model_name`, `model_no`, and `description`)
- **Price Range:**  
  `?type=accessories&min_price=1000&max_price=8000`
- **Pagination:**  
  `?type=accessories&page=1&page_size=15`

#### Sample Request:
```http
GET /api/product/products-filtered/?type=accessories&brand=Shimano&category=Components+%26+Spares&speed=12+Speed&min_price=2000&max_price=10000 HTTP/1.1
Host: server.boatridersports.in
```

#### Response `200 OK`:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 19,
      "unique_id": "a93fc660-3122-4a0f-90be-d2eb4b238381",
      "product_type": "accessories",
      "name": "Shimano XT M8100 12-Speed Chain",
      "model_name": "Deore XT",
      "model_no": "CN-M8100",
      "category": "Components & Spares",
      "sub_category": "Chains",
      "brand": "Shimano",
      "description": "High performance 12-speed chain with quick link and SIL-TEC chromizing treatment.",
      "special_tag": "Bestseller",
      "speed": "12 Speed",
      "tire_type": null,
      "hub_width": null,
      "valve_type": null,
      "size": "126 Links",
      "ml": null,
      "color": "Silver",
      "bike_mounted_type": null,
      "material": "Alloy Steel / SIL-TEC",
      "warranty": "2 Years",
      "price": "3500.00",
      "stock": 15,
      "is_available": true,
      "is_out_of_stock": false,
      "is_discount": true,
      "discount_price": "3150.00",
      "discount_percentage": "10.00",
      "accessory_images": [
        {
          "id": 24,
          "image": "https://server.boatridersports.in/media/accessory_images/cn-m8100-main.jpg"
        }
      ],
      "is_dark": false,
      "online_purchase_enabled": true,
      "shipping_charge": "0.00",
      "created": "2026-11-11T17:01:00Z"
    }
  ]
}
```

---

## 4. TypeScript Definitions

```typescript
// types/accessories.ts

export interface AccessoryImage {
  id: number;
  image: string;
}

export interface AccessoryItem {
  id: number;
  unique_id: string;
  product_type: 'accessories';
  name: string;
  model_name?: string | null;
  model_no?: string | null;
  category: string;
  sub_category: string;
  brand?: string | null;
  description: string;
  special_tag?: string | null;
  
  // Specific Filter / Spec Attributes
  speed?: string | null;
  tire_type?: string | null;
  hub_width?: string | null;
  valve_type?: string | null;
  size?: string | null;
  ml?: string | null;
  color?: string | null;
  bike_mounted_type?: string | null;
  material?: string | null;
  warranty?: string | null;

  // Pricing & Stock
  price: string;
  stock: number;
  is_available: boolean;
  is_out_of_stock: boolean;
  is_discount: boolean;
  discount_price: string;
  discount_percentage: string;
  
  // Media & Settings
  accessory_images: AccessoryImage[];
  is_dark: boolean;
  online_purchase_enabled: boolean;
  shipping_charge: string;
  created: string;
}

export interface AccessoriesFilterSidebarData {
  product_type: 'accessories';
  brands: string[];
  categories: string[];
  sub_categories: string[];
  model_numbers: string[];
  model_names: string[];
  speeds: string[];
  tire_types: string[];
  hub_widths: string[];
  valve_types: string[];
  sizes: string[];
  ml: string[];
  colors: string[];
  bike_mounted_types: string[];
  materials: string[];
  warranties: string[];
  mrp_range: {
    min_price: number;
    max_price: number;
  };
  special_tags: string[];
}

export interface AccessoriesActiveFilterState {
  search: string;
  brand: string[];
  category: string[];
  sub_category: string[];
  model_no: string[];
  model_name: string[];
  speed: string[];
  tire_type: string[];
  hub_width: string[];
  valve_type: string[];
  size: string[];
  ml: string[];
  color: string[];
  bike_mounted_type: string[];
  material: string[];
  warranty: string[];
  special_tag: string[];
  min_price?: number;
  max_price?: number;
}
```

---

## 5. Next.js Frontend Implementation Guide

### 5.1. Building Query String Utility
Use this utility to construct the exact URL for the API with repeating array keys:

```typescript
// utils/buildAccessoriesFilterQuery.ts
import { AccessoriesActiveFilterState } from '@/types/accessories';

export function buildAccessoriesFilterQuery(filters: AccessoriesActiveFilterState, page: number = 1): string {
  const params = new URLSearchParams();
  params.append('type', 'accessories');
  params.append('page', page.toString());

  if (filters.search?.trim()) {
    params.append('name', filters.search.trim());
  }

  // Multi-select array parameters
  const arrayKeys: (keyof AccessoriesActiveFilterState)[] = [
    'brand',
    'category',
    'sub_category',
    'model_no',
    'model_name',
    'speed',
    'tire_type',
    'hub_width',
    'valve_type',
    'size',
    'ml',
    'color',
    'bike_mounted_type',
    'material',
    'warranty',
    'special_tag',
  ];

  arrayKeys.forEach((key) => {
    const values = filters[key];
    if (Array.isArray(values)) {
      values.forEach((val) => {
        if (val) params.append(key, val);
      });
    }
  });

  if (typeof filters.min_price === 'number') {
    params.append('min_price', filters.min_price.toString());
  }
  if (typeof filters.max_price === 'number') {
    params.append('max_price', filters.max_price.toString());
  }

  return params.toString();
}
```

---

### 5.2. Filter Sidebar Accordion Layout
Organize the 16 filter segments into logical, collapsible groups for clean UX:

```tsx
// Suggested UI Accordion Structure
1. Brand & Categories
   - Brand (Multi-select Checkboxes with search)
   - Category (Pills / Radio)
   - Sub Category (Multi-select Checkboxes)

2. Model Identifiers
   - Model Name (e.g. Deore XT, GX Eagle)
   - Model No. (e.g. RD-M8100, CN-M7100)

3. Drivetrain & Wheels Specs
   - Speed (e.g. 12 Speed, 11 Speed, Single Speed)
   - Tire Type (e.g. Tubeless Ready, Clincher, Folding Bead)
   - Hub Width (e.g. 148mm Boost, 142mm, 100mm)
   - Valve Type (e.g. Presta, Schrader)

4. Physical & Sizing Specs
   - Size (Pills: S, M, L, XL, 29x2.4, 700x28c)
   - Volume / Ml (Pills: 100ml, 250ml, 500ml, 1L)
   - Color (Color chips / Checkboxes)
   - Material (e.g. Alloy, Carbon, Steel, Composite)
   - Bike Mounted Type (e.g. Handlebar, Frame, Saddle)

5. Warranty & Price Range
   - Warranty (e.g. 1 Year, 2 Years, Lifetime)
   - MRP Range (Dual Slider: Min Price — Max Price)
```

---

### 5.3. Displaying Badges on Product Cards
When rendering an accessory card in the product grid, display the relevant attributes if present:

```tsx
// components/AccessoryCard.tsx
export const AccessoryCard = ({ product }: { product: AccessoryItem }) => {
  const displayPrice = product.is_discount ? product.discount_price : product.price;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition p-4 flex flex-col justify-between">
      <div>
        {/* Brand & Special Tag */}
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            {product.brand || product.sub_category}
          </span>
          {product.special_tag && (
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-50 text-red-600">
              {product.special_tag}
            </span>
          )}
        </div>

        {/* Thumbnail Image */}
        <div className="relative aspect-square w-full mb-3 bg-gray-50 rounded-lg overflow-hidden flex items-center justify-center">
          <img
            src={product.accessory_images[0]?.image || '/placeholder-accessory.png'}
            alt={product.name}
            className="object-contain w-full h-full p-2"
          />
        </div>

        {/* Product Title & Model No */}
        <h3 className="font-semibold text-gray-900 text-sm line-clamp-2 leading-snug mb-1">
          {product.name}
        </h3>
        {product.model_no && (
          <p className="text-[11px] text-gray-400 font-mono mb-2">
            Model: {product.model_no}
          </p>
        )}

        {/* Dynamic Attribute Chips (show whichever exist) */}
        <div className="flex flex-wrap gap-1 mb-3">
          {product.speed && (
            <span className="text-[10px] bg-blue-50 text-blue-700 font-medium px-2 py-0.5 rounded">
              {product.speed}
            </span>
          )}
          {product.tire_type && (
            <span className="text-[10px] bg-emerald-50 text-emerald-700 font-medium px-2 py-0.5 rounded">
              {product.tire_type}
            </span>
          )}
          {product.ml && (
            <span className="text-[10px] bg-purple-50 text-purple-700 font-medium px-2 py-0.5 rounded">
              {product.ml}
            </span>
          )}
          {product.size && (
            <span className="text-[10px] bg-gray-100 text-gray-700 font-medium px-2 py-0.5 rounded">
              {product.size}
            </span>
          )}
          {product.material && (
            <span className="text-[10px] bg-amber-50 text-amber-800 font-medium px-2 py-0.5 rounded">
              {product.material}
            </span>
          )}
        </div>
      </div>

      {/* Pricing & Availability */}
      <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
        <div>
          <span className="text-base font-bold text-gray-900">₹{displayPrice}</span>
          {product.is_discount && (
            <span className="text-xs text-gray-400 line-through ml-2">₹{product.price}</span>
          )}
        </div>

        {product.is_out_of_stock ? (
          <span className="text-xs font-semibold text-red-500">Out of Stock</span>
        ) : (
          <button className="text-xs font-medium bg-black text-white px-3 py-1.5 rounded-lg hover:bg-gray-800 transition">
            Add to Cart
          </button>
        )}
      </div>
    </div>
  );
};
```

---

## 6. Verification Checklist for Frontend

1. **Sidebar API Call:** Verify `GET /api/product/products-filter-side-bar/?sidebar=accessories` loads all non-empty filter options.
2. **Filters URL Sync:** Verify checking/unchecking filters appends/removes the appropriate query params from the URL.
3. **Empty Filter Handling:** If a filter category (e.g. `ml` or `valve_types`) has 0 items in the catalog, either collapse or hide its accordion section.
4. **Active Filter Tags:** Render dismissible pills at the top of the product grid for each active filter (e.g. `[12 Speed ✕]`, `[Shimano ✕]`, `[₹1000 - ₹5000 ✕]`) with a "Clear All" button.
5. **Pagination Reset:** Ensure changing any filter resets current page to `page=1`.

