"""
Unit tests for services layer
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

# Import services and models
from app.services.template_service import TemplateService
from app.services.quality_service import QualityService
from app.core.providers import ProviderConfig, GenerationRequest, GenerationResponse
from app.models.database import Template, AIProvider, GenerationTask as DBGenerationRequest


class TestTemplateService:
    """Test TemplateService functionality"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.delete = Mock()
        db.query = Mock()
        db.close = Mock()
        return db

    @pytest.fixture
    def template_service(self, mock_db):
        """Create TemplateService instance with mocked database"""
        return TemplateService(mock_db)

    @pytest.fixture
    def mock_template(self):
        """Mock template object"""
        template = Mock(spec=Template)
        template.id = 1
        template.name = "Test Template"
        template.system_prompt = "Test system prompt"
        template.user_prompt = "Hello {name}, welcome to {company}!"
        template.output_schema = json.dumps({"message": "string", "status": "string"})
        template.is_active = True
        template.created_at = datetime.now()
        template.updated_at = datetime.now()
        return template

    def test_create_template_success(self, template_service, mock_db, mock_template):
        """Test successful template creation"""
        # Setup
        template_data = {
            "name": "Test Template",
            "system_prompt": "Test system prompt",
            "user_prompt": "Hello {name}",
            "output_schema": json.dumps({"field1": "string"})
        }

        # Execute
        result = template_service.create_template(template_data)

        # Verify
        assert isinstance(result, Template)
        assert result.name == "Test Template"
        assert result.system_prompt == "Test system_prompt"
        assert result.user_prompt == "Hello {name}"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_template_found(self, template_service, mock_db, mock_template):
        """Test getting template when found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        # Execute
        result = template_service.get_template(1)

        # Verify
        assert result == mock_template
        mock_db.query.assert_called_once_with(Template)

    def test_get_template_not_found(self, template_service, mock_db):
        """Test getting template when not found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = template_service.get_template(999)

        # Verify
        assert result is None
        mock_db.query.assert_called_once_with(Template)

    def test_get_all_templates(self, template_service, mock_db):
        """Test getting all templates"""
        # Setup
        mock_templates = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.all.return_value = mock_templates

        # Execute
        result = template_service.get_all_templates()

        # Verify
        assert result == mock_templates
        mock_db.query.assert_called_once_with(Template)

    def test_update_template_success(self, template_service, mock_db, mock_template):
        """Test successful template update"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        update_data = {
            "name": "Updated Template",
            "system_prompt": "Updated system prompt"
        }

        # Execute
        result = template_service.update_template(1, update_data)

        # Verify
        assert result == mock_template
        assert mock_template.name == "Updated Template"
        assert mock_template.system_prompt == "Updated system prompt"
        mock_db.commit.assert_called_once()

    def test_update_template_not_found(self, template_service, mock_db):
        """Test updating template when not found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        update_data = {"name": "Updated Template"}

        # Execute and verify
        with pytest.raises(ValueError, match="Template not found"):
            template_service.update_template(999, update_data)

    def test_delete_template_success(self, template_service, mock_db, mock_template):
        """Test successful template deletion"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        # Execute
        result = template_service.delete_template(1)

        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(mock_template)
        mock_db.commit.assert_called_once()

    def test_delete_template_not_found(self, template_service, mock_db):
        """Test deleting template when not found"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = template_service.delete_template(999)

        # Verify
        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_create_generation_request_success(self, template_service, mock_db, mock_template):
        """Test generation request creation"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        input_data = {"name": "John", "company": "Acme"}

        # Execute
        result = template_service.create_generation_request(1, input_data)

        # Verify
        assert isinstance(result, GenerationRequest)
        assert result.system_prompt == "Test system prompt"
        assert result.user_prompt == "Hello John, welcome to Acme!"
        assert result.variables == input_data

    def test_create_generation_request_template_not_found(self, template_service, mock_db):
        """Test generation request with non-existent template"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        input_data = {"name": "John"}

        # Execute and verify
        with pytest.raises(ValueError, match="Template not found"):
            template_service.create_generation_request(999, input_data)

    def test_create_generation_request_missing_variables(self, template_service, mock_db, mock_template):
        """Test generation request with missing variables"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        input_data = {"name": "John"}  # Missing 'company' variable

        # Execute and verify
        with pytest.raises(ValueError, match="Missing variable"):
            template_service.create_generation_request(1, input_data)

    def test_validate_template_output_valid(self, template_service):
        """Test validation of valid template output"""
        # Setup
        output_schema = {"message": "string", "status": "string"}
        output_data = {"message": "Hello World", "status": "success"}

        # Execute
        result = template_service.validate_template_output(output_schema, output_data)

        # Verify
        assert result is True

    def test_validate_template_output_missing_fields(self, template_service):
        """Test validation of output with missing required fields"""
        # Setup
        output_schema = {"message": "string", "status": "string", "count": "integer"}
        output_data = {"message": "Hello World", "status": "success"}  # Missing count

        # Execute
        result = template_service.validate_template_output(output_schema, output_data)

        # Verify
        assert result is False

    def test_validate_template_output_invalid_json(self, template_service):
        """Test validation with invalid JSON output"""
        # Setup
        output_schema = {"message": "string"}
        invalid_json = "This is not valid JSON"

        # Execute and verify
        with pytest.raises(ValueError, match="Invalid JSON"):
            template_service.validate_template_output(output_schema, invalid_json)

    def test_get_production_volume_template_found(self, template_service, mock_db, mock_template):
        """Test getting production volume template when it exists"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template

        # Execute
        result = template_service.get_production_volume_template()

        # Verify
        assert result == mock_template
        mock_db.query.assert_called_once_with(Template)

    def test_get_production_volume_template_not_found(self, template_service, mock_db):
        """Test getting production volume template when it doesn't exist"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = template_service.get_production_volume_template()

        # Verify
        assert result is None

    @patch('app.services.template_service.datetime')
    def test_create_production_volume_template_success(self, mock_datetime, template_service, mock_db):
        """Test creating production volume template"""
        # Setup
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"

        # Execute
        result = template_service.create_production_volume_template()

        # Verify
        assert isinstance(result, Template)
        assert result.name == "Production Volume Generation"
        assert "wine industry analyst" in result.system_prompt.lower()
        assert "production volume" in result.system_prompt.lower()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_production_volume_template_already_exists(self, template_service, mock_db):
        """Test creating production volume template when it already exists"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        # Execute and verify
        with pytest.raises(Exception, match="Production Volume template already exists"):
            template_service.create_production_volume_template()


class TestQualityService:
    """Test QualityService functionality"""

    @pytest.fixture
    def quality_service(self):
        """Create QualityService instance"""
        return QualityService()

    def test_check_content_quality_perfect(self, quality_service):
        """Test quality check for perfect content"""
        # Setup
        content = "This is an excellent piece of content that is well-written, informative, and meets all quality standards. It provides comprehensive information and follows best practices."
        rules = ["min_length", "contains_keywords", "no_empty_lines"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is True
        assert result.score >= 80
        assert len(result.issues) == 0
        assert len(result.suggestions) >= 0

    def test_check_content_quality_too_short(self, quality_service):
        """Test quality check for content that's too short"""
        # Setup
        content = "Short"
        rules = ["min_length"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is False
        assert result.score < 50
        assert any("too short" in issue.lower() for issue in result.issues)

    def test_check_content_quality_missing_keywords(self, quality_service):
        """Test quality check for content missing required keywords"""
        # Setup
        content = "This is some random text without important terms."
        rules = ["contains_keywords"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is False
        assert result.score < 70
        assert any("keywords" in issue.lower() for issue in result.issues)

    def test_check_content_quality_empty_lines(self, quality_service):
        """Test quality check for content with excessive empty lines"""
        # Setup
        content = "Line 1\n\n\n\n\nLine 2"  # Multiple empty lines
        rules = ["no_empty_lines"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is False
        assert result.score < 80
        assert any("empty lines" in issue.lower() for issue in result.issues)

    def test_check_content_quality_no_rules(self, quality_service):
        """Test quality check with no rules specified"""
        # Setup
        content = "Any content"
        rules = []

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is True
        assert result.score == 100
        assert len(result.issues) == 0

    def test_check_content_quality_empty_content(self, quality_service):
        """Test quality check for empty content"""
        # Setup
        content = ""
        rules = ["min_length"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is False
        assert result.score == 0
        assert any("empty" in issue.lower() for issue in result.issues)

    def test_check_content_quality_whitespace_only(self, quality_service):
        """Test quality check for content with only whitespace"""
        # Setup
        content = "   \n\t  \n   "
        rules = ["min_length"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is False
        assert result.score == 0

    def test_check_content_quality_custom_rules(self, quality_service):
        """Test quality check with custom validation rules"""
        # Setup
        content = "This content needs to have specific format and requirements."
        rules = ["custom_format_check"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify - custom rule should check for format requirements
        assert isinstance(result.is_valid, bool)
        assert 0 <= result.score <= 100

    def test_check_content_quality_multiple_issues(self, quality_service):
        """Test quality check that identifies multiple issues"""
        # Setup
        content = "Short.\n\n\nMissing keywords"
        rules = ["min_length", "contains_keywords", "no_empty_lines"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        assert result.is_valid is False
        assert result.score < 50
        assert len(result.issues) >= 2  # Should find multiple issues
        assert len(result.suggestions) >= 1  # Should provide suggestions

    def test_quality_scoring_consistency(self, quality_service):
        """Test that quality scoring is consistent"""
        # Setup
        content = "This is a moderately good piece of content that has some issues but overall provides value to the reader."
        rules = ["min_length", "contains_keywords"]

        # Execute multiple times and verify consistency
        results = []
        for _ in range(5):
            result = quality_service.check_content_quality(content, rules)
            results.append(result.score)

        # Verify all scores are the same (consistent scoring)
        assert all(score == results[0] for score in results)

    def test_check_content_quality_with_suggestions(self, quality_service):
        """Test that quality check provides helpful suggestions"""
        # Setup
        content = "brief"
        rules = ["min_length", "contains_keywords"]

        # Execute
        result = quality_service.check_content_quality(content, rules)

        # Verify
        if not result.is_valid:
            assert len(result.suggestions) > 0
            assert all(isinstance(suggestion, str) for suggestion in result.suggestions)