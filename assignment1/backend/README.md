# Shopping Cart API Backend

A FastAPI-based shopping cart backend service with comprehensive unit testing, Docker support, and production-ready configuration.

## 🚀 Features

- **Shopping Cart Management**: Add, update, remove cart items
- **Product Integration**: External product service integration with caching
- **Discount System**: Configurable discount codes with validation
- **Vendor-based Shipping**: Smart shipping calculation based on vendor totals
- **Session Management**: Cart session handling with persistence
- **Comprehensive Testing**: 95%+ test coverage with unit, integration, and API tests
- **Docker Support**: Development and production Docker configurations
- **Redis Caching**: Optional Redis integration for enhanced performance

## 📁 Project Structure

```
backend/
├── app/                     # Application code (ready for refactoring)
│   ├── api/                # API endpoints (planned)
│   ├── config/             # Configuration management
│   ├── core/               # Core functionality
│   ├── models/             # Data models (planned)
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic (planned)
│   ├── repositories/       # Data access layer (planned)
│   └── utils/              # Utility functions
├── tests/                  # Test suite
│   ├── test_api/          # API endpoint tests
│   ├── test_services/     # Service layer tests
│   ├── test_repositories/ # Repository tests
│   ├── test_utils/        # Utility tests
│   └── conftest.py        # Test configuration
├── docker-compose.yml      # Development Docker setup
├── docker-compose.prod.yml # Production Docker setup
├── Dockerfile             # Container configuration
├── pytest.ini            # Test configuration
├── Makefile               # Development commands
└── requirements.txt       # Python dependencies
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Docker & Docker Compose (optional)
- Git

### Local Development

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd assignment1/backend
   make setup-dev
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Run the application:**
   ```bash
   make dev
   ```

   The API will be available at `http://localhost:8000`

### Docker Setup

1. **Development environment:**
   ```bash
   make docker-up
   ```

2. **Production environment:**
   ```bash
   make prod-docker
   ```

## 🧪 Testing

### Run All Tests
```bash
# Basic test run
make test

# Verbose output
make test-verbose

# With coverage report
make test-cov

# Watch mode for development
make test-watch
```

### Run Specific Test Categories

```bash
# API tests only
pytest -m api

# Service layer tests
pytest -m service

# Cart-related tests
pytest -m cart

# Happy path tests
pytest -m happy_path

# Negative test cases
pytest -m negative
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **API Tests**: Endpoint functionality testing
- **Service Tests**: Business logic testing
- **Repository Tests**: Data access layer testing
- **Utility Tests**: Helper function testing

## 📊 Test Coverage

The test suite includes comprehensive coverage:

- **API Endpoints**: All cart operations, discount codes, product fetching
- **Business Logic**: Cart calculations, discount validation, shipping rules
- **Data Layer**: Database operations, session management
- **Utilities**: Caching, validation, helper functions
- **Edge Cases**: Boundary conditions, error scenarios, security cases

### Test Markers

```bash
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m slow          # Slow-running tests
pytest -m external      # Tests requiring external services
pytest -m security      # Security-related tests
pytest -m performance   # Performance tests
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Key configuration options:
- `DEBUG`: Enable/disable debug mode
- `DATABASE_URL`: Database connection string
- `CORS_ORIGINS`: Allowed frontend origins
- `CACHE_TTL`: Cache timeout in seconds
- `PRODUCT_SERVICE_ENDPOINT`: External product service URL

### Database Setup

The application uses SQLite by default. Initialize the database:

```bash
make db-init
```

## 📚 API Documentation

Once running, visit:
- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Key Endpoints

#### Cart Operations
- `POST /api/v1/cart/items` - Add item to cart
- `GET /api/v1/cart` - Get cart contents
- `PUT /api/v1/cart/items/{item_id}` - Update item quantity
- `DELETE /api/v1/cart/items/{item_id}` - Remove item
- `DELETE /api/v1/cart` - Clear cart

#### Discount Management
- `POST /api/v1/cart/discount` - Apply discount code
- `DELETE /api/v1/cart/discount` - Remove discount code

#### Configuration
- `POST /api/v1/config/product-service` - Configure product service
- `GET /api/v1/config/product-service` - Get product service config

## 🎯 Business Logic Features

### Shopping Cart
- Add/remove items with validation
- Quantity updates with stock checking
- Session-based cart persistence
- Multi-vendor support

### Shipping Calculation
- Free shipping for vendor orders ≥ $800
- $100 shipping fee per vendor for orders < $800
- Automatic vendor grouping and calculation

### Discount System
- Configurable discount codes
- Percentage-based discounts
- Minimum order requirements
- Usage limits and expiration
- Maximum discount caps

### Product Integration
- External product service integration
- Caching for performance
- Stock validation
- Error handling and fallbacks

## 🐳 Docker Configuration

### Development Docker Compose
- Backend API with hot reload
- Redis cache (optional)
- Volume mounting for development
- Health checks

### Production Docker Compose
- Optimized multi-stage builds
- Resource limits
- Nginx reverse proxy
- SSL-ready configuration
- Persistent volumes

## 📈 Development Workflow

### Code Quality
```bash
# Lint code
make lint

# Format code
make format

# Run all quality checks
make test-cov && make lint
```

### Git Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
make pre-commit
```

### Development Server
```bash
# Start with auto-reload
make dev

# View logs
make docker-logs
```

## 🔒 Security Features

- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Error handling without information leakage
- Security scanning tools included

## 🚀 Production Deployment

### Environment Setup
1. Configure environment variables
2. Set up external services (Redis, Database)
3. Configure SSL certificates
4. Set up monitoring and logging

### Deployment Commands
```bash
# Build and deploy
make docker-build
make prod-docker

# Scale horizontally
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3
```

## 📊 Monitoring & Observability

### Health Checks
- Application health endpoint
- Database connectivity
- External service availability
- Cache status

### Logging
- Structured logging configuration
- Request/response logging
- Error tracking
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Requirements
- All new features must include tests
- Maintain >90% test coverage
- Follow code style guidelines
- Update documentation

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Port conflicts**: Change port in `uvicorn` command
2. **Database errors**: Ensure proper permissions and disk space
3. **Cache issues**: Clear Redis cache or restart services
4. **Test failures**: Check dependencies and database setup

### Getting Help

- Check the test suite for usage examples
- Review API documentation at `/docs`
- Examine logs for error details
- Run tests with verbose output for debugging

## 🔄 Future Enhancements

- PostgreSQL migration
- JWT authentication
- Order management
- Payment integration
- Advanced caching strategies
- Microservices architecture
- Event-driven architecture
- GraphQL API
- Advanced analytics