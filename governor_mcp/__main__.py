"""Entry point for Governor MCP server: python -m governor_mcp"""

import sys


def main():
    """Run the Governor MCP server"""
    from .server import create_server

    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
