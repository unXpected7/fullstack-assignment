from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class ProviderConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., pattern="^(openai|azure_openai)$")
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = None
    model: str = Field(default="gpt-3.5-turbo")
    max_tokens: int = Field(default=2000, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0, le=2)
    timeout: int = Field(default=30, ge=1, le=300)


class ProviderConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider_type: Optional[str] = Field(None, pattern="^(openai|azure_openai)$")
    api_key: Optional[str] = Field(None, min_length=1)
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=200000)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    timeout: Optional[int] = Field(None, ge=1, le=300)
    is_active: Optional[bool] = None


class ProviderConfigResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    api_key: str
    base_url: Optional[str]
    model: str
    max_tokens: int
    temperature: float
    timeout: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=1)
    user_prompt_template: str = Field(..., min_length=1)
    output_format_requirements: Optional[str] = None
    quality_check_rules: Optional[Dict[str, Any]] = None
    is_active: bool = True


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    user_prompt_template: Optional[str] = Field(None, min_length=1)
    output_format_requirements: Optional[str] = None
    quality_check_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    system_prompt: str
    user_prompt_template: str
    output_format_requirements: Optional[str]
    quality_check_rules: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerationRequest(BaseModel):
    template_id: int = Field(..., ge=1)
    input_data: Dict[str, Any] = Field(..., min_items=1)
    provider_id: Optional[int] = Field(None, ge=1)
    max_tokens: Optional[int] = Field(None, ge=1, le=200000)
    temperature: Optional[float] = Field(None, ge=0, le=2)


class BatchGenerationRequest(BaseModel):
    template_id: int = Field(..., ge=1)
    input_data_list: List[Dict[str, Any]] = Field(..., min_items=1)
    provider_id: Optional[int] = Field(None, ge=1)
    max_tokens: Optional[int] = Field(None, ge=1, le=200000)
    temperature: Optional[float] = Field(None, ge=0, le=2)


class GenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_time: Optional[float] = None


class GenerationStatusResponse(BaseModel):
    task_id: str
    status: str
    input_data: Optional[Dict[str, Any]] = None
    generated_content: Optional[str] = None
    confidence_score: Optional[float] = None
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualityCheckRequest(BaseModel):
    content: str = Field(..., min_length=1)
    template_rules: Optional[Dict[str, Any]] = None


class QualityCheckResponse(BaseModel):
    is_valid: bool
    score: int = Field(..., ge=0, le=100)
    issues: List[str]
    suggestions: List[str]


class TestProviderRequest(BaseModel):
    provider_id: int = Field(..., ge=1)


class TestProviderResponse(BaseModel):
    is_connected: bool
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    test_result: Optional[str] = None