from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import asyncio
from typing import List

from app.models.database import get_db, GenerationTask, Template, AIProvider
from app.services.template_service import TemplateService
from app.services.quality_service import QualityService
from app.core.providers import ProviderFactory, GenerationRequest, GenerationResponse
from app.api.schemas import (
    GenerationRequest as GenerationRequestSchema,
    BatchGenerationRequest,
    GenerationResponse as GenerationResponseSchema,
    GenerationStatusResponse,
    QualityCheckRequest,
    QualityCheckResponse
)
from app.models.database import get_db, GenerationTask

router = APIRouter(prefix="/api/v1/ai/generate", tags=["Content Generation"])


@router.post("/", response_model=GenerationResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def generate_content(
    request: GenerationRequestSchema,
    db: Session = Depends(get_db)
):
    """Generate content using AI"""
    # Validate template
    template_service = TemplateService(db)
    template = template_service.get_template(request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {request.template_id} not found"
        )

    # Get provider (use template's default or specified provider)
    if request.provider_id:
        provider = db.query(AIProvider).filter(AIProvider.id == request.provider_id).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider with ID {request.provider_id} not found"
            )
    else:
        # Use first active provider as default
        provider = db.query(AIProvider).filter(AIProvider.is_active == True).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active provider available"
            )
        request.provider_id = provider.id

    # Create generation task
    task_id = str(uuid.uuid4())
    task = GenerationTask(
        task_id=task_id,
        template_id=request.template_id,
        provider_id=request.provider_id,
        input_data=request.input_data,
        status="pending"
    )
    db.add(task)
    db.commit()

    # Run generation in background
    asyncio.create_task(_run_generation_task(task_id, db))

    return GenerationResponseSchema(
        task_id=task_id,
        status="pending",
        message="Content generation started",
        estimated_time=30  # Rough estimate
    )


@router.post("/batch", response_model=GenerationResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def generate_content_batch(
    request: BatchGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate content for multiple inputs in batch"""
    # Validate template
    template_service = TemplateService(db)
    template = template_service.get_template(request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {request.template_id} not found"
        )

    # Get provider (use template's default or specified provider)
    if request.provider_id:
        provider = db.query(AIProvider).filter(AIProvider.id == request.provider_id).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider with ID {request.provider_id} not found"
            )
    else:
        # Use first active provider as default
        provider = db.query(AIProvider).filter(AIProvider.is_active == True).first()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active provider available"
            )
        request.provider_id = provider.id

    # Create generation tasks for each input
    task_ids = []
    for input_data in request.input_data_list:
        task_id = str(uuid.uuid4())
        task = GenerationTask(
            task_id=task_id,
            template_id=request.template_id,
            provider_id=request.provider_id,
            input_data=input_data,
            status="pending"
        )
        db.add(task)
        task_ids.append(task_id)

    db.commit()

    # Run generation tasks in parallel (with concurrency limit)
    await asyncio.gather(*[_run_generation_task(task_id, db) for task_id in task_ids])

    return GenerationResponseSchema(
        task_id=f"batch_{uuid.uuid4()}",
        status="pending",
        message=f"Batch generation started for {len(request.input_data_list)} items",
        estimated_time=60  # Rough estimate for batch
    )


@router.get("/{task_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get generation status for a task"""
    task = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation task with ID {task_id} not found"
        )

    return task


@router.post("/quality-check", response_model=QualityCheckResponse)
async def check_content_quality(
    request: QualityCheckRequest,
    db: Session = Depends(get_db)
):
    """Check content quality against rules"""
    if request.template_rules:
        # Use provided template rules
        quality_result = QualityService.check_content_quality(request.content, request.template_rules)
    else:
        # Use general quality check
        quality_result = QualityService.check_content_quality(request.content, {})

    return QualityCheckResponse(
        is_valid=quality_result.is_valid,
        score=quality_result.score,
        issues=quality_result.issues,
        suggestions=quality_result.suggestions
    )


async def _run_generation_task(task_id: str, db: Session):
    """Background task to run content generation"""
    try:
        # Get task from database
        task = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
        if not task:
            return

        # Update status to processing
        task.status = "processing"
        db.commit()

        # Get provider and template
        provider = db.query(AIProvider).filter(AIProvider.id == task.provider_id).first()
        template = db.query(Template).filter(Template.id == task.template_id).first()

        if not provider or not template:
            task.status = "failed"
            task.error_message = "Provider or template not found"
            db.commit()
            return

        # Create provider instance
        provider_config = None
        if provider.provider_type == "openai":
            from app.core.providers import ProviderConfig
            provider_config = ProviderConfig(
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

        provider_instance = ProviderFactory.create_provider(provider_config)

        # Create generation request
        template_service = TemplateService(db)
        gen_request = template_service.create_generation_request(task.template_id, task.input_data)

        # Generate content
        start_time = asyncio.get_event_loop().time()
        gen_response = await provider_instance.generate_content(gen_request)
        end_time = asyncio.get_event_loop().time()

        # Update task with results
        task.status = "completed" if gen_response.content and not gen_response.error else "failed"
        task.generated_content = gen_response.content
        task.confidence_score = gen_response.confidence_score
        task.tokens_used = gen_response.tokens_used
        task.processing_time = end_time - start_time
        task.error_message = gen_response.error

        # Validate output quality
        validation_result = template_service.validate_template_output(template, gen_response.content)
        if not validation_result["is_valid"]:
            task.error_message = f"Quality validation failed: {', '.join(validation_result['issues'])}"
            task.status = "failed"

        db.commit()

    except Exception as e:
        # Update task with error
        task = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()