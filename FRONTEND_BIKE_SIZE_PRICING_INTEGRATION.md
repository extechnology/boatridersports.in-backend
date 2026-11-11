# Boatrider Sports — Frontend Implementation Prompt: Bike Size-Specific Pricing & Stock

> **Instruction for Frontend Developer / AI Agent:**  
> Implement and update the **Bike Product Details Page (PDP)**, **Product Cards / Catalog Listing**, and **Cart Drawer / Cart Page** in the Boatrider Sports frontend (Next.js / React / Tailwind CSS).  
> The backend has been upgraded so that **each bike size variant has its own independent price, discount price, discount percentage, and stock quantity** (`bike_sizes`). When users switch between sizes, the price and stock availability must update dynamically in real time.

---

## 1. System Overview & Backend API Updates

### 1.1. Bike Detail Endpoint: `GET /api/products/get-product/?type=bike&id=<unique_id>`
The bike response now provides `bike_sizes` alongside the backwards-compatible `sizes` array:

```json
{
  "unique_id": "8f8b5e2a-14d2-43bb-a87a-62df7bc81001",
  "name": "Trek Domane AL 2 Disc",
  "product_type": "bike",
  "brand": "Trek",
  "category": "Road Bikes",
  "price": "95000.00",
  "is_discount": true,
  "discount_price": "89000.00",
  "discount_percentage": "6.32",
  "stock": 10,
  "is_available": true,
  "is_out_of_stock": false,

  "sizes": ["S", "M", "L", "XL"],

  "bike_sizes": [
    {
      "id": 101,
      "size_id": 1,
      "size": "S",
      "price": "95000.00",
      "stock": 4,
      "is_available": true,
      "is_out_of_stock": false,
      "is_discount": true,
      "discount_price": "89000.00",
      "discount_percentage": "6.32"
    },
    {
      "id": 102,
      "size_id": 2,
      "size": "M",
      "price": "98000.00",
      "stock": 3,
      "is_available": true,
      "is_out_of_stock": false,
      "is_discount": false,
      "discount_price": "0.00",
      "discount_percentage": "0.00"
    },
    {
      "id": 103,
      "size_id": 3,
      "size": "L",
      "price": "102000.00",
      "stock": 0,
      "is_available": false,
      "is_out_of_stock": true,
      "is_discount": false,
      "discount_price": "0.00",
      "discount_percentage": "0.00"
    },
    {
      "id": 104,
      "size_id": 4,
      "size": "XL",
      "price": "105000.00",
      "stock": 2,
      "is_available": true,
      "is_out_of_stock": false,
      "is_discount": true,
      "discount_price": "99000.00",
      "discount_percentage": "5.71"
    }
  ]
}
```

### 1.2. Cart Item Endpoint: `GET /api/user-cart/`
Each bike item in `user_cart_bike_items` now returns dynamic size-pricing attributes:

```json
{
  "id": 55,
  "bike": { "name": "Trek Domane AL 2 Disc", ... },
  "size": { "size": "XL" },
  "color": { ... },
  "quantity": 1,
  "size_price": "105000.00",
  "size_discount_price": "99000.00",
  "effective_price": "99000.00"
}
```

---

## 2. TypeScript Data Interfaces

Update your TypeScript definitions (e.g. `types/product.ts` and `types/cart.ts`):

```typescript
// types/product.ts

export interface BikeSizeVariant {
  id: number;
  size_id: number;
  size: string; // e.g. "S", "M", "52cm"
  price: string | number; // base price for this size
  stock: number;
  is_available: boolean;
  is_out_of_stock: boolean;
  is_discount: boolean;
  discount_price: string | number;
  discount_percentage: string | number;
}

export interface BikeProduct {
  id: number;
  unique_id: string;
  name: string;
  product_type: 'bike';
  brand: string;
  category: string;
  price: string | number;
  stock: number;
  is_available: boolean;
  is_out_of_stock: boolean;
  is_discount: boolean;
  discount_price: string | number;
  discount_percentage: string | number;

  sizes: string[]; // List of size strings e.g. ["S", "M", "L"]
  bike_sizes?: BikeSizeVariant[]; // Detailed size variants with pricing & stock

  bike_colors: any[];
  featured_image?: string;
  images?: string[];
  description: string;
  // ... other existing fields
}

// types/cart.ts

export interface CartBikeItem {
  id: number;
  bike: BikeProduct;
  size: { size: string };
  color: { color: string; color_name?: string };
  quantity: number;
  size_price?: string;
  size_discount_price?: string;
  effective_price?: string; // The exact unit price charged
}
```

---

## 3. UI Implementation Details

### 3.1. Bike Details Page (PDP) — Dynamic Size & Price Switching

When viewing a bike:
1. Default `selectedSize` should be initialized to the first available size (e.g. the first size with `!is_out_of_stock` and `stock > 0`), or the first entry in `bike_sizes`.
2. Find `currentVariant = bike.bike_sizes?.find(s => s.size === selectedSize)`.
3. Compute the active prices:
   - **Current Selling Price:**  
     If `currentVariant` has `is_discount` and `discount_price > 0`, display `currentVariant.discount_price`.  
     Else if `currentVariant` has `price > 0`, display `currentVariant.price`.  
     Else fall back to bike base price (`bike.discount_price` if `bike.is_discount` else `bike.price`).
   - **Original / MRP Price (Strikethrough):**  
     If `currentVariant` has `is_discount`, display `currentVariant.price` with strikethrough.
   - **Discount Percentage Badge:**  
     Display `currentVariant.discount_percentage`% OFF badge if discounted.
   - **Stock Availability:**  
     - If `currentVariant?.is_out_of_stock || currentVariant?.stock <= 0`:
       - Show red badge: **"Out of Stock"**
       - Disable **"Add to Cart"** and **"Buy Now"** buttons.
     - Else if `currentVariant?.stock <= 3`:
       - Show amber badge: **"Only X left in stock — order soon!"**
       - Enable CTA buttons.
     - Else:
       - Show green badge: **"In Stock"**
       - Enable CTA buttons.

#### React Component Example: `BikeProductPricing.tsx`

```tsx
import React, { useState, useMemo } from 'react';
import { BikeProduct, BikeSizeVariant } from '@/types/product';

interface Props {
  bike: BikeProduct;
  onAddToCart: (size: string, variant?: BikeSizeVariant) => void;
  onBuyNow: (size: string, variant?: BikeSizeVariant) => void;
}

export const BikeProductPricing: React.FC<Props> = ({ bike, onAddToCart, onBuyNow }) => {
  const sizeVariants = bike.bike_sizes || [];

  // Determine initial selected size: first in-stock variant or first available
  const initialSize = useMemo(() => {
    if (sizeVariants.length > 0) {
      const inStock = sizeVariants.find((v) => !v.is_out_of_stock && v.stock > 0);
      return inStock ? inStock.size : sizeVariants[0].size;
    }
    return bike.sizes?.[0] || '';
  }, [sizeVariants, bike.sizes]);

  const [selectedSize, setSelectedSize] = useState<string>(initialSize);

  // Active size variant object
  const activeVariant = useMemo(() => {
    return sizeVariants.find((v) => v.size === selectedSize);
  }, [sizeVariants, selectedSize]);

  // Pricing calculations
  const { currentPrice, originalPrice, hasDiscount, discountPercent, isOutOfStock, stockCount } = useMemo(() => {
    if (activeVariant && Number(activeVariant.price) > 0) {
      const isDisc = activeVariant.is_discount && Number(activeVariant.discount_price) > 0;
      return {
        currentPrice: isDisc ? Number(activeVariant.discount_price) : Number(activeVariant.price),
        originalPrice: isDisc ? Number(activeVariant.price) : null,
        hasDiscount: isDisc,
        discountPercent: Number(activeVariant.discount_percentage) || 0,
        isOutOfStock: activeVariant.is_out_of_stock || activeVariant.stock <= 0,
        stockCount: activeVariant.stock,
      };
    }

    // Fallback to bike's base pricing if no size variant exists
    const baseDisc = bike.is_discount && Number(bike.discount_price) > 0;
    return {
      currentPrice: baseDisc ? Number(bike.discount_price) : Number(bike.price),
      originalPrice: baseDisc ? Number(bike.price) : null,
      hasDiscount: baseDisc,
      discountPercent: Number(bike.discount_percentage) || 0,
      isOutOfStock: bike.is_out_of_stock || bike.stock <= 0,
      stockCount: bike.stock,
    };
  }, [activeVariant, bike]);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-6">
      {/* 1. PRICE DISPLAY */}
      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-extrabold text-gray-900">
          {formatCurrency(currentPrice)}
        </span>
        {hasDiscount && originalPrice && (
          <span className="text-lg text-gray-400 line-through">
            {formatCurrency(originalPrice)}
          </span>
        )}
        {hasDiscount && discountPercent > 0 && (
          <span className="px-2.5 py-0.5 text-xs font-bold text-red-700 bg-red-100 rounded-full">
            {discountPercent}% OFF
          </span>
        )}
      </div>

      {/* 2. STOCK AVAILABILITY BADGE */}
      <div>
        {isOutOfStock ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded-md">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            Out of Stock for Size {selectedSize}
          </span>
        ) : stockCount <= 3 ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-md">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Only {stockCount} left in size {selectedSize} — order soon
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            In Stock
          </span>
        )}
      </div>

      {/* 3. SIZE SELECTOR PILLS */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-semibold text-gray-900">
            Select Size: <span className="text-red-600 font-bold">{selectedSize}</span>
          </label>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {(sizeVariants.length > 0 ? sizeVariants : bike.sizes.map((s) => ({ size: s } as any))).map((item: any) => {
            const sizeLabel = item.size;
            const isSelected = selectedSize === sizeLabel;
            const itemOutOfStock = item.is_out_of_stock || (item.stock !== undefined && item.stock <= 0);

            return (
              <button
                key={sizeLabel}
                type="button"
                onClick={() => setSelectedSize(sizeLabel)}
                className={`min-w-[52px] px-3.5 py-2 text-sm font-medium rounded-lg border transition-all ${
                  isSelected
                    ? 'border-red-600 bg-red-600 text-white shadow-sm ring-2 ring-red-600/20'
                    : itemOutOfStock
                    ? 'border-gray-200 bg-gray-50 text-gray-400 line-through cursor-pointer'
                    : 'border-gray-200 bg-white text-gray-800 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                {sizeLabel}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. ACTION BUTTONS */}
      <div className="flex gap-3 pt-2">
        <button
          type="button"
          disabled={isOutOfStock}
          onClick={() => onAddToCart(selectedSize, activeVariant)}
          className="flex-1 py-3 px-6 text-sm font-bold rounded-xl border-2 border-red-600 text-red-600 hover:bg-red-50 transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
        </button>

        <button
          type="button"
          disabled={isOutOfStock}
          onClick={() => onBuyNow(selectedSize, activeVariant)}
          className="flex-1 py-3 px-6 text-sm font-bold rounded-xl bg-red-600 text-white hover:bg-red-700 transition shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isOutOfStock ? 'Unavailable' : 'Buy Now'}
        </button>
      </div>
    </div>
  );
};
```

---

### 3.2. Product Listing Cards (Catalog / Shop Page)

When displaying bikes on the catalog grid:
- If a bike has sizes with varying prices, display a price range or starting price:
  - E.g.: `From ₹95,000` (lowest available size price) or `₹95,000 - ₹1,05,000`.

#### Helper function:
```typescript
export function getBikePriceDisplay(bike: BikeProduct): { label: string; current: number; isRange: boolean } {
  if (bike.bike_sizes && bike.bike_sizes.length > 0) {
    const validPrices = bike.bike_sizes
      .map((v) => (v.is_discount && Number(v.discount_price) > 0 ? Number(v.discount_price) : Number(v.price)))
      .filter((p) => p > 0);

    if (validPrices.length > 0) {
      const min = Math.min(...validPrices);
      const max = Math.max(...validPrices);
      if (min !== max) {
        return { label: `From ₹${min.toLocaleString('en-IN')}`, current: min, isRange: true };
      }
      return { label: `₹${min.toLocaleString('en-IN')}`, current: min, isRange: false };
    }
  }

  // Fallback
  const base = bike.is_discount && Number(bike.discount_price) > 0 ? Number(bike.discount_price) : Number(bike.price);
  return { label: `₹${base.toLocaleString('en-IN')}`, current: base, isRange: false };
}
```

---

### 3.3. Cart Drawer & Checkout Items

In `CartItem.tsx`:
- Render the unit price and subtotal using `item.effective_price`:
```tsx
const unitPrice = Number(item.effective_price || item.size_price || item.bike.price);
const originalUnitPrice = Number(item.size_price || item.bike.price);
const hasDiscount = originalUnitPrice > unitPrice;

return (
  <div className="flex justify-between items-center py-3">
    <div>
      <h4 className="font-semibold text-gray-900">{item.bike.name}</h4>
      <p className="text-xs text-gray-500">
        Size: {item.size?.size} • Color: {item.color?.color_name || item.color?.color}
      </p>
    </div>

    <div className="text-right">
      <div className="font-bold text-gray-900">
        ₹{(unitPrice * item.quantity).toLocaleString('en-IN')}
      </div>
      {hasDiscount && (
        <div className="text-xs text-gray-400 line-through">
          ₹{(originalUnitPrice * item.quantity).toLocaleString('en-IN')}
        </div>
      )}
    </div>
  </div>
);
```

---

## 4. Key Rules & Backward Compatibility

1. **Fallback if `bike_sizes` is missing or empty:**  
   Always fall back cleanly to `bike.price`, `bike.discount_price`, `bike.discount_percentage`, and `bike.sizes`.
2. **Payload for Cart remains unchanged:**  
   `POST /api/user-cart/` still accepts:
   ```json
   {
     "product_type": "bike",
     "product_id": "<bike_unique_id>",
     "size": "<selected_size_string>",
     "color": "<selected_color_string>",
     "quantity": 1
   }
   ```
   The backend automatically looks up the matching `BikeSizesModel` row for that `(bike, size)` pair and calculates the exact price and stock.
3. **No Breaking Changes:**  
   Existing `bike.sizes` array of strings is preserved for backwards compatibility.

---

## 5. Definition of Done (DoD)

- [ ] Product details page displays the price, discount price, discount badge, and stock status corresponding to the selected size.
- [ ] Switching sizes immediately updates the visible price and stock badge.
- [ ] Selecting an out-of-stock size disables the "Add to Cart" and "Buy Now" buttons and shows "Out of Stock".
- [ ] Product catalog cards show "From ₹XX,XXX" if size prices vary across sizes.
- [ ] Cart drawer and cart page display the correct size-specific price for each bike item.

