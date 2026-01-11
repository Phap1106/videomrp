# app/api/__init__.py
from fastapi import APIRouter

from app.api.endpoints import router

api_router = APIRouter()
api_router.include_router(router, tags=["videos"])
