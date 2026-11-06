"""Main application entry point for Bookstore eCommerce Agent Backend."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config import settings
from src.database import Base, async_session_factory, engine
from src.routers import agent_router, books_router, orders_router
from src.services.book_service import BookService

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bookstore.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing database schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial bookstore catalog
    async with async_session_factory() as session:
        try:
            service = BookService(session)
            await service.seed_initial_catalog()
            await session.commit()
            logger.info("Initial catalog seed check completed.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error during catalog initialization: {e}")

    yield

    logger.info("Shutting down application and closing database engine...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic eCommerce Bookstore Backend powered by Tool-Calling Architecture.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware configured securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global safe exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sanitize internal errors without exposing internal traces."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}", exc_info=settings.DEBUG)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support if the issue persists."},
    )


# Register API Routers
app.include_router(books_router)
app.include_router(orders_router)
app.include_router(agent_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container probes."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    # Bind explicitly to 127.0.0.1 for local/safe network execution
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
