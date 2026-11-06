"""Unit tests for Order and Customer Service Agentic Tools."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.tools.base import default_registry


@pytest.mark.asyncio
async def test_place_order_and_discount_tool(test_db_session: AsyncSession):
    """Test placing an order with a discount coupon."""
    context = {"db": test_db_session}

    # Place order for book #1
    result = await default_registry.execute_tool(
        name="place_order",
        tool_call_id="call_ord_1",
        arguments={
            "customer_email": "alice@example.com",
            "customer_name": "Alice Smith",
            "shipping_address": "123 Bookworm Lane, NY 10001",
            "items": [{"book_id": 1, "quantity": 2}],
            "coupon_code": "WELCOME10",
        },
        context=context,
    )

    assert result.success is True
    order = result.data["order"]
    assert order["customer_email"] == "alice@example.com"
    assert order["coupon_code"] == "WELCOME10"
    assert order["discount_amount"] > 0
    assert order["status"] == "confirmed"

    # Verify inventory was decremented
    inv_res = await default_registry.execute_tool(
        name="check_inventory",
        tool_call_id="call_inv_check",
        arguments={"book_id": 1},
        context=context,
    )
    assert inv_res.data["inventory"]["stock"] == 23  # started with 25


@pytest.mark.asyncio
async def test_order_status_and_cancellation(test_db_session: AsyncSession):
    """Test checking status and cancelling an order."""
    context = {"db": test_db_session}

    # Place an order
    place_res = await default_registry.execute_tool(
        name="place_order",
        tool_call_id="call_ord_2",
        arguments={
            "customer_email": "bob@example.com",
            "customer_name": "Bob Reader",
            "shipping_address": "456 Page St, Boston MA",
            "items": [{"book_id": 2, "quantity": 1}],
        },
        context=context,
    )
    order_id = place_res.data["order"]["id"]

    # Check status
    status_res = await default_registry.execute_tool(
        name="get_order_status",
        tool_call_id="call_stat_1",
        arguments={"order_id": order_id},
        context=context,
    )
    assert status_res.data["found"] is True
    assert status_res.data["order"]["id"] == order_id

    # Cancel order
    cancel_res = await default_registry.execute_tool(
        name="cancel_order",
        tool_call_id="call_canc_1",
        arguments={"order_id": order_id},
        context=context,
    )
    assert cancel_res.data["success"] is True
    assert cancel_res.data["order"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_policy_and_coupon_tools(test_db_session: AsyncSession):
    """Test policy lookup and coupon validation tools."""
    context = {"db": test_db_session}

    # Validate valid coupon
    coupon_res = await default_registry.execute_tool(
        name="validate_coupon_code",
        tool_call_id="call_coup_1",
        arguments={"coupon_code": "BOOKWORM20"},
        context=context,
    )
    assert coupon_res.data["valid"] is True
    assert coupon_res.data["discount_percentage"] == 20

    # Policy inquiry
    policy_res = await default_registry.execute_tool(
        name="get_store_policies",
        tool_call_id="call_pol_1",
        arguments={"topic": "shipping"},
        context=context,
    )
    assert "policy" in policy_res.data
    assert "shipping" in policy_res.data["policy"].lower()
