# Boatrider Sports — Frontend Integration Guide: Price Range & Specifications Filter (Next.js)

> **Instruction for Frontend Developer / Next.js AI Assistant:**
> Implement the **Price Range (MRP Range) Slider & Specification Filters (e.g., `ml`, `brand`, etc.)** on the Spares & Accessories shopping page (`/shop/accessories`) in the Next.js application (`boatridersports-in.vercel.app`).
> 
> The backend already returns dynamic `price_range` / `mrp_range` bounds and specification values (such as `ml: ["50", "550"]`) from `/api/product/products-filter-side-bar/?sidebar=accessories`, and fully supports `min_price`, `max_price`, and `ml` query filtering on `/api/product/products-filtered/?type=accessories`.

---

## 1. Backend API Specification

### 1.1 Sidebar Metadata Endpoint
```http
GET https://server.boatridersports.in/api/product/products-filter-side-bar/?sidebar=accessories
```

#### Response Structure (Truncated for relevant fields):
```json
{
  "product_type": "accessories",
  "price_range": {
    "min_price": 749.0,
    "max_price": 136589.0
  },
  "mrp_range": {
    "min_price": 749.0,
    "max_price": 136589.0
  },
  "ml": [
    "50",
    "550"
  ],
  "brands": [
    "CATEYE",
    "SHIMANO",
    "Trek"
  ],
  "categories": [
    "Accessories",
    "Cassette & free Wheels",
    "Gear",
    "Lube",
    "Spares",
    "Wheels"
  ],
  "sub_categories": [
    "Bells & Horns",
    "Dry Lube",
    "Gears",
    "Lights & Reflectors",
    "Pedal Set",
    "Spares"
  ],
  "speeds": ["7/8", "11 Speed", "12 Speed"],
  "tire_types": ["Tubeless Ready", "Clincher"],
  "sizes": ["15 to 25 Lumina", "500 Lumina", "BSA"]
}
```

---

### 1.2 Filtered Products Endpoint
```http
GET https://server.boatridersports.in/api/product/products-filtered/?type=accessories&min_price=1000&max_price=5000&ml=550&page=1
```

#### Query Parameters:
| Parameter | Type | Required | Description | Example |
|---|---|---|---|---|
| `type` | string | **Yes** | Must always be `"accessories"` | `type=accessories` |
| `min_price` | number | No | Minimum price filter (evaluates `discount_price` if on sale, otherwise `price`) | `min_price=1000` |
| `max_price` | number | No | Maximum price filter | `max_price=5000` |
| `ml` | string / array | No | Liquid / bottle volume (e.g. water bottles, tubeless sealant, lubes) | `ml=550` or `ml=500ml` |
| `category` | string / array | No | Category name (supports multi-select & singular/plural matching) | `category=Accessories&category=Gear` |
| `sub_category` | string / array | No | Subcategory name | `sub_category=Gears` |
| `brand` | string / array | No | Brand name (case-insensitive) | `brand=SHIMANO` |
| `page` | number | No | Page number (default: `1`) | `page=1` |
| `page_size` | number | No | Page size (default: `15`, max: `100`) | `page_size=15` |

---

## 2. Next.js Component Architecture

```
components/
└── shop/
    ├── accessories/
    │   ├── AccessoriesFilterSidebar.tsx     <-- Main filter drawer / sidebar
    │   ├── PriceRangeFilter.tsx             <-- Dual-slider + Min/Max numeric inputs
    │   ├── MlVolumeFilter.tsx               <-- Quick pill / checkbox selector for ml
    │   ├── FilterSectionWrapper.tsx         <-- Collapsible accordion with counter
    │   └── ActiveFilterPills.tsx            <-- Chips at top with 'Clear All'
```

---

## 3. Implementation Code

### 3.1. Type Definitions (`types/accessoriesFilter.ts`)

```typescript
export interface PriceRangeData {
  min_price: number;
  max_price: number;
}

export interface AccessoriesSidebarData {
  product_type: string;
  price_range: PriceRangeData;
  mrp_range: PriceRangeData;
  ml: string[];
  brands: string[];
  categories: string[];
  sub_categories: string[];
  speeds?: string[];
  tire_types?: string[];
  sizes?: string[];
  colors?: string[];
  materials?: string[];
  warranties?: string[];
  special_tags?: string[];
}

export interface ActiveAccessoriesFilters {
  category: string[];
  sub_category: string[];
  brand: string[];
  min_price: number | null;
  max_price: number | null;
  ml: string[];
  speed: string[];
  tire_type: string[];
  size: string[];
  page: number;
}
```

---

### 3.2. Price Range Component (`components/shop/accessories/PriceRangeFilter.tsx`)

This component provides:
1. Dual-range visual sliders.
2. Direct numeric Min & Max inputs with currency symbol (`₹`).
3. 400ms debounce to prevent spamming the backend API on every pixel drag.
4. Auto-validation (`min_price <= max_price`).

```tsx
"use client";

import React, { useState, useEffect, useCallback } from "react";

interface PriceRangeFilterProps {
  serverMin: number;
  serverMax: number;
  currentMin: number | null;
  currentMax: number | null;
  onChange: (min: number | null, max: number | null) => void;
}

export const PriceRangeFilter: React.FC<PriceRangeFilterProps> = ({
  serverMin,
  serverMax,
  currentMin,
  currentMax,
  onChange,
}) => {
  const minLimit = Math.floor(serverMin || 0);
  const maxLimit = Math.ceil(serverMax || 150000);

  // Local state for smooth slider dragging
  const [localMin, setLocalMin] = useState<number>(currentMin ?? minLimit);
  const [localMax, setLocalMax] = useState<number>(currentMax ?? maxLimit);

  // Sync when props change (e.g. user resets filters or page reloads from URL)
  useEffect(() => {
    setLocalMin(currentMin ?? minLimit);
    setLocalMax(currentMax ?? maxLimit);
  }, [currentMin, currentMax, minLimit, maxLimit]);

  // Debounced notification to parent / URL
  useEffect(() => {
    const timer = setTimeout(() => {
      const isDefaultMin = localMin <= minLimit;
      const isDefaultMax = localMax >= maxLimit;

      onChange(
        isDefaultMin ? null : localMin,
        isDefaultMax ? null : localMax
      );
    }, 350);

    return () => clearTimeout(timer);
  }, [localMin, localMax, minLimit, maxLimit, onChange]);

  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (!isNaN(val) && val <= localMax) {
      setLocalMin(Math.max(minLimit, val));
    }
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (!isNaN(val) && val >= localMin) {
      setLocalMax(Math.min(maxLimit, val));
    }
  };

  // Percentage for track highlight
  const minPercent = Math.min(
    100,
    Math.max(0, ((localMin - minLimit) / (maxLimit - minLimit || 1)) * 100)
  );
  const maxPercent = Math.min(
    100,
    Math.max(0, ((localMax - minLimit) / (maxLimit - minLimit || 1)) * 100)
  );

  return (
    <div className="flex flex-col gap-4 py-3">
      {/* Visual Slider Bar */}
      <div className="relative w-full h-2 my-2">
        {/* Gray Background Track */}
        <div className="absolute w-full h-2 bg-gray-200 rounded-full" />
        
        {/* Red Active Track */}
        <div
          className="absolute h-2 bg-red-600 rounded-full"
          style={{ left: `${minPercent}%`, width: `${maxPercent - minPercent}%` }}
        />

        {/* Dual Native Range Inputs Overlay */}
        <input
          type="range"
          min={minLimit}
          max={maxLimit}
          step={100}
          value={localMin}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (v <= localMax - 100) setLocalMin(v);
          }}
          className="absolute pointer-events-none appearance-none w-full h-2 bg-transparent z-20 
                     [&::-webkit-slider-thumb]:pointer-events-auto 
                     [&::-webkit-slider-thumb]:appearance-none 
                     [&::-webkit-slider-thumb]:w-4 
                     [&::-webkit-slider-thumb]:h-4 
                     [&::-webkit-slider-thumb]:rounded-full 
                     [&::-webkit-slider-thumb]:bg-red-600 
                     [&::-webkit-slider-thumb]:border-2 
                     [&::-webkit-slider-thumb]:border-white 
                     [&::-webkit-slider-thumb]:shadow-md 
                     [&::-webkit-slider-thumb]:cursor-pointer"
        />
        <input
          type="range"
          min={minLimit}
          max={maxLimit}
          step={100}
          value={localMax}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (v >= localMin + 100) setLocalMax(v);
          }}
          className="absolute pointer-events-none appearance-none w-full h-2 bg-transparent z-20 
                     [&::-webkit-slider-thumb]:pointer-events-auto 
                     [&::-webkit-slider-thumb]:appearance-none 
                     [&::-webkit-slider-thumb]:w-4 
                     [&::-webkit-slider-thumb]:h-4 
                     [&::-webkit-slider-thumb]:rounded-full 
                     [&::-webkit-slider-thumb]:bg-red-600 
                     [&::-webkit-slider-thumb]:border-2 
                     [&::-webkit-slider-thumb]:border-white 
                     [&::-webkit-slider-thumb]:shadow-md 
                     [&::-webkit-slider-thumb]:cursor-pointer"
        />
      </div>

      {/* Numeric Min & Max Input Boxes */}
      <div className="flex items-center justify-between gap-3 text-sm">
        <div className="flex-1">
          <label className="text-xs text-gray-500 font-medium block mb-1">Min Price</label>
          <div className="relative flex items-center">
            <span className="absolute left-2.5 text-gray-500 text-xs font-semibold">₹</span>
            <input
              type="number"
              value={localMin}
              onChange={handleMinChange}
              className="w-full pl-6 pr-2 py-1.5 border border-gray-300 rounded-md text-xs font-medium focus:ring-1 focus:ring-red-500 focus:outline-none"
              placeholder={minLimit.toString()}
            />
          </div>
        </div>

        <span className="text-gray-400 mt-5 font-bold">-</span>

        <div className="flex-1">
          <label className="text-xs text-gray-500 font-medium block mb-1">Max Price</label>
          <div className="relative flex items-center">
            <span className="absolute left-2.5 text-gray-500 text-xs font-semibold">₹</span>
            <input
              type="number"
              value={localMax}
              onChange={handleMaxChange}
              className="w-full pl-6 pr-2 py-1.5 border border-gray-300 rounded-md text-xs font-medium focus:ring-1 focus:ring-red-500 focus:outline-none"
              placeholder={maxLimit.toString()}
            />
          </div>
        </div>
      </div>

      {/* Quick Action: Reset Price */}
      {(currentMin !== null || currentMax !== null) && (
        <button
          type="button"
          onClick={() => {
            setLocalMin(minLimit);
            setLocalMax(maxLimit);
            onChange(null, null);
          }}
          className="text-xs text-red-600 hover:text-red-700 underline text-right transition"
        >
          Reset price range
        </button>
      )}
    </div>
  );
};
```

---

### 3.3. Volume / Ml Filter Component (`components/shop/accessories/MlVolumeFilter.tsx`)

The user specifically highlighted `Ml: 550` (for water bottles, sealants, etc.). This component displays volume options as attractive interactive pills:

```tsx
"use client";

import React from "react";

interface MlVolumeFilterProps {
  availableMl: string[]; // e.g. ["50", "550", "500ml", "1L"]
  selectedMl: string[];
  onChange: (selected: string[]) => void;
}

export const MlVolumeFilter: React.FC<MlVolumeFilterProps> = ({
  availableMl,
  selectedMl,
  onChange,
}) => {
  if (!availableMl || availableMl.length === 0) return null;

  const toggleOption = (val: string) => {
    if (selectedMl.includes(val)) {
      onChange(selectedMl.filter((item) => item !== val));
    } else {
      onChange([...selectedMl, val]);
    }
  };

  // Helper to format "550" into "550 ml" if not already formatted
  const formatMlDisplay = (val: string) => {
    const lower = val.toLowerCase().trim();
    if (lower.endsWith("ml") || lower.endsWith("l")) return val;
    return `${val} ml`;
  };

  return (
    <div className="flex flex-wrap gap-2 py-2">
      {availableMl.map((mlVal) => {
        const isSelected = selectedMl.includes(mlVal);
        return (
          <button
            key={mlVal}
            type="button"
            onClick={() => toggleOption(mlVal)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all duration-150 ${
              isSelected
                ? "bg-red-600 border-red-600 text-white shadow-sm"
                : "bg-white border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50"
            }`}
          >
            {formatMlDisplay(mlVal)}
          </button>
        );
      })}
    </div>
  );
};
```

---

### 3.4. URL Query Builder Utility (`utils/accessoriesFilterUrl.ts`)

Ensures multi-select parameters and price range encode properly without losing values:

```typescript
export function buildAccessoriesQuery(
  filters: {
    category?: string[];
    sub_category?: string[];
    brand?: string[];
    min_price?: number | null;
    max_price?: number | null;
    ml?: string[];
    speed?: string[];
    tire_type?: string[];
    size?: string[];
    page?: number;
  }
): string {
  const params = new URLSearchParams();

  // Always specify product type
  params.set("type", "accessories");

  // Arrays: multiple keys (e.g. ?category=Gear&category=Accessories)
  filters.category?.forEach((c) => params.append("category", c));
  filters.sub_category?.forEach((sc) => params.append("sub_category", sc));
  filters.brand?.forEach((b) => params.append("brand", b));
  filters.ml?.forEach((m) => params.append("ml", m));
  filters.speed?.forEach((s) => params.append("speed", s));
  filters.tire_type?.forEach((t) => params.append("tire_type", t));
  filters.size?.forEach((sz) => params.append("size", sz));

  // Numeric Price Range
  if (filters.min_price != null) {
    params.set("min_price", filters.min_price.toString());
  }
  if (filters.max_price != null) {
    params.set("max_price", filters.max_price.toString());
  }

  // Pagination
  if (filters.page && filters.page > 1) {
    params.set("page", filters.page.toString());
  }

  return params.toString();
}
```

---

### 3.5. Integrating in Next.js Page Sidebar (`components/shop/accessories/AccessoriesFilterSidebar.tsx`)

```tsx
"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { PriceRangeFilter } from "./PriceRangeFilter";
import { MlVolumeFilter } from "./MlVolumeFilter";
import { AccessoriesSidebarData } from "@/types/accessoriesFilter";
import { buildAccessoriesQuery } from "@/utils/accessoriesFilterUrl";

export const AccessoriesFilterSidebar = () => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [sidebarData, setSidebarData] = useState<AccessoriesSidebarData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // 1. Fetch Sidebar Metadata from Backend
  useEffect(() => {
    async function fetchSidebar() {
      try {
        setLoading(true);
        const res = await fetch(
          "https://server.boatridersports.in/api/product/products-filter-side-bar/?sidebar=accessories"
        );
        if (res.ok) {
          const data: AccessoriesSidebarData = await res.json();
          setSidebarData(data);
        }
      } catch (err) {
        console.error("Failed to load filter sidebar data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSidebar();
  }, []);

  // 2. Read active filter values from URL searchParams
  const selectedCategories = searchParams.getAll("category");
  const selectedSubCategories = searchParams.getAll("sub_category");
  const selectedBrands = searchParams.getAll("brand");
  const selectedMl = searchParams.getAll("ml");

  const minPriceParam = searchParams.get("min_price");
  const maxPriceParam = searchParams.get("max_price");
  const currentMinPrice = minPriceParam ? Number(minPriceParam) : null;
  const currentMaxPrice = maxPriceParam ? Number(maxPriceParam) : null;

  // 3. Helper to update URL
  const updateUrl = (updated: Parameters<typeof buildAccessoriesQuery>[0]) => {
    const queryString = buildAccessoriesQuery({
      category: selectedCategories,
      sub_category: selectedSubCategories,
      brand: selectedBrands,
      ml: selectedMl,
      min_price: currentMinPrice,
      max_price: currentMaxPrice,
      ...updated,
      page: 1, // Reset to page 1 on filter change
    });
    router.push(`${pathname}?${queryString}`, { scroll: false });
  };

  const handlePriceChange = (min: number | null, max: number | null) => {
    updateUrl({ min_price: min, max_price: max });
  };

  const handleMlChange = (mlList: string[]) => {
    updateUrl({ ml: mlList });
  };

  const clearAllFilters = () => {
    router.push(`${pathname}?type=accessories`, { scroll: false });
  };

  const hasActiveFilters =
    selectedCategories.length > 0 ||
    selectedSubCategories.length > 0 ||
    selectedBrands.length > 0 ||
    selectedMl.length > 0 ||
    currentMinPrice !== null ||
    currentMaxPrice !== null;

  if (loading || !sidebarData) {
    return (
      <div className="p-4 space-y-4 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/2"></div>
        <div className="h-24 bg-gray-200 rounded"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  const serverMin = sidebarData.price_range?.min_price ?? sidebarData.mrp_range?.min_price ?? 0;
  const serverMax = sidebarData.price_range?.max_price ?? sidebarData.mrp_range?.max_price ?? 150000;

  return (
    <aside className="w-full md:w-64 bg-white p-4 border-r border-gray-200">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100">
        <h3 className="font-bold text-gray-900 text-base">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="text-xs text-red-600 hover:text-red-700 font-semibold transition"
          >
            Clear All
          </button>
        )}
      </div>

      {/* 🔹 PRICE RANGE FILTER */}
      <div className="py-4 border-b border-gray-100">
        <h4 className="font-semibold text-gray-800 text-sm mb-1">Price Range</h4>
        <PriceRangeFilter
          serverMin={serverMin}
          serverMax={serverMax}
          currentMin={currentMinPrice}
          currentMax={currentMaxPrice}
          onChange={handlePriceChange}
        />
      </div>

      {/* 🔹 VOLUME / ML FILTER (Only renders if products have ml values) */}
      {sidebarData.ml && sidebarData.ml.length > 0 && (
        <div className="py-4 border-b border-gray-100">
          <h4 className="font-semibold text-gray-800 text-sm mb-1">Capacity / Volume (ml)</h4>
          <MlVolumeFilter
            availableMl={sidebarData.ml}
            selectedMl={selectedMl}
            onChange={handleMlChange}
          />
        </div>
      )}

      {/* 🔹 CATEGORIES ACCORDION (Already in place) */}
      {/* ...existing category checkboxes... */}

      {/* 🔹 SUB CATEGORIES ACCORDION (Already in place) */}
      {/* ...existing subcategory checkboxes... */}
    </aside>
  );
};
```

---

## 4. Testing & Verification Checklist

1. **Verify Price Filter:**
   - Slide minimum price to `₹2,000` and max to `₹10,000`.
   - Ensure URL updates to: `?type=accessories&min_price=2000&max_price=10000`.
   - Verify product grid updates to show only items priced within range (including items on discount price).

2. **Verify Ml Filter:**
   - Click the `550 ml` pill (e.g. for Lidl-Trek Team Water Bottle).
   - Ensure URL updates to: `?type=accessories&ml=550`.
   - Verify bottle appears in the grid.

3. **Verify Combined Filter:**
   - Check `Accessories` category, `Gears` subcategory, and set `max_price=5000`.
   - Ensure query `?type=accessories&category=Accessories&sub_category=Gears&max_price=5000` returns the gear sprocket and accessories under ₹5,000.
