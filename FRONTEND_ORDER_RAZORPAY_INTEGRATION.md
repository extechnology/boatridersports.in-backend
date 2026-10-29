# Frontend Order & Razorpay Payment Integration Guide

This document contains the complete specification and integration code for connecting the frontend (Checkout Page, Razorpay Payment Modal, and Order History Page) with the backend Order services.

---

## 1. Prerequisites & Setup

### 1.1 Include Razorpay Checkout SDK
Add the official Razorpay Checkout SDK in your project:

**HTML (`index.html` or Next.js `_document.tsx` / `layout.tsx`):**
```html
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

**Or Dynamic Script Loader (React Hook):**
```javascript
export const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};
```

### 1.2 Authentication Headers
All order endpoints (except the server-to-server webhook) require the JWT user token:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## 2. API Endpoints Specification

### 2.1 Endpoint: Create Order & Initialize Razorpay

Creates a pending order in the database from the user's active cart and generates the Razorpay order ID.

- **URL:** `POST /api/order/razorpay/create-order/`  
  *(Direct alias: `POST /api/order/razorpay-create-order/`)*  
  *(Legacy route: `POST /api/order/create-order/` with `"payment_gateway": "razorpay"`)*
- **Auth:** `Bearer <token>`

#### Request Body
```json
{
  "address_id": "8f94d0a2-2cb5-455f-bb5d-a773bcde1100", // Required: unique_id of selected UserAddress
  "currency": "INR" // Optional, default is "INR"
}
```

#### Success Response (`200 OK`)
```json
{
  "order_id": "order-3e2849e7-4977-4c31-9041-3d7b88e1bc98",
  "razorpay_order_id": "order_P0kLmN12345678",
  "amount": 5499900, // Amount in PAISE (₹54,999.00 = 5499900 paise)
  "currency": "INR",
  "razorpay_key_id": "rzp_test_xxxxxxxxxxxxxx",
  "order": {
    "id": 14,
    "unique_id": "order-3e2849e7-4977-4c31-9041-3d7b88e1bc98",
    "user": 5,
    "status": "Pending",
    "payment_status": false,
    "payment_gateway": "razorpay",
    "razorpay_order_id": "order_P0kLmN12345678",
    "razorpay_payment_id": null,
    "razorpay_signature": null,
    "total_amount": "54999.00",
    "total_items": 2,
    "invoice": null,
    "deliverd_at": null,
    "tracking_id": null,
    "shipped_via": null,
    "created_at": "2026-10-28T11:30:00.123456Z",
    "updated_at": "2026-10-28T11:30:02.789101Z",
    "user_address": {
      "id": 3,
      "unique_id": "8f94d0a2-2cb5-455f-bb5d-a773bcde1100",
      "name": "Rahul Sharma",
      "phone_number": "9876543210",
      "address": "Flat 402, Skyline Heights, MG Road",
      "city": "Kochi",
      "state": "Kerala",
      "pincode": "682001",
      "address_type": "Home",
      "landmark": "Near Metro Pillar 120",
      "alternate_phone_number": null,
      "is_default": true
    },
    "all_products": [
      {
        "id": 21,
        "quantity": 1,
        "price": "49999.00",
        "subtotal": "49999.00",
        "created_at": "2026-10-28T11:30:01.000000Z",
        "updated_at": "2026-10-28T11:30:01.000000Z",
        "bike": {
          "id": 2,
          "unique_id": "c8a41234-5678-4abc-9def-0123456789ab",
          "name": "Trek Marlin 7 Gen 3",
          "price": "49999.00",
          "discount_price": "49999.00",
          "is_discount": false,
          "stock": 8,
          "product_type": "bike"
        },
        "color": {
          "id": 4,
          "color": {
            "color_name": "Matte Nautical Navy"
          },
          "bike_images": [
            { "image": "https://server.boatridersports.in/media/bike_images/trek_marlin7_navy.jpg" }
          ]
        },
        "size": {
          "id": 2,
          "size": "M"
        }
      },
      {
        "id": 22,
        "quantity": 1,
        "price": "5000.00",
        "subtotal": "5000.00",
        "created_at": "2026-10-28T11:30:01.000000Z",
        "updated_at": "2026-10-28T11:30:01.000000Z",
        "accessory": {
          "id": 6,
          "unique_id": "b1c23456-7890-4def-1234-56789abcdef0",
          "name": "Bontrager Solstice MIPS Helmet",
          "price": "5000.00",
          "product_type": "accessories",
          "accessory_images": [
            { "image": "https://server.boatridersports.in/media/accessory_images/helmet_front.jpg" }
          ]
        }
      }
    ]
  }
}
```

#### Error Responses
- **`400 Bad Request` (Empty Cart):**
  ```json
  { "error": "Cart is empty" }
  ```
- **`400 Bad Request` (Missing address):**
  ```json
  { "error": "address_id is required" }
  ```
- **`404 Not Found` (Address or Cart not found):**
  ```json
  { "error": "Address not found" }
  ```

---

### 2.2 Endpoint: Verify Razorpay Payment

Called by the frontend immediately after Razorpay checkout returns payment success. Verifies cryptographic signature, marks order `Processing`, deducts inventory, generates invoice PDF, triggers confirmation email, and clears cart.

- **URL:** `POST /api/order/razorpay/verify-order/`  
  *(Direct alias: `POST /api/order/razorpay-verify-order/`)*  
  *(Legacy route: `POST /api/order/verify-order/`)*
- **Auth:** `Bearer <token>`

#### Request Body
```json
{
  "order_id": "order-3e2849e7-4977-4c31-9041-3d7b88e1bc98",
  "razorpay_order_id": "order_P0kLmN12345678",
  "razorpay_payment_id": "pay_P0kPqR87654321",
  "razorpay_signature": "9ef2c1b8971f4567890abcdef1234567890abcdef1234567890abcdef1234567"
}
```

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Payment verified successfully",
  "order_status": "Processing"
}
```

#### Verification Failed Response (`400 Bad Request`)
```json
{
  "status": "failed",
  "message": "Payment signature verification failed: Razorpay Signature Verification Failed"
}
```

---

### 2.3 Endpoint: Cancel Order (When Payment is Dismissed or Cancelled)

Called when the user closes the payment modal, abandons checkout, or explicitly cancels the order. Marks the order `Cancelled` and automatically triggers an email notification to the customer **without** any invoice attachment.

- **URL:** `POST /api/order/razorpay/cancel-order/`  
  *(Direct alias: `POST /api/order/razorpay-cancel-order/`)*  
  *(Generic route: `POST /api/order/cancel-order/`)*
- **Auth:** `Bearer <token>`

#### Request Body
```json
{
  "order_id": "order-3e2849e7-4977-4c31-9041-3d7b88e1bc98", // or "razorpay_order_id": "order_P0kLmN12345678"
  "reason": "Payment cancelled by user" // Optional custom cancellation reason
}
```

#### Success Response (`200 OK`)
```json
{
  "status": "cancelled",
  "message": "Order cancelled successfully",
  "order_id": "order-3e2849e7-4977-4c31-9041-3d7b88e1bc98",
  "order_status": "Cancelled"
}
```

---

### 2.4 Endpoint: Get User Orders (Order History)

Fetches all orders placed by the authenticated customer.

- **URL:** `GET /api/order/user-orders/`
- **Auth:** `Bearer <token>`

#### Success Response (`200 OK`)
```json
[
  {
    "id": 14,
    "unique_id": "order-3e2849e7-4977-4c31-9041-3d7b88e1bc98",
    "status": "Processing", // Statuses: "Pending" | "Processing" | "Shipped" | "Delivered" | "Cancelled" | "Failed"
    "payment_status": true,
    "payment_gateway": "razorpay",
    "razorpay_order_id": "order_P0kLmN12345678",
    "razorpay_payment_id": "pay_P0kPqR87654321",
    "total_amount": "54999.00",
    "total_items": 2,
    "invoice": "https://server.boatridersports.in/media/invoices/invoice_order-3e2849e7-4977-4c31-9041-3d7b88e1bc98.pdf",
    "tracking_id": "BLUEDART-8891230",
    "shipped_via": "BlueDart Express",
    "deliverd_at": null,
    "created_at": "2026-10-28T11:30:00.123456Z",
    "updated_at": "2026-10-28T11:32:15.654321Z",
    "user_address": {
      "name": "Rahul Sharma",
      "phone_number": "9876543210",
      "address": "Flat 402, Skyline Heights, MG Road",
      "city": "Kochi",
      "state": "Kerala",
      "pincode": "682001",
      "address_type": "Home"
    },
    "all_products": [
      {
        "id": 21,
        "quantity": 1,
        "price": "49999.00",
        "subtotal": "49999.00",
        "bike": {
          "unique_id": "c8a41234-5678-4abc-9def-0123456789ab",
          "name": "Trek Marlin 7 Gen 3",
          "price": "49999.00"
        },
        "color": {
          "color": { "color_name": "Matte Nautical Navy" },
          "bike_images": [
            { "image": "https://server.boatridersports.in/media/bike_images/trek_marlin7_navy.jpg" }
          ]
        },
        "size": {
          "size": "M"
        }
      },
      {
        "id": 22,
        "quantity": 1,
        "price": "5000.00",
        "subtotal": "5000.00",
        "accessory": {
          "unique_id": "b1c23456-7890-4def-1234-56789abcdef0",
          "name": "Bontrager Solstice MIPS Helmet",
          "price": "5000.00",
          "accessory_images": [
            { "image": "https://server.boatridersports.in/media/accessory_images/helmet_front.jpg" }
          ]
        }
      }
    ]
  }
]
```

---

## 3. Email Notification Policy

| Event / Payment Outcome | Order Status | Email Notification Sent? | Invoice PDF Generated & Attached? |
| :--- | :--- | :--- | :--- |
| **Payment Verified Successfully** | `Processing` | **YES** (`Order Confirmation`) | **YES** (PDF generated and attached) |
| **User Cancelled / Modal Dismissed** | `Cancelled` | **YES** (`Order Cancelled`) | **NO** (No invoice attached) |
| **Payment Signature Failure** | `Failed` | **YES** (`Order Payment Failed`) | **NO** (No invoice attached) |
| **Gateway Webhook Failure (`payment.failed`)** | `Failed` | **YES** (`Order Payment Failed`) | **NO** (No invoice attached) |

---

## 4. Frontend Integration Code (React / Next.js)

### `services/paymentService.js`
```javascript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://server.boatridersports.in';

const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
};

/**
 * Cancels a pending order when checkout is dismissed
 */
export async function cancelOrder(orderId, reason = 'Payment cancelled by user') {
  try {
    const res = await axios.post(
      `${API_BASE}/api/order/razorpay/cancel-order/`,
      { order_id: orderId, reason },
      getAuthHeaders()
    );
    return res.data;
  } catch (err) {
    console.error('Failed to report order cancellation:', err);
    return null;
  }
}

/**
 * Initiates Razorpay payment popup
 * @param {string} addressId - unique_id of the selected UserAddress
 * @param {object} user - Current user object with email and name
 * @param {function} onSuccess - Callback when verification succeeds
 * @param {function} onCancel - Callback when checkout is cancelled / dismissed
 * @param {function} onError - Callback when error occurs
 */
export async function handleRazorpayCheckout({ addressId, user, onSuccess, onCancel, onError }) {
  try {
    // 1. Create order on backend
    const createRes = await axios.post(
      `${API_BASE}/api/order/razorpay/create-order/`,
      { address_id: addressId, currency: 'INR' },
      getAuthHeaders()
    );

    const {
      order_id,
      razorpay_order_id,
      amount,
      currency,
      razorpay_key_id,
      order,
    } = createRes.data;

    // 2. Configure Razorpay modal options
    const options = {
      key: razorpay_key_id,
      amount: amount, // in paise
      currency: currency || 'INR',
      name: 'BoatRider Sports',
      description: `Order #${order_id}`,
      order_id: razorpay_order_id,
      prefill: {
        name: order.user_address?.name || user?.fullname || '',
        email: user?.email || '',
        contact: order.user_address?.phone_number || user?.phone || '',
      },
      theme: {
        color: '#1a73e8',
      },
      handler: async function (response) {
        // 3. Verify signature on backend (triggers confirmation email + invoice PDF)
        try {
          const verifyPayload = {
            order_id: order_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          };

          const verifyRes = await axios.post(
            `${API_BASE}/api/order/razorpay/verify-order/`,
            verifyPayload,
            getAuthHeaders()
          );

          if (verifyRes.data.status === 'success') {
            if (onSuccess) onSuccess(order_id);
          } else {
            if (onError) onError('Payment verification failed.');
          }
        } catch (verifyErr) {
          const errMsg = verifyErr.response?.data?.message || 'Verification failed.';
          if (onError) onError(errMsg);
        }
      },
      modal: {
        ondismiss: async function () {
          // Notify backend so order is cancelled and cancellation email (NO invoice) is sent
          await cancelOrder(order_id, 'Customer closed payment popup without completing');
          if (onCancel) onCancel(order_id);
          else if (onError) onError('Payment cancelled by user.');
        },
      },
    };

    // 4. Open Razorpay Popup
    const razorpayInstance = new window.Razorpay(options);
    razorpayInstance.on('payment.failed', async function (resp) {
      await cancelOrder(order_id, `Payment failed: ${resp.error.description}`);
      if (onError) onError(`Payment failed: ${resp.error.description}`);
    });
    razorpayInstance.open();

  } catch (err) {
    const errorMsg = err.response?.data?.error || 'Unable to create order.';
    if (onError) onError(errorMsg);
  }
}
```

---

## 5. UI Checklist

- [ ] **Checkout Page:** Disable checkout button when the request is in progress to prevent double submissions.
- [ ] **Amount Conversion:** Remember that `amount` returned in `create-order` is in **paise**. Divide by `100` (`amount / 100`) to display in rupees.
- [ ] **Success Page:** On payment verification success, navigate to `/order-success?order_id=${order_id}` and clear the local frontend cart state.
- [ ] **Cancellation Handling:** On modal dismissal, user is notified and backend marks order as `Cancelled` (triggering cancellation email with no invoice).
- [ ] **Orders Page:**
  - Status badges: `Pending` (yellow), `Processing` (blue), `Shipped` (purple), `Delivered` (green), `Failed` / `Cancelled` (red).
  - Download Invoice: Render link to `order.invoice` only if not `null` (only present on paid/processing orders).
  - Tracking Details: Display `tracking_id` and `shipped_via` if available.
