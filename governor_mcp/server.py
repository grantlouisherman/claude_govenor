"""FastMCP server setup for Governor MCP"""

from fastmcp import FastMCP

from .tools import (
    governor_assess,
    governor_approve,
    governor_log_action,
    governor_create_plan,
    governor_execute_step,
    governor_check_status,
    governor_abort,
    governor_get_history,
)

# Create the MCP server
mcp = FastMCP(
    name="governor",
    instructions="""Governor MCP - AI Agent Behavior Governance

This server provides tools to assess and control AI agent operations based on risk levels:

- LOW RISK: Operations can proceed without additional approval
- MEDIUM RISK: Require user confirmation before proceeding
- HIGH RISK: Require structured plan with step-by-step approval

Workflow:
1. Call governor_assess before any operation to determine risk level
2. For MEDIUM risk: Call governor_approve to record user confirmation
3. For HIGH risk: Call governor_create_plan, then governor_approve, then governor_execute_step
4. Use governor_check_status to monitor progress
5. Use governor_abort if something goes wrong
6. Use governor_get_history for audit trail

Risk Classification:
- Resources: memory(0) → local_file(1) → api(2) → sensitive_file(3) → database(4) → system(5)
- Actions: read(0.5x) → write(1.5x) → delete(2.5x) → execute(3.0x)
- Scope: single(1.0x) → multiple(1.5x) → collection(2.0x) → system(3.0x)
- Risk Score = Resource × Action × Scope
- LOW: score < 3, MEDIUM: 3-8, HIGH: > 8
""",
)


# Register tools with the MCP server
@mcp.tool()
async def assess(
    operation: str,
    description: str = "",
    context: str = "",
) -> dict:
    """
    Assess the risk level of an operation before execution.

    This is the primary entry point for the Governor MCP. Call this before
    performing any operation to determine if it's LOW, MEDIUM, or HIGH risk.

    Args:
        operation: The operation to assess (command, action description, etc.)
        description: Human-readable description of what the operation does
        context: Additional context (file paths, URLs, targets, etc.)

    Returns:
        Assessment result with risk_level, risk_score, and recommendations
    """
    return await governor_assess(operation, description, context)


@mcp.tool()
async def approve(
    target_type: str,
    target_id: str,
    approved: bool,
    reason: str = "",
) -> dict:
    """
    Record user approval or denial for an assessment, plan, or step.

    Args:
        target_type: Type of target - "assessment", "plan", or "step"
        target_id: ID of the assessment, plan, or step
        approved: True if approved, False if denied
        reason: Optional reason for the decision

    Returns:
        Approval record with next steps guidance
    """
    return await governor_approve(target_type, target_id, approved, reason)


@mcp.tool()
async def log_action(
    action: str,
    operation: str,
    risk_level: str = "medium",
    details: dict | None = None,
    success: bool = True,
    error: str = "",
) -> dict:
    """
    Log an action for audit trail purposes.

    Use for medium-risk operations that don't require a full plan
    but should be tracked.

    Args:
        action: The action type (e.g., "modify_file", "call_api")
        operation: Description of the specific operation
        risk_level: Risk level - "low", "medium", or "high"
        details: Additional details to log
        success: Whether the action succeeded
        error: Error message if action failed

    Returns:
        Audit entry confirmation
    """
    return await governor_log_action(action, operation, risk_level, details, success, error)


@mcp.tool()
async def create_plan(
    assessment_id: str,
    name: str,
    description: str,
    steps: list[dict],
    auto_submit: bool = True,
) -> dict:
    """
    Create a structured execution plan for a high-risk operation.

    Each step should include description, operation, expected_outcome,
    and optionally rollback_action for recovery.

    Args:
        assessment_id: ID of the risk assessment that triggered plan creation
        name: Short name for the plan
        description: Detailed description of what the plan accomplishes
        steps: List of step definitions
        auto_submit: Automatically submit for approval (default True)

    Returns:
        Plan details with step IDs and next steps
    """
    return await governor_create_plan(assessment_id, name, description, steps, auto_submit)


@mcp.tool()
async def execute_step(
    plan_id: str,
    step_id: str,
    actual_operation: str = "",
    actual_outcome: str = "",
    skip: bool = False,
) -> dict:
    """
    Execute an approved step with deviation detection.

    Records step execution and checks for deviations from the planned
    operation. Detects and reports any discrepancies.

    Args:
        plan_id: ID of the plan containing the step
        step_id: ID of the step to execute
        actual_operation: The operation that was actually executed
        actual_outcome: The actual result/outcome of execution
        skip: Set to True to skip this step

    Returns:
        Execution result with deviation report and next step info
    """
    return await governor_execute_step(plan_id, step_id, actual_operation, actual_outcome, skip)


@mcp.tool()
async def check_status(
    plan_id: str = "",
    assessment_id: str = "",
    include_session_summary: bool = False,
) -> dict:
    """
    Query the status of a plan, assessment, or session.

    Args:
        plan_id: ID of a specific plan to check
        assessment_id: ID of a specific assessment to check
        include_session_summary: Include overview of all session state

    Returns:
        Status information for requested items
    """
    return await governor_check_status(plan_id, assessment_id, include_session_summary)


@mcp.tool()
async def abort(
    plan_id: str,
    reason: str = "",
) -> dict:
    """
    Abort a plan and get rollback suggestions for completed steps.

    Args:
        plan_id: ID of the plan to abort
        reason: Reason for aborting the plan

    Returns:
        Abort confirmation with rollback suggestions in reverse order
    """
    return await governor_abort(plan_id, reason)


@mcp.tool()
async def get_history(
    limit: int = 20,
    offset: int = 0,
    risk_level: str = "",
    action: str = "",
    plan_id: str = "",
    assessment_id: str = "",
    success_only: bool = False,
    failures_only: bool = False,
    include_stats: bool = False,
) -> dict:
    """
    Retrieve the audit trail of governor actions.

    Args:
        limit: Maximum number of entries to return (default 20)
        offset: Number of entries to skip (for pagination)
        risk_level: Filter by risk level
        action: Filter by action type
        plan_id: Filter by plan ID
        assessment_id: Filter by assessment ID
        success_only: Only show successful actions
        failures_only: Only show failed actions
        include_stats: Include audit statistics

    Returns:
        Audit history with entries and optional stats
    """
    return await governor_get_history(
        limit, offset, risk_level, action, plan_id,
        assessment_id, success_only, failures_only, include_stats
    )


def create_server() -> FastMCP:
    """Create and return the MCP server instance"""
    return mcp
