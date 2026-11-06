"""Base Tool classes, Registry, and execution interfaces."""
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from pydantic import BaseModel
from src.schemas.agent import ToolDefinition, ToolExecutionResult


class BaseTool:
    """Represents an agentic tool with schema introspection and async execution."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        schema_model: Optional[Type[BaseModel]] = None,
    ):
        self.name = name
        self.description = description.strip()
        self.func = func
        self.schema_model = schema_model

    def get_definition(self) -> ToolDefinition:
        """Generate JSON Schema representation for LLM function calling / tools API."""
        if self.schema_model:
            schema = self.schema_model.model_json_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            return ToolDefinition(
                name=self.name,
                description=self.description,
                parameters={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            )

        # Introspect function signature if no explicit Pydantic model is supplied
        sig = inspect.signature(self.func)
        type_hints = get_type_hints(self.func)
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ["self", "db", "session", "context"]:
                continue  # Injected dependencies

            param_type = type_hints.get(param_name, str)
            type_str = "string"
            if param_type in [int, float]:
                type_str = "number" if param_type is float else "integer"
            elif param_type is bool:
                type_str = "boolean"
            elif param_type in [list, List]:
                type_str = "array"

            properties[param_name] = {
                "type": type_str,
                "description": f"Parameter {param_name}",
            }

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
            },
        )

    async def execute(self, tool_call_id: str, kwargs: Dict[str, Any], context: Dict[str, Any]) -> ToolExecutionResult:
        """Safely execute the tool with given arguments and context."""
        try:
            # Check if function accepts context / db
            sig = inspect.signature(self.func)
            call_kwargs = dict(kwargs)

            for key in ["db", "session", "context"]:
                if key in sig.parameters and key in context:
                    call_kwargs[key] = context[key]

            if inspect.iscoroutinefunction(self.func):
                result = await self.func(**call_kwargs)
            else:
                result = self.func(**call_kwargs)

            # Convert result if it's a Pydantic model
            if isinstance(result, BaseModel):
                data = result.model_dump()
            elif hasattr(result, "to_dict"):
                data = result.to_dict()
            elif isinstance(result, list):
                data = [item.to_dict() if hasattr(item, "to_dict") else item for item in result]
            else:
                data = result

            return ToolExecutionResult(
                tool_call_id=tool_call_id,
                tool_name=self.name,
                success=True,
                data=data,
                error=None,
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_call_id=tool_call_id,
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e),
            )


class ToolRegistry:
    """Central registry for discovering, inspecting, and running agentic tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, name: str, description: str, schema_model: Optional[Type[BaseModel]] = None):
        """Decorator to register a function as an agentic tool."""
        def decorator(func: Callable):
            tool = BaseTool(name=name, description=description, func=func, schema_model=schema_model)
            self._tools[name] = tool
            return func
        return decorator

    def add_tool(self, tool: BaseTool):
        """Add an instantiated BaseTool."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Fetch tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List all tool definitions for LLM schemas."""
        return [tool.get_definition() for tool in self._tools.values()]

    async def execute_tool(
        self,
        name: str,
        tool_call_id: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """Find and execute a registered tool."""
        tool = self.get_tool(name)
        if not tool:
            return ToolExecutionResult(
                tool_call_id=tool_call_id,
                tool_name=name,
                success=False,
                data=None,
                error=f"Tool '{name}' is not registered in the system.",
            )
        return await tool.execute(tool_call_id, arguments, context)


# Global default registry for bookstore agent
default_registry = ToolRegistry()
