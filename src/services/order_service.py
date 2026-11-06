"""Order service implementing order lifecycle, discounts, and inventory deduction."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.book import Book
from src.models.order import Order, OrderItem, OrderStatus
from src.schemas.order import OrderCreate


# Active promotional discount codes
VALID_COUPONS = {
    "WELCOME10": 0.10,  # 10% off
    "BOOKWORM20": 0.20,  # 20% off
    "READMORE15": 0.15,  # 15% off
}


class OrderService:
    """Manages order creation, pricing calculation, status updates, and cancellation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Fetch order by ID."""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_orders_by_email(self, email: str) -> List[Order]:
        """Fetch all orders for a specific customer email."""
        stmt = (
            select(Order)
            .where(Order.customer_email == email.strip().lower())
            .order_by(Order.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_order(self, order_in: OrderCreate) -> Order:
        """Create a new customer order, calculate totals, and deduct inventory."""
        subtotal = 0.0
        order_items: List[OrderItem] = []

        # Validate items and inventory
        for item_data in order_in.items:
            stmt = select(Book).where(Book.id == item_data.book_id)
            res = await self.db.execute(stmt)
            book = res.scalar_one_or_none()

            if not book:
                raise ValueError(f"Book with ID {item_data.book_id} not found.")

            if book.stock < item_data.quantity:
                raise ValueError(
                    f"Insufficient stock for '{book.title}'. Requested: {item_data.quantity}, Available: {book.stock}"
                )

            # Deduct stock
            book.stock -= item_data.quantity
            line_total = book.price * item_data.quantity
            subtotal += line_total

            order_item = OrderItem(
                book_id=book.id,
                quantity=item_data.quantity,
                unit_price=book.price,
            )
            order_items.append(order_item)

        # Apply coupon if valid
        discount_amount = 0.0
        coupon_applied = None
        if order_in.coupon_code:
            code = order_in.coupon_code.strip().upper()
            if code in VALID_COUPONS:
                discount_rate = VALID_COUPONS[code]
                discount_amount = subtotal * discount_rate
                coupon_applied = code
            else:
                raise ValueError(f"Invalid coupon code: {order_in.coupon_code}")

        total_amount = max(0.0, subtotal - discount_amount)

        order = Order(
            customer_email=order_in.customer_email.strip().lower(),
            customer_name=order_in.customer_name.strip(),
            shipping_address=order_in.shipping_address.strip(),
            status=OrderStatus.CONFIRMED,
            total_amount=total_amount,
            discount_amount=discount_amount,
            coupon_code=coupon_applied,
            items=order_items,
        )

        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def cancel_order(self, order_id: int) -> Order:
        """Cancel an order and restock items if eligible."""
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order #{order_id} not found.")

        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError(f"Order #{order_id} cannot be cancelled in state '{order.status.value}'.")

        # Restock books
        for item in order.items:
            stmt = select(Book).where(Book.id == item.book_id)
            res = await self.db.execute(stmt)
            book = res.scalar_one_or_none()
            if book:
                book.stock += item.quantity

        order.status = OrderStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def update_order_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        """Update the lifecycle status of an order."""
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        order.status = status
        await self.db.flush()
        await self.db.refresh(order)
        return order
