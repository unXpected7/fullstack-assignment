"""
Unit tests for API endpoints
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
import asyncio
from datetime import datetime

# Import the FastAPI app
from main import app

# Import models and schemas
from app.core.providers import ProviderConfig, GenerationRequest, GenerationResponse
from app.models.database import AIProvider, Template, GenerationTask as DBGenerationRequest


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.delete = Mock()
    db.query = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_provider_config():
    """Mock provider configuration"""
    return ProviderConfig(
        id=1,
        name="Test Provider",
        provider_type="openai",
        api_key="test_api_key",
        model="gpt-3.5-turbo",
        max_tokens=2000,
        temperature=0.7,
        timeout=30,
        is_active=True
    )


@pytest.fixture
def mock_template():
    """Mock template"""
    template = Mock(spec=Template)
    template.id = 1
    template.name = "Test Template"
    template.system_prompt = "Test system prompt"
    template.user_prompt = "Hello {name}"
    template.output_schema = json.dumps({"field1": "string", "field2": "number"})
    template.is_active = True
    template.created_at = datetime.now().isoformat()
    template.updated_at = datetime.now().isoformat()
    return template


class TestProviderEndpoints:
    """Test provider management endpoints"""

    @patch('app.api.providers.get_db')
    @patch('app.api.providers.ProviderFactory.create_provider')
    def test_create_provider_success(self, mock_factory, mock_get_db, client, mock_provider_config):
        """Test successful provider creation"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock the provider
        mock_provider_instance = Mock()
        mock_provider_instance.test_connection = AsyncMock(return_value=True)
        mock_factory.return_value = mock_provider_instance

        # Test request
        provider_data = {
            "name": "Test Provider",
            "provider_type": "openai",
            "api_key": "test_api_key",
            "model": "gpt-3.5-turbo"
        }

        response = client.post("/providers/", json=provider_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Provider"
        assert data["provider_type"] == "openai"
        assert data["api_key"] == "test_api_key"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.api.providers.get_db')
    def test_get_providers_empty(self, mock_get_db, client):
        """Test getting providers when none exist"""
        mock_db = Mock()
        mock_db.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        response = client.get("/providers/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @patch('app.api.providers.get_db')
    def test_get_provider_by_id_success(self, mock_get_db, client, mock_provider_config):
        """Test successful provider retrieval by ID"""
        mock_db = Mock()
        mock_provider = Mock(spec=Provider)
        mock_provider.id = 1
        mock_provider.name = "Test Provider"
        mock_provider.provider_type = "openai"
        mock_provider.api_key = "test_api_key"
        mock_provider.model = "gpt-3.5-turbo"
        mock_provider.max_tokens = 2000
        mock_provider.temperature = 0.7
        mock_provider.timeout = 30
        mock_provider.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        mock_get_db.return_value = mock_db

        response = client.get("/providers/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Provider"

    @patch('app.api.providers.get_db')
    def test_get_provider_not_found(self, mock_get_db, client):
        """Test getting provider that doesn't exist"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get("/providers/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.providers.get_db')
    @patch('app.api.providers.ProviderFactory.create_provider')
    def test_update_provider_success(self, mock_factory, mock_get_db, client):
        """Test successful provider update"""
        mock_db = Mock()
        mock_provider = Mock(spec=Provider)
        mock_provider.id = 1
        mock_provider.name = "Old Name"
        mock_provider.provider_type = "openai"
        mock_provider.api_key = "old_key"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        mock_get_db.return_value = mock_db

        update_data = {
            "name": "Updated Provider",
            "model": "gpt-4"
        }

        response = client.put("/providers/1", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Provider"
        assert data["model"] == "gpt-4"
        mock_db.commit.assert_called_once()

    @patch('app.api.providers.get_db')
    def test_delete_provider_success(self, mock_get_db, client):
        """Test successful provider deletion"""
        mock_db = Mock()
        mock_provider = Mock(spec=Provider)
        mock_provider.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        mock_get_db.return_value = mock_db

        response = client.delete("/providers/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
        mock_db.delete.assert_called_once_with(mock_provider)
        mock_db.commit.assert_called_once()

    @patch('app.api.providers.get_db')
    @patch('app.api.providers.ProviderFactory.create_provider')
    async def test_test_provider_connection_success(self, mock_factory, mock_get_db, client):
        """Test successful provider connection test"""
        mock_db = Mock()
        mock_provider = Mock(spec=Provider)
        mock_provider.id = 1
        mock_provider.provider_type = "openai"
        mock_provider.api_key = "test_key"
        mock_provider.base_url = None
        mock_provider.model = "gpt-3.5-turbo"
        mock_provider.max_tokens = 2000
        mock_provider.temperature = 0.7
        mock_provider.timeout = 30

        mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        mock_get_db.return_value = mock_db

        # Mock the provider instance
        mock_provider_instance = Mock()
        mock_provider_instance.test_connection = AsyncMock(return_value=True)
        mock_factory.return_value = mock_provider_instance

        response = client.post("/providers/1/test")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["connected"] is True


class TestTemplateEndpoints:
    """Test template management endpoints"""

    @patch('app.api.templates.get_db')
    def test_create_template_success(self, mock_get_db, client):
        """Test successful template creation"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        template_data = {
            "name": "Test Template",
            "system_prompt": "Test system prompt",
            "user_prompt": "Hello {name}",
            "output_schema": json.dumps({"field1": "string"})
        }

        response = client.post("/templates/", json=template_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Template"
        assert data["system_prompt"] == "Test system prompt"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.api.templates.get_db')
    def test_get_templates_empty(self, mock_get_db, client):
        """Test getting templates when none exist"""
        mock_db = Mock()
        mock_db.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        response = client.get("/templates/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @patch('app.api.templates.get_db')
    def test_get_template_by_id_success(self, mock_get_db, client, mock_template):
        """Test successful template retrieval by ID"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        response = client.get("/templates/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Template"

    @patch('app.api.templates.get_db')
    def test_get_template_not_found(self, mock_get_db, client):
        """Test getting template that doesn't exist"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get("/templates/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.templates.get_db')
    def test_update_template_success(self, mock_get_db, client, mock_template):
        """Test successful template update"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        update_data = {
            "name": "Updated Template",
            "system_prompt": "Updated system prompt"
        }

        response = client.put("/templates/1", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Template"
        assert data["system_prompt"] == "Updated system prompt"
        mock_db.commit.assert_called_once()

    @patch('app.api.templates.get_db')
    def test_delete_template_success(self, mock_get_db, client, mock_template):
        """Test successful template deletion"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        response = client.delete("/templates/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
        mock_db.delete.assert_called_once_with(mock_template)
        mock_db.commit.assert_called_once()


class TestGenerationEndpoints:
    """Test content generation endpoints"""

    @patch('app.api.generation.get_db')
    @patch('app.api.generation.ProviderFactory.create_provider')
    def test_generate_content_success(self, mock_factory, mock_get_db, client, mock_provider_config, mock_template):
        """Test successful content generation"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_template, mock_provider_config]
        mock_get_db.return_value = mock_db

        # Mock the provider instance
        mock_provider_instance = Mock()
        expected_response = GenerationResponse(
            content="Generated content",
            model_used="gpt-3.5-turbo",
            tokens_used=100,
            processing_time=1.5
        )
        mock_provider_instance.generate_content = AsyncMock(return_value=expected_response)
        mock_factory.return_value = mock_provider_instance

        generation_data = {
            "template_id": 1,
            "provider_id": 1,
            "variables": {"name": "John"}
        }

        response = client.post("/generation/generate", json=generation_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Generated content"
        assert data["model_used"] == "gpt-3.5-turbo"
        assert data["tokens_used"] == 100

    @patch('app.api.generation.get_db')
    def test_generate_content_template_not_found(self, mock_get_db, client):
        """Test generation with non-existent template"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        generation_data = {
            "template_id": 999,
            "provider_id": 1,
            "variables": {"name": "John"}
        }

        response = client.post("/generation/generate", json=generation_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.generation.get_db')
    def test_generate_content_provider_not_found(self, mock_get_db, client, mock_template):
        """Test generation with non-existent provider"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_template, None]
        mock_get_db.return_value = mock_db

        generation_data = {
            "template_id": 1,
            "provider_id": 999,
            "variables": {"name": "John"}
        }

        response = client.post("/generation/generate", json=generation_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.generation.get_db')
    def test_batch_generate_success(self, mock_get_db, client, mock_template):
        """Test successful batch generation"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_db.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        batch_data = {
            "template_id": 1,
            "provider_id": 1,
            "items": [
                {"variables": {"name": "John"}},
                {"variables": {"name": "Jane"}}
            ]
        }

        response = client.post("/generation/batch", json=batch_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "processing"

    @patch('app.api.generation.get_db')
    def test_get_generation_status_success(self, mock_get_db, client):
        """Test getting generation status"""
        mock_db = Mock()
        mock_request = Mock(spec=DBGenerationRequest)
        mock_request.id = 1
        mock_request.status = "completed"
        mock_request.result = json.dumps({"content": "Generated content"})
        mock_request.error_message = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_request
        mock_get_db.return_value = mock_db

        response = client.get("/generation/status/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["content"] == "Generated content"

    @patch('app.api.generation.get_db')
    def test_get_generation_status_not_found(self, mock_get_db, client):
        """Test getting status for non-existent generation request"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get("/generation/status/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestQualityCheckEndpoint:
    """Test quality check endpoint"""

    def test_check_content_quality_success(self, client):
        """Test successful content quality check"""
        quality_data = {
            "content": "This is a well-written test content with proper structure and sufficient detail.",
            "rules": ["min_length", "contains_keywords"]
        }

        response = client.post("/generation/quality-check", json=quality_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "is_valid" in data
        assert "score" in data
        assert "issues" in data
        assert "suggestions" in data

    def test_check_content_quality_missing_content(self, client):
        """Test quality check with missing content"""
        quality_data = {
            "rules": ["min_length"]
        }

        response = client.post("/generation/quality-check", json=quality_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_check_content_quality_empty_content(self, client):
        """Test quality check with empty content"""
        quality_data = {
            "content": "",
            "rules": ["min_length"]
        }

        response = client.post("/generation/quality-check", json=quality_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_valid"] is False
        assert data["score"] == 0


class TestErrorHandling:
    """Test general error handling"""

    @patch('app.api.providers.get_db')
    def test_database_error_handling(self, mock_get_db, client):
        """Test handling of database errors"""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = mock_db

        response = client.get("/providers/")

        # Should return 500 for database errors
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in request body"""
        response = client.post(
            "/providers/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.providers.ProviderFactory.create_provider')
    def test_provider_creation_error(self, mock_factory, mock_get_db, client):
        """Test handling of provider creation errors"""
        mock_factory.side_effect = Exception("Invalid provider configuration")

        provider_data = {
            "name": "Test Provider",
            "provider_type": "invalid_type",
            "api_key": "test_key"
        }

        response = client.post("/providers/", json=provider_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR