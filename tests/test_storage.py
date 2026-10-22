import time
from pathlib import Path

import pytest

from whatsapp_mcp.meta import assert_service_window, normalize_phone
from whatsapp_mcp.storage import Storage


def test_duplicate_and_search(tmp_path: Path):
    db = Storage(tmp_path / "messages.db")
    assert db.inbound("wamid.1", "5511999999999", "text", "Olá, suporte!", int(time.time()))
    assert not db.inbound("wamid.1", "5511999999999", "text", "dup", int(time.time()))
    assert db.conversations(20)[0]["message_count"] == 1
    assert db.search("suporte", "", 20)[0]["id"] == "wamid.1"
    assert db.messages("5511999999999", 20)[0]["body"] == "Olá, suporte!"


def test_prepared_is_one_shot(tmp_path: Path):
    db = Storage(tmp_path / "messages.db")
    token = db.prepare("5511999999999", {"type": "template"}, 600)
    contact, payload = db.reserve(token)
    assert contact == "5511999999999"
    assert payload["type"] == "template"
    with pytest.raises(ValueError):
        db.reserve(token)
    db.finalize(token, "sent", "wamid.2")


def test_window_and_phone(tmp_path: Path):
    db = Storage(tmp_path / "messages.db")
    number = normalize_phone("+55 (11) 99999-9999")
    assert number == "5511999999999"
    with pytest.raises(PermissionError):
        assert_service_window(db, number)
    db.inbound("wamid.1", number, "text", "oi", int(time.time()))
    assert_service_window(db, number)
    with pytest.raises(ValueError):
        normalize_phone("foo")
