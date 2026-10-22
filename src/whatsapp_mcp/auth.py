"""Verificação JWT via provedor OAuth/OIDC externo (sem emitir tokens próprios)."""
from __future__ import annotations

import jwt
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier

from .config import Settings


class JwtVerifier(TokenVerifier):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.jwks = jwt.PyJWKClient(settings.oauth_jwks_url, cache_jwk_set=True, lifespan=300)

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self.settings.oauth_audience,
                issuer=self.settings.oauth_issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
                leeway=30,
            )
            subject = str(claims["sub"])
            if subject not in self.settings.oauth_allowed_subjects:
                return None
            raw_scopes = claims.get("scope", "")
            scopes = raw_scopes.split() if isinstance(raw_scopes, str) else claims.get("scp", [])
            if not isinstance(scopes, list):
                return None
            return AccessToken(
                token=token,
                client_id=str(claims.get("azp", claims.get("client_id", "oauth-client"))),
                scopes=[str(item) for item in scopes],
                resource=self.settings.oauth_resource,
                subject=subject,
            )
        except (jwt.PyJWTError, ValueError, KeyError, TypeError):
            return None


def require_scope(settings: Settings, scope: str) -> None:
    """No modo local, a segurança é exclusivamente a interface loopback."""
    if settings.auth_mode == "local":
        return
    auth = get_access_token()
    if auth is None or scope not in auth.scopes:
        raise PermissionError(f"Escopo OAuth exigido: {scope}")
