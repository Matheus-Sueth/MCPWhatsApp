"""Cliente da WhatsApp Cloud API, sem reenvio automático de POST."""
from __future__ import annotations

import re
import time
from typing import Any

import httpx

from .config import Settings
from .storage import Storage


def normalize_phone(value: str) -> str:
    normalized = re.sub(r"[\s()+-]", "", value)
    if not re.fullmatch(r"\d{8,15}", normalized):
        raise ValueError("Use número internacional com DDI, sem prefixo 00")
    return normalized


def assert_recipient(settings: Settings, number: str) -> str:
    contact = normalize_phone(number)
    if not settings.enable_send:
        raise PermissionError("Envio desabilitado: MCP_ENABLE_SEND=false")
    if contact not in settings.allowed_recipients:
        raise PermissionError("Contato fora da allowlist de envio")
    return contact


def assert_service_window(storage: Storage, contact: str) -> None:
    last = storage.last_inbound(contact)
    now = int(time.time())
    if last is None or last > now + 60 or now - last >= 24 * 3600:
        raise PermissionError(
            "Mensagem livre fora da janela de 24h; use template aprovado pela Meta"
        )


async def send_meta(settings: Settings, payload: dict[str, Any]) -> str:
    if not settings.access_token or not settings.phone_number_id:
        raise RuntimeError("Integração com Meta não configurada")
    url = (
        f"https://graph.facebook.com/{settings.graph_version}/"
        f"{settings.phone_number_id}/messages"
    )
    headers = {"Authorization": f"Bearer {settings.access_token}"}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            # Nunca vazar payloads ou tokens em erros apresentados ao modelo.
            raise RuntimeError(f"Meta Graph API rejeitou requisição (HTTP {response.status_code})")
        data = response.json()
        message_id = data["messages"][0]["id"]
        if not isinstance(message_id, str) or not message_id:
            raise ValueError("Identificador da resposta inválido")
        return message_id
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise RuntimeError("Envio à Meta não pôde ser confirmado; não tente novamente automaticamente") from exc
