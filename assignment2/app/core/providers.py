from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import time
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential


class ProviderConfig(BaseModel):
    """Configuration for AI provider"""
    id: Optional[int] = None
    name: str
    provider_type: str  # "openai", "azure_openai"
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GenerationRequest(BaseModel):
    """Request for content generation"""
    system_prompt: str
    user_prompt: str
    variables: Dict[str, Any] = {}
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class GenerationResponse(BaseModel):
    """Response from content generation"""
    content: str
    model_used: str
    tokens_used: int
    processing_time: float
    confidence_score: Optional[float] = None
    error: Optional[str] = None


class QualityCheckResult(BaseModel):
    """Result of quality check"""
    is_valid: bool
    score: int  # 0-100
    issues: List[str]
    suggestions: List[str]


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.retry_config = {
            'wait': wait_exponential(multiplier=1, min=4, max=10),
            'stop': stop_after_attempt(3),
            'retry': retry_if_exception_type((Exception,))
        }

    @abstractmethod
    async def generate_content(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using the AI provider"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the AI provider"""
        pass

    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider configuration"""
        pass

    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template string"""
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing variable in template: {e}")
        except Exception as e:
            raise ValueError(f"Error substituting variables: {e}")


class ProviderFactory:
    """Factory for creating AI providers"""

    @staticmethod
    def create_provider(config: ProviderConfig) -> AIProvider:
        """Create appropriate provider based on config"""
        if config.provider_type.lower() == "openai":
            from app.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config)
        elif config.provider_type.lower() == "azure_openai":
            from app.providers.azure_provider import AzureOpenAIProvider
            return AzureOpenAIProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")


# Tenacity retry configuration
from tenacity import retry_if_exception_type

retry_config = {
    'wait': wait_exponential(multiplier=1, min=4, max=10),
    'stop': stop_after_attempt(3),
    'retry': retry_if_exception_type((Exception,))
}