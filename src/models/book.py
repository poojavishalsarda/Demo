"""Book and catalog database models."""
from sqlalchemy import Column, Integer, String, Float, Text
from src.database import Base


class Book(Base):
    """Book entity in the store catalog."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    isbn = Column(String(32), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=False, default=4.5)
    tags = Column(String(255), nullable=False, default="")  # Comma-separated tags

    def to_dict(self) -> dict:
        """Convert model instance to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "category": self.category,
            "description": self.description,
            "price": round(self.price, 2),
            "stock": self.stock,
            "rating": self.rating,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else [],
        }
