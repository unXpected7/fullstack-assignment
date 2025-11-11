from typing import Dict, Any, List
import re
import json
from app.core.providers import QualityCheckResult


class QualityService:
    """Service for checking content quality"""

    @staticmethod
    def check_content_quality(content: str, template_rules: Dict[str, Any]) -> QualityCheckResult:
        """Check content quality against template rules"""
        issues = []
        suggestions = []
        score = 100

        # Basic content validation
        if not content or not content.strip():
            issues.append("Content is empty")
            score -= 50
        else:
            content_length = len(content.strip())
            if content_length < 10:
                issues.append("Content is too short")
                score -= 20
            elif content_length > 10000:
                issues.append("Content is extremely long")
                score -= 10

        # Check JSON format if expected
        if template_rules.get("require_json_format", False):
            try:
                parsed_content = json.loads(content)
                score += 10  # Bonus for valid JSON
            except json.JSONDecodeError:
                issues.append("Content is not valid JSON")
                score -= 30
                suggestions.append("Ensure content is properly formatted JSON")

        # Check specific template rules
        if template_rules:
            # Required fields check
            if "required_fields" in template_rules:
                if template_rules["require_json_format"]:
                    try:
                        parsed_content = json.loads(content)
                        for field in template_rules["required_fields"]:
                            if field not in parsed_content:
                                issues.append(f"Missing required field: {field}")
                                score -= 15
                    except json.JSONDecodeError:
                        pass  # Already handled above

            # Valid classifications check
            if "valid_classifications" in template_rules and template_rules["require_json_format"]:
                try:
                    parsed_content = json.loads(content)
                    if "classification" in parsed_content:
                        if parsed_content["classification"] not in template_rules["valid_classifications"]:
                            issues.append(f"Invalid classification: {parsed_content['classification']}")
                            score -= 20
                except json.JSONDecodeError:
                    pass

            # Confidence range check
            if "confidence_range" in template_rules and template_rules["require_json_format"]:
                try:
                    parsed_content = json.loads(content)
                    if "confidence" in parsed_content:
                        min_conf, max_conf = template_rules["confidence_range"]
                        if not (min_conf <= parsed_content["confidence"] <= max_conf):
                            issues.append(f"Confidence out of range: {parsed_content['confidence']}")
                            score -= 15
                except json.JSONDecodeError:
                    pass

            # Reasoning length check
            if "max_reasoning_length" in template_rules and template_rules["require_json_format"]:
                try:
                    parsed_content = json.loads(content)
                    if "reasoning" in parsed_content:
                        reasoning_length = len(parsed_content["reasoning"])
                        max_length = template_rules["max_reasoning_length"]
                        if reasoning_length > max_length:
                            issues.append(f"Reasoning too long: {reasoning_length} characters")
                            score -= 10
                            suggestions.append(f"Shorten reasoning to {max_length} characters or less")
                except json.JSONDecodeError:
                    pass

        # Additional quality checks
        score += QualityService._check_content_structure(content)
        score += QualityService._check_language_quality(content)
        score += QualityService._check_relevance(content)

        # Ensure score is within bounds
        score = max(0, min(100, score))

        # Convert issues to proper format
        formatted_issues = []
        for issue in issues:
            if issue not in formatted_issues:
                formatted_issues.append(issue)

        formatted_suggestions = []
        for suggestion in suggestions:
            if suggestion not in formatted_suggestions:
                formatted_suggestions.append(suggestion)

        return QualityCheckResult(
            is_valid=score >= 70,  # Consider valid if score >= 70
            score=score,
            issues=formatted_issues,
            suggestions=formatted_suggestions
        )

    @staticmethod
    def _check_content_structure(content: str) -> int:
        """Check content structure and return score adjustment"""
        adjustment = 0

        # Check for proper sentence structure
        if re.search(r'\. [A-Z]', content):
            adjustment += 5

        # Check for line breaks (good readability)
        if '\n' in content:
            adjustment += 3

        # Check for bullet points or numbered lists
        if re.search(r'^[0-9]+\.|\*|\-', content, re.MULTILINE):
            adjustment += 5

        return adjustment

    @staticmethod
    def _check_language_quality(content: str) -> int:
        """Check language quality and return score adjustment"""
        adjustment = 0

        # Check for excessive capitalization
        if len(re.findall(r'[A-Z]{3,}', content)) > 5:
            adjustment -= 5

        # Check for excessive punctuation
        if content.count('!') > 3 or content.count('?') > 3:
            adjustment -= 3

        # Check for proper spacing
        if re.search(r'\s{2,}', content):
            adjustment -= 5

        return adjustment

    @staticmethod
    def _check_relevance(content: str) -> int:
        """Check content relevance and return score adjustment"""
        adjustment = 0

        # Check for content-specific keywords
        relevant_keywords = ["wine", "production", "bottles", "volume", "winery", "region"]
        keyword_count = sum(1 for keyword in relevant_keywords if keyword.lower() in content.lower())

        if keyword_count > 0:
            adjustment += min(keyword_count * 5, 20)
        else:
            adjustment -= 10

        return adjustment

    @staticmethod
    def evaluate_production_volume_output(content: str) -> QualityCheckResult:
        """Evaluate production volume specific output"""
        rules = {
            "require_json_format": True,
            "required_fields": ["production_volume", "classification", "reasoning", "confidence"],
            "valid_classifications": ["Micro", "Rare", "Small", "Medium", "Common", "Unknown"],
            "confidence_range": [0.1, 1.0],
            "max_reasoning_length": 500
        }

        return QualityService.check_content_quality(content, rules)