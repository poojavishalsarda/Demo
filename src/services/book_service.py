"""Book service implementing business logic for bookstore catalog."""
from typing import List, Optional, Tuple
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.book import Book
from src.schemas.book import BookCreate, BookUpdate, BookFilter


class BookService:
    """Handles catalog search, CRUD, and inventory management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Fetch a single book by ID."""
        stmt = select(Book).where(Book.id == book_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """Fetch a single book by ISBN."""
        stmt = select(Book).where(Book.isbn == isbn)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_books(self, filters: BookFilter) -> Tuple[List[Book], int]:
        """Search books with filtering, keyword search, and pagination."""
        conditions = []

        if filters.query:
            q = f"%{filters.query.strip().lower()}%"
            conditions.append(
                or_(
                    Book.title.ilike(q),
                    Book.author.ilike(q),
                    Book.description.ilike(q),
                    Book.tags.ilike(q),
                    Book.category.ilike(q),
                )
            )

        if filters.category:
            conditions.append(Book.category.ilike(f"%{filters.category.strip()}%"))

        if filters.max_price is not None:
            conditions.append(Book.price <= filters.max_price)

        if filters.min_rating is not None:
            conditions.append(Book.rating >= filters.min_rating)

        if filters.in_stock_only:
            conditions.append(Book.stock > 0)

        query_stmt = select(Book)
        if conditions:
            query_stmt = query_stmt.where(and_(*conditions))

        # Order by rating and stock
        query_stmt = query_stmt.order_by(Book.rating.desc(), Book.stock.desc())
        
        # Execute query
        exec_stmt = query_stmt.offset(filters.offset).limit(filters.limit)
        result = await self.db.execute(exec_stmt)
        books = list(result.scalars().all())

        return books, len(books)

    async def create_book(self, book_in: BookCreate) -> Book:
        """Add a new book to the catalog."""
        tags_str = ",".join(book_in.tags) if book_in.tags else ""
        book = Book(
            title=book_in.title,
            author=book_in.author,
            isbn=book_in.isbn,
            category=book_in.category,
            description=book_in.description,
            price=book_in.price,
            stock=book_in.stock,
            rating=book_in.rating,
            tags=tags_str,
        )
        self.db.add(book)
        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def update_book(self, book_id: int, book_in: BookUpdate) -> Optional[Book]:
        """Update existing book details."""
        book = await self.get_book_by_id(book_id)
        if not book:
            return None

        update_data = book_in.model_dump(exclude_unset=True)
        if "tags" in update_data and update_data["tags"] is not None:
            update_data["tags"] = ",".join(update_data["tags"])

        for field, value in update_data.items():
            setattr(book, field, value)

        await self.db.flush()
        await self.db.refresh(book)
        return book

    async def check_inventory(self, book_id: int) -> Optional[dict]:
        """Check current stock level for a book."""
        book = await self.get_book_by_id(book_id)
        if not book:
            return None
        return {
            "book_id": book.id,
            "title": book.title,
            "stock": book.stock,
            "in_stock": book.stock > 0,
            "price": book.price,
        }

    async def seed_initial_catalog(self) -> None:
        """Seed initial bookstore catalog if empty."""
        stmt = select(Book).limit(1)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none() is not None:
            return

        sample_books = [
            Book(
                title="Designing Data-Intensive Applications",
                author="Martin Kleppmann",
                isbn="9781449373320",
                category="Technology",
                description="The definitive guide to distributed systems, storage engines, stream processing, and data architecture.",
                price=39.99,
                stock=25,
                rating=4.9,
                tags="data,architecture,distributed systems,databases",
            ),
            Book(
                title="Clean Code: A Handbook of Agile Software Craftsmanship",
                author="Robert C. Martin",
                isbn="9780132350884",
                category="Technology",
                description="Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.",
                price=34.50,
                stock=18,
                rating=4.7,
                tags="programming,software engineering,clean code,refactoring",
            ),
            Book(
                title="Artificial Intelligence: A Modern Approach",
                author="Stuart Russell and Peter Norvig",
                isbn="9780134610993",
                category="Artificial Intelligence",
                description="The comprehensive standard textbook covering search, reasoning, machine learning, and multi-agent systems.",
                price=79.99,
                stock=12,
                rating=4.8,
                tags="ai,agents,machine learning,deep learning,robotics",
            ),
            Book(
                title="Dune",
                author="Frank Herbert",
                isbn="9780441013593",
                category="Sci-Fi",
                description="Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides, heir to a noble family.",
                price=16.99,
                stock=40,
                rating=4.8,
                tags="scifi,classic,space opera,epic",
            ),
            Book(
                title="Project Hail Mary",
                author="Andy Weir",
                isbn="9780593135204",
                category="Sci-Fi",
                description="A lone astronaut must save the earth from disaster in this gripping science fiction adventure.",
                price=18.50,
                stock=30,
                rating=4.9,
                tags="scifi,space,adventure,science",
            ),
            Book(
                title="Thinking, Fast and Slow",
                author="Daniel Kahneman",
                isbn="9780374533557",
                category="Psychology",
                description="Nobel laureate Daniel Kahneman explores the two systems that drive the way we think and make choices.",
                price=14.99,
                stock=22,
                rating=4.6,
                tags="psychology,behavioral economics,decision making,mind",
            ),
            Book(
                title="Atomic Habits",
                author="James Clear",
                isbn="9780735211292",
                category="Self-Help",
                description="An easy and proven way to build good habits and break bad ones.",
                price=15.20,
                stock=50,
                rating=4.9,
                tags="productivity,habits,self-improvement,psychology",
            ),
            Book(
                title="Building Microservices",
                author="Sam Newman",
                isbn="9781492034025",
                category="Technology",
                description="Designing fine-grained systems, service modeling, integration, and asynchronous architectures.",
                price=44.95,
                stock=15,
                rating=4.7,
                tags="microservices,cloud,architecture,distributed systems",
            ),
        ]
        self.db.add_all(sample_books)
        await self.db.flush()
