"""Audit logging for Governor MCP"""

import uuid
from datetime import datetime
from typing import Any

from .models import AuditEntry, RiskLevel


class AuditLogger:
    """Manages audit log entries for action tracking"""

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def log(
        self,
        action: str,
        operation: str,
        risk_level: RiskLevel,
        details: dict[str, Any] | None = None,
        assessment_id: str | None = None,
        plan_id: str | None = None,
        step_id: str | None = None,
        success: bool = True,
        error: str | None = None,
    ) -> AuditEntry:
        """Create and store an audit log entry"""
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            action=action,
            operation=operation,
            risk_level=risk_level,
            details=details or {},
            assessment_id=assessment_id,
            plan_id=plan_id,
            step_id=step_id,
            success=success,
            error=error,
        )
        self._entries.append(entry)
        return entry

    def get_entries(
        self,
        limit: int | None = None,
        offset: int = 0,
        risk_level: RiskLevel | None = None,
        action: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        assessment_id: str | None = None,
        plan_id: str | None = None,
        success_only: bool = False,
        failures_only: bool = False,
    ) -> list[AuditEntry]:
        """Query audit entries with optional filters"""
        entries = self._entries.copy()

        # Apply filters
        if risk_level is not None:
            entries = [e for e in entries if e.risk_level == risk_level]

        if action is not None:
            entries = [e for e in entries if e.action == action]

        if since is not None:
            entries = [e for e in entries if e.timestamp >= since]

        if until is not None:
            entries = [e for e in entries if e.timestamp <= until]

        if assessment_id is not None:
            entries = [e for e in entries if e.assessment_id == assessment_id]

        if plan_id is not None:
            entries = [e for e in entries if e.plan_id == plan_id]

        if success_only:
            entries = [e for e in entries if e.success]

        if failures_only:
            entries = [e for e in entries if not e.success]

        # Sort by timestamp descending (most recent first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        if offset > 0:
            entries = entries[offset:]

        if limit is not None:
            entries = entries[:limit]

        return entries

    def get_entry(self, entry_id: str) -> AuditEntry | None:
        """Get a specific audit entry by ID"""
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_stats(self) -> dict[str, Any]:
        """Get audit log statistics"""
        total = len(self._entries)
        if total == 0:
            return {
                "total_entries": 0,
                "by_risk_level": {},
                "by_action": {},
                "success_rate": None,
            }

        by_risk = {}
        by_action = {}
        success_count = 0

        for entry in self._entries:
            # Count by risk level
            level = entry.risk_level.value
            by_risk[level] = by_risk.get(level, 0) + 1

            # Count by action
            by_action[entry.action] = by_action.get(entry.action, 0) + 1

            # Count successes
            if entry.success:
                success_count += 1

        return {
            "total_entries": total,
            "by_risk_level": by_risk,
            "by_action": by_action,
            "success_rate": success_count / total,
        }

    def clear(self):
        """Clear all audit entries"""
        self._entries.clear()


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def reset_audit_logger() -> AuditLogger:
    """Reset the global audit logger"""
    global _audit_logger
    _audit_logger = AuditLogger()
    return _audit_logger
