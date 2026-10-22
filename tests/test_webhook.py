import hashlib
import hmac

from whatsapp_mcp.server import valid_signature


def test_signature_accepts_valid():
    body = b'{"object":"whatsapp_business_account"}'
    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert valid_signature(body, signature, "secret")
    assert not valid_signature(body + b" ", signature, "secret")
    assert not valid_signature(body, signature, "other")
    assert not valid_signature(body, "", "secret")
