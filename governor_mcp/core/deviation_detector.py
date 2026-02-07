"""Deviation detection for plan execution"""

from dataclasses import dataclass
from typing import Any

from ..state import PlanStep


@dataclass
class DeviationReport:
    """Report of detected deviations from expected plan execution"""
    step_id: str
    has_deviation: bool
    severity: str  # "none", "minor", "major", "critical"
    deviations: list[dict[str, Any]]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "has_deviation": self.has_deviation,
            "severity": self.severity,
            "deviations": self.deviations,
            "recommendations": self.recommendations,
        }


class DeviationDetector:
    """Detects deviations between planned and actual execution"""

    def detect(
        self,
        step: PlanStep,
        actual_operation: str,
        actual_outcome: str,
    ) -> DeviationReport:
        """
        Detect deviations between planned step and actual execution.

        Args:
            step: The planned step
            actual_operation: The operation that was actually executed
            actual_outcome: The actual outcome of the execution

        Returns:
            DeviationReport with findings
        """
        deviations = []
        recommendations = []

        # Check operation deviation
        operation_deviation = self._check_operation_deviation(
            step.operation, actual_operation
        )
        if operation_deviation:
            deviations.append(operation_deviation)

        # Check outcome deviation
        outcome_deviation = self._check_outcome_deviation(
            step.expected_outcome, actual_outcome
        )
        if outcome_deviation:
            deviations.append(outcome_deviation)

        # Determine severity
        severity = self._calculate_severity(deviations)

        # Generate recommendations
        recommendations = self._generate_recommendations(deviations, severity)

        return DeviationReport(
            step_id=step.id,
            has_deviation=len(deviations) > 0,
            severity=severity,
            deviations=deviations,
            recommendations=recommendations,
        )

    def _check_operation_deviation(
        self,
        planned: str,
        actual: str,
    ) -> dict[str, Any] | None:
        """Check for deviations in the operation executed"""
        if not planned or not actual:
            return None

        planned_normalized = self._normalize(planned)
        actual_normalized = self._normalize(actual)

        if planned_normalized == actual_normalized:
            return None

        # Calculate similarity
        similarity = self._calculate_similarity(planned_normalized, actual_normalized)

        if similarity >= 0.9:
            return None  # Minor differences (whitespace, etc.)

        deviation_type = "minor" if similarity >= 0.7 else "major"

        return {
            "type": "operation_deviation",
            "deviation_type": deviation_type,
            "planned": planned,
            "actual": actual,
            "similarity": similarity,
            "message": f"Operation differs from plan (similarity: {similarity:.1%})",
        }

    def _check_outcome_deviation(
        self,
        expected: str,
        actual: str,
    ) -> dict[str, Any] | None:
        """Check for deviations in the outcome"""
        if not expected or not actual:
            return None

        expected_lower = expected.lower()
        actual_lower = actual.lower()

        # Check for error indicators in actual outcome
        error_indicators = [
            "error", "failed", "exception", "traceback",
            "denied", "forbidden", "unauthorized", "timeout",
            "not found", "does not exist", "cannot", "unable",
        ]

        has_error = any(indicator in actual_lower for indicator in error_indicators)

        if has_error:
            return {
                "type": "outcome_deviation",
                "deviation_type": "critical",
                "expected": expected,
                "actual": actual,
                "message": "Execution resulted in error or failure",
            }

        # Check for success indicators
        success_indicators = [
            "success", "completed", "done", "created",
            "updated", "deleted", "ok", "passed",
        ]

        expected_success = any(indicator in expected_lower for indicator in success_indicators)
        actual_success = any(indicator in actual_lower for indicator in success_indicators)

        if expected_success and not actual_success:
            return {
                "type": "outcome_deviation",
                "deviation_type": "major",
                "expected": expected,
                "actual": actual,
                "message": "Expected success but outcome is unclear",
            }

        return None

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove extra whitespace and convert to lowercase
        return " ".join(text.lower().split())

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity between two texts"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 and not words2:
            return 1.0

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _calculate_severity(self, deviations: list[dict[str, Any]]) -> str:
        """Calculate overall severity from all deviations"""
        if not deviations:
            return "none"

        severity_order = ["minor", "major", "critical"]
        max_severity = "minor"

        for deviation in deviations:
            dev_type = deviation.get("deviation_type", "minor")
            if severity_order.index(dev_type) > severity_order.index(max_severity):
                max_severity = dev_type

        return max_severity

    def _generate_recommendations(
        self,
        deviations: list[dict[str, Any]],
        severity: str,
    ) -> list[str]:
        """Generate recommendations based on deviations"""
        if severity == "none":
            return ["Execution proceeded as planned"]

        recommendations = []

        if severity == "critical":
            recommendations.append("STOP: Critical deviation detected")
            recommendations.append("Review error output and assess impact")
            recommendations.append("Consider rolling back completed steps")

        if severity == "major":
            recommendations.append("CAUTION: Significant deviation from plan")
            recommendations.append("Verify actual outcome before proceeding")
            recommendations.append("Consider updating plan if deviation is acceptable")

        if severity == "minor":
            recommendations.append("NOTE: Minor deviation detected")
            recommendations.append("Review changes and confirm acceptability")

        for deviation in deviations:
            if deviation.get("type") == "operation_deviation":
                recommendations.append(
                    f"Operation similarity: {deviation.get('similarity', 0):.1%}"
                )

        return recommendations
