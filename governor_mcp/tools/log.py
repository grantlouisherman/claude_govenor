"""Governor log tool - audit logging for operations"""

from typing import Any

from ..state import RiskLevel
from ..state.audit import get_audit_logger


async def governor_log_action(
    action: str,
    operation: str,
    risk_level: str = "medium",
    details: dict[str, Any] | None = None,
    success: bool = True,
    error: str = "",
) -> dict[str, Any]:
    """
    Log an action for audit trail purposes.

    Use this tool to record medium-risk operations that don't require
    a full plan but should be tracked for audit purposes.

    Args:
        action: The action type (e.g., "modify_file", "call_api", "update_config")
        operation: Description of the specific operation
        risk_level: Risk level - "low", "medium", or "high"
        details: Additional details to log (optional)
        success: Whether the action succeeded
        error: Error message if action failed

    Returns:
        Audit entry confirmation including:
        - entry_id: ID of the audit entry
        - logged: Confirmation of logging
    """
    audit = get_audit_logger()

    # Parse risk level
    try:
        level = RiskLevel(risk_level.lower())
    except ValueError:
        level = RiskLevel.MEDIUM

    # Create the audit entry
    entry = audit.log(
        action=action,
        operation=operation,
        risk_level=level,
        details=details or {},
        success=success,
        error=error or None,
    )

    return {
        "entry_id": entry.id,
        "logged": True,
        "action": action,
        "operation": operation,
        "risk_level": level.value,
        "success": success,
        "timestamp": entry.timestamp.isoformat(),
    }
