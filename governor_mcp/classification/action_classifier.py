"""Action and scope classification for Governor MCP"""

from enum import Enum

from .patterns import READ_ONLY_PATTERNS, matches_any_pattern


class ActionType(str, Enum):
    """Types of actions with associated risk multipliers"""
    READ = "read"        # Read/view operations (multiplier: 0.5x)
    WRITE = "write"      # Create/modify operations (multiplier: 1.5x)
    DELETE = "delete"    # Delete/remove operations (multiplier: 2.5x)
    EXECUTE = "execute"  # Execute/run operations (multiplier: 3.0x)


class ScopeType(str, Enum):
    """Scope of operations with associated risk multipliers"""
    SINGLE = "single"        # Single item (multiplier: 1.0x)
    MULTIPLE = "multiple"    # Multiple items (multiplier: 1.5x)
    COLLECTION = "collection"  # Collection/batch (multiplier: 2.0x)
    SYSTEM = "system"        # System-wide (multiplier: 3.0x)


# Risk multipliers for actions
ACTION_MULTIPLIERS = {
    ActionType.READ: 0.5,
    ActionType.WRITE: 1.5,
    ActionType.DELETE: 2.5,
    ActionType.EXECUTE: 3.0,
}

# Risk multipliers for scope
SCOPE_MULTIPLIERS = {
    ScopeType.SINGLE: 1.0,
    ScopeType.MULTIPLE: 1.5,
    ScopeType.COLLECTION: 2.0,
    ScopeType.SYSTEM: 3.0,
}


class ActionClassifier:
    """Classifies actions and scope based on operation descriptions"""

    # Keywords for action classification
    READ_KEYWORDS = [
        "read", "get", "fetch", "retrieve", "view", "show", "display",
        "list", "find", "search", "query", "select", "look", "check",
        "inspect", "examine", "browse", "scan", "cat", "head", "tail",
        "grep", "ls", "dir", "print", "echo", "describe", "status",
    ]

    WRITE_KEYWORDS = [
        "write", "create", "add", "insert", "update", "modify", "change",
        "edit", "set", "put", "post", "patch", "save", "store", "upload",
        "append", "replace", "overwrite", "touch", "mkdir", "install",
        "configure", "enable", "init", "generate", "build", "compile",
    ]

    DELETE_KEYWORDS = [
        "delete", "remove", "drop", "truncate", "clear", "purge", "clean",
        "uninstall", "destroy", "erase", "wipe", "rm", "rmdir", "del",
        "unlink", "reset", "revoke", "disable", "expire", "invalidate",
    ]

    EXECUTE_KEYWORDS = [
        "execute", "run", "start", "launch", "invoke", "call", "trigger",
        "deploy", "apply", "migrate", "push", "publish", "release", "ship",
        "sudo", "exec", "spawn", "fork", "eval", "script", "command",
        "restart", "reboot", "shutdown", "kill", "stop", "terminate",
    ]

    # Keywords for scope classification
    SINGLE_KEYWORDS = [
        "a", "an", "one", "single", "this", "that", "the", "specific",
    ]

    MULTIPLE_KEYWORDS = [
        "multiple", "several", "some", "few", "many", "these", "those",
        "batch", "group", "set", "list", "array",
    ]

    COLLECTION_KEYWORDS = [
        "all", "every", "each", "entire", "whole", "complete", "full",
        "collection", "table", "directory", "folder", "repository",
        "database", "schema", "namespace", "bucket", "queue",
    ]

    SYSTEM_KEYWORDS = [
        "system", "global", "server", "cluster", "infrastructure",
        "environment", "production", "staging", "network", "service",
        "platform", "organization", "account", "root", "admin",
    ]

    def classify_action(self, operation: str) -> tuple[ActionType, float]:
        """
        Classify the action type and return the risk multiplier.

        Args:
            operation: The operation description

        Returns:
            Tuple of (ActionType, risk_multiplier)
        """
        operation_lower = operation.lower()

        # Check if it's a read-only operation first
        if matches_any_pattern(operation, READ_ONLY_PATTERNS):
            return ActionType.READ, ACTION_MULTIPLIERS[ActionType.READ]

        # Check action keywords in order of severity (highest first)
        if any(kw in operation_lower for kw in self.EXECUTE_KEYWORDS):
            return ActionType.EXECUTE, ACTION_MULTIPLIERS[ActionType.EXECUTE]

        if any(kw in operation_lower for kw in self.DELETE_KEYWORDS):
            return ActionType.DELETE, ACTION_MULTIPLIERS[ActionType.DELETE]

        if any(kw in operation_lower for kw in self.WRITE_KEYWORDS):
            return ActionType.WRITE, ACTION_MULTIPLIERS[ActionType.WRITE]

        if any(kw in operation_lower for kw in self.READ_KEYWORDS):
            return ActionType.READ, ACTION_MULTIPLIERS[ActionType.READ]

        # Default to write (moderate risk)
        return ActionType.WRITE, ACTION_MULTIPLIERS[ActionType.WRITE]

    def classify_scope(self, operation: str, context: str = "") -> tuple[ScopeType, float]:
        """
        Classify the scope of an operation and return the risk multiplier.

        Args:
            operation: The operation description
            context: Additional context

        Returns:
            Tuple of (ScopeType, risk_multiplier)
        """
        combined = f"{operation} {context}".lower()

        # Check scope keywords in order of severity (highest first)
        if any(kw in combined for kw in self.SYSTEM_KEYWORDS):
            return ScopeType.SYSTEM, SCOPE_MULTIPLIERS[ScopeType.SYSTEM]

        if any(kw in combined for kw in self.COLLECTION_KEYWORDS):
            return ScopeType.COLLECTION, SCOPE_MULTIPLIERS[ScopeType.COLLECTION]

        if any(kw in combined for kw in self.MULTIPLE_KEYWORDS):
            return ScopeType.MULTIPLE, SCOPE_MULTIPLIERS[ScopeType.MULTIPLE]

        # Default to single (lowest scope risk)
        return ScopeType.SINGLE, SCOPE_MULTIPLIERS[ScopeType.SINGLE]

    def get_action_multiplier(self, action_type: ActionType) -> float:
        """Get the risk multiplier for an action type"""
        return ACTION_MULTIPLIERS.get(action_type, 1.0)

    def get_scope_multiplier(self, scope_type: ScopeType) -> float:
        """Get the risk multiplier for a scope type"""
        return SCOPE_MULTIPLIERS.get(scope_type, 1.0)

    def get_action_description(self, action_type: ActionType) -> str:
        """Get a human-readable description of the action type"""
        descriptions = {
            ActionType.READ: "Read-only operation that does not modify data",
            ActionType.WRITE: "Write operation that creates or modifies data",
            ActionType.DELETE: "Destructive operation that removes data",
            ActionType.EXECUTE: "Execution of commands or processes",
        }
        return descriptions.get(action_type, "Unknown action type")

    def get_scope_description(self, scope_type: ScopeType) -> str:
        """Get a human-readable description of the scope type"""
        descriptions = {
            ScopeType.SINGLE: "Affects a single item",
            ScopeType.MULTIPLE: "Affects multiple items",
            ScopeType.COLLECTION: "Affects an entire collection or batch",
            ScopeType.SYSTEM: "System-wide impact",
        }
        return descriptions.get(scope_type, "Unknown scope type")
