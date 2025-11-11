# Senior Developer - Coding Assignment #1

## Overview

**Duration**: 3 days  
**Submission**: GitHub repository or zip file  
**Deadline**: 3 days from assignment date  

---

## Task: Shopping Cart System

Design and implement a shopping cart system with a web UI and RESTful API. The system should allow users to add items to cart, update quantities, apply discounts, and calculate totals including shipping costs.

---

## Requirements

### 1. Backend API

#### 1.1 Cart Management
- Add items to cart
- Update item quantities
- Remove items from cart
- Clear cart
- Get cart details with calculated totals

#### 1.2 Price Calculation
- Calculate subtotal (sum of item prices × quantities)
- Apply discount codes (percentage discount)
- Calculate shipping costs based on the following rules:

**Shipping Calculation Rules:**

1. **Free Shipping Threshold**
   - Free shipping threshold: $800
   - If vendor subtotal >= $800: that vendor's shipping = $0
   - If vendor subtotal < $800: that vendor's shipping = $100

2. **Vendor-Based Shipping**
   - Each vendor has its own shipping fee calculation
   - Group cart items by vendor
   - For each vendor:
     - Calculate vendor subtotal (sum of items from that vendor)
     - If vendor subtotal >= $800: shipping = $0
     - If vendor subtotal < $800: shipping = $100
   - Total shipping = sum of all vendor shipping fees

3. **Shipping Total**
   - `shipping_base` = sum of all vendor shipping fees
   - `shipping_total` = shipping_base (surcharge can be ignored for this assignment)

**Discount Code:**
- Support percentage discount (e.g., 10% off)
- Example: If subtotal = $100 and discount code = "SAVE10" (10% off), discount = $10

**Final Calculation:**
- Subtotal = sum(item_price × quantity)
- Discount = subtotal × discount_percentage
- Shipping = calculated based on vendor rules above
- Final Total = subtotal - discount + shipping

**Example:**
- Cart has 2 vendors:
  - Vendor A: subtotal = $900 → shipping = $0 (free shipping)
  - Vendor B: subtotal = $500 → shipping = $100
- Subtotal: $1400
- Discount: $140 (10% off)
- Shipping: $100
- Final Total: $1400 - $140 + $100 = $1360

#### 1.3 External Service Integration
- **Configurable external API endpoint** for product information
- Support HTTP GET requests to fetch product details (price, stock, etc.)
- Handle authentication (API key, Bearer token)
- Cache product information

#### 1.4 API Endpoints

```
POST   /api/v1/cart/items                - Add item to cart
GET    /api/v1/cart                      - Get cart details
PUT    /api/v1/cart/items/{item_id}       - Update item quantity
DELETE /api/v1/cart/items/{item_id}       - Remove item from cart
DELETE /api/v1/cart                      - Clear cart
POST   /api/v1/cart/discount             - Apply discount code
DELETE /api/v1/cart/discount             - Remove discount
POST   /api/v1/config/product-service    - Configure external product API
GET    /api/v1/config/product-service    - Get configuration
```

### 2. Frontend UI

#### 2.1 Cart Page
- Display cart items with images, names, prices, quantities
- Quantity adjustment controls (+/- buttons or input)
- Remove item button
- Subtotal, discount, shipping, and total display
- Discount code input field
- Checkout button

#### 2.2 UI Requirements
- Responsive design (desktop-first)
- Clean, modern interface
- Loading states and error handling
- Real-time price updates when quantities change
- No framework required (vanilla JS or lightweight library)

### 3. Technical Requirements

#### 3.1 Tech Stack
- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite or PostgreSQL
- **Frontend**: HTML + JavaScript (vanilla or lightweight library)
- **Testing**: pytest

#### 3.2 Data Model
Design tables for:
- Cart sessions
- Cart items
- Discount codes (optional)

#### 3.3 External Product API Configuration
- Store external API configuration (endpoint, auth, headers)
- Provide API to configure external product service
- Support fetching product details from external API

---

## Sample Files

### Sample Product Data

For testing, you can use a simple mock product API or create sample data. Products should have:
- `id` - Product ID
- `name` - Product name
- `price` - Unit price
- `stock` - Available stock
- `vendor_id` - Vendor ID (required for shipping calculation)
- `vendor_name` - Vendor name (optional)
- `image_url` - Product image URL (optional)

**Sample External API Response:**
```json
{
  "id": "prod_001",
  "name": "Product Name",
  "price": 99.99,
  "stock": 50,
  "vendor_id": "vendor_001",
  "vendor_name": "Vendor A",
  "image_url": "https://example.com/image.jpg"
}
```

**Note**: Products must have `vendor_id` to support vendor-based shipping calculation.

---

## Submission

1. GitHub repository or zip file
2. Include:
   - Source code
   - Tests
   - README.md (setup, API docs, external API configuration)
   - requirements.txt

---

## Notes

- Focus on quality over quantity
- Document design decisions
- Provide clear instructions for configuring external product API endpoint
- Ensure the system can work with any external product API endpoint
- Implement shipping rules exactly as specified above (vendor-based shipping with $800 free shipping threshold)

Good luck!
