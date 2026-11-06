"""Order and OrderItem database models."""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class OrderStatus(str, enum.Enum):
    """Enumeration of order lifecycle states."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    """Order placed by a customer."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    shipping_address = Column(String(500), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    coupon_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self) -> dict:
        """Convert order model to dictionary."""
        return {
            "id": self.id,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "shipping_address": self.shipping_address,
            "status": self.status.value if isinstance(self.status, OrderStatus) else self.status,
            "total_amount": round(self.total_amount, 2),
            "discount_amount": round(self.discount_amount, 2),
            "coupon_code": self.coupon_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }


class OrderItem(Base):
    """Line item in an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    book = relationship("Book", lazy="selectin")

    def to_dict(self) -> dict:
        """Convert order item to dictionary."""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "book_id": self.book_id,
            "book_title": self.book.title if self.book else None,
            "quantity": self.quantity,
            "unit_price": round(self.unit_price, 2),
            "subtotal": round(self.quantity * self.unit_price, 2),
        }
