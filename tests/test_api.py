"""Integration tests for FastAPI REST API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test health check route."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_and_filter_books(async_client: AsyncClient):
    """Test book listing API."""
    response = await async_client.get("/api/v1/books?category=Sci-Fi")
    assert response.status_code == 200
    books = response.json()
    assert len(books) >= 1
    assert all(b["category"] == "Sci-Fi" for b in books)


@pytest.mark.asyncio
async def test_order_creation_flow(async_client: AsyncClient):
    """Test complete order creation and status check over REST API."""
    payload = {
        "customer_email": "charlie@example.com",
        "customer_name": "Charlie Brown",
        "shipping_address": "789 Peanut Blvd, MN",
        "coupon_code": "WELCOME10",
        "items": [{"book_id": 1, "quantity": 1}],
    }

    create_res = await async_client.post("/api/v1/orders", json=payload)
    assert create_res.status_code == 201
    order = create_res.json()
    assert order["id"] > 0
    assert order["status"] == "confirmed"
    assert order["discount_amount"] > 0

    # Fetch order by ID
    get_res = await async_client.get(f"/api/v1/orders/{order['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["customer_email"] == "charlie@example.com"


@pytest.mark.asyncio
async def test_agent_tools_discovery(async_client: AsyncClient):
    """Test discovering available agentic tools via REST API."""
    response = await async_client.get("/api/v1/agent/tools")
    assert response.status_code == 200
    tools = response.json()
    tool_names = [t["name"] for t in tools]
    assert "search_books" in tool_names
    assert "place_order" in tool_names
    assert "recommend_books" in tool_names
    assert "get_store_policies" in tool_names


@pytest.mark.asyncio
async def test_agent_chat_api(async_client: AsyncClient):
    """Test conversational agent endpoint."""
    payload = {
        "messages": [
            {"role": "user", "content": "Show me books on clean code and software craftsmanship"}
        ],
        "max_steps": 3,
    }

    response = await async_client.post("/api/v1/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Clean Code" in data["reply"]
    assert "search_books" in data["tools_used"]
    assert len(data["steps"]) >= 1
