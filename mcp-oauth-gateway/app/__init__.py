"""
MCP OAuth Gateway

Centralized OAuth authorization service for MCP servers following
MCP 2025-06-18 specification.

This gateway provides:
- OAuth 2.1 authorization flows (PKCE mandatory)
- Protected Resource Metadata (RFC 9728)
- Dynamic Client Registration (RFC 7591)
- Token storage and refresh
- Per-user delegated authentication for Microsoft providers
"""

__version__ = "1.0.0"
