"""Top-level API router.

Aggregates every feature router. As features arrive, create a module under
`app/api/routes/` and include it here, e.g.:

    from app.api.routes import products
    api_router.include_router(products.router, prefix="/products", tags=["products"])
"""

from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
