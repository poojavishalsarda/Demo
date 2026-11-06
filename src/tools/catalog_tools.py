"""Catalog and book discovery agentic tools."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.book import BookFilter
from src.services.book_service import BookService
from src.tools.base import default_registry


class SearchBooksInput(BaseModel):
    """Input parameters for searching catalog."""
    query: Optional[str] = Field(None, description="Keywords to match in title, author, description, or tags (e.g., 'distributed systems', 'Frank Herbert', 'clean code')")
    category: Optional[str] = Field(None, description="Book category/genre (e.g., 'Technology', 'Sci-Fi', 'Psychology', 'Artificial Intelligence')")
    max_price: Optional[float] = Field(None, description="Maximum book price in USD")
    min_rating: Optional[float] = Field(None, description="Minimum average rating between 1.0 and 5.0")
    in_stock_only: bool = Field(default=False, description="Filter for books with available stock > 0")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of books to return")


class GetBookDetailsInput(BaseModel):
    """Input parameters for retrieving book details."""
    book_id: int = Field(..., description="Unique integer ID of the book in the catalog")


class CheckInventoryInput(BaseModel):
    """Input parameters for checking inventory."""
    book_id: int = Field(..., description="Unique integer ID of the book to check stock for")


@default_registry.register(
    name="search_books",
    description="Search the bookstore catalog by keywords, category, price limit, or rating. Returns matching books with prices, stock, ratings, and IDs.",
    schema_model=SearchBooksInput,
)
async def search_books(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
    limit: int = 5,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """Execute catalog search."""
    if not db:
        raise ValueError("Database session is required to search books.")

    service = BookService(db)
    filters = BookFilter(
        query=query,
        category=category,
        max_price=max_price,
        min_rating=min_rating,
        in_stock_only=in_stock_only,
        limit=limit,
    )
    books, count = await service.search_books(filters)
    return {
        "count": count,
        "books": [b.to_dict() for b in books],
    }


@default_registry.register(
    name="get_book_details",
    description="Retrieve comprehensive information for a specific book including full description, ISBN, stock, author, and price given its book_id.",
    schema_model=GetBookDetailsInput,
)
async def get_book_details(book_id: int, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Fetch complete details for a book."""
    if not db:
        raise ValueError("Database session is required.")

    service = BookService(db)
    book = await service.get_book_by_id(book_id)
    if not book:
        return {"found": False, "message": f"Book with ID {book_id} was not found."}

    return {"found": True, "book": book.to_dict()}


@default_registry.register(
    name="check_inventory",
    description="Check real-time stock levels and availability for a book given its book_id.",
    schema_model=CheckInventoryInput,
)
async def check_inventory(book_id: int, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Check inventory for a book."""
    if not db:
        raise ValueError("Database session is required.")

    service = BookService(db)
    inv = await service.check_inventory(book_id)
    if not inv:
        return {"found": False, "message": f"Book with ID {book_id} was not found."}

    return {"found": True, "inventory": inv}
