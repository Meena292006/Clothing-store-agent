
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Product Model
class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float
    sizes: list[str]
    colors: list[str]
    stock: int
    description: str
    image_url: str
    tags: list[str] = []
    rating: float = 0.0
    review_count: int = 0
    trending: bool = False

# Cart Item Model
class CartItem(BaseModel):
    product_id: str
    product_name: str
    size: str
    color: str
    quantity: int
    price: float

# Cart Model
class Cart(BaseModel):
    session_id: str
    items: list[CartItem] = []
    total: float = 0.0

# Order Model
class Order(BaseModel):
    id: str
    session_id: str
    items: list[CartItem]
    total: float
    status: str = "pending"
    created_at: str = datetime.now().isoformat()

# Customer Profile Model
class CustomerProfile(BaseModel):
    session_id: str
    name: Optional[str] = None
    preferred_size: Optional[str] = None
    style_preferences: list[str] = []
    budget_range: Optional[str] = None
    past_orders: list[str] = []

# Chat Message Model
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str = datetime.now().isoformat()

# Agent Response Model
class AgentResponse(BaseModel):
    message: str
    products: list[Product] = []
    intent: str = "general"

# Search Filter Model
class SearchFilter(BaseModel):
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    size: Optional[str] = None
    color: Optional[str] = None