import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.template_service import TemplateService
from app.models.database import Template
from app.core.providers import GenerationRequest


class TestTemplateService:
    """Test cases for Template Service"""

    def setup_method(self):
        """Setup test data"""
        self.db = Mock()
        self.template_service = TemplateService(self.db)

        self.mock_template = Mock()
        self.mock_template.id = 1
        self.mock_template.name = "Test Template"
        self.mock_template.system_prompt = "Test system prompt"
        self.mock_template.user_prompt_template = "Hello {name}"
        self.mock_template.quality_check_rules = {
            "required_fields": ["name"],
            "valid_values": ["test", "example"]
        }

    def test_create_template(self):
        """Test template creation"""
        template_data = {
            "name": "Test Template",
            "description": "Test description",
            "system_prompt": "Test system prompt",
            "user_prompt_template": "Hello {name}",
            "quality_check_rules": {}
        }

        self.db.add = Mock()
        self.db.commit = Mock()
        self.db.refresh = Mock()

        result = self.template_service.create_template(template_data)

        assert result.name == "Test Template"
        assert result.system_prompt == "Test system prompt"
        assert self.db.add.called
        assert self.db.commit.called

    def test_get_template_found(self):
        """Test getting existing template"""
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_template

        result = self.template_service.get_template(1)

        assert result is self.mock_template

    def test_get_template_not_found(self):
        """Test getting non-existent template"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.template_service.get_template(99)

        assert result is None

    def test_get_all_templates(self):
        """Test getting all templates"""
        mock_templates = [self.mock_template]
        self.db.query.return_value.all.return_value = mock_templates

        result = self.template_service.get_all_templates()

        assert len(result) == 1
        assert result[0] == self.mock_template

    def test_update_template(self):
        """Test template update"""
        update_data = {"name": "Updated Template"}

        self.db.query.return_value.filter.return_value.first.return_value = self.mock_template
        self.db.commit = Mock()
        self.db.refresh = Mock()

        result = self.template_service.update_template(1, update_data)

        assert result.name == "Updated Template"
        assert self.db.commit.called

    def test_update_template_not_found(self):
        """Test updating non-existent template"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.template_service.update_template(99, {})

        assert result is None

    def test_delete_template(self):
        """Test template deletion"""
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_template
        self.db.delete = Mock()
        self.db.commit = Mock()

        result = self.template_service.delete_template(1)

        assert result is True
        assert self.db.delete.called

    def test_delete_template_not_found(self):
        """Test deleting non-existent template"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.template_service.delete_template(99)

        assert result is False

    def test_create_generation_request(self):
        """Test generation request creation"""
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_template

        input_data = {"name": "John"}
        result = self.template_service.create_generation_request(1, input_data)

        assert isinstance(result, GenerationRequest)
        assert result.system_prompt == "Test system prompt"
        assert result.user_prompt == "Hello John"

    def test_create_generation_template_not_found(self):
        """Test generation request creation with non-existent template"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Template with ID 1 not found"):
            self.template_service.create_generation_request(1, {})

    def test_validate_template_output_valid(self):
        """Test template output validation - valid case"""
        self.mock_template.quality_check_rules = {
            "required_fields": ["field1", "field2"],
            "valid_classifications": ["ClassA", "ClassB"]
        }

        valid_output = '{"field1": "value1", "field2": "value2", "classification": "ClassA"}'

        result = self.template_service.validate_template_output(self.mock_template, valid_output)

        assert result["is_valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_template_output_missing_fields(self):
        """Test template output validation - missing required fields"""
        self.mock_template.quality_check_rules = {
            "required_fields": ["field1", "field2"]
        }

        invalid_output = '{"field1": "value1"}'  # Missing field2

        result = self.template_service.validate_template_output(self.mock_template, invalid_output)

        assert result["is_valid"] is False
        assert "Missing required field: field2" in result["issues"]

    def test_validate_template_output_invalid_json(self):
        """Test template output validation - invalid JSON"""
        invalid_output = '{"field1": "value1", invalid json}'

        result = self.template_service.validate_template_output(self.mock_template, invalid_output)

        assert result["is_valid"] is False
        assert "Invalid JSON format in output" in result["issues"]

    def test_get_production_volume_template_found(self):
        """Test getting existing production volume template"""
        mock_pv_template = Mock()
        mock_pv_template.name = "Production Volume Generation"

        self.db.query.return_value.filter.return_value.first.return_value = mock_pv_template

        result = self.template_service.get_production_volume_template()

        assert result is mock_pv_template

    def test_get_production_volume_template_not_found(self):
        """Test getting non-existent production volume template"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.template_service.get_production_volume_template()

        assert result is None

    def test_create_production_volume_template(self):
        """Test creating production volume template"""
        self.db.add = Mock()
        self.db.commit = Mock()
        self.db.refresh = Mock()

        result = self.template_service.create_production_volume_template()

        assert result.name == "Production Volume Generation"
        assert "wine production volume estimation" in result.system_prompt.lower()
        assert self.db.add.called

    def test_create_production_volume_template_already_exists(self):
        """Test creating production volume template when already exists"""
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_template

        with pytest.raises(Exception, match="Production Volume template already exists"):
            self.template_service.create_production_volume_template()