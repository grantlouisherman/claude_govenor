"""Resource type classification for Governor MCP"""

from enum import Enum

from .patterns import (
    SENSITIVE_FILE_PATTERNS,
    DATABASE_PATTERNS,
    API_PATTERNS,
    SYSTEM_COMMAND_PATTERNS,
    matches_any_pattern,
)


class ResourceType(str, Enum):
    """Types of resources ordered by base risk level"""
    MEMORY = "memory"            # In-memory operations (risk: 0)
    LOCAL_FILE = "local_file"    # Local file system (risk: 1)
    EXTERNAL_API = "external_api"  # External API calls (risk: 2)
    SENSITIVE_FILE = "sensitive_file"  # Credentials, secrets (risk: 3)
    DATABASE = "database"        # Database operations (risk: 4)
    SYSTEM_COMMAND = "system_command"  # System-level commands (risk: 5)


# Base risk scores for each resource type
RESOURCE_RISK_SCORES = {
    ResourceType.MEMORY: 0,
    ResourceType.LOCAL_FILE: 1,
    ResourceType.EXTERNAL_API: 2,
    ResourceType.SENSITIVE_FILE: 3,
    ResourceType.DATABASE: 4,
    ResourceType.SYSTEM_COMMAND: 5,
}


class ResourceClassifier:
    """Classifies resources based on type and risk level"""

    def classify(self, operation: str, context: str = "") -> tuple[ResourceType, float]:
        """
        Classify a resource and return its type and base risk score.

        Args:
            operation: The operation description or command
            context: Additional context (file paths, URLs, etc.)

        Returns:
            Tuple of (ResourceType, base_risk_score)
        """
        combined = f"{operation} {context}".strip()

        # Check patterns in order of risk (highest first)
        if matches_any_pattern(combined, SYSTEM_COMMAND_PATTERNS):
            return ResourceType.SYSTEM_COMMAND, RESOURCE_RISK_SCORES[ResourceType.SYSTEM_COMMAND]

        if matches_any_pattern(combined, DATABASE_PATTERNS):
            return ResourceType.DATABASE, RESOURCE_RISK_SCORES[ResourceType.DATABASE]

        if matches_any_pattern(combined, SENSITIVE_FILE_PATTERNS):
            return ResourceType.SENSITIVE_FILE, RESOURCE_RISK_SCORES[ResourceType.SENSITIVE_FILE]

        if matches_any_pattern(combined, API_PATTERNS):
            return ResourceType.EXTERNAL_API, RESOURCE_RISK_SCORES[ResourceType.EXTERNAL_API]

        # Check for generic file operations
        if self._is_file_operation(combined):
            return ResourceType.LOCAL_FILE, RESOURCE_RISK_SCORES[ResourceType.LOCAL_FILE]

        # Default to memory (lowest risk)
        return ResourceType.MEMORY, RESOURCE_RISK_SCORES[ResourceType.MEMORY]

    def _is_file_operation(self, text: str) -> bool:
        """Check if the operation involves file system access"""
        file_indicators = [
            # File extensions
            ".txt", ".json", ".yaml", ".yml", ".xml", ".csv",
            ".py", ".js", ".ts", ".java", ".go", ".rs", ".rb",
            ".md", ".html", ".css", ".sh", ".bash",

            # Path indicators
            "/", "\\", "path", "file", "directory", "folder",

            # File operations
            "read", "write", "save", "load", "open", "create",
            "delete", "remove", "copy", "move", "rename",
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in file_indicators)

    def get_risk_score(self, resource_type: ResourceType) -> float:
        """Get the base risk score for a resource type"""
        return RESOURCE_RISK_SCORES.get(resource_type, 0)

    def get_resource_description(self, resource_type: ResourceType) -> str:
        """Get a human-readable description of the resource type"""
        descriptions = {
            ResourceType.MEMORY: "In-memory operation with no persistent side effects",
            ResourceType.LOCAL_FILE: "Local file system access",
            ResourceType.EXTERNAL_API: "External API or network operation",
            ResourceType.SENSITIVE_FILE: "Sensitive file containing credentials or secrets",
            ResourceType.DATABASE: "Database operation",
            ResourceType.SYSTEM_COMMAND: "System-level command execution",
        }
        return descriptions.get(resource_type, "Unknown resource type")
