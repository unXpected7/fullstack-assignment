# Shopping Cart System

A full-stack shopping cart system with RESTful API and responsive web interface, built with FastAPI and vanilla JavaScript.

## Overview

This shopping cart system implements all requirements from the senior developer coding assignment, including:

- **Backend API**: FastAPI with SQLite database and comprehensive business logic
- **Frontend UI**: Responsive cart interface with real-time updates
- **Advanced Features**: Vendor-based shipping calculation, discount codes, external product API integration
- **Testing**: Comprehensive pytest test suite with mocking

## Features

### Backend Features
- **Cart Management**: Add, update, remove, and clear cart items
- **Price Calculation**: Accurate subtotal, discount, and shipping calculations
- **Vendor-Based Shipping**: $800 free shipping threshold per vendor
- **Discount Codes**: Percentage-based discount support
- **External API Integration**: Configurable product information fetching
- **Caching**: TTL-based product information caching
- **Database**: SQLite with proper schema and relationships

### Frontend Features
- **Responsive Design**: Desktop-first mobile-friendly interface
- **Real-time Updates**: Immediate price and quantity updates
- **Error Handling**: Comprehensive loading states and error messages
- **User Experience**: Modern, clean interface with smooth interactions
- **Session Management**: Persistent cart sessions

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: SQLite
- **Language**: Python 3.10+
- **HTTP Client**: httpx for external API calls
- **Caching**: cachetools with 5-minute TTL
- **Testing**: pytest with async support

### Frontend
- **Core**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Styling**: CSS Grid, Flexbox, Responsive Design
- **Architecture**: Class-based JavaScript with async/await

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup Instructions

1. **Clone the repository** (or extract the zip file):
   ```bash
   cd shopping-cart-system
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the Backend Server**:
   ```bash
   python main.py
   ```
   The API will be available at: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

4. **Frontend Usage**:
   - Open `frontend/index.html` in a web browser
   - Or use a local development server:
   ```bash
   # Option 1: Python built-in server
   cd frontend
   python -m http.server 3000

   # Option 2: Node.js server (if installed)
   npx http-server frontend -p 3000
   ```

   Access the frontend at: `http://localhost:3000` or `file:///path/to/frontend/index.html`

## API Documentation

### Base URL
- Development: `http://localhost:8000/api/v1`

### Endpoints

#### Cart Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/cart/items` | Add item to cart |
| `GET` | `/cart` | Get cart details |
| `PUT` | `/cart/items/{item_id}` | Update item quantity |
| `DELETE` | `/cart/items/{item_id}` | Remove item from cart |
| `DELETE` | `/cart` | Clear entire cart |

#### Discount Codes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/cart/discount` | Apply discount code |
| `DELETE` | `/cart/discount` | Remove discount code |

#### Product Service Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/config/product-service` | Configure external product API |
| `GET` | `/config/product-service` | Get current configuration |

#### General

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API health check |

### Request Examples

#### Add Item to Cart
```json
POST /api/v1/cart/items
{
  "product_id": "prod_001",
  "quantity": 2
}
```

#### Apply Discount Code
```json
POST /api/v1/cart/discount
{
  "code": "SAVE10"
}
```

#### Configure External Product API
```json
POST /api/v1/config/product-service
{
  "endpoint": "https://api.example.com/products",
  "api_key": "your_api_key",
  "headers": {
    "Authorization": "Bearer token"
  }
}
```

### Response Format

#### Cart Response
```json
{
  "session_id": "abc123def456",
  "items": [
    {
      "id": 1,
      "product_id": "prod_001",
      "product_name": "Wireless Headphones",
      "price": 99.99,
      "quantity": 2,
      "vendor_id": "vendor_001",
      "vendor_name": "TechCorp",
      "image_url": "https://example.com/image.jpg"
    }
  ],
  "subtotal": 199.98,
  "discount": 0.00,
  "shipping": 100.00,
  "total": 299.98,
  "discount_code": null
}
```

## Business Logic

### Shipping Calculation Rules

1. **Free Shipping Threshold**: $800 per vendor
   - If vendor subtotal ≥ $800: shipping = $0
   - If vendor subtotal < $800: shipping = $100

2. **Vendor-Based Shipping**:
   - Cart items are grouped by vendor
   - Shipping fee is calculated for each vendor separately
   - Total shipping = sum of all vendor shipping fees

3. **Example Calculation**:
   - Vendor A: $900 subtotal → $0 shipping
   - Vendor B: $500 subtotal → $100 shipping
   - **Total shipping: $100**

### Discount Code System

- **Type**: Percentage-based discounts (e.g., 10% off)
- **Format**: Case-insensitive, stored in uppercase
- **Validation**: Predefined codes with percentage values
- **Sample Codes**: SAVE10 (10%), SAVE20 (20%), SAVE15 (15%)

### Final Calculation Formula
```
Subtotal = Σ(item_price × quantity)
Discount = Subtotal × (discount_percentage / 100)
Shipping = Σ(vendor_shipping_fees)
Total = Subtotal - Discount + Shipping
```

## Testing

### Backend Tests

Run the comprehensive test suite:
```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage

The test suite includes:
- **Cart Operations**: Add, update, remove, clear items
- **Price Calculations**: Subtotal, discount, shipping logic
- **Discount Codes**: Valid and invalid code handling
- **Error Handling**: HTTP status codes and error messages
- **Shipping Rules**: Multi-vendor shipping calculations
- **External API**: Mocked product fetching
- **Database Operations**: Session and item management

### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: API endpoint testing
3. **Business Logic Tests**: Price calculation verification
4. **Error Scenario Tests**: Failure mode testing

## External Product API Integration

### Configuration

The system supports configurable external product APIs:

1. **Setup Configuration**:
   ```bash
   POST /api/v1/config/product-service
   {
     "endpoint": "https://api.example.com/products",
     "api_key": "your_api_key",
     "headers": {"Authorization": "Bearer token"}
   }
   ```

2. **Required Product Fields**:
   ```json
   {
     "id": "product_id",
     "name": "Product Name",
     "price": 99.99,
     "stock": 50,
     "vendor_id": "vendor_001",
     "vendor_name": "Vendor Name",
     "image_url": "https://example.com/image.jpg"
   }
   ```

### Features

- **Caching**: 5-minute TTL for product information
- **Authentication**: API key and header support
- **Error Handling**: Graceful fallback for API failures
- **Stock Validation**: Real-time stock checking before adding items

## Frontend Usage

### Basic Operations

1. **Add Items**: Currently for testing, add items via API or use sample products
2. **Update Quantities**: Use +/- buttons or input field
3. **Remove Items**: Click the ✕ button on any item
4. **Apply Discounts**: Enter discount codes in the summary section
5. **Clear Cart**: Use the "Clear Cart" button

### Development Features

- **Debug Functions**: Open browser console for debug tools:
  ```javascript
  addSampleProducts(); // Add sample products for testing
  debugCart(); // Show current cart state
  ```

- **Session Persistence**: Cart sessions are stored in localStorage
- **Real-time Updates**: All changes update the UI immediately

## Sample Data

### Discount Codes
- `SAVE10` - 10% off
- `SAVE20` - 20% off
- `SAVE15` - 15% off

### Sample Products (for testing)
```javascript
// Add these via browser console for testing:
addSampleProducts();

// Sample products structure:
[
  { id: 'prod_001', name: 'Wireless Headphones', vendor: 'TechCorp' },
  { id: 'prod_002', name: 'Coffee Maker', vendor: 'HomeGoods Inc' },
  { id: 'prod_003', name: 'Running Shoes', vendor: 'SportGear' }
]
```

## Database Schema

### Tables

#### cart_sessions
- `id` (TEXT, Primary Key) - Session identifier
- `created_at` (TIMESTAMP) - Session creation time
- `updated_at` (TIMESTAMP) - Last update time

#### cart_items
- `id` (INTEGER, Primary Key, Autoincrement) - Item ID
- `session_id` (TEXT, Foreign Key) - Session reference
- `product_id` (TEXT) - External product ID
- `product_name` (TEXT) - Product name
- `price` (REAL) - Item price
- `quantity` (INTEGER) - Item quantity
- `vendor_id` (TEXT) - Vendor ID
- `vendor_name` (TEXT) - Vendor name
- `image_url` (TEXT) - Product image URL

#### discount_codes
- `code` (TEXT, Primary Key) - Discount code
- `percentage` (REAL) - Discount percentage (0-100)
- `is_active` (BOOLEAN) - Code status
- `created_at` (TIMESTAMP) - Creation time

#### product_service_config
- `id` (INTEGER, Primary Key, Autoincrement) - Config ID
- `endpoint` (TEXT) - API endpoint URL
- `api_key` (TEXT) - API authentication key
- `headers` (TEXT) - JSON headers
- `is_active` (BOOLEAN) - Configuration status
- `created_at` (TIMESTAMP) - Creation time

## Deployment

### Backend Deployment

1. **Production Environment**:
   - Use PostgreSQL instead of SQLite
   - Set up proper CORS origins
   - Configure environment variables
   - Use production WSGI server (Gunicorn)

2. **Docker Deployment**:
   ```dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   COPY backend/ .
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

### Frontend Deployment

1. **Static Deployment**: Copy frontend folder to any web server
2. **CDN Deployment**: Host on cloud storage (AWS S3, Vercel, Netlify)
3. **Build Process**: For larger projects, consider build tools

## Configuration

### Environment Variables

Create a `.env` file for configuration:
```
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=sqlite:///shopping_cart.db
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### External API Configuration

Configure via API endpoint:
```bash
curl -X POST "http://localhost:8000/api/v1/config/product-service" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://your-api.com/products",
    "api_key": "your_api_key",
    "headers": {"Authorization": "Bearer token"}
  }'
```

## Troubleshooting

### Common Issues

1. **Backend Won't Start**:
   - Check Python version (3.10+ required)
   - Install dependencies: `pip install -r requirements.txt`
   - Check port availability: `netstat -tlnp | grep 8000`

2. **Frontend Not Loading**:
   - Ensure backend is running on `localhost:8000`
   - Check browser console for JavaScript errors
   - Verify API base URL in cart.js

3. **Database Issues**:
   - Delete `shopping_cart.db` file to reset database
   - Check file permissions in backend directory

4. **CORS Issues**:
   - Check CORS configuration in main.py
   - Verify frontend origin matches allowed origins

### Debug Mode

Enable debug logging by modifying main.py:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Development Setup

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run test suite: `python -m pytest`
5. Commit and push changes

### Code Standards

- Follow PEP 8 for Python code
- Use meaningful variable names
- Include docstrings for functions
- Write tests for new features
- Update documentation for changes

## License

This project is for educational and demonstration purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Test with sample data
4. Check browser console for errors

---

**Note**: This implementation is designed to meet the specific requirements of the senior developer coding assignment. It demonstrates best practices in API design, database management, frontend development, and testing.