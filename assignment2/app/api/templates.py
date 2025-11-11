from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db, Template
from app.services.template_service import TemplateService
from app.api.schemas import (
    TemplateCreate, TemplateUpdate, TemplateResponse
)

router = APIRouter(prefix="/api/v1/ai/templates", tags=["AI Templates"])


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new template"""
    # Check if template with same name already exists
    existing_template = db.query(Template).filter(
        Template.name == template_data.name
    ).first()
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template_data.name}' already exists"
        )

    template_service = TemplateService(db)
    template = template_service.create_template(template_data.model_dump())

    return template


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all templates"""
    template_service = TemplateService(db)
    templates = template_service.get_all_templates(active_only=active_only)

    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific template by ID"""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )

    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a template"""
    template_service = TemplateService(db)
    template = template_service.update_template(template_id, template_data.model_dump(exclude_unset=True))

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )

    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Delete a template"""
    template_service = TemplateService(db)
    deleted = template_service.delete_template(template_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )

    return {"message": f"Template with ID {template_id} deleted successfully"}


@router.post("/production-volume", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_production_volume_template(
    db: Session = Depends(get_db)
):
    """Create the Production Volume template"""
    template_service = TemplateService(db)

    # Check if production volume template already exists
    existing_template = template_service.get_production_volume_template()
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Production Volume template already exists"
        )

    template = template_service.create_production_volume_template()
    return template


@router.get("/production-volume", response_model=TemplateResponse)
async def get_production_volume_template(
    db: Session = Depends(get_db)
):
    """Get the Production Volume template"""
    template_service = TemplateService(db)
    template = template_service.get_production_volume_template()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production Volume template not found"
        )

    return template


@router.post("/{template_id}/validate")
async def validate_template_output(
    template_id: int,
    content: str,
    db: Session = Depends(get_db)
):
    """Validate template output against quality rules"""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )

    validation_result = template_service.validate_template_output(template, content)

    return validation_result