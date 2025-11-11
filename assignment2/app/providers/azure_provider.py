import openai
import httpx
from typing import Dict, Any, Optional
from app.core.providers import AIProvider, ProviderConfig, GenerationRequest, GenerationResponse
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import json
from azure.identity import DefaultAzureCredential


class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI provider implementation"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = self._initialize_client()
        self.deployment_name = config.model  # In Azure, deployment name is the model identifier

    def _initialize_client(self) -> openai.AsyncAzureOpenAI:
        """Initialize Azure OpenAI client"""
        # Use DefaultAzureCredential for authentication
        if not self.config.base_url:
            raise ValueError("Azure endpoint URL is required")

        return openai.AsyncAzureOpenAI(
            azure_endpoint=self.config.base_url,
            api_key=self.config.api_key,  # API key can be used as alternative to DefaultAzureCredential
            api_version="2023-12-01-preview",  # This is the standard version for most models
            azure_ad_token="",
            azure_ad_token_provider=None  # We'll use API key for simplicity
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: None
    )
    async def generate_content(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using Azure OpenAI API"""
        start_time = time.time()

        try:
            # Substitute variables in prompts
            system_prompt = self._substitute_variables(request.system_prompt, request.variables)
            user_prompt = self._substitute_variables(request.user_prompt, request.variables)

            # Prepare API request with Azure-specific parameters
            api_request = {
                "deployment_id": self.deployment_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
            }

            # Make API call
            response = await self.client.chat.completions.create(**api_request)

            end_time = time.time()
            processing_time = end_time - start_time

            # Extract response content
            content = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Calculate confidence score based on response quality
            confidence_score = self._calculate_confidence_score(response)

            return GenerationResponse(
                content=content,
                model_used=self.deployment_name,
                tokens_used=tokens_used,
                processing_time=processing_time,
                confidence_score=confidence_score
            )

        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time

            return GenerationResponse(
                content="",
                model_used=self.deployment_name,
                tokens_used=0,
                processing_time=processing_time,
                error=str(e)
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: False
    )
    async def test_connection(self) -> bool:
        """Test connection to Azure OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                deployment_id=self.deployment_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return response.choices[0].message.content is not None
        except Exception:
            return False

    def validate_config(self) -> list[str]:
        """Validate Azure OpenAI provider configuration"""
        errors = []

        if not self.config.api_key:
            errors.append("API key is required for Azure OpenAI")

        if not self.config.name:
            errors.append("Provider name is required")

        if not self.config.base_url:
            errors.append("Azure endpoint URL is required")

        if not self.deployment_name:
            errors.append("Deployment name is required")

        if not (0 <= self.config.temperature <= 2):
            errors.append("Temperature must be between 0 and 2")

        if self.config.max_tokens < 1 or self.config.max_tokens > 200000:
            errors.append("Max tokens must be between 1 and 200000")

        # Azure-specific validation
        if not self._is_valid_azure_endpoint():
            errors.append("Invalid Azure endpoint URL format")

        return errors

    def _is_valid_azure_endpoint(self) -> bool:
        """Validate Azure endpoint URL format"""
        if not self.config.base_url:
            return False

        # Check if it's a valid Azure endpoint
        if "openai.azure.com" not in self.config.base_url:
            return False

        # Basic URL format validation
        if not self.config.base_url.startswith("https://"):
            return False

        return True

    def _calculate_confidence_score(self, response) -> float:
        """Calculate confidence score based on response quality"""
        score = 75.0  # Base score for Azure (slightly lower than OpenAI)

        # Adjust based on response length
        if response.usage and response.usage.total_tokens > 100:
            score += 10
        elif response.usage and response.usage.total_tokens < 50:
            score -= 20

        # Adjust based on stop reason
        if hasattr(response.choices[0], 'finish_reason'):
            if response.choices[0].finish_reason == 'stop':
                score += 10
            elif response.choices[0].finish_reason == 'length':
                score -= 10

        # Azure-specific factors
        if hasattr(response, 'id'):
            score += 5  # Azure responses have unique IDs

        # Clamp score between 0 and 100
        return max(0.0, min(100.0, score))