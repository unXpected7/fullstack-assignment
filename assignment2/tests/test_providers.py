import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.providers.openai_provider import OpenAIProvider
from app.providers.azure_provider import AzureOpenAIProvider
from app.core.providers import ProviderConfig, GenerationRequest


class TestOpenAIProvider:
    """Test cases for OpenAI Provider"""

    def setup_method(self):
        """Setup test data"""
        self.config = ProviderConfig(
            name="Test OpenAI Provider",
            provider_type="openai",
            api_key="test_api_key",
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7
        )

    @pytest.mark.asyncio
    async def test_generate_content_success(self):
        """Test successful content generation"""
        # Mock OpenAI client
        with patch('app.providers.openai_provider.openai.AsyncOpenAI') as mock_client:
            # Mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage = Mock()
            mock_response.usage.total_tokens = 100

            mock_client.return_value = Mock()
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(self.config)
            request = GenerationRequest(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt",
                variables={"name": "test"}
            )

            result = await provider.generate_content(request)

            assert result.content == "Test response"
            assert result.model_used == "gpt-3.5-turbo"
            assert result.tokens_used == 100
            assert result.error is None

    @pytest.mark.asyncio
    async def test_generate_content_error(self):
        """Test content generation with error"""
        with patch('app.providers.openai_provider.openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

            provider = OpenAIProvider(self.config)
            request = GenerationRequest(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt"
            )

            result = await provider.generate_content(request)

            assert result.content == ""
            assert result.error == "API Error"

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection"""
        with patch('app.providers.openai_provider.openai.AsyncOpenAI') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "test"

            mock_client.return_value = Mock()
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(self.config)
            result = await provider.test_connection()

            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection failure"""
        with patch('app.providers.openai_provider.openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(side_effect=Exception("Connection Error"))

            provider = OpenAIProvider(self.config)
            result = await provider.test_connection()

            assert result is False

    def test_validate_config_success(self):
        """Test successful configuration validation"""
        provider = OpenAIProvider(self.config)
        errors = provider.validate_config()

        assert len(errors) == 0

    def test_validate_config_missing_api_key(self):
        """Test configuration validation with missing API key"""
        config = ProviderConfig(
            name="Test Provider",
            provider_type="openai",
            api_key="",
            model="gpt-3.5-turbo"
        )

        provider = OpenAIProvider(config)
        errors = provider.validate_config()

        assert "API key is required" in errors

    def test_variable_substitution(self):
        """Test variable substitution in prompts"""
        provider = OpenAIProvider(self.config)

        template = "Hello {name}, you are {age} years old"
        variables = {"name": "John", "age": "30"}

        result = provider._substitute_variables(template, variables)

        assert result == "Hello John, you are 30 years old"


class TestAzureOpenAIProvider:
    """Test cases for Azure OpenAI Provider"""

    def setup_method(self):
        """Setup test data"""
        self.config = ProviderConfig(
            name="Test Azure Provider",
            provider_type="azure_openai",
            api_key="test_api_key",
            base_url="https://test-resource.openai.azure.com/",
            model="deployment-name",
            max_tokens=1000,
            temperature=0.7
        )

    @pytest.mark.asyncio
    async def test_generate_content_success(self):
        """Test successful content generation"""
        with patch('app.providers.azure_provider.openai.AsyncAzureOpenAI') as mock_client:
            # Mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Azure test response"
            mock_response.usage = Mock()
            mock_response.usage.total_tokens = 150

            mock_client.return_value = Mock()
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = AzureOpenAIProvider(self.config)
            request = GenerationRequest(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt"
            )

            result = await provider.generate_content(request)

            assert result.content == "Azure test response"
            assert result.model_used == "deployment-name"
            assert result.tokens_used == 150

    def test_is_valid_azure_endpoint(self):
        """Test Azure endpoint validation"""
        provider = AzureOpenAIProvider(self.config)

        # Valid endpoint
        assert provider._is_valid_azure_endpoint() is True

        # Invalid endpoint
        invalid_config = ProviderConfig(
            name="Invalid Azure Provider",
            provider_type="azure_openai",
            api_key="test_key",
            base_url="https://invalid-url.com/",
            model="test"
        )

        invalid_provider = AzureOpenAIProvider(invalid_config)
        assert invalid_provider._is_valid_azure_endpoint() is False

    def test_validate_config_missing_endpoint(self):
        """Test configuration validation with missing endpoint"""
        config = ProviderConfig(
            name="Test Azure Provider",
            provider_type="azure_openai",
            api_key="test_key",
            model="test"
        )

        provider = AzureOpenAIProvider(config)
        errors = provider.validate_config()

        assert "Azure endpoint URL is required" in errors