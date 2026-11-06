"""Unit tests for Catalog Agentic Tools."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.tools.base import default_registry


@pytest.mark.asyncio
async def test_search_books_tool(test_db_session: AsyncSession):
    """Test searching books by topic or keyword."""
    context = {"db": test_db_session}
    
    result = await default_registry.execute_tool(
        name="search_books",
        tool_call_id="call_test_1",
        arguments={"query": "data", "limit": 3},
        context=context,
    )

    assert result.success is True
    assert result.error is None
    assert result.data["count"] >= 1
    found_titles = [b["title"] for b in result.data["books"]]
    assert any("Designing Data-Intensive Applications" in t for t in found_titles)


@pytest.mark.asyncio
async def test_get_book_details_tool(test_db_session: AsyncSession):
    """Test fetching details for an existing book."""
    context = {"db": test_db_session}

    # Fetch book ID 1
    result = await default_registry.execute_tool(
        name="get_book_details",
        tool_call_id="call_test_2",
        arguments={"book_id": 1},
        context=context,
    )

    assert result.success is True
    assert result.data["found"] is True
    book = result.data["book"]
    assert book["id"] == 1
    assert "author" in book
    assert "price" in book


@pytest.mark.asyncio
async def test_check_inventory_tool(test_db_session: AsyncSession):
    """Test inventory check tool."""
    context = {"db": test_db_session}

    result = await default_registry.execute_tool(
        name="check_inventory",
        tool_call_id="call_test_3",
        arguments={"book_id": 1},
        context=context,
    )

    assert result.success is True
    assert result.data["found"] is True
    inv = result.data["inventory"]
    assert inv["stock"] > 0
    assert inv["in_stock"] is True
