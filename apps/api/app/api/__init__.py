"""API v1 router.

Aggregates all v1 endpoint routers.
Mounted at /api/v1 in main.py.
"""

from fastapi import APIRouter

from app.api import health
from app.api.v1 import users, habitats, ai_identities

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(habitats.router, prefix="/habitats", tags=["habitats"])
api_router.include_router(ai_identities.router, prefix="/ai-identities", tags=["ai-identities"])

# Future phases will add:
# api_router.include_router(habitats_router, tags=["habitats"])
# api_router.include_router(conversations_router, tags=["conversations"])
# etc.
