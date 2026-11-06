"""Unit tests for Agent Engine reasoning loop."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.agent.engine import AgentEngine
from src.schemas.agent import ChatMessage
from src.tools.base import default_registry


@pytest.mark.asyncio
async def test_agent_search_reasoning(test_db_session: AsyncSession):
    """Test agent reasoning and tool invocation for catalog search queries."""
    engine = AgentEngine(db=test_db_session, registry=default_registry)
    
    messages = [
        ChatMessage(role="user", content="Can you find books about distributed systems or data?")
    ]

    response = await engine.run(messages=messages)
    assert response.reply is not None
    assert "Designing Data-Intensive Applications" in response.reply
    assert "search_books" in response.tools_used
    assert len(response.steps) >= 1
    assert response.steps[0].tool_results[0].success is True


@pytest.mark.asyncio
async def test_agent_policy_reasoning(test_db_session: AsyncSession):
    """Test agent reasoning on customer policy questions."""
    engine = AgentEngine(db=test_db_session, registry=default_registry)

    messages = [
        ChatMessage(role="user", content="What is your return policy?")
    ]

    response = await engine.run(messages=messages)
    assert "get_store_policies" in response.tools_used
    assert "30 days" in response.reply


@pytest.mark.asyncio
async def test_agent_recommendation_reasoning(test_db_session: AsyncSession):
    """Test agent book recommendations."""
    engine = AgentEngine(db=test_db_session, registry=default_registry)

    messages = [
        ChatMessage(role="user", content="Can you recommend some sci-fi books?")
    ]

    response = await engine.run(messages=messages)
    assert "recommend_books" in response.tools_used
    assert ("Dune" in response.reply or "Project Hail Mary" in response.reply)
