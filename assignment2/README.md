# AI Content Generation System

A comprehensive AI-powered content generation system built with FastAPI that supports multiple AI providers, template-based generation, and quality checking.

## Features

- **Multi-Provider Support**: OpenAI and Azure OpenAI integration
- **Template Management**: Create, read, update, and delete templates
- **Content Generation**: Single and batch content generation
- **Quality Checking**: Content validation and scoring (0-100)
- **Production Volume Template**: Specialized template for wine production volume estimation
- **Variable Substitution**: Dynamic content generation based on input data
- **Retry Logic**: Robust error handling and retry mechanisms
- **API Documentation**: Interactive API docs with FastAPI

## Tech Stack

- **Backend**: FastAPI 0.104.1
- **Database**: SQLite (configurable for PostgreSQL)
- **AI Libraries**: OpenAI, Azure OpenAI
- **Testing**: pytest with mocking
- **Data Processing**: pandas, openpyxl

## Project Structure

```
assignment2/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── providers.py       # Provider management API
│   │   ├── templates.py       # Template management API
│   │   ├── generation.py      # Content generation API
│   │   └── schemas.py         # Pydantic schemas
│   ├── core/                  # Core business logic
│   │   └── providers.py       # Abstract provider interface
│   ├── providers/             # Provider implementations
│   │   ├── openai_provider.py  # OpenAI provider
│   │   └── azure_provider.py  # Azure OpenAI provider
│   ├── models/                # Database models
│   │   └── database.py       # SQLAlchemy models
│   ├── services/              # Business logic services
│   │   ├── template_service.py # Template management
│   │   └── quality_service.py # Quality checking
│   └── utils/                 # Utility functions
│       └── excel_reader.py    # Excel data processing
├── tests/                     # Unit tests
├── config/                    # Configuration files
├── sku_sample.xlsx           # Sample wine data
├── main.py                   # Application entry point
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd assignment2
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_URL=https://api.openai.com/v1

AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Database Configuration
DATABASE_URL=sqlite:///./ai_content_generation.db

# Application Settings
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
```

## Running the Application

### Development Mode

```bash
python main.py
```

The application will start on `http://localhost:8000`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Provider Management

#### Create Provider
```http
POST /api/v1/ai/providers
```
```json
{
  "name": "OpenAI Provider",
  "provider_type": "openai",
  "api_key": "your-api-key",
  "model": "gpt-3.5-turbo",
  "max_tokens": 2000,
  "temperature": 0.7
}
```

#### List Providers
```http
GET /api/v1/ai/providers
```

#### Get Provider
```http
GET /api/v1/ai/providers/{provider_id}
```

#### Update Provider
```http
PUT /api/v1/ai/providers/{provider_id}
```

#### Delete Provider
```http
DELETE /api/v1/ai/providers/{provider_id}
```

#### Test Provider
```http
POST /api/v1/ai/providers/{provider_id}/test
```

### Template Management

#### Create Template
```http
POST /api/v1/ai/templates
```
```json
{
  "name": "Production Volume Generation",
  "description": "Generates production volume for wine products",
  "system_prompt": "You are an expert wine analyst...",
  "user_prompt_template": "Analyze this wine: {wine_name}",
  "quality_check_rules": {
    "required_fields": ["production_volume", "classification"]
  }
}
```

#### Create Production Volume Template
```http
POST /api/v1/ai/templates/production-volume
```

#### List Templates
```http
GET /api/v1/ai/templates
```

#### Get Template
```http
GET /api/v1/ai/templates/{template_id}
```

#### Update Template
```http
PUT /api/v1/ai/templates/{template_id}
```

#### Delete Template
```http
DELETE /api/v1/ai/templates/{template_id}
```

### Content Generation

#### Generate Content
```http
POST /api/v1/ai/generate
```
```json
{
  "template_id": 1,
  "input_data": {
    "wine_id": "S000001",
    "full_wine_name": "Sample Wine",
    "vintage": "2020",
    "winery": "Test Winery",
    "region": "Burgundy",
    "ranking": "Grand Cru"
  },
  "provider_id": 1
}
```

#### Batch Generation
```http
POST /api/v1/ai/generate/batch
```

#### Get Generation Status
```http
GET /api/v1/ai/generate/{task_id}
```

#### Quality Check
```http
POST /api/v1/ai/quality/check
```
```json
{
  "content": '{"production_volume": "5000", "classification": "Rare"}',
  "template_rules": {
    "required_fields": ["production_volume", "classification"]
  }
}
```

## Production Volume Template

### Overview
The Production Volume template is specifically designed to estimate production volumes for wine products based on available data.

### Input Fields
- `wine_id` - Product ID
- `full_wine_name` - Complete product name
- `vintage` - Vintage year
- `winery` - Winery name
- `region` - Geographic region
- `ranking` - Quality classification/ranking

### Output Classification
- **Micro production**: Less than 5,000 bottles
- **Rare**: 5,000 - 10,000 bottles
- **Small**: 10,000 - 30,000 bottles
- **Medium**: 30,000 - 100,000 bottles
- **Common**: More than 100,000 bottles
- **Unknown**: Insufficient information

### Sample Output
```json
{
  "production_volume": 7500,
  "classification": "Rare",
  "reasoning": "Based on the Grand Cru ranking and premium positioning",
  "confidence": 0.8
}
```

## Testing

### Run Unit Tests
```bash
pytest -v
```

### Run Production Volume Test
```bash
python test_production_volume.py
```

### Test Coverage
The test suite covers:
- Provider implementations (OpenAI, Azure)
- Template management
- Content generation
- Quality checking
- Excel data processing

## Usage Examples

### Example 1: Create and Use Production Volume Template

1. Create a production volume template:
```bash
curl -X POST "http://localhost:8000/api/v1/ai/templates/production-volume"
```

2. Create an OpenAI provider:
```bash
curl -X POST "http://localhost:8000/api/v1/ai/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My OpenAI",
    "provider_type": "openai",
    "api_key": "your-key",
    "model": "gpt-3.5-turbo"
  }'
```

3. Generate production volume for a wine:
```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "provider_id": 1,
    "input_data": {
      "wine_id": "S000001",
      "full_wine_name": "Domaine de la Romanée-Conti",
      "vintage": "2020",
      "winery": "Domaine de la Romanée-Conti",
      "region": "Burgundy",
      "ranking": "Grand Cru"
    }
  }'
```

### Example 2: Batch Processing

```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "provider_id": 1,
    "input_data_list": [
      {
        "wine_id": "S000001",
        "full_wine_name": "Wine A",
        "vintage": "2020",
        "winery": "Winery A",
        "region": "Burgundy",
        "ranking": "Grand Cru"
      },
      {
        "wine_id": "S000002",
        "full_wine_name": "Wine B",
        "vintage": "2019",
        "winery": "Winery B",
        "region": "Bordeaux",
        "ranking": "Premier Cru"
      }
    ]
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./ai_content_generation.db` |
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI provider |
| `OPENAI_API_URL` | OpenAI API endpoint | `https://api.openai.com/v1` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required for Azure provider |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint URL | Required for Azure provider |
| `AZURE_OPENAI_API_VERSION` | API version | `2023-12-01-preview` |
| `DEBUG` | Debug mode | `False` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |

### Database Configuration

The system uses SQLite by default but can be configured for PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/ai_content_db
```

## Design Decisions

### 1. Architecture Pattern
- **Strategy Pattern**: Used for different AI providers to allow easy extension
- **Factory Pattern**: Used for creating provider instances
- **Service Layer**: Separated business logic from API layer

### 2. Template System
- **Dynamic Variable Substitution**: Supports `{variable_name}` syntax
- **Quality Rules**: JSON-based validation rules for template outputs
- **Production Volume Specialization**: Dedicated template for wine industry

### 3. Error Handling
- **Retry Logic**: Exponential backoff for API failures
- **Comprehensive Validation**: Input validation at multiple layers
- **Graceful Degradation**: System continues working even if some providers fail

### 4. Performance Considerations
- **Async Processing**: FastAPI async support for concurrent requests
- **Background Tasks**: Long-running generation tasks processed asynchronously
- **Database Optimization**: Efficient queries and connection management

## Production Deployment

### Docker Deployment

1. Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Build and run:
```bash
docker build -t ai-content-generation .
docker run -p 8000:8000 ai-content-generation
```

### Production Considerations

1. **Security**:
   - Use HTTPS in production
   - Store API keys in secure environment variables
   - Implement rate limiting

2. **Monitoring**:
   - Add logging and monitoring
   - Track API usage and performance
   - Monitor generation success rates

3. **Scalability**:
   - Use PostgreSQL for production databases
   - Consider message queues for batch processing
   - Implement caching for frequent requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the test examples
- Examine the configuration templates