"""API Routers package."""
from src.routers.books import router as books_router
from src.routers.orders import router as orders_router
from src.routers.agent import router as agent_router

__all__ = ["books_router", "orders_router", "agent_router"]
