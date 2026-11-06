"""Book recommendation and discovery tools."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.book import Book
from src.tools.base import default_registry


class RecommendBooksInput(BaseModel):
    """Input parameters for personalized or contextual recommendations."""
    topic_or_genre: str = Field(..., description="Target interest topic, genre, or domain (e.g. 'Data Systems', 'Productivity', 'Sci-Fi')")
    max_budget: Optional[float] = Field(None, description="Optional maximum price per book")
    limit: int = Field(default=3, ge=1, le=10, description="Number of recommendations to return")


class SimilarBooksInput(BaseModel):
    """Input parameters for finding books similar to a given title."""
    book_id: int = Field(..., description="ID of reference book")
    limit: int = Field(default=3, ge=1, le=5, description="Number of similar books to return")


@default_registry.register(
    name="recommend_books",
    description="Generate tailored book recommendations based on user interests, topics, genres, and budget constraints.",
    schema_model=RecommendBooksInput,
)
async def recommend_books(
    topic_or_genre: str,
    max_budget: Optional[float] = None,
    limit: int = 3,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """Provide book recommendations."""
    if not db:
        raise ValueError("Database session is required.")

    q = f"%{topic_or_genre.strip().lower()}%"
    stmt = select(Book).where(
        or_(
            Book.category.ilike(q),
            Book.tags.ilike(q),
            Book.title.ilike(q),
            Book.description.ilike(q),
        )
    )

    if max_budget is not None:
        stmt = stmt.where(Book.price <= max_budget)

    stmt = stmt.order_by(Book.rating.desc()).limit(limit)
    res = await db.execute(stmt)
    books = list(res.scalars().all())

    # Fallback to top rated if no exact topic matched
    if not books:
        fallback_stmt = select(Book).order_by(Book.rating.desc()).limit(limit)
        res_fb = await db.execute(fallback_stmt)
        books = list(res_fb.scalars().all())
        reason = f"No direct match for '{topic_or_genre}'; showing store bestsellers."
    else:
        reason = f"Matched recommendations for '{topic_or_genre}'."

    return {
        "reason": reason,
        "recommendations": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "price": b.price,
                "rating": b.rating,
                "category": b.category,
                "description": b.description,
            }
            for b in books
        ],
    }


@default_registry.register(
    name="find_similar_books",
    description="Find related or alternative books in the same category or with matching thematic tags.",
    schema_model=SimilarBooksInput,
)
async def find_similar_books(
    book_id: int,
    limit: int = 3,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """Find similar books to a target book."""
    if not db:
        raise ValueError("Database session is required.")

    # Fetch reference book
    res = await db.execute(select(Book).where(Book.id == book_id))
    target = res.scalar_one_or_none()
    if not target:
        return {"found": False, "message": f"Reference book #{book_id} not found."}

    # Find books in same category excluding target
    stmt = (
        select(Book)
        .where(Book.id != target.id, Book.category == target.category)
        .order_by(Book.rating.desc())
        .limit(limit)
    )
    res_similar = await db.execute(stmt)
    similar = list(res_similar.scalars().all())

    return {
        "reference_book": {"id": target.id, "title": target.title, "category": target.category},
        "similar_books": [b.to_dict() for b in similar],
    }
