"""Configuração fail-closed, sem segredos no repositório."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def csv_set(value: str) -> frozenset[str]:
    return frozenset(item.strip() for item in value.split(",") if item.strip())


def flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, str(default)).strip().lower()
    if raw not in {"true", "false", "1", "0", "yes", "no"}:
        raise ValueError(f"{name} precisa ser booleano")
    return raw in {"true", "1", "yes"}


@dataclass(frozen=True)
class Settings:
    access_token: str
    phone_number_id: str
    verify_token: str
    app_secret: str
    graph_version: str
    database_path: Path
    enable_send: bool
    allowed_recipients: frozenset[str]
    approval_ttl_seconds: int
    auth_mode: str
    bind_host: str
    port: int
    public_host: str
    allowed_origins: tuple[str, ...]
    oauth_issuer: str
    oauth_jwks_url: str
    oauth_audience: str
    oauth_resource: str
    oauth_allowed_subjects: frozenset[str]

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        s = cls(
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip(),
            phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
            verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip(),
            app_secret=os.getenv("WHATSAPP_APP_SECRET", "").strip(),
            graph_version=os.getenv("WHATSAPP_GRAPH_VERSION", "v25.0").strip(),
            database_path=Path(os.getenv("WHATSAPP_DATABASE_PATH", "data/whatsapp.sqlite3")),
            enable_send=flag("MCP_ENABLE_SEND"),
            allowed_recipients=csv_set(os.getenv("MCP_ALLOWED_RECIPIENTS", "")),
            approval_ttl_seconds=int(os.getenv("MCP_APPROVAL_TTL_SECONDS", "600")),
            auth_mode=os.getenv("MCP_AUTH_MODE", "local").strip().lower(),
            bind_host=os.getenv("MCP_BIND_HOST", "127.0.0.1").strip(),
            port=int(os.getenv("MCP_PORT", "8000")),
            public_host=os.getenv("MCP_PUBLIC_HOST", "").strip().lower(),
            allowed_origins=tuple(sorted(csv_set(os.getenv("MCP_ALLOWED_ORIGINS", "")))),
            oauth_issuer=os.getenv("OAUTH_ISSUER_URL", "").strip(),
            oauth_jwks_url=os.getenv("OAUTH_JWKS_URL", "").strip(),
            oauth_audience=os.getenv("OAUTH_AUDIENCE", "").strip(),
            oauth_resource=os.getenv("OAUTH_RESOURCE_URL", "").strip(),
            oauth_allowed_subjects=csv_set(os.getenv("OAUTH_ALLOWED_SUBJECTS", "")),
        )
        s.validate()
        return s

    def validate(self) -> None:
        if not re.fullmatch(r"v\d+\.\d+", self.graph_version):
            raise ValueError("WHATSAPP_GRAPH_VERSION inválida")
        if self.phone_number_id and not self.phone_number_id.isdigit():
            raise ValueError("WHATSAPP_PHONE_NUMBER_ID inválido")
        if not 1 <= self.approval_ttl_seconds <= 3600:
            raise ValueError("MCP_APPROVAL_TTL_SECONDS fora do intervalo 1..3600")
        if not 1 <= self.port <= 65535:
            raise ValueError("MCP_PORT inválida")
        if self.auth_mode not in {"local", "oauth"}:
            raise ValueError("MCP_AUTH_MODE deve ser local ou oauth")
        if self.auth_mode == "local" and self.bind_host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("MCP local nunca pode escutar em interface pública")
        if self.auth_mode == "oauth":
            values = (
                self.oauth_issuer, self.oauth_jwks_url, self.oauth_audience,
                self.oauth_resource, self.public_host,
            )
            if not all(values) or not self.oauth_allowed_subjects:
                raise ValueError("OAuth requer issuer, JWKS, audience, resource, public host e subjects autorizados")
            if any(urlparse(value).scheme != "https" for value in
                   (self.oauth_issuer, self.oauth_jwks_url, self.oauth_resource)):
                raise ValueError("URLs de OAuth precisam usar HTTPS")
            resource = urlparse(self.oauth_resource)
            if resource.path != "/mcp" or resource.hostname != self.public_host:
                raise ValueError("OAUTH_RESOURCE_URL deve ser https://MCP_PUBLIC_HOST/mcp")
            if ":" in self.public_host or "/" in self.public_host:
                raise ValueError("MCP_PUBLIC_HOST deve ser apenas o hostname")
            if self.enable_send and not self.allowed_recipients:
                raise ValueError("Envio requer lista de destinatários permitidos")
        if any(not re.fullmatch(r"\d{8,15}", n) for n in self.allowed_recipients):
            raise ValueError("MCP_ALLOWED_RECIPIENTS deve conter números internacionais sem +")
        if self.enable_send and not self.access_token:
            raise ValueError("Envio habilitado sem token da Meta")
