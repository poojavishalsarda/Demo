"""Agentic reasoning engine, tool loop, and multi-turn execution."""
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.schemas.agent import (
    AgentRequest,
    AgentResponse,
    AgentThoughtStep,
    ChatMessage,
    ToolCall,
    ToolExecutionResult,
)
from src.tools.base import ToolRegistry, default_registry
from src.agent.prompts import BOOKSTORE_AGENT_SYSTEM_PROMPT

logger = logging.getLogger("bookstore.agent")


class AgentEngine:
    """Executes the agentic reasoning and tool invocation loop."""

    def __init__(
        self,
        db: AsyncSession,
        registry: ToolRegistry = default_registry,
        model_provider: Optional[str] = None,
    ):
        self.db = db
        self.registry = registry
        self.model_provider = model_provider or settings.AGENT_MODEL_PROVIDER

    async def run(
        self,
        messages: List[ChatMessage],
        customer_email: Optional[str] = None,
        max_steps: int = 5,
    ) -> AgentResponse:
        """Execute the agent loop with reasoning steps and tool calls."""
        steps: List[AgentThoughtStep] = []
        tools_used: List[str] = []

        # Find the latest user message
        user_messages = [m for m in messages if m.role == "user"]
        latest_user_text = user_messages[-1].content if user_messages else ""

        # Context provided to tools
        context = {
            "db": self.db,
            "customer_email": customer_email,
        }

        # Determine tool calls based on intent / LLM reasoning
        step_count = 0
        current_thought = "Analyzing user inquiry to identify required bookstore operations and agent tools."
        
        while step_count < max_steps:
            step_count += 1
            planned_calls = self._plan_tools(latest_user_text, customer_email, step_count)

            if not planned_calls:
                # No more tools needed; synthesize final answer
                break

            step = AgentThoughtStep(
                step=step_count,
                thought=current_thought,
                tool_calls=planned_calls,
                tool_results=[],
            )

            for call in planned_calls:
                if call.name not in tools_used:
                    tools_used.append(call.name)

                result = await self.registry.execute_tool(
                    name=call.name,
                    tool_call_id=call.id,
                    arguments=call.arguments,
                    context=context,
                )
                step.tool_results.append(result)

            steps.append(step)
            # For multi-step queries, break after first coherent tool execution in deterministic mode
            break

        # Synthesize final response from tool executions
        reply = self._synthesize_response(latest_user_text, steps)

        return AgentResponse(
            reply=reply,
            steps=steps,
            tools_used=tools_used,
        )

    def _plan_tools(
        self,
        user_query: str,
        customer_email: Optional[str],
        step: int,
    ) -> List[ToolCall]:
        """Plan which agent tools should be called based on query semantics."""
        q = user_query.lower()
        tool_calls: List[ToolCall] = []

        # 1. Order Status Tracking
        order_num_match = re.search(r"order\s*(?:#|number|id)?\s*(\d+)", q)
        if ("order status" in q or "track" in q or "where is my order" in q or "check order" in q) and order_num_match:
            order_id = int(order_num_match.group(1))
            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="get_order_status",
                    arguments={"order_id": order_id},
                )
            )
            return tool_calls

        # 2. Cancel Order
        if ("cancel" in q and "order" in q) and order_num_match:
            order_id = int(order_num_match.group(1))
            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="cancel_order",
                    arguments={"order_id": order_id},
                )
            )
            return tool_calls

        # 3. Customer Past Orders
        if ("my orders" in q or "past orders" in q or "order history" in q) and customer_email:
            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="get_customer_orders",
                    arguments={"customer_email": customer_email},
                )
            )
            return tool_calls

        # 4. Coupon Validation
        coupon_match = re.search(r"(?:coupon|promo|code)\s+([A-Z0-9]{5,15})", user_query)
        if coupon_match or "discount code" in q or "promo code" in q or "coupon" in q:
            code = coupon_match.group(1) if coupon_match else "WELCOME10"
            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="validate_coupon_code",
                    arguments={"coupon_code": code},
                )
            )
            return tool_calls

        # 5. Store Policies (Shipping, Returns, Refunds, Discounts)
        if any(w in q for w in ["return", "refund", "shipping", "delivery", "policy", "digital"]):
            topic = "returns"
            if "shipping" in q or "delivery" in q:
                topic = "shipping"
            elif "refund" in q:
                topic = "refunds"
            elif "discount" in q:
                topic = "discounts"
            elif "digital" in q or "ebook" in q:
                topic = "digital_books"

            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="get_store_policies",
                    arguments={"topic": topic},
                )
            )
            return tool_calls

        # 6. Recommendation query
        if any(w in q for w in ["recommend", "suggestion", "suggest", "similar to", "what should i read"]):
            genre = "Technology"
            if "scifi" in q or "sci-fi" in q or "space" in q or "dune" in q:
                genre = "Sci-Fi"
            elif "psychology" in q or "habit" in q:
                genre = "Psychology"
            elif "ai" in q or "artificial intelligence" in q:
                genre = "Artificial Intelligence"

            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="recommend_books",
                    arguments={"topic_or_genre": genre, "limit": 3},
                )
            )
            return tool_calls

        # 7. Inventory check
        book_id_match = re.search(r"book\s*(?:#|id)?\s*(\d+)", q)
        if ("inventory" in q or "stock" in q or "available" in q) and book_id_match:
            b_id = int(book_id_match.group(1))
            tool_calls.append(
                ToolCall(
                    id=str(uuid.uuid4())[:8],
                    name="check_inventory",
                    arguments={"book_id": b_id},
                )
            )
            return tool_calls

        # 8. General Search / Catalog Lookups
        cleaned_query = re.sub(r"(search|find|show me|look for|books? about|books? by)", "", q).strip()
        search_term = cleaned_query if len(cleaned_query) > 2 else None

        tool_calls.append(
            ToolCall(
                id=str(uuid.uuid4())[:8],
                name="search_books",
                arguments={"query": search_term, "limit": 4},
            )
        )
        return tool_calls

    def _synthesize_response(self, user_query: str, steps: List[AgentThoughtStep]) -> str:
        """Synthesize natural language response based on executed tool data."""
        if not steps or not steps[0].tool_results:
            return "Hello! I am your Bookstore AI Concierge. How can I help you discover books, check orders, or explore recommendations today?"

        first_step = steps[0]
        res = first_step.tool_results[0]

        if not res.success:
            return f"I encountered an issue processing your request: {res.error}."

        data = res.data or {}

        # Handle search_books
        if res.tool_name == "search_books":
            books = data.get("books", [])
            if not books:
                return "I couldn't find any books matching your specific criteria in our catalog. Try searching with broader keywords or checking our recommended categories!"
            lines = ["Here are the books I found for you:"]
            for b in books:
                stock_status = f"In Stock ({b['stock']} available)" if b.get("stock", 0) > 0 else "Out of Stock"
                lines.append(
                    f"• **{b['title']}** by {b['author']} — **${b['price']:.2f}** | Rating: {b.get('rating', 'N/A')}⭐ | {stock_status} (ID: {b['id']})"
                )
            return "\n".join(lines)

        # Handle recommend_books
        if res.tool_name == "recommend_books":
            recs = data.get("recommendations", [])
            lines = [f"{data.get('reason', 'Here are our top recommendations for you')}:"]
            for b in recs:
                lines.append(
                    f"• **{b['title']}** by {b['author']} — **${b['price']:.2f}** | {b['category']} | {b.get('rating', 'N/A')}⭐ (ID: {b['id']})"
                )
            return "\n".join(lines)

        # Handle get_order_status
        if res.tool_name == "get_order_status":
            if not data.get("found"):
                return data.get("message", "Order not found.")
            order = data.get("order", {})
            return (
                f"**Order #{order['id']}** for {order['customer_name']}:\n"
                f"• Status: **{order['status'].upper()}**\n"
                f"• Total: **${order['total_amount']:.2f}**\n"
                f"• Items: {len(order.get('items', []))} item(s)\n"
                f"• Shipping to: {order['shipping_address']}"
            )

        # Handle cancel_order
        if res.tool_name == "cancel_order":
            return data.get("message", "Order cancellation processed.")

        # Handle get_store_policies
        if res.tool_name == "get_store_policies":
            if "policy" in data:
                return f"**Store Policy ({data.get('topic', 'General').title()}):**\n{data['policy']}"
            return "Here are our store policies: " + json.dumps(data.get("all_policies", {}), indent=2)

        # Handle validate_coupon_code
        if res.tool_name == "validate_coupon_code":
            return data.get("message", "Coupon checked.")

        # Handle check_inventory
        if res.tool_name == "check_inventory":
            inv = data.get("inventory", {})
            if not data.get("found"):
                return data.get("message", "Book not found.")
            status_str = f"in stock with {inv.get('stock')} units available" if inv.get("in_stock") else "currently out of stock"
            return f"**{inv.get('title')}** (ID: {inv.get('book_id')}) is {status_str} at ${inv.get('price'):.2f}."

        return f"Operation completed successfully. Result: {data}"
