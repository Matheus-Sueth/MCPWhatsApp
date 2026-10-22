import pytest

from whatsapp_mcp.config import Settings


def test_local_never_binds_public(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_MODE", "local")
    monkeypatch.setenv("MCP_BIND_HOST", "0.0.0.0")
    with pytest.raises(ValueError, match="local"):
        Settings.from_env()


def test_oauth_requires_claims(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_MODE", "oauth")
    monkeypatch.setenv("MCP_BIND_HOST", "0.0.0.0")
    monkeypatch.delenv("OAUTH_ALLOWED_SUBJECTS", raising=False)
    with pytest.raises(ValueError, match="OAuth"):
        Settings.from_env()
