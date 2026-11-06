"""Customer support and policy inquiry agentic tools."""
from typing import Any, Dict
from pydantic import BaseModel, Field
from src.services.order_service import VALID_COUPONS
from src.tools.base import default_registry


STORE_POLICIES = {
    "shipping": "Standard delivery takes 3-5 business days. Express next-day shipping is available on all domestic orders. Free shipping on orders over $50.",
    "returns": "Items can be returned within 30 days of delivery in original condition. Return shipping labels are free for store credit exchanges.",
    "refunds": "Refunds are processed to the original payment method within 5 business days after returned items are inspected at our warehouse.",
    "discounts": "We offer seasonal promotion codes including WELCOME10 (10% off for new shoppers) and BOOKWORM20 (20% off selected reading list items). Only one coupon can be applied per order.",
    "digital_books": "eBooks and Audiobooks are delivered instantly to your registered account upon successful payment and are non-refundable once downloaded.",
}


class StorePoliciesInput(BaseModel):
    """Input for querying store customer policy knowledge."""
    topic: str = Field(
        ...,
        description="Policy topic: 'shipping', 'returns', 'refunds', 'discounts', 'digital_books', or 'all'",
    )


class ValidateCouponInput(BaseModel):
    """Input for validating a promotional coupon code."""
    coupon_code: str = Field(..., description="Coupon code string to check (e.g., 'WELCOME10', 'BOOKWORM20')")


@default_registry.register(
    name="get_store_policies",
    description="Retrieve bookstore customer policies regarding shipping, returns, refunds, discount rules, and digital book fulfillment.",
    schema_model=StorePoliciesInput,
)
def get_store_policies(topic: str) -> Dict[str, Any]:
    """Retrieve policy information."""
    topic_key = topic.strip().lower()
    if topic_key == "all":
        return {"policies": STORE_POLICIES}

    if topic_key in STORE_POLICIES:
        return {"topic": topic_key, "policy": STORE_POLICIES[topic_key]}

    # Partial match fallback
    for k, v in STORE_POLICIES.items():
        if topic_key in k or k in topic_key:
            return {"topic": k, "policy": v}

    return {
        "topic": topic,
        "message": f"No specific policy entry for '{topic}'. Available topics are: {list(STORE_POLICIES.keys())}.",
        "all_policies": STORE_POLICIES,
    }


@default_registry.register(
    name="validate_coupon_code",
    description="Check if a promo/coupon code is valid and retrieve the discount percentage.",
    schema_model=ValidateCouponInput,
)
def validate_coupon_code(coupon_code: str) -> Dict[str, Any]:
    """Check coupon discount percentage."""
    code = coupon_code.strip().upper()
    if code in VALID_COUPONS:
        discount_pct = int(VALID_COUPONS[code] * 100)
        return {
            "valid": True,
            "coupon_code": code,
            "discount_percentage": discount_pct,
            "message": f"Coupon '{code}' is valid for {discount_pct}% off your order total.",
        }
    return {
        "valid": False,
        "coupon_code": coupon_code,
        "message": f"Coupon code '{coupon_code}' is invalid or expired.",
    }
