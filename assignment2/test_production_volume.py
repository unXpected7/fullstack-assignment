#!/usr/bin/env python3
"""
Test script for Production Volume generation template
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.excel_reader import ExcelReader
from app.models.database import get_db, create_tables
from app.services.template_service import TemplateService
from app.core.providers import ProviderConfig, ProviderFactory
from app.api.schemas import GenerationRequestSchema
from app.models.database import GenerationTask


def load_test_data():
    """Load test data from Excel file"""
    try:
        data = ExcelReader.read_excel_data("sku_sample.xlsx")
        print(f"Loaded {len(data)} wine records")

        # Get required columns for production volume generation
        required_columns = ["wine_id", "full_wine_name", "vintage", "winery", "region", "ranking"]
        validation = ExcelReader.validate_required_columns("sku_sample.xlsx", required_columns)

        if not validation["is_valid"]:
            print(f"Error: Missing required columns: {validation['missing_columns']}")
            return []

        # Filter for sample data (first 5 records)
        sample_data = data[:5]
        print(f"Using first {len(sample_data)} records for testing")

        for i, item in enumerate(sample_data):
            print(f"Record {i+1}: {item['wine_id']} - {item['full_wine_name']}")

        return sample_data

    except Exception as e:
        print(f"Error loading test data: {e}")
        return []


def test_template_creation():
    """Test template creation"""
    print("\n=== Testing Template Creation ===")

    db = next(get_db())
    try:
        template_service = TemplateService(db)

        # Check if production volume template exists
        template = template_service.get_production_volume_template()
        if template:
            print(f"Production Volume template found: {template.name}")
            print(f"Template ID: {template.id}")
            return template.id
        else:
            print("Creating Production Volume template...")
            template = template_service.create_production_volume_template()
            print(f"Template created with ID: {template.id}")
            return template.id

    except Exception as e:
        print(f"Error in template creation: {e}")
        return None
    finally:
        db.close()


def mock_provider_test():
    """Test provider creation with mocked responses"""
    print("\n=== Testing Provider Configuration ===")

    db = next(get_db())
    try:
        from app.models.database import AIProvider

        # Create a test provider
        from datetime import datetime
        provider = AIProvider(
            name="Test Provider",
            provider_type="openai",
            api_key="test_key",
            model="gpt-3.5-turbo",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(provider)
        db.commit()
        db.refresh(provider)

        print(f"Test provider created with ID: {provider.id}")
        return provider.id

    except Exception as e:
        print(f"Error creating test provider: {e}")
        return None
    finally:
        db.close()


async def test_generation_with_mock_data(template_id, provider_id):
    """Test content generation with mock data"""
    print("\n=== Testing Content Generation ===")

    db = next(get_db())
    try:
        from app.services.template_service import TemplateService

        template_service = TemplateService(db)

        # Test data
        test_input = {
            "wine_id": "S000001",
            "full_wine_name": "Sample Wine",
            "vintage": "2020",
            "winery": "Test Winery",
            "region": "Test Region",
            "ranking": "Grand Cru"
        }

        print(f"Test input: {test_input}")

        # Create generation request
        request = GenerationRequestSchema(
            template_id=template_id,
            input_data=test_input,
            provider_id=provider_id
        )

        # Simulate generation (mock response)
        from app.models.database import GenerationTask
        import uuid
        from datetime import datetime

        # Create a mock generation task
        task = GenerationTask(
            task_id=str(uuid.uuid4()),
            template_id=template_id,
            provider_id=provider_id,
            input_data=test_input,
            status="completed",
            generated_content='{"production_volume": "5000", "classification": "Rare", "reasoning": "Based on the Grand Cru ranking and premium positioning", "confidence": 0.8}',
            confidence_score=0.8,
            tokens_used=150,
            processing_time=2.5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"Mock generation task created: {task.task_id}")
        print(f"Generated content: {task.generated_content}")

        # Validate the output
        template = template_service.get_template(template_id)
        validation_result = template_service.validate_template_output(template, task.generated_content)

        print(f"Validation result: {validation_result}")

        return task.task_id

    except Exception as e:
        print(f"Error in generation test: {e}")
        return None
    finally:
        db.close()


def test_quality_check():
    """Test quality checking functionality"""
    print("\n=== Testing Quality Check ===")

    from app.services.quality_service import QualityService

    # Test content
    test_content = '{"production_volume": "5000", "classification": "Rare", "reasoning": "Based on the Grand Cru ranking and premium positioning", "confidence": 0.8}'

    # Test quality check
    rules = {
        "require_json_format": True,
        "required_fields": ["production_volume", "classification", "reasoning", "confidence"],
        "valid_classifications": ["Micro", "Rare", "Small", "Medium", "Common", "Unknown"],
        "confidence_range": [0.1, 1.0],
        "max_reasoning_length": 500
    }

    result = QualityService.check_content_quality(test_content, rules)

    print(f"Quality check result:")
    print(f"  Is valid: {result.is_valid}")
    print(f"  Score: {result.score}")
    print(f"  Issues: {result.issues}")
    print(f"  Suggestions: {result.suggestions}")

    return result.is_valid


def main():
    """Main test function"""
    print("Starting Production Volume Generation Test")
    print("=" * 50)

    # Initialize database
    create_tables()

    # Load test data
    test_data = load_test_data()
    if not test_data:
        print("No test data available. Exiting.")
        return

    # Test template creation
    template_id = test_template_creation()
    if not template_id:
        print("Template creation failed. Exiting.")
        return

    # Test provider creation
    provider_id = mock_provider_test()
    if not provider_id:
        print("Provider creation failed. Exiting.")
        return

    # Test content generation
    task_id = await test_generation_with_mock_data(template_id, provider_id)
    if not task_id:
        print("Generation test failed. Exiting.")
        return

    # Test quality check
    quality_passed = test_quality_check()

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"✓ Template created: {template_id}")
    print(f"✓ Provider created: {provider_id}")
    print(f"✓ Generation task: {task_id}")
    print(f"✓ Quality check: {'Passed' if quality_passed else 'Failed'}")

    if all([template_id, provider_id, task_id, quality_passed]):
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed.")


if __name__ == "__main__":
    asyncio.run(main())