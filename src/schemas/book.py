"""Pydantic schemas for Book domain."""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BookBase(BaseModel):
    """Base book fields."""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the book")
    author: str = Field(..., min_length=1, max_length=255, description="Author name")
    isbn: str = Field(..., min_length=10, max_length=32, description="International Standard Book Number")
    category: str = Field(..., min_length=1, max_length=100, description="Genre or category")
    description: str = Field(default="", description="Summary or description")
    price: float = Field(..., gt=0, description="Retail price in USD")
    stock: int = Field(default=0, ge=0, description="Available stock quantity")
    rating: float = Field(default=4.5, ge=0.0, le=5.0, description="Average review rating")
    tags: List[str] = Field(default_factory=list, description="List of keyword tags")


class BookCreate(BookBase):
    """Schema for creating a new book."""
    pass


class BookUpdate(BaseModel):
    """Schema for updating an existing book."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    tags: Optional[List[str]] = None


class BookRead(BookBase):
    """Schema for returning book details."""
    model_config = ConfigDict(from_attributes=True)
    id: int


class BookFilter(BaseModel):
    """Schema for filtering and searching the catalog."""
    query: Optional[str] = Field(None, description="Keyword search in title, author, or description")
    category: Optional[str] = Field(None, description="Category filter")
    max_price: Optional[float] = Field(None, gt=0, description="Maximum price filter")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    in_stock_only: bool = Field(default=False, description="Filter only items currently in stock")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
