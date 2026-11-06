"""Order processing and customer checkout REST API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate
from src.services.order_service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders & Checkout"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED, summary="Create a new customer order")
async def create_order(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Place an order, validate inventory, calculate discounts, and adjust stock."""
    service = OrderService(db)
    try:
        order = await service.create_order(order_in)
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{order_id}", response_model=OrderRead, summary="Get order details by ID")
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch order status and items by order ID."""
    service = OrderService(db)
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found",
        )
    return order


@router.get("/customer/{customer_email}", response_model=List[OrderRead], summary="List orders for customer email")
async def get_customer_orders(customer_email: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all orders placed with a customer email."""
    service = OrderService(db)
    orders = await service.get_orders_by_email(customer_email)
    return orders


@router.post("/{order_id}/cancel", response_model=OrderRead, summary="Cancel an order")
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel an active order and return items to stock."""
    service = OrderService(db)
    try:
        order = await service.cancel_order(order_id)
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{order_id}/status", response_model=OrderRead, summary="Update order fulfillment status")
async def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update order lifecycle status."""
    service = OrderService(db)
    order = await service.update_order_status(order_id, status_in.status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found",
        )
    return order
