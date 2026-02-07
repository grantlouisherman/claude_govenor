"""Risk assessment engine for Governor MCP"""

import uuid
from typing import Any

from ..classification import (
    ResourceClassifier,
    ActionClassifier,
    ResourceType,
    ActionType,
    ScopeType,
)
from ..state import Assessment, RiskLevel


# Risk thresholds
LOW_THRESHOLD = 3.0
MEDIUM_THRESHOLD = 8.0


class RiskAssessor:
    """Assesses risk levels for operations based on composite scoring"""

    def __init__(self):
        self.resource_classifier = ResourceClassifier()
        self.action_classifier = ActionClassifier()

    def assess(
        self,
        operation: str,
        description: str = "",
        context: str = "",
    ) -> Assessment:
        """
        Perform a risk assessment on an operation.

        Risk Score = Resource Base Score × Action Multiplier × Scope Multiplier

        Thresholds:
        - score < 3: LOW risk
        - score 3-8: MEDIUM risk
        - score > 8: HIGH risk

        Args:
            operation: The operation to assess (command, description, etc.)
            description: Human-readable description of what the operation does
            context: Additional context (file paths, targets, etc.)

        Returns:
            Assessment object with risk classification
        """
        # Classify resource type
        resource_type, resource_score = self.resource_classifier.classify(operation, context)

        # Classify action type
        action_type, action_multiplier = self.action_classifier.classify_action(operation)

        # Classify scope
        scope_type, scope_multiplier = self.action_classifier.classify_scope(operation, context)

        # Calculate composite risk score
        risk_score = resource_score * action_multiplier * scope_multiplier

        # Determine risk level
        risk_level = self._calculate_risk_level(risk_score)

        # Build factors dictionary
        factors = {
            "resource": {
                "type": resource_type.value,
                "base_score": resource_score,
                "description": self.resource_classifier.get_resource_description(resource_type),
            },
            "action": {
                "type": action_type.value,
                "multiplier": action_multiplier,
                "description": self.action_classifier.get_action_description(action_type),
            },
            "scope": {
                "type": scope_type.value,
                "multiplier": scope_multiplier,
                "description": self.action_classifier.get_scope_description(scope_type),
            },
            "calculation": f"{resource_score} × {action_multiplier} × {scope_multiplier} = {risk_score}",
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, resource_type, action_type, scope_type
        )

        return Assessment(
            id=str(uuid.uuid4()),
            operation=operation,
            description=description or self._generate_description(operation, action_type),
            resource_type=resource_type.value,
            action_type=action_type.value,
            scope=scope_type.value,
            risk_score=risk_score,
            risk_level=risk_level,
            factors=factors,
            recommendations=recommendations,
        )

    def _calculate_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score < LOW_THRESHOLD:
            return RiskLevel.LOW
        elif score <= MEDIUM_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def _generate_description(self, operation: str, action_type: ActionType) -> str:
        """Generate a default description for an operation"""
        action_verbs = {
            ActionType.READ: "Reading",
            ActionType.WRITE: "Writing/modifying",
            ActionType.DELETE: "Deleting",
            ActionType.EXECUTE: "Executing",
        }
        verb = action_verbs.get(action_type, "Performing")
        return f"{verb}: {operation[:100]}{'...' if len(operation) > 100 else ''}"

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        resource_type: ResourceType,
        action_type: ActionType,
        scope_type: ScopeType,
    ) -> list[str]:
        """Generate recommendations based on assessment"""
        recommendations = []

        if risk_level == RiskLevel.LOW:
            recommendations.append("Operation can proceed without additional approval")
            return recommendations

        if risk_level == RiskLevel.MEDIUM:
            recommendations.append("User confirmation required before proceeding")

            if resource_type == ResourceType.EXTERNAL_API:
                recommendations.append("Verify API endpoint and credentials are correct")

            if action_type == ActionType.WRITE:
                recommendations.append("Consider creating a backup before modification")

        if risk_level == RiskLevel.HIGH:
            recommendations.append("Create a structured execution plan with step-by-step approval")
            recommendations.append("Document rollback procedures for each step")

            if resource_type == ResourceType.DATABASE:
                recommendations.append("Ensure database backup exists before proceeding")
                recommendations.append("Consider running in a transaction with rollback capability")

            if resource_type == ResourceType.SENSITIVE_FILE:
                recommendations.append("Verify credential handling follows security best practices")
                recommendations.append("Ensure sensitive data is not logged or exposed")

            if resource_type == ResourceType.SYSTEM_COMMAND:
                recommendations.append("Review command for unintended side effects")
                recommendations.append("Consider running in isolated/sandboxed environment first")

            if action_type == ActionType.DELETE:
                recommendations.append("Confirm deletion targets are correct")
                recommendations.append("Verify backup exists before deletion")

            if scope_type == ScopeType.SYSTEM:
                recommendations.append("Assess impact on dependent systems")
                recommendations.append("Consider staged rollout if possible")

        return recommendations

    def get_thresholds(self) -> dict[str, float]:
        """Get the current risk thresholds"""
        return {
            "low_max": LOW_THRESHOLD,
            "medium_max": MEDIUM_THRESHOLD,
        }
