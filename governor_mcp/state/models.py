"""Data models for Governor MCP state management"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """Risk level classification for operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StepStatus(str, Enum):
    """Status of a plan step"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStatus(str, Enum):
    """Status of an execution plan"""
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class Assessment:
    """Risk assessment result for an operation"""
    id: str
    operation: str
    description: str
    resource_type: str
    action_type: str
    scope: str
    risk_score: float
    risk_level: RiskLevel
    factors: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "operation": self.operation,
            "description": self.description,
            "resource_type": self.resource_type,
            "action_type": self.action_type,
            "scope": self.scope,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "factors": self.factors,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PlanStep:
    """A single step in an execution plan"""
    id: str
    order: int
    description: str
    operation: str
    expected_outcome: str
    rollback_action: str | None = None
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None
    executed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order": self.order,
            "description": self.description,
            "operation": self.operation,
            "expected_outcome": self.expected_outcome,
            "rollback_action": self.rollback_action,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class Plan:
    """Structured execution plan for high-risk operations"""
    id: str
    name: str
    description: str
    assessment_id: str
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    current_step_index: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "assessment_id": self.assessment_id,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def get_current_step(self) -> PlanStep | None:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_to_next_step(self) -> PlanStep | None:
        self.current_step_index += 1
        self.updated_at = datetime.now()
        return self.get_current_step()


@dataclass
class Approval:
    """Record of user approval or denial"""
    id: str
    target_type: str  # "assessment", "plan", "step"
    target_id: str
    approved: bool
    reason: str | None = None
    conditions: list[str] = field(default_factory=list)
    approved_by: str = "user"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "approved": self.approved,
            "reason": self.reason,
            "conditions": self.conditions,
            "approved_by": self.approved_by,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AuditEntry:
    """Audit log entry for tracking actions"""
    id: str
    action: str
    operation: str
    risk_level: RiskLevel
    details: dict[str, Any] = field(default_factory=dict)
    assessment_id: str | None = None
    plan_id: str | None = None
    step_id: str | None = None
    success: bool = True
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "operation": self.operation,
            "risk_level": self.risk_level.value,
            "details": self.details,
            "assessment_id": self.assessment_id,
            "plan_id": self.plan_id,
            "step_id": self.step_id,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }
