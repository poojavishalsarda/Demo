"""Bookstore Catalog REST API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.book import BookCreate, BookFilter, BookRead, BookUpdate
from src.services.book_service import BookService

router = APIRouter(prefix="/api/v1/books", tags=["Books & Catalog"])


@router.get("", response_model=List[BookRead], summary="List and search books with filters")
async def list_books(
    query: Optional[str] = Query(None, description="Keywords to match across title, author, tags"),
    category: Optional[str] = Query(None, description="Category filter"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price filter"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    in_stock_only: bool = Query(False, description="Filter for in-stock books only"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve catalog books with optional filtering and pagination."""
    service = BookService(db)
    filters = BookFilter(
        query=query,
        category=category,
        max_price=max_price,
        min_rating=min_rating,
        in_stock_only=in_stock_only,
        limit=limit,
        offset=offset,
    )
    books, _ = await service.search_books(filters)
    return books


@router.get("/{book_id}", response_model=BookRead, summary="Get book details by ID")
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch complete details of a single book."""
    service = BookService(db)
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found",
        )
    return book


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED, summary="Add a new book to catalog")
async def create_book(book_in: BookCreate, db: AsyncSession = Depends(get_db)):
    """Add a new book title to the catalog."""
    service = BookService(db)
    existing = await service.get_book_by_isbn(book_in.isbn)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN '{book_in.isbn}' already exists",
        )
    book = await service.create_book(book_in)
    return book


@router.patch("/{book_id}", response_model=BookRead, summary="Update an existing book")
async def update_book(
    book_id: int,
    book_in: BookUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update fields of an existing book."""
    service = BookService(db)
    book = await service.update_book(book_id, book_in)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found",
        )
    return book


@router.get("/{book_id}/inventory", summary="Check inventory for a specific book")
async def check_inventory(book_id: int, db: AsyncSession = Depends(get_db)):
    """Check stock and availability for a book."""
    service = BookService(db)
    inv = await service.check_inventory(book_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found",
        )
    return inv
