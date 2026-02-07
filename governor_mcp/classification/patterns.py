"""Regex patterns for classifying resources and operations"""

import re

# Sensitive file patterns - files that contain credentials, secrets, or sensitive config
SENSITIVE_FILE_PATTERNS = [
    # Environment and config files
    re.compile(r"\.env($|\..*)", re.IGNORECASE),
    re.compile(r"\.env\.local", re.IGNORECASE),
    re.compile(r"\.env\.production", re.IGNORECASE),
    re.compile(r"secrets?\.(ya?ml|json|toml)", re.IGNORECASE),
    re.compile(r"credentials?\.(ya?ml|json|toml)", re.IGNORECASE),
    re.compile(r"config\.prod(uction)?\.(ya?ml|json|toml)", re.IGNORECASE),

    # Key files
    re.compile(r".*\.pem$", re.IGNORECASE),
    re.compile(r".*\.key$", re.IGNORECASE),
    re.compile(r".*\.p12$", re.IGNORECASE),
    re.compile(r".*\.pfx$", re.IGNORECASE),
    re.compile(r"id_rsa.*", re.IGNORECASE),
    re.compile(r"id_ed25519.*", re.IGNORECASE),
    re.compile(r".*_rsa$", re.IGNORECASE),

    # AWS and cloud credentials
    re.compile(r"\.aws/credentials", re.IGNORECASE),
    re.compile(r"\.aws/config", re.IGNORECASE),
    re.compile(r"gcloud.*\.json", re.IGNORECASE),
    re.compile(r"service[-_]?account.*\.json", re.IGNORECASE),

    # Password and token files
    re.compile(r".*password.*", re.IGNORECASE),
    re.compile(r".*token.*\.txt", re.IGNORECASE),
    re.compile(r"\.netrc", re.IGNORECASE),
    re.compile(r"\.npmrc", re.IGNORECASE),
    re.compile(r"\.pypirc", re.IGNORECASE),

    # Database config
    re.compile(r"database\.ya?ml", re.IGNORECASE),
    re.compile(r"db\.config\.(js|ts|json)", re.IGNORECASE),

    # Kubernetes secrets
    re.compile(r".*secret.*\.ya?ml", re.IGNORECASE),
]

# Database patterns - files and operations related to databases
DATABASE_PATTERNS = [
    # SQL files
    re.compile(r".*\.sql$", re.IGNORECASE),

    # Database files
    re.compile(r".*\.db$", re.IGNORECASE),
    re.compile(r".*\.sqlite3?$", re.IGNORECASE),
    re.compile(r".*\.mdb$", re.IGNORECASE),

    # Database connection strings and operations
    re.compile(r"(postgres|postgresql|mysql|mongodb|redis|sqlite)://", re.IGNORECASE),
    re.compile(r"(DROP|TRUNCATE|ALTER)\s+(TABLE|DATABASE|SCHEMA)", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+\w+", re.IGNORECASE),
    re.compile(r"(INSERT|UPDATE)\s+INTO", re.IGNORECASE),
    re.compile(r"SELECT\s+.*\s+FROM\s+\w+", re.IGNORECASE),

    # Migration files
    re.compile(r"migrations?/.*\.(sql|py|rb|js|ts)", re.IGNORECASE),
    re.compile(r".*migration.*\.(sql|py|rb|js|ts)", re.IGNORECASE),
]

# API patterns - external service interactions
API_PATTERNS = [
    # HTTP methods
    re.compile(r"(GET|POST|PUT|DELETE|PATCH)\s+https?://", re.IGNORECASE),
    re.compile(r"fetch\s*\(\s*['\"]https?://", re.IGNORECASE),
    re.compile(r"axios\.(get|post|put|delete|patch)", re.IGNORECASE),
    re.compile(r"requests?\.(get|post|put|delete|patch)", re.IGNORECASE),
    re.compile(r"http\.request", re.IGNORECASE),
    re.compile(r"curl\s+", re.IGNORECASE),

    # API endpoints
    re.compile(r"/api/v\d+/", re.IGNORECASE),
    re.compile(r"api\..*\.com", re.IGNORECASE),
    re.compile(r"graphql", re.IGNORECASE),
    re.compile(r"webhook", re.IGNORECASE),
]

# System command patterns - potentially dangerous system operations
SYSTEM_COMMAND_PATTERNS = [
    # Destructive commands
    re.compile(r"\brm\s+-rf?\b", re.IGNORECASE),
    re.compile(r"\brmdir\b", re.IGNORECASE),
    re.compile(r"\bdel\s+/[sfq]", re.IGNORECASE),  # Windows del with flags

    # System modification
    re.compile(r"\bchmod\b", re.IGNORECASE),
    re.compile(r"\bchown\b", re.IGNORECASE),
    re.compile(r"\bsudo\b", re.IGNORECASE),
    re.compile(r"\bsu\s+-", re.IGNORECASE),

    # Package management (can modify system)
    re.compile(r"\b(apt|yum|dnf|pacman|brew)\s+(install|remove|purge)", re.IGNORECASE),
    re.compile(r"\bpip\s+install\b", re.IGNORECASE),
    re.compile(r"\bnpm\s+(install|uninstall)\s+-g", re.IGNORECASE),

    # Process control
    re.compile(r"\bkill\s+-9?\b", re.IGNORECASE),
    re.compile(r"\bkillall\b", re.IGNORECASE),
    re.compile(r"\bsystemctl\s+(stop|restart|disable)", re.IGNORECASE),

    # Network operations
    re.compile(r"\biptables\b", re.IGNORECASE),
    re.compile(r"\bnetstat\b", re.IGNORECASE),
    re.compile(r"\bssh\b.*@", re.IGNORECASE),
]

# Read-only patterns - operations that are typically safe
READ_ONLY_PATTERNS = [
    re.compile(r"\bcat\s+", re.IGNORECASE),
    re.compile(r"\bless\s+", re.IGNORECASE),
    re.compile(r"\bhead\s+", re.IGNORECASE),
    re.compile(r"\btail\s+", re.IGNORECASE),
    re.compile(r"\bgrep\s+", re.IGNORECASE),
    re.compile(r"\bfind\s+", re.IGNORECASE),
    re.compile(r"\bls\s+", re.IGNORECASE),
    re.compile(r"\bpwd\b", re.IGNORECASE),
    re.compile(r"\bwhoami\b", re.IGNORECASE),
    re.compile(r"SELECT\s+.*\s+FROM", re.IGNORECASE),
    re.compile(r"\.read\(", re.IGNORECASE),
    re.compile(r"open\(.*,\s*['\"]r['\"]", re.IGNORECASE),
]


def matches_any_pattern(text: str, patterns: list[re.Pattern]) -> bool:
    """Check if text matches any of the given patterns"""
    return any(pattern.search(text) for pattern in patterns)


def get_matching_patterns(text: str, patterns: list[re.Pattern]) -> list[str]:
    """Get list of pattern strings that match the text"""
    return [pattern.pattern for pattern in patterns if pattern.search(text)]
