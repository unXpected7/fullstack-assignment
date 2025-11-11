from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
from app.models.database import Template, GenerationTask
from app.core.providers import GenerationRequest
import json


class TemplateService:
    """Service for managing AI templates"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(self, template_data: Dict[str, Any]) -> Template:
        """Create a new template"""
        template = Template(
            name=template_data["name"],
            description=template_data.get("description", ""),
            system_prompt=template_data["system_prompt"],
            user_prompt_template=template_data["user_prompt_template"],
            output_format_requirements=template_data.get("output_format_requirements", ""),
            quality_check_rules=template_data.get("quality_check_rules", {}),
            is_active=template_data.get("is_active", True)
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template(self, template_id: int) -> Optional[Template]:
        """Get a template by ID"""
        return self.db.query(Template).filter(Template.id == template_id).first()

    def get_all_templates(self, active_only: bool = False) -> List[Template]:
        """Get all templates"""
        query = self.db.query(Template)
        if active_only:
            query = query.filter(Template.is_active == True)
        return query.all()

    def update_template(self, template_id: int, template_data: Dict[str, Any]) -> Optional[Template]:
        """Update a template"""
        template = self.get_template(template_id)
        if not template:
            return None

        for key, value in template_data.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = None  # Let database handle the timestamp
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        template = self.get_template(template_id)
        if not template:
            return False

        self.db.delete(template)
        self.db.commit()
        return True

    def create_generation_request(self, template_id: int, input_data: Dict[str, Any]) -> GenerationRequest:
        """Create a generation request from template and input data"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")

        return GenerationRequest(
            system_prompt=template.system_prompt,
            user_prompt=template.user_prompt_template,
            variables=input_data,
            max_tokens=None,
            temperature=None
        )

    def get_production_volume_template(self) -> Optional[Template]:
        """Get the Production Volume template"""
        return self.db.query(Template).filter(
            Template.name.ilike("%production volume%") |
            Template.name.ilike("%production_volume%")
        ).first()

    def create_production_volume_template(self) -> Template:
        """Create the Production Volume template"""
        template_data = {
            "name": "Production Volume Generation",
            "description": "Generates production volume information for wine products based on available data",
            "system_prompt": """You are an expert wine industry analyst specializing in production volume estimation. Your task is to determine the production volume for wine products based on the provided information.

Follow these guidelines:
1. Analyze the wine information carefully including type, origin, pricing, and quality indicators
2. Consider typical production volumes for different wine categories and regions
3. Use the price point as an indicator of rarity and production volume
4. Consider the ranking/classification as an indicator of production scale
5. Provide exact numbers if clearly indicated
6. Estimate based on available information when exact numbers aren't available

Production Volume Classification:
- Micro production: Less than 5,000 bottles
- Rare: 5,000 - 10,000 bottles
- Small: 10,000 - 30,000 bottles
- Medium: 30,000 - 100,000 bottles
- Common: More than 100,000 bottles
- Unknown: Insufficient information to determine

Respond with a JSON object containing:
- production_volume: The estimated number (or classification)
- classification: The category (Micro, Rare, Small, Medium, Common, Unknown)
- reasoning: Your reasoning for the classification
- confidence: Your confidence level (0.1 to 1.0)""",
            "user_prompt_template": """Please analyze the following wine product and determine its production volume:

Wine Information:
- Wine ID: {wine_id}
- Full Name: {full_wine_name}
- Vintage: {vintage}
- Winery: {winery}
- Region: {region}
- Ranking: {ranking}

Provide your analysis in the requested JSON format.""",
            "output_format_requirements": "JSON object with production_volume, classification, reasoning, and confidence fields",
            "quality_check_rules": {
                "required_fields": ["production_volume", "classification", "reasoning", "confidence"],
                "valid_classifications": ["Micro", "Rare", "Small", "Medium", "Common", "Unknown"],
                "confidence_range": [0.1, 1.0],
                "max_reasoning_length": 500
            },
            "is_active": True
        }

        return self.create_template(template_data)

    def validate_template_output(self, template: Template, output: str) -> Dict[str, Any]:
        """Validate template output against quality check rules"""
        try:
            if template.quality_check_rules:
                rules = template.quality_check_rules

                # Parse output as JSON
                output_data = json.loads(output)

                validation_result = {
                    "is_valid": True,
                    "issues": [],
                    "suggestions": []
                }

                # Check required fields
                if "required_fields" in rules:
                    for field in rules["required_fields"]:
                        if field not in output_data:
                            validation_result["is_valid"] = False
                            validation_result["issues"].append(f"Missing required field: {field}")

                # Check valid classifications if applicable
                if "valid_classifications" in rules and "classification" in output_data:
                    if output_data["classification"] not in rules["valid_classifications"]:
                        validation_result["is_valid"] = False
                        validation_result["issues"].append(f"Invalid classification: {output_data['classification']}")

                # Check confidence range if applicable
                if "confidence_range" in rules and "confidence" in output_data:
                    min_conf, max_conf = rules["confidence_range"]
                    if not (min_conf <= output_data["confidence"] <= max_conf):
                        validation_result["is_valid"] = False
                        validation_result["issues"].append(f"Confidence out of range: {output_data['confidence']}")

                # Check reasoning length if applicable
                if "max_reasoning_length" in rules and "reasoning" in output_data:
                    if len(output_data["reasoning"]) > rules["max_reasoning_length"]:
                        validation_result["issues"].append(f"Reasoning too long: {len(output_data['reasoning'])} characters")
                        validation_result["suggestions"].append("Shorten the reasoning text")

                return validation_result

            return {"is_valid": True, "issues": [], "suggestions": []}

        except json.JSONDecodeError:
            return {
                "is_valid": False,
                "issues": ["Invalid JSON format in output"],
                "suggestions": ["Ensure output is valid JSON"]
            }
        except Exception as e:
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "suggestions": ["Check template output format"]
            }