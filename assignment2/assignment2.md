# Senior Developer - Coding Assignment #2

## Overview

**Duration**: 3 days  
**Submission**: GitHub repository or zip file  
**Deadline**: 3 days from assignment date  

---

## Task: AI Content Generation System

Design and implement an AI-powered content generation system that can generate product information using configurable AI models. The system should support template-based generation and quality checking.

---

## Requirements

### 1. AI Service Integration

#### 1.1 Multi-Provider Support
- Support at least 2 AI providers (e.g., OpenAI, Azure OpenAI)
- **Configurable API endpoints** for each provider (You can mock for the test)
- Handle different authentication methods
- Abstract provider differences behind a common interface

#### 1.2 Content Generation
- Generate content based on templates and prompts
- Support variable substitution in prompts
- Handle API responses and errors
- Implement retry logic for API failures

#### 1.3 Quality Checking
- Validate generated content against rules
- Check content length, format, completeness
- Score content quality (0-100)

### 2. Template System

#### 2.1 Template Management
- Create, read, update, delete templates
- Templates should include:
  - System prompt
  - User prompt template with variables
  - Output format requirements
  - Quality check rules

#### 2.2 Production Volume Generation
You need to implement a template for **Production Volume** generation. The template should:

**Objective**: Generate production volume information for wine products based on available data.

**Input Fields**: The system will provide the following fields from the sample Excel file:
- `wine_id` - Product ID
- `full_wine_name` - Full product name
- `vintage` - Vintage year
- `winery` - Winery name
- `region` - Region
- `ranking` - Classification/ranking

**Output Requirements**:
- Determine production volume (number of bottles produced)
- If exact number is available, provide it
- If not available, estimate based on available information
- Classify as: Micro production (<5,000), Rare (5,000-10,000), Small (10,000-30,000), Medium (30,000-100,000), Common (>100,000)
- If uncertain, return "unknown"

**Your Task**: Design the system prompt and user prompt template for this use case. 

### 3. API Design

#### 3.1 Provider Configuration
```
POST   /api/v1/ai/providers              - Add AI provider
GET    /api/v1/ai/providers              - List providers
PUT    /api/v1/ai/providers/{id}         - Update provider
DELETE /api/v1/ai/providers/{id}         - Remove provider
POST   /api/v1/ai/providers/{id}/test    - Test provider connection
```

#### 3.2 Template Management
```
POST   /api/v1/ai/templates              - Create template
GET    /api/v1/ai/templates              - List templates
GET    /api/v1/ai/templates/{id}          - Get template
PUT    /api/v1/ai/templates/{id}          - Update template
DELETE /api/v1/ai/templates/{id}          - Delete template
```

#### 3.3 Content Generation
```
POST   /api/v1/ai/generate               - Generate content
POST   /api/v1/ai/generate/batch         - Batch generation
GET    /api/v1/ai/generate/{task_id}     - Get generation status
```

#### 3.4 Quality Check
```
POST   /api/v1/ai/quality/check          - Check content quality
```

### 4. Technical Requirements

#### 4.1 Tech Stack
- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite or PostgreSQL
- **AI Libraries**: openai, or httpx for custom providers
- **Testing**: pytest with mocking

#### 4.2 Architecture
- Abstract AI provider interface
- Strategy pattern for different providers
- Template engine for prompt management
- Quality check rules engine

#### 4.3 Configuration
- Store AI provider configurations (endpoint, API key, model, etc.)
- Support environment variables for sensitive data
- Provide API to configure providers dynamically

---

## Sample Files

### Sample Excel File (sample_sku.xlsx)

A sample Excel file will be provided separately with SKU data. The file contains product information including:
- `wine_id` - Product ID
- `full_wine_name` - Full product name
- `vintage` - Vintage year
- `winery` - Winery name
- `region` - Region name
- `ranking` - Classification/ranking
- `production_volume` - Target field to generate (initially empty)

Use this file to test your Production Volume generation template.

---

## Submission

1. GitHub repository or zip file
2. Include:
   - Source code
   - Tests
   - README.md (setup, provider configuration, API docs, template design explanation)
   - requirements.txt
---

## Notes

- Focus on clean architecture and extensibility
- Document design decisions, especially for the Production Volume template
- Provide clear instructions for configuring AI provider endpoints
- Mock AI responses in tests
- Design the Production Volume prompt based on the requirements above

Good luck!
