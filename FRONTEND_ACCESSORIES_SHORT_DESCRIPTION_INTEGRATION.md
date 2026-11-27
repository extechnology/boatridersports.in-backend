# Boatrider Sports — Frontend Integration Guide: Accessories `short_description`

> **Instruction for Frontend Developer / Next.js AI Agent:**
> The backend has been updated to include a `short_description` field for all accessories in the product catalog.
> Follow this guide to update your TypeScript types, Product Detail Page, Product Cards, MegaMenu, and SEO metadata.

---

## 1. Overview & Endpoints

The `short_description` attribute is an optional text field (`string | null`) designed for product subtitles, summary taglines, card excerpts, and SEO descriptions.

It is now included in all accessory API responses:

| # | Endpoint | Method | Location in Response |
|---|---|---|---|
| 1 | `/api/product/product-detail-page/accessories/<id_or_unique_id>/` | `GET` | Root of accessory object: `data.short_description` |
| 2 | `/api/product/products-filtered/?type=accessories` | `GET` | Each item in `data.results[].short_description` |
| 3 | `/api/product/navbar-items/` | `GET` | Each item in `data.accessories[].items[].short_description` |

---

## 2. API Response Payload Examples

### 2.1. Accessory Detail Page (`GET /api/product/product-detail-page/accessories/<unique_id>/`)

```json
{
  "id": 20,
  "unique_id": "716b01ad-61a2-4978-a4c1-1066f5181905",
  "product_type": "accessories",
  "name": "Stan's NoTubes Tubeless Sealant",
  "model_name": null,
  "model_no": "ST0070",
  "short_description": "High performance sealant for tubeless setups.",
  "description": "Premium liquid latex tire sealant engineered to seal punctures up to 6.5mm rapidly...",
  "category": "Spares",
  "sub_category": "Cassettes & Chains",
  "brand": "Stan's NoTubes",
  "special_tag": "Bestseller",
  "speed": null,
  "tire_type": "Tubeless Ready",
  "hub_width": null,
  "valve_type": "Presta",
  "size": null,
  "ml": "500ml",
  "color": null,
  "bike_mounted_type": null,
  "material": null,
  "warranty": "2 Years",
  "price": "1200.00",
  "stock": 25,
  "is_available": true,
  "is_out_of_stock": false,
  "is_discount": false,
  "discount_price": "0.00",
  "discount_percentage": "0.00",
  "accessory_images": [
    "https://server.boatridersports.in/media/accessory_images/sealant_front.jpg"
  ],
  "is_dark": false,
  "online_purchase_enabled": true,
  "shipping_charge": "0.00",
  "created": "2026-11-24T14:06:55.123Z"
}
```

### 2.2. Filtered Accessories List (`GET /api/product/products-filtered/?type=accessories`)

```json
{
  "count": 18,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 20,
      "unique_id": "716b01ad-61a2-4978-a4c1-1066f5181905",
      "product_type": "accessories",
      "name": "Stan's NoTubes Tubeless Sealant",
      "model_name": null,
      "model_no": "ST0070",
      "short_description": "High performance sealant for tubeless setups.",
      "category": "Spares",
      "sub_category": "Cassettes & Chains",
      "brand": "Stan's NoTubes",
      "price": "1200.00",
      "is_discount": false,
      "discount_price": "0.00",
      "discount_percentage": "0.00",
      "accessory_images": [ ... ]
    }
  ]
}
```

### 2.3. Navbar Items (`GET /api/product/navbar-items/`)

```json
{
  "bikes": [ ... ],
  "accessories": [
    {
      "title": "Spares",
      "image": "https://server.boatridersports.in/media/...",
      "items": [
        {
          "unique_id": "716b01ad-61a2-4978-a4c1-1066f5181905",
          "product_type": "accessories",
          "name": "Stan's NoTubes Tubeless Sealant",
          "short_description": "High performance sealant for tubeless setups.",
          "category": "Spares",
          "sub_category": "Cassettes & Chains",
          "price": "1200.00",
          "brand": "Stan's NoTubes",
          "is_discount": false,
          "discount_price": "0.00",
          "discount_percentage": "0.00"
        }
      ]
    }
  ]
}
```

---

## 3. TypeScript Type Definition

Update your shared accessories type definition (e.g. `src/types/accessories.ts` or `src/types/product.ts`):

```typescript
export interface AccessoryItem {
  id: number;
  unique_id: string;
  product_type: 'accessories';
  name: string;
  model_name?: string | null;
  model_no?: string | null;
  
  // 🔹 New field:
  short_description?: string | null;
  
  description: string;
  category: string;
  sub_category: string;
  brand?: string | null;
  special_tag?: string | null;

  // Technical Specifications
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

  // Pricing & Inventory
  price: string;
  stock: number;
  is_available: boolean;
  is_out_of_stock: boolean;
  is_discount: boolean;
  discount_price: string;
  discount_percentage: string;

  // Media & Settings
  accessory_images: { id?: number; image: string }[] | string[];
  is_dark?: boolean;
  online_purchase_enabled?: boolean;
  shipping_charge?: string;
  created?: string;
}
```

---

## 4. UI Implementation Examples

### 4.1. Product Detail Page (`src/app/product/[id]/page.tsx`)

Render `short_description` right beneath the product title / brand as a subtitle before the price or specifications:

```tsx
import React from 'react';
import { AccessoryItem } from '@/types/accessories';

interface ProductHeaderProps {
  product: AccessoryItem;
}

export const AccessoryHeader: React.FC<ProductHeaderProps> = ({ product }) => {
  return (
    <div className="space-y-2">
      {/* Brand & Special Tag */}
      {product.brand && (
        <span className="text-xs uppercase tracking-wider text-red-500 font-semibold">
          {product.brand}
        </span>
      )}

      {/* Main Title */}
      <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
        {product.name}
      </h1>

      {/* 🔹 Short Description / Subtitle */}
      {product.short_description && (
        <p className="text-sm md:text-base text-zinc-400 font-normal leading-relaxed pt-1">
          {product.short_description}
        </p>
      )}

      {/* Price */}
      <div className="flex items-baseline gap-3 pt-2">
        <span className="text-2xl font-bold text-white">
          ₹{product.is_discount ? product.discount_price : product.price}
        </span>
        {product.is_discount && (
          <span className="text-base text-zinc-500 line-through">
            ₹{product.price}
          </span>
        )}
      </div>
    </div>
  );
};
```

---

### 4.2. Product Card / Grid Item (`src/components/common/ProductCard.tsx`)

If your product card has room for an excerpt, render `short_description` with a 2-line clamp:

```tsx
{product.short_description && (
  <p className="text-xs text-zinc-400 line-clamp-2 mt-1 leading-normal">
    {product.short_description}
  </p>
)}
```

---

### 4.3. MegaMenu Item Excerpt (`src/components/common/MegaMenu.tsx`)

Inside the MegaMenu dropdown when previewing products:

```tsx
<div className="p-3">
  <h4 className="text-sm font-medium text-white truncate">{item.name}</h4>
  {item.short_description && (
    <p className="text-xs text-zinc-400 line-clamp-1 mt-0.5">
      {item.short_description}
    </p>
  )}
  <p className="text-sm font-semibold text-red-500 mt-1">₹{item.price}</p>
</div>
```

---

### 4.4. SEO & OpenGraph Meta Tags (`generateMetadata`)

In Next.js App Router:

```tsx
export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const product = await fetchAccessory(params.id);
  const metaDescription = product.short_description || product.description.slice(0, 160);

  return {
    title: `${product.name} | Boatrider Sports`,
    description: metaDescription,
    openGraph: {
      title: product.name,
      description: metaDescription,
      images: product.accessory_images?.[0] ? [product.accessory_images[0]] : [],
    },
  };
}
```

---

## 5. Notes & Verification Checklist

- [ ] **Optional Field Safety**: Always use conditional rendering (`{product.short_description && ...}`) since some older items may not yet have a short description.
- [ ] **Search Synchronization**: The backend search query parameter (`?name=keyword`) automatically searches across `name`, `model_name`, `model_no`, `description`, and `short_description`.
- [ ] **Admin Form**: The `short_description` field is now directly editable in the Django Admin for every accessory.
