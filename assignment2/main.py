from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.providers import router as providers_router
from app.api.templates import router as templates_router
from app.api.generation import router as generation_router
from app.models.database import create_tables
from app.utils.excel_reader import ExcelReader
import os
from dotenv import load_dotenv

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Content Generation System",
    description="An AI-powered content generation system with configurable providers and templates",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(providers_router)
app.include_router(templates_router)
app.include_router(generation_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database and sample data on startup"""
    create_tables()

    # Initialize production volume template if it doesn't exist
    from app.services.template_service import TemplateService
    from app.models.database import SessionLocal

    db = SessionLocal()
    try:
        template_service = TemplateService(db)
        if not template_service.get_production_volume_template():
            template_service.create_production_volume_template()
            print("Production Volume template created")
    except Exception as e:
        print(f"Error creating Production Volume template: {e}")
    finally:
        db.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Content Generation System",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "providers": "/api/v1/ai/providers",
            "templates": "/api/v1/ai/templates",
            "generation": "/api/v1/ai/generate"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}


@app.post("/load-sample-data")
async def load_sample_data():
    """Load sample SKU data for testing"""
    try:
        # Check if SKU file exists
        sku_file = "sku_sample.xlsx"
        if not os.path.exists(sku_file):
            raise HTTPException(
                status_code=404,
                detail=f"Sample file {sku_file} not found"
            )

        # Read and validate the data
        from app.utils.excel_reader import ExcelReader

        # Validate required columns
        required_columns = ["wine_id", "full_wine_name", "vintage", "winery", "region", "ranking"]
        validation = ExcelReader.validate_required_columns(sku_file, required_columns)

        if not validation["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {validation['missing_columns']}"
            )

        # Get statistics
        stats = ExcelReader.get_statistics(sku_file)

        return {
            "message": "Sample data loaded successfully",
            "file_path": sku_file,
            "statistics": stats,
            "validation": validation
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading sample data: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )