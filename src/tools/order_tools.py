"""Order management and customer purchasing agentic tools."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.order import OrderCreate, OrderItemCreate
from src.services.order_service import OrderService
from src.tools.base import default_registry


class OrderItemInput(BaseModel):
    """Line item for order creation."""
    book_id: int = Field(..., description="The ID of the book being purchased")
    quantity: int = Field(1, ge=1, le=50, description="Quantity of books to purchase")


class PlaceOrderInput(BaseModel):
    """Input parameters for placing a bookstore order."""
    customer_email: EmailStr = Field(..., description="Customer's email address")
    customer_name: str = Field(..., description="Customer's full name")
    shipping_address: str = Field(..., description="Physical destination shipping address")
    items: List[OrderItemInput] = Field(..., description="List of book items and quantities to purchase")
    coupon_code: Optional[str] = Field(None, description="Optional discount promo code (e.g. 'WELCOME10', 'BOOKWORM20')")


class GetOrderStatusInput(BaseModel):
    """Input parameters for checking an existing order's status."""
    order_id: int = Field(..., description="Numeric identifier of the order")


class GetCustomerOrdersInput(BaseModel):
    """Input parameters for retrieving all orders of a customer."""
    customer_email: EmailStr = Field(..., description="Email address of the customer")


class CancelOrderInput(BaseModel):
    """Input parameters for cancelling an order."""
    order_id: int = Field(..., description="Numeric identifier of the order to cancel")


@default_registry.register(
    name="place_order",
    description="Place a new book order for a customer. Validates stock availability, applies discounts/coupons, and creates confirmed order.",
    schema_model=PlaceOrderInput,
)
async def place_order(
    customer_email: str,
    customer_name: str,
    shipping_address: str,
    items: List[Dict[str, Any]],
    coupon_code: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """Place customer order via tool call."""
    if not db:
        raise ValueError("Database session is required to place order.")

    order_items = [
        OrderItemCreate(book_id=item["book_id"], quantity=item.get("quantity", 1))
        for item in items
    ]

    order_in = OrderCreate(
        customer_email=customer_email,
        customer_name=customer_name,
        shipping_address=shipping_address,
        coupon_code=coupon_code,
        items=order_items,
    )

    service = OrderService(db)
    order = await service.create_order(order_in)
    return {
        "success": True,
        "message": f"Order #{order.id} has been successfully placed!",
        "order": order.to_dict(),
    }


@default_registry.register(
    name="get_order_status",
    description="Check the current fulfillment status, items, tracking, and details of an order using its order_id.",
    schema_model=GetOrderStatusInput,
)
async def get_order_status(order_id: int, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Check order status."""
    if not db:
        raise ValueError("Database session is required.")

    service = OrderService(db)
    order = await service.get_order_by_id(order_id)
    if not order:
        return {"found": False, "message": f"No order found with ID #{order_id}."}

    return {"found": True, "order": order.to_dict()}


@default_registry.register(
    name="get_customer_orders",
    description="Retrieve all past and active orders for a customer by providing their email address.",
    schema_model=GetCustomerOrdersInput,
)
async def get_customer_orders(customer_email: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """List customer orders."""
    if not db:
        raise ValueError("Database session is required.")

    service = OrderService(db)
    orders = await service.get_orders_by_email(customer_email)
    return {
        "customer_email": customer_email,
        "order_count": len(orders),
        "orders": [o.to_dict() for o in orders],
    }


@default_registry.register(
    name="cancel_order",
    description="Cancel an active order if it has not yet shipped. Restores inventory stock automatically.",
    schema_model=CancelOrderInput,
)
async def cancel_order(order_id: int, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Cancel customer order."""
    if not db:
        raise ValueError("Database session is required.")

    service = OrderService(db)
    try:
        order = await service.cancel_order(order_id)
        return {
            "success": True,
            "message": f"Order #{order_id} was successfully cancelled.",
            "order": order.to_dict(),
        }
    except ValueError as e:
        return {
            "success": False,
            "message": str(e),
        }
