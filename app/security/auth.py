"""
security/auth.py
Supabase JWT verification as a FastAPI dependency.

Supabase (client-side) signs users in and issues an access token (HS256, signed
with the project's JWT secret). Our API only verifies that token locally — no
network per request. Fails closed: no/invalid token, or no secret configured,
means no access.

# ponytail: HS256 legacy JWT secret. If the project switches to asymmetric
# signing keys (RS256/ES256), verify via the project's JWKS instead.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if cred is None or not cred.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    if not settings.SUPABASE_JWT_SECRET:
        # No secret => cannot verify => deny everything (fail closed).
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Auth not configured (SUPABASE_JWT_SECRET)")

    try:
        payload = jwt.decode(
            cred.credentials,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")

    return {"id": payload.get("sub"), "email": payload.get("email"), "claims": payload}
