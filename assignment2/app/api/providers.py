from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import get_db, AIProvider
from app.core.providers import ProviderConfig, ProviderFactory
from app.api.schemas import (
    ProviderConfigCreate, ProviderConfigUpdate, ProviderConfigResponse,
    TestProviderRequest, TestProviderResponse
)
from app.core.providers import GenerationRequest

router = APIRouter(prefix="/api/v1/ai/providers", tags=["AI Providers"])


@router.post("/", response_model=ProviderConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new AI provider"""
    # Check if provider with same name already exists
    existing_provider = db.query(AIProvider).filter(
        AIProvider.name == provider_data.name
    ).first()
    if existing_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider with name '{provider_data.name}' already exists"
        )

    # Create provider in database
    db_provider = AIProvider(
        name=provider_data.name,
        provider_type=provider_data.provider_type,
        api_key=provider_data.api_key,
        base_url=provider_data.base_url,
        model=provider_data.model,
        max_tokens=provider_data.max_tokens,
        temperature=provider_data.temperature,
        timeout=provider_data.timeout,
        is_active=provider_data.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)

    return db_provider


@router.get("/", response_model=List[ProviderConfigResponse])
async def list_providers(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all AI providers"""
    query = db.query(AIProvider)
    if active_only:
        query = query.filter(AIProvider.is_active == True)

    return query.all()


@router.get("/{provider_id}", response_model=ProviderConfigResponse)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific AI provider by ID"""
    provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with ID {provider_id} not found"
        )
    return provider


@router.put("/{provider_id}", response_model=ProviderConfigResponse)
async def update_provider(
    provider_id: int,
    provider_data: ProviderConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update an AI provider"""
    provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with ID {provider_id} not found"
        )

    # Update provider fields
    update_data = provider_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)

    provider.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(provider)

    return provider


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Delete an AI provider"""
    provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with ID {provider_id} not found"
        )

    db.delete(provider)
    db.commit()

    return {"message": f"Provider with ID {provider_id} deleted successfully"}


@router.post("/{provider_id}/test", response_model=TestProviderResponse)
async def test_provider_connection(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Test connection to an AI provider"""
    provider = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with ID {provider_id} not found"
        )

    try:
        # Create provider config
        config = ProviderConfig(
            name=provider.name,
            provider_type=provider.provider_type,
            api_key=provider.api_key,
            base_url=provider.base_url,
            model=provider.model,
            max_tokens=provider.max_tokens,
            temperature=provider.temperature,
            timeout=provider.timeout,
            is_active=provider.is_active
        )

        # Create provider instance
        provider_instance = ProviderFactory.create_provider(config)

        # Test connection
        import time
        start_time = time.time()
        is_connected = await provider_instance.test_connection()
        response_time = time.time() - start_time

        return TestProviderResponse(
            is_connected=is_connected,
            response_time=response_time if is_connected else None,
            error_message=None if is_connected else "Connection test failed",
            test_result="Connection successful" if is_connected else "Connection failed"
        )

    except Exception as e:
        return TestProviderResponse(
            is_connected=False,
            response_time=None,
            error_message=str(e),
            test_result="Connection failed with error"
        )