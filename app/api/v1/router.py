"""
api/v1/router.py
Aggregates all v1 endpoint routers.

Auth policy: /auth/signup and /auth/login are PUBLIC; every other /api/v1 route
requires a valid Supabase JWT (verified by get_current_user). Without a token,
nothing else is reachable.
"""

from fastapi import APIRouter, Depends

from api.v1.endpoints import auth, query, dataset, validate, pipeline, model, predict, agent
from security.auth import get_current_user

api_router = APIRouter(prefix="/api/v1")

# ── Public (no token) ────────────────────────────────────────────────────────
api_router.include_router(auth.public_router)

# ── Protected (valid Supabase JWT required) ─────────────────────────────────
_auth = [Depends(get_current_user)]
api_router.include_router(auth.me_router, dependencies=_auth)
api_router.include_router(agent.router, dependencies=_auth)
api_router.include_router(query.router, dependencies=_auth)
api_router.include_router(dataset.router, dependencies=_auth)
api_router.include_router(validate.router, dependencies=_auth)
api_router.include_router(pipeline.router, dependencies=_auth)
api_router.include_router(model.router, dependencies=_auth)
api_router.include_router(predict.router, dependencies=_auth)
