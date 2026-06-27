"""Top-level API router. Aggregates every feature router."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    cart,
    dashboard,
    health,
    orders,
    products,
    reviews,
    uploads,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(reviews.router, tags=["reviews"])  # paths are absolute
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
