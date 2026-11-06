"""Pydantic schemas for Order domain."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from src.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """Schema for adding an item to an order."""
    book_id: int = Field(..., gt=0, description="Database ID of the book")
    quantity: int = Field(default=1, ge=1, le=100, description="Quantity to purchase")


class OrderItemRead(BaseModel):
    """Schema for displaying order item details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    book_title: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float


class OrderCreate(BaseModel):
    """Schema for placing an order."""
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_name: str = Field(..., min_length=2, max_length=255, description="Customer full name")
    shipping_address: str = Field(..., min_length=5, max_length=500, description="Delivery address")
    coupon_code: Optional[str] = Field(None, max_length=50, description="Optional promotional discount code")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items to purchase")


class OrderRead(BaseModel):
    """Schema for returning order summary and items."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_email: str
    customer_name: str
    shipping_address: str
    status: OrderStatus
    total_amount: float
    discount_amount: float
    coupon_code: Optional[str] = None
    created_at: datetime
    items: List[OrderItemRead] = Field(default_factory=list)


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""
    status: OrderStatus
