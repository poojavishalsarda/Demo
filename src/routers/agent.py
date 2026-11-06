"""Agentic Tool execution and conversation REST API endpoints."""
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.agent.engine import AgentEngine
from src.database import get_db
from src.schemas.agent import (
    AgentRequest,
    AgentResponse,
    ToolDefinition,
    ToolExecutionResult,
)
from src.tools.base import default_registry

router = APIRouter(prefix="/api/v1/agent", tags=["Agentic AI Assistant"])


@router.post("/chat", response_model=AgentResponse, summary="Chat with the Bookstore AI Agent")
async def chat_with_agent(
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Interact with the Agentic Bookstore Concierge.
    
    The agent dynamically reasons, selects, and executes domain tools to satisfy user requests,
    such as searching the catalog, checking inventory, tracking orders, or validating promotional discounts.
    """
    engine = AgentEngine(db=db, registry=default_registry)
    response = await engine.run(
        messages=request.messages,
        customer_email=request.customer_email,
        max_steps=request.max_steps,
    )
    return response


@router.get("/tools", response_model=List[ToolDefinition], summary="List all available Agentic Tools")
async def list_agent_tools():
    """Retrieve OpenAPI / Function-calling JSON Schema definitions for all registered tools."""
    return default_registry.list_tools()


@router.post(
    "/tools/{tool_name}/execute",
    response_model=ToolExecutionResult,
    summary="Directly execute an Agentic Tool",
)
async def execute_tool_directly(
    tool_name: str,
    arguments: Dict[str, Any] = Body(default_factory=dict),
    customer_email: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Directly invoke an agent tool by name with parameter arguments."""
    tool = default_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent tool '{tool_name}' not found.",
        )

    context = {"db": db, "customer_email": customer_email}
    tool_call_id = f"call_{str(uuid.uuid4())[:8]}"
    result = await default_registry.execute_tool(
        name=tool_name,
        tool_call_id=tool_call_id,
        arguments=arguments,
        context=context,
    )
    return result
