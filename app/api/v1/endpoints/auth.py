"""
api/v1/endpoints/auth.py
Auth endpoints.

  public_router  (no token needed): POST /auth/signup, POST /auth/login
  me_router      (token required):  GET  /auth/me

login/signup proxy to Supabase Auth so you can get a token without a frontend.
Real apps typically sign in via the Supabase client SDK; either way the token
is what the rest of the API verifies.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from core.config import settings
from schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from security.auth import get_current_user

public_router = APIRouter(prefix="/auth", tags=["Auth"])
me_router = APIRouter(prefix="/auth", tags=["Auth"])


def _supabase_ready() -> None:
    if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
        raise HTTPException(503, "Supabase not configured (SUPABASE_URL / SUPABASE_ANON_KEY).")


def _headers() -> dict:
    return {"apikey": settings.SUPABASE_ANON_KEY, "Content-Type": "application/json"}


@public_router.post("/signup", response_model=TokenResponse, summary="Sign up via Supabase")
def signup(body: SignupRequest) -> TokenResponse:
    _supabase_ready()
    r = httpx.post(f"{settings.SUPABASE_URL}/auth/v1/signup",
                   headers=_headers(), json={"email": body.email, "password": body.password},
                   timeout=15)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, f"Signup failed: {r.text}")
    d = r.json()
    # Depending on project settings, signup may or may not return a session token.
    return TokenResponse(access_token=d.get("access_token", ""),
                         expires_in=d.get("expires_in"), user=d.get("user"))


@public_router.post("/login", response_model=TokenResponse, summary="Log in via Supabase")
def login(body: LoginRequest) -> TokenResponse:
    _supabase_ready()
    r = httpx.post(f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
                   headers=_headers(), json={"email": body.email, "password": body.password},
                   timeout=15)
    if r.status_code != 200:
        raise HTTPException(401, f"Login failed: {r.text}")
    d = r.json()
    return TokenResponse(access_token=d["access_token"], expires_in=d.get("expires_in"),
                         user=d.get("user"))


@me_router.get("/me", response_model=UserResponse, summary="Current user (from token)")
def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.get("id"), email=user.get("email"))
