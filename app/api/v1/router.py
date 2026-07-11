"""
api/v1/router.py
Aggregates all v1 endpoint routers into a single APIRouter.
"""

from fastapi import APIRouter
from api.v1.endpoints import query, dataset, pipeline, model

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(query.router)
api_router.include_router(dataset.router)
api_router.include_router(pipeline.router)
api_router.include_router(model.router)
