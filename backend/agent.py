import os
import json
import uuid
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic import BaseModel
from typing import Optional
from database import (
    get_all_products, get_product_by_id,
    get_cart, save_cart, get_memory, save_memory,
    save_order, get_style_profile, save_style_profile,
    add_to_wishlist, get_wishlist, save_outfit,
    get_outfits, add_review, get_reviews, track_event
)
from vector_store import search_products

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')

model = GroqModel('llama-3.3-70b-versatile')

class ShoppingResponse(BaseModel):
    message: str
    intent: str
    suggested_products: list[str] = []
    outfit_name: Optional[str] = None
    outfit_occasion: Optional[str] = None
    style_tips: list[str] = []

class OutfitResponse(BaseModel):
    outfit_name: str
    occasion: str
    description: str
    items: list[str]
    styling_tips: list[str]
    total_budget: str

class StyleProfileResponse(BaseModel):
    body_type: str
    style_keywords: list[str]
    recommended_colors: list[str]
    avoided_styles: list[str]
    occasions: list[str]
    size_advice: str
    budget_range: str

class ReviewSummary(BaseModel):
    summary: str
    pros: list[str]
    cons: list[str]
    verdict: str

# Main shopping agent
shopping_agent = Agent(
    model=model,
    output_type=ShoppingResponse,
    system_prompt="""
    You are Bella, a world-class personal fashion stylist for an
    exclusive online clothing store. You are warm, knowledgeable,
    and deeply passionate about helping people look and feel amazing.

    Your expertise:
    - Building complete outfits not just single items
    - Understanding body types and what flatters each
    - Seasonal and occasion-based styling
    - Budget-conscious fashion advice
    - Color theory and coordination
    - Current fashion trends

    Available categories: dresses, tops, bottoms, swimwear, accessories, footwear

    Always:
    - Suggest complete outfits with multiple complementary pieces
    - Give specific styling advice
    - Consider the customer's stated budget
    - Remember preferences from earlier in the conversation
    - Be enthusiastic but not overwhelming
    - Ask one follow-up question to refine recommendations

    Return JSON with:
    - message: your warm, detailed stylist response
    - intent: one of [search, outfit, recommend, add_cart, checkout, style_quiz, general]
    - suggested_products: list of specific product names you mention
    - outfit_name: name for the complete outfit if suggesting one
    - outfit_occasion: occasion this outfit is for
    - style_tips: 2-3 specific styling tips
    """
)

# Outfit generator agent
outfit_agent = Agent(
    model=model,
    output_type=OutfitResponse,
    system_prompt="""
    You are an expert fashion coordinator. Generate complete,
    cohesive outfit combinations from available products.

    When creating outfits:
    - Ensure color harmony
    - Match the occasion perfectly
    - Balance proportions
    - Include accessories when appropriate
    - Consider the total price

    Return a complete outfit as JSON with name, occasion,
    description, items list, styling tips, and total budget.
    """
)

# Style profile agent
style_agent = Agent(
    model=model,
    output_type=StyleProfileResponse,
    system_prompt="""
    You are a professional fashion consultant who creates
    detailed style profiles. Based on customer information,
    determine their style DNA.

    Analyze: body type, color preferences, lifestyle,
    occasions, budget, and personal style keywords.

    Return a comprehensive style profile as JSON.
    """
)

# Review summarizer agent
review_agent = Agent(
    model=model,
    output_type=ReviewSummary,
    system_prompt="""
    You are a fashion product analyst. Summarize customer
    reviews into clear, helpful insights.

    Identify: overall sentiment, key pros, key cons,
    and give a final verdict.

    Return structured JSON with summary, pros, cons, verdict.
    """
)

async def chat_with_agent(session_id: str, user_message: str):
    memory = get_memory(session_id)
    messages = memory["messages"]
    profile = memory["profile"]
    style_profile = get_style_profile(session_id)

    # Build rich context
    memory_context = ""
    if profile:
        memory_context = f"Customer preferences: {json.dumps(profile)}\n"
    if style_profile:
        memory_context += f"Style profile: {json.dumps(style_profile)}\n"
    if messages:
        recent = messages[-8:]
        history = "\n".join([
            f"{m['role']}: {m['content']}" for m in recent
        ])
        memory_context += f"Recent conversation:\n{history}\n"

    # Semantic product search
    relevant_products = search_products(user_message, n_results=6)
    products_context = ""
    if relevant_products:
        products_context = "Relevant products available:\n"
        for p in relevant_products:
            products_context += (
                f"- {p['name']}: ${p['price']} | "
                f"Colors: {', '.join(p['colors'])} | "
                f"Sizes: {', '.join(p['sizes'])} | "
                f"Rating: {p['rating']:.1f}\n"
            )

    full_prompt = f"""
{memory_context}
{products_context}
Customer message: {user_message}
Respond as Bella the fashion stylist.
"""

    result = await shopping_agent.run(full_prompt)
    response = result.output

    # Update memory
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": response.message})

    # Auto-extract profile info
    msg_lower = user_message.lower()
    for size in ["xs", "s", "m", "l", "xl", "xxl"]:
        if f"size {size}" in msg_lower or f"wear {size}" in msg_lower:
            profile["preferred_size"] = size.upper()
    if "$" in user_message or "budget" in msg_lower:
        profile["budget"] = user_message
    if any(w in msg_lower for w in ["prefer", "like", "love", "hate", "avoid"]):
        profile["style_notes"] = profile.get("style_notes", "") + " | " + user_message

    save_memory(session_id, messages[-20:], profile)

    # Match suggested products
    all_products = get_all_products()
    suggested = []
    for pname in response.suggested_products:
        for p in all_products:
            if any(w in p["name"].lower() for w in pname.lower().split()):
                if p not in suggested:
                    suggested.append(p)
                break
    if not suggested:
        suggested = relevant_products[:4]

    # Save outfit if generated
    outfit_id = None
    if response.outfit_name and suggested:
        outfit_id = save_outfit(
            session_id=session_id,
            name=response.outfit_name,
            product_ids=[p["id"] for p in suggested[:4]],
            occasion=response.outfit_occasion or "casual",
            ai_description=response.message,
            total_price=sum(p["price"] for p in suggested[:4])
        )

    # Track event
    track_event(session_id, "chat", data={"message": user_message[:100]})

    return {
        "message": response.message,
        "intent": response.intent,
        "products": suggested,
        "style_tips": response.style_tips,
        "outfit_name": response.outfit_name,
        "outfit_id": outfit_id,
        "session_id": session_id
    }

async def generate_outfit(session_id: str, occasion: str, budget: float):
    all_products = get_all_products()
    affordable = [p for p in all_products if p["price"] <= budget * 0.6]

    products_list = "\n".join([
        f"- {p['name']} (${p['price']}, {p['category']}, colors: {', '.join(p['colors'])})"
        for p in affordable[:20]
    ])

    prompt = f"""
    Create a complete outfit for: {occasion}
    Budget: ${budget}
    Available products:
    {products_list}
    Select 3-5 items that work perfectly together.
    """

    result = await outfit_agent.run(prompt)
    response = result.output

    # Match products
    matched = []
    for item_name in response.items:
        for p in all_products:
            if any(w in p["name"].lower() for w in item_name.lower().split()):
                if p not in matched:
                    matched.append(p)
                break

    outfit_id = save_outfit(
        session_id=session_id,
        name=response.outfit_name,
        product_ids=[p["id"] for p in matched],
        occasion=response.occasion,
        ai_description=response.description,
        total_price=sum(p["price"] for p in matched)
    )

    track_event(session_id, "outfit_generated",
                data={"occasion": occasion, "budget": budget})

    return {
        "outfit_id": outfit_id,
        "outfit_name": response.outfit_name,
        "occasion": response.occasion,
        "description": response.description,
        "styling_tips": response.styling_tips,
        "products": matched,
        "total_price": sum(p["price"] for p in matched)
    }

async def build_style_profile(session_id: str, quiz_answers: dict):
    prompt = f"""
    Build a style profile from these quiz answers:
    - Body type feeling: {quiz_answers.get('body_type', 'not specified')}
    - Typical occasions: {quiz_answers.get('occasions', 'casual')}
    - Favorite colors: {quiz_answers.get('colors', 'neutral')}
    - Style inspiration: {quiz_answers.get('inspiration', 'classic')}
    - Budget range: {quiz_answers.get('budget', '$30-$80')}
    - Sizes: {quiz_answers.get('sizes', 'M')}
    Create a detailed style profile.
    """

    result = await style_agent.run(prompt)
    response = result.output

    profile_data = {
        "body_type": response.body_type,
        "style_keywords": response.style_keywords,
        "preferred_colors": response.recommended_colors,
        "avoided_colors": response.avoided_styles,
        "occasions": response.occasions,
        "budget_min": float(quiz_answers.get("budget_min", 20)),
        "budget_max": float(quiz_answers.get("budget_max", 150)),
        "preferred_sizes": quiz_answers.get("sizes", {}),
    }

    save_style_profile(session_id, profile_data)
    track_event(session_id, "style_profile_created")

    # Get personalized recommendations
    search_query = " ".join(response.style_keywords[:3])
    recommended = search_products(search_query, n_results=6)

    return {
        "profile": profile_data,
        "size_advice": response.size_advice,
        "recommendations": recommended
    }

async def summarize_reviews(product_id: str):
    reviews = get_reviews(product_id)
    if not reviews:
        return None
    reviews_text = "\n".join([
        f"Rating: {r['rating']}/5 — {r['review_text']}"
        for r in reviews[:10]
    ])
    prompt = f"Summarize these product reviews:\n{reviews_text}"
    result = await review_agent.run(prompt)
    return result.output

async def add_to_cart(session_id, product_id, size, color, quantity=1):
    product = get_product_by_id(product_id)
    if not product:
        return {"error": "Product not found"}
    cart = get_cart(session_id)
    items = cart["items"]
    found = False
    for item in items:
        if item["product_id"] == product_id and item["size"] == size:
            item["quantity"] += quantity
            found = True
            break
    if not found:
        items.append({
            "product_id": product_id,
            "product_name": product["name"],
            "size": size,
            "color": color,
            "quantity": quantity,
            "price": product["price"],
            "image_url": product["image_url"]
        })
    total = sum(i["price"] * i["quantity"] for i in items)
    save_cart(session_id, items, total)
    track_event(session_id, "add_to_cart", product_id=product_id)
    return {
        "message": f"{product['name']} added to cart!",
        "cart_total": total,
        "cart_items": len(items)
    }

async def place_order(session_id: str):
    cart = get_cart(session_id)
    if not cart["items"]:
        return {"error": "Cart is empty"}
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    save_order(order_id, session_id, cart["items"], cart["total"])
    save_cart(session_id, [], 0.0)
    track_event(session_id, "order_placed",
                data={"order_id": order_id, "total": cart["total"]})
    return {
        "order_id": order_id,
        "total": cart["total"],
        "status": "confirmed",
        "message": f"Order {order_id} placed successfully!"
    }