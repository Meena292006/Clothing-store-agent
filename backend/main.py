from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import (
    init_db, get_all_products, get_product_by_id,
    get_cart, get_order, get_orders_by_session,
    get_style_profile, get_wishlist,
    add_to_wishlist, remove_from_wishlist,
    get_outfits, add_review, get_reviews,
    get_trending_products, get_products_by_category,
    track_event
)
from vector_store import build_vector_store
from agent import (
    chat_with_agent, add_to_cart, place_order,
    generate_outfit, build_style_profile,
    summarize_reviews
)
from seed_products import seed_products
import uuid

app = FastAPI(title="AI Clothing Store — Production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Request Models ──────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class CartRequest(BaseModel):
    session_id: str
    product_id: str
    size: str
    color: str
    quantity: int = 1

class OutfitRequest(BaseModel):
    session_id: str
    occasion: str
    budget: float

class StyleQuizRequest(BaseModel):
    session_id: str
    body_type: str
    occasions: str
    colors: str
    inspiration: str
    budget_min: float
    budget_max: float
    sizes: dict

class WishlistRequest(BaseModel):
    session_id: str
    product_id: str
    ai_note: Optional[str] = ""

class ReviewRequest(BaseModel):
    session_id: str
    product_id: str
    rating: int
    review_text: str

# ── Startup ──────────────────────────────
@app.on_event("startup")
async def startup():
    print("Starting AI Clothing Store...")
    init_db()
    seed_products()
    build_vector_store()
    print("Ready!")

# ── Core Routes ──────────────────────────────
@app.get("/")
async def root():
    return {"message": "AI Clothing Store API", "version": "2.0"}

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        response = await chat_with_agent(session_id, request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Product Routes ──────────────────────────────
@app.get("/products")
async def get_products(category: Optional[str] = None):
    if category:
        return get_products_by_category(category)
    return get_all_products()

@app.get("/products/trending")
async def trending():
    return get_trending_products()

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    track_event(None, "product_view", product_id=product_id)
    return product

# ── Cart Routes ──────────────────────────────
@app.post("/cart/add")
async def add_item(request: CartRequest):
    return await add_to_cart(
        request.session_id, request.product_id,
        request.size, request.color, request.quantity
    )

@app.get("/cart/{session_id}")
async def view_cart(session_id: str):
    return get_cart(session_id)

# ── Order Routes ──────────────────────────────
@app.post("/order/{session_id}")
async def create_order(session_id: str):
    return await place_order(session_id)

@app.get("/order/{order_id}")
async def get_order_detail(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/orders/history/{session_id}")
async def order_history(session_id: str):
    return get_orders_by_session(session_id)

# ── Outfit Routes ──────────────────────────────
@app.post("/outfit/generate")
async def generate_outfit_route(request: OutfitRequest):
    try:
        return await generate_outfit(
            request.session_id,
            request.occasion,
            request.budget
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/outfit/saved/{session_id}")
async def get_saved_outfits(session_id: str):
    return get_outfits(session_id)

# ── Style Profile Routes ──────────────────────────────
@app.post("/style/quiz")
async def style_quiz(request: StyleQuizRequest):
    try:
        return await build_style_profile(request.session_id, {
            "body_type": request.body_type,
            "occasions": request.occasions,
            "colors": request.colors,
            "inspiration": request.inspiration,
            "budget_min": request.budget_min,
            "budget_max": request.budget_max,
            "sizes": request.sizes
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/style/profile/{session_id}")
async def get_profile(session_id: str):
    profile = get_style_profile(session_id)
    if not profile:
        return {"message": "No profile yet"}
    return profile

# ── Wishlist Routes ──────────────────────────────
@app.post("/wishlist/add")
async def wishlist_add(request: WishlistRequest):
    add_to_wishlist(
        request.session_id,
        request.product_id,
        request.ai_note
    )
    return {"message": "Added to wishlist!"}

@app.get("/wishlist/{session_id}")
async def get_wishlist_route(session_id: str):
    return get_wishlist(session_id)

@app.delete("/wishlist/{wishlist_id}")
async def remove_wishlist(wishlist_id: str):
    remove_from_wishlist(wishlist_id)
    return {"message": "Removed from wishlist"}

# ── Review Routes ──────────────────────────────
@app.post("/review")
async def post_review(request: ReviewRequest):
    summary = await summarize_reviews(request.product_id)
    ai_summary = summary.summary if summary else ""
    add_review(
        request.product_id, request.session_id,
        request.rating, request.review_text, ai_summary
    )
    return {"message": "Review added!", "ai_summary": ai_summary}

@app.get("/reviews/{product_id}")
async def product_reviews(product_id: str):
    reviews = get_reviews(product_id)
    summary = await summarize_reviews(product_id)
    return {
        "reviews": reviews,
        "summary": summary.dict() if summary else None
    }