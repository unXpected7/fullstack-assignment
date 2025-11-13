"""
Unit tests for core providers functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import json

# Import core provider classes
from app.core.providers import (
    ProviderConfig, GenerationRequest, GenerationResponse,
    QualityCheckResult, AIProvider, ProviderFactory, retry_config
)


class TestProviderConfig:
    """Test ProviderConfig model"""

    def test_provider_config_creation_with_minimal_data(self):
        """Test creating provider config with minimal required data"""
        config = ProviderConfig(
            name="Test Provider",
            provider_type="openai",
            api_key="test_key"
        )

        assert config.name == "Test Provider"
        assert config.provider_type == "openai"
        assert config.api_key == "test_key"
        assert config.base_url is None
        assert config.model == "gpt-3.5-turbo"  # Default value
        assert config.max_tokens == 2000  # Default value
        assert config.temperature == 0.7  # Default value
        assert config.timeout == 30  # Default value
        assert config.is_active is True  # Default value

    def test_provider_config_creation_with_all_data(self):
        """Test creating provider config with all data"""
        config = ProviderConfig(
            id=1,
            name="Full Provider",
            provider_type="azure_openai",
            api_key="azure_key",
            base_url="https://example.com",
            model="gpt-4",
            max_tokens=4000,
            temperature=0.5,
            timeout=60,
            is_active=False,
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )

        assert config.id == 1
        assert config.name == "Full Provider"
        assert config.provider_type == "azure_openai"
        assert config.api_key == "azure_key"
        assert config.base_url == "https://example.com"
        assert config.model == "gpt-4"
        assert config.max_tokens == 4000
        assert config.temperature == 0.5
        assert config.timeout == 60
        assert config.is_active is False

    def test_provider_config_serialization(self):
        """Test provider config serialization"""
        config = ProviderConfig(
            name="Test Provider",
            provider_type="openai",
            api_key="secret_key"
        )

        # Test dict conversion
        config_dict = config.model_dump()
        assert config_dict["name"] == "Test Provider"
        assert config_dict["provider_type"] == "openai"
        assert config_dict["api_key"] == "secret_key"

    def test_provider_config_validation(self):
        """Test provider config validation"""
        # Valid configs should not raise exceptions
        ProviderConfig(name="Valid", provider_type="openai", api_key="key")
        ProviderConfig(name="Valid", provider_type="azure_openai", api_key="key")

        # Invalid provider type should still work (validation happens elsewhere)
        config = ProviderConfig(name="Test", provider_type="invalid_type", api_key="key")
        assert config.provider_type == "invalid_type"


class TestGenerationRequest:
    """Test GenerationRequest model"""

    def test_generation_request_creation_minimal(self):
        """Test creating generation request with minimal data"""
        request = GenerationRequest(
            system_prompt="System prompt",
            user_prompt="User prompt"
        )

        assert request.system_prompt == "System prompt"
        assert request.user_prompt == "User prompt"
        assert request.variables == {}
        assert request.max_tokens is None
        assert request.temperature is None

    def test_generation_request_creation_with_all_data(self):
        """Test creating generation request with all data"""
        variables = {"name": "John", "age": 30}
        request = GenerationRequest(
            system_prompt="System prompt",
            user_prompt="Hello {name}",
            variables=variables,
            max_tokens=1000,
            temperature=0.8
        )

        assert request.system_prompt == "System prompt"
        assert request.user_prompt == "Hello {name}"
        assert request.variables == variables
        assert request.max_tokens == 1000
        assert request.temperature == 0.8

    def test_generation_request_complex_variables(self):
        """Test generation request with complex variables"""
        variables = {
            "user": {"name": "John", "age": 30},
            "items": ["item1", "item2"],
            "count": 42,
            "active": True
        }

        request = GenerationRequest(
            system_prompt="Test",
            user_prompt="Test",
            variables=variables
        )

        assert request.variables == variables
        assert request.variables["user"]["name"] == "John"
        assert request.variables["items"][0] == "item1"


class TestGenerationResponse:
    """Test GenerationResponse model"""

    def test_generation_response_creation_success(self):
        """Test creating successful generation response"""
        response = GenerationResponse(
            content="Generated content",
            model_used="gpt-3.5-turbo",
            tokens_used=150,
            processing_time=2.5,
            confidence_score=0.95
        )

        assert response.content == "Generated content"
        assert response.model_used == "gpt-3.5-turbo"
        assert response.tokens_used == 150
        assert response.processing_time == 2.5
        assert response.confidence_score == 0.95
        assert response.error is None

    def test_generation_response_creation_with_error(self):
        """Test creating generation response with error"""
        response = GenerationResponse(
            content="",
            model_used="gpt-3.5-turbo",
            tokens_used=0,
            processing_time=1.0,
            error="API rate limit exceeded"
        )

        assert response.content == ""
        assert response.error == "API rate limit exceeded"
        assert response.confidence_score is None

    def test_generation_response_optional_fields(self):
        """Test generation response with optional fields omitted"""
        response = GenerationResponse(
            content="Content",
            model_used="gpt-4",
            tokens_used=100,
            processing_time=1.5
        )

        assert response.confidence_score is None
        assert response.error is None


class TestQualityCheckResult:
    """Test QualityCheckResult model"""

    def test_quality_check_result_perfect(self):
        """Test quality check result for perfect content"""
        result = QualityCheckResult(
            is_valid=True,
            score=100,
            issues=[],
            suggestions=[]
        )

        assert result.is_valid is True
        assert result.score == 100
        assert result.issues == []
        assert result.suggestions == []

    def test_quality_check_result_with_issues(self):
        """Test quality check result with issues"""
        result = QualityCheckResult(
            is_valid=False,
            score=45,
            issues=["Content too short", "Missing keywords"],
            suggestions=["Add more detail", "Include relevant keywords"]
        )

        assert result.is_valid is False
        assert result.score == 45
        assert len(result.issues) == 2
        assert "Content too short" in result.issues
        assert len(result.suggestions) == 2
        assert "Add more detail" in result.suggestions


class MockAIProvider(AIProvider):
    """Mock implementation of AIProvider for testing"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.call_count = 0
        self.last_request = None

    async def generate_content(self, request: GenerationRequest) -> GenerationResponse:
        self.call_count += 1
        self.last_request = request

        # Simulate processing time
        await asyncio.sleep(0.01)

        return GenerationResponse(
            content=f"Generated: {request.user_prompt}",
            model_used=self.config.model,
            tokens_used=100,
            processing_time=0.1
        )

    async def test_connection(self) -> bool:
        return True

    def validate_config(self) -> list:
        issues = []
        if not self.config.api_key:
            issues.append("API key is required")
        return issues


class TestAIProvider:
    """Test AIProvider abstract class through mock implementation"""

    @pytest.fixture
    def mock_config(self):
        """Create mock provider config"""
        return ProviderConfig(
            name="Mock Provider",
            provider_type="mock",
            api_key="mock_key",
            model="mock-model"
        )

    @pytest.fixture
    def mock_provider(self, mock_config):
        """Create mock AI provider instance"""
        return MockAIProvider(mock_config)

    def test_provider_initialization(self, mock_provider, mock_config):
        """Test provider initialization"""
        assert mock_provider.config == mock_config
        assert mock_provider.call_count == 0

    def test_substitute_variables_success(self, mock_provider):
        """Test successful variable substitution"""
        template = "Hello {name}, you are {age} years old."
        variables = {"name": "John", "age": 30}

        result = mock_provider._substitute_variables(template, variables)

        assert result == "Hello John, you are 30 years old."

    def test_substitute_variables_missing_key(self, mock_provider):
        """Test variable substitution with missing key"""
        template = "Hello {name}, you are {age} years old."
        variables = {"name": "John"}  # Missing 'age'

        with pytest.raises(ValueError, match="Missing variable"):
            mock_provider._substitute_variables(template, variables)

    def test_substitute_variables_extra_variables(self, mock_provider):
        """Test variable substitution with extra variables"""
        template = "Hello {name}"
        variables = {"name": "John", "age": 30, "city": "NYC"}  # Extra variables

        result = mock_provider._substitute_variables(template, variables)

        assert result == "Hello John"

    def test_substitute_variables_complex_types(self, mock_provider):
        """Test variable substitution with complex types"""
        template = "User: {user}, Items: {items}"
        variables = {
            "user": {"name": "John", "age": 30},
            "items": ["item1", "item2"]
        }

        result = mock_provider._substitute_variables(template, variables)

        assert "User: {'name': 'John', 'age': 30}" in result
        assert "Items: ['item1', 'item2']" in result

    def test_substitute_variables_empty_template(self, mock_provider):
        """Test variable substitution with empty template"""
        template = ""
        variables = {"name": "John"}

        result = mock_provider._substitute_variables(template, variables)

        assert result == ""

    def test_substitute_variables_no_variables(self, mock_provider):
        """Test variable substitution with no variables"""
        template = "Hello World"
        variables = {}

        result = mock_provider._substitute_variables(template, variables)

        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_generate_content(self, mock_provider):
        """Test content generation"""
        request = GenerationRequest(
            system_prompt="Test system",
            user_prompt="Hello {name}",
            variables={"name": "John"}
        )

        response = await mock_provider.generate_content(request)

        assert response.content == "Generated: Hello John"
        assert response.model_used == "mock-model"
        assert response.tokens_used == 100
        assert response.processing_time > 0
        assert mock_provider.call_count == 1

    @pytest.mark.asyncio
    async def test_test_connection(self, mock_provider):
        """Test connection testing"""
        result = await mock_provider.test_connection()
        assert result is True

    def test_validate_config_valid(self, mock_provider):
        """Test configuration validation with valid config"""
        issues = mock_provider.validate_config()
        assert issues == []

    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config"""
        config = ProviderConfig(
            name="Invalid Provider",
            provider_type="mock",
            api_key=""  # Empty API key
        )
        provider = MockAIProvider(config)

        issues = provider.validate_config()
        assert len(issues) > 0
        assert any("API key" in issue for issue in issues)

    def test_retry_config_initialization(self, mock_provider):
        """Test retry configuration initialization"""
        assert 'wait' in mock_provider.retry_config
        assert 'stop' in mock_provider.retry_config
        assert 'retry' in mock_provider.retry_config


class TestProviderFactory:
    """Test ProviderFactory class"""

    @patch('app.providers.openai_provider.OpenAIProvider')
    def test_create_openai_provider(self, mock_openai_class):
        """Test creating OpenAI provider"""
        config = ProviderConfig(
            name="OpenAI Provider",
            provider_type="openai",
            api_key="openai_key"
        )

        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        provider = ProviderFactory.create_provider(config)

        mock_openai_class.assert_called_once_with(config)
        assert provider == mock_openai_instance

    @patch('app.providers.azure_provider.AzureOpenAIProvider')
    def test_create_azure_provider(self, mock_azure_class):
        """Test creating Azure OpenAI provider"""
        config = ProviderConfig(
            name="Azure Provider",
            provider_type="azure_openai",
            api_key="azure_key",
            base_url="https://example.com"
        )

        mock_azure_instance = Mock()
        mock_azure_class.return_value = mock_azure_instance

        provider = ProviderFactory.create_provider(config)

        mock_azure_class.assert_called_once_with(config)
        assert provider == mock_azure_instance

    def test_create_provider_case_insensitive(self):
        """Test that provider type is case insensitive"""
        with patch('app.providers.openai_provider.OpenAIProvider') as mock_openai:
            mock_openai.return_value = Mock()

            # Test lowercase
            config1 = ProviderConfig(name="Test1", provider_type="openai", api_key="key")
            ProviderFactory.create_provider(config1)

            # Test uppercase
            config2 = ProviderConfig(name="Test2", provider_type="OPENAI", api_key="key")
            ProviderFactory.create_provider(config2)

            # Test mixed case
            config3 = ProviderConfig(name="Test3", provider_type="OpenAI", api_key="key")
            ProviderFactory.create_provider(config3)

            # All should call the same OpenAI provider
            assert mock_openai.call_count == 3

    def test_create_unsupported_provider_type(self):
        """Test creating provider with unsupported type"""
        config = ProviderConfig(
            name="Unsupported Provider",
            provider_type="unsupported_type",
            api_key="key"
        )

        with pytest.raises(ValueError, match="Unsupported provider type"):
            ProviderFactory.create_provider(config)

    def test_create_provider_with_azure_case_variations(self):
        """Test Azure provider creation with different case variations"""
        with patch('app.providers.azure_provider.AzureOpenAIProvider') as mock_azure:
            mock_azure.return_value = Mock()

            # Test different case variations
            variations = ["azure_openai", "AZURE_OPENAI", "Azure_OpenAI"]

            for variation in variations:
                config = ProviderConfig(
                    name=f"Test {variation}",
                    provider_type=variation,
                    api_key="key"
                )
                ProviderFactory.create_provider(config)

            assert mock_azure.call_count == len(variations)


class TestRetryConfig:
    """Test retry configuration"""

    def test_retry_config_structure(self):
        """Test retry configuration structure"""
        assert 'wait' in retry_config
        assert 'stop' in retry_config
        assert 'retry' in retry_config

    @patch('tenacity.stop_after_attempt')
    @patch('tenacity.wait_exponential')
    @patch('tenacity.retry_if_exception_type')
    def test_retry_config_components(self, mock_retry, mock_wait, mock_stop):
        """Test retry configuration components"""
        # Re-import to trigger the component creation
        from app.core.providers import retry_config

        # Verify that tenacity functions were called
        mock_wait.assert_called()
        mock_stop.assert_called()
        mock_retry.assert_called()

    def test_retry_config_values(self):
        """Test retry configuration values"""
        # These are the expected values from the implementation
        expected_wait_multiplier = 1
        expected_wait_min = 4
        expected_wait_max = 10
        expected_stop_attempts = 3

        # The actual configuration should have these values
        wait_config = retry_config['wait']
        stop_config = retry_config['stop']

        # Verify configuration structure
        assert hasattr(wait_config, 'multiplier')
        assert hasattr(wait_config, 'min')
        assert hasattr(wait_config, 'max')


class TestIntegrationScenarios:
    """Integration tests for core providers"""

    @pytest.mark.asyncio
    async def test_provider_lifecycle(self):
        """Test complete provider lifecycle"""
        # Create provider
        config = ProviderConfig(
            name="Test Provider",
            provider_type="mock",
            api_key="test_key"
        )
        provider = MockAIProvider(config)

        # Validate config
        issues = provider.validate_config()
        assert len(issues) == 0

        # Test connection
        connection_ok = await provider.test_connection()
        assert connection_ok is True

        # Generate content
        request = GenerationRequest(
            system_prompt="Test",
            user_prompt="Hello {name}",
            variables={"name": "World"}
        )
        response = await provider.generate_content(request)

        assert response.content == "Generated: Hello World"
        assert response.model_used == config.model
        assert response.tokens_used > 0
        assert response.processing_time > 0

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in provider operations"""
        config = ProviderConfig(
            name="Error Provider",
            provider_type="mock",
            api_key="test_key"
        )
        provider = MockAIProvider(config)

        # Test template error
        with pytest.raises(ValueError):
            provider._substitute_variables("Hello {missing_var}", {})

    def test_provider_factory_error_scenarios(self):
        """Test error scenarios in provider factory"""
        # Test None config
        with pytest.raises(AttributeError):
            ProviderFactory.create_provider(None)

        # Test config with missing provider_type
        config = ProviderConfig(name="Test", provider_type="", api_key="key")
        with pytest.raises(ValueError, match="Unsupported provider type"):
            ProviderFactory.create_provider(config)