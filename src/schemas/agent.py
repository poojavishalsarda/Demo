"""Schemas for Agentic Tool calling and conversational loop."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single turn in the conversational dialogue."""
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="Role of the message author")
    content: Optional[str] = Field(default="", description="Text message content")
    name: Optional[str] = Field(None, description="Tool name when role is 'tool' or tool function call")
    tool_call_id: Optional[str] = Field(None, description="Identifier linking tool result to call")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls initiated by assistant")


class ToolParameterProperty(BaseModel):
    """JSON Schema definition for an individual parameter."""
    type: str
    description: str
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """OpenAPI/JSON Schema definition of an Agentic Tool."""
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Detailed description of tool capability and when to use it")
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []},
        description="JSON schema describing parameters accepted by the tool",
    )


class ToolCall(BaseModel):
    """Specification of a tool to be invoked by the agent."""
    id: str = Field(..., description="Invocation UUID / ID")
    name: str = Field(..., description="Target tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Parsed arguments for the tool")


class ToolExecutionResult(BaseModel):
    """Structured result returned by a tool execution."""
    tool_call_id: str
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class AgentRequest(BaseModel):
    """Request payload sent to the Bookstore AI Agent."""
    messages: List[ChatMessage] = Field(..., description="Full or recent conversation history")
    customer_email: Optional[str] = Field(None, description="Optional customer email for personalization")
    max_steps: int = Field(default=5, ge=1, le=10, description="Max reasoning/tool execution steps")


class AgentThoughtStep(BaseModel):
    """Individual reasoning / tool invocation step by the agent."""
    step: int
    thought: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolExecutionResult] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Final response returned by the Bookstore AI Agent."""
    reply: str = Field(..., description="Natural language response to the user")
    steps: List[AgentThoughtStep] = Field(default_factory=list, description="Reasoning and tool execution traces")
    tools_used: List[str] = Field(default_factory=list, description="List of unique tool names used")
