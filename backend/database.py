import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "clothing_store.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            sizes TEXT NOT NULL,
            colors TEXT NOT NULL,
            stock INTEGER NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL,
            tags TEXT DEFAULT "[]",
            rating REAL DEFAULT 0.0,
            review_count INTEGER DEFAULT 0,
            trending INTEGER DEFAULT 0
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT "confirmed",
            created_at TEXT NOT NULL,
            estimated_delivery TEXT,
            tracking_steps TEXT DEFAULT "[]"
        )
    ''')

    # Cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            session_id TEXT PRIMARY KEY,
            items TEXT NOT NULL DEFAULT "[]",
            total REAL DEFAULT 0.0
        )
    ''')

    # Memory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            session_id TEXT PRIMARY KEY,
            messages TEXT NOT NULL DEFAULT "[]",
            profile TEXT NOT NULL DEFAULT "{}"
        )
    ''')

    # Style profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS style_profiles (
            session_id TEXT PRIMARY KEY,
            body_type TEXT,
            height TEXT,
            weight TEXT,
            preferred_colors TEXT DEFAULT "[]",
            avoided_colors TEXT DEFAULT "[]",
            occasions TEXT DEFAULT "[]",
            style_keywords TEXT DEFAULT "[]",
            budget_min REAL DEFAULT 0,
            budget_max REAL DEFAULT 200,
            preferred_sizes TEXT DEFAULT "{}",
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # Wishlists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishlists (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            ai_note TEXT,
            added_at TEXT NOT NULL
        )
    ''')

    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            review_text TEXT,
            ai_summary TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    # Outfit combinations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outfit_combos (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            name TEXT NOT NULL,
            product_ids TEXT NOT NULL,
            occasion TEXT,
            ai_description TEXT,
            total_price REAL,
            created_at TEXT NOT NULL
        )
    ''')

    # Analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            event_type TEXT NOT NULL,
            product_id TEXT,
            data TEXT DEFAULT "{}",
            created_at TEXT NOT NULL
        )
    ''')

    # ── Migrations: add missing columns to existing tables ──
    migrations = [
        "ALTER TABLE products ADD COLUMN tags TEXT DEFAULT '[]'",
        "ALTER TABLE products ADD COLUMN rating REAL DEFAULT 0.0",
        "ALTER TABLE products ADD COLUMN review_count INTEGER DEFAULT 0",
        "ALTER TABLE products ADD COLUMN trending INTEGER DEFAULT 0",
    ]
    for sql in migrations:
        try:
            cursor.execute(sql)
        except Exception:
            pass  # column already exists — safe to ignore

    conn.commit()
    conn.close()
    print("Database initialized successfully")

# ── Product functions ──────────────────────────────
def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    return [_parse_product(row) for row in rows]

def get_product_by_id(product_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return _parse_product(row) if row else None

def get_trending_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE trending=1 ORDER BY rating DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_parse_product(row) for row in rows]

def get_products_by_category(category: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE category=?", (category,))
    rows = cursor.fetchall()
    conn.close()
    return [_parse_product(row) for row in rows]

def _parse_product(row):
    if not row:
        return None
    
    # Safely convert sqlite3.Row to dict to check keys
    row_dict = dict(row)
    
    return {
        "id": row_dict.get("id"),
        "name": row_dict.get("name"),
        "category": row_dict.get("category"),
        "price": row_dict.get("price"),
        "sizes": json.loads(row_dict.get("sizes", "[]")),
        "colors": json.loads(row_dict.get("colors", "[]")),
        "stock": row_dict.get("stock", 0),
        "description": row_dict.get("description", ""),
        "image_url": row_dict.get("image_url", ""),
        "tags": json.loads(row_dict.get("tags", "[]")) if row_dict.get("tags") else [],
        "rating": row_dict.get("rating", 0.0),
        "review_count": row_dict.get("review_count", 0),
        "trending": bool(row_dict.get("trending", 0))
    }

# ── Cart functions ──────────────────────────────
def get_cart(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM carts WHERE session_id=?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "session_id": row["session_id"],
            "items": json.loads(row["items"]),
            "total": row["total"]
        }
    return {"session_id": session_id, "items": [], "total": 0.0}

def save_cart(session_id: str, items: list, total: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO carts (session_id, items, total) VALUES (?, ?, ?)',
        (session_id, json.dumps(items), total)
    )
    conn.commit()
    conn.close()

# ── Memory functions ──────────────────────────────
def get_memory(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory WHERE session_id=?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "messages": json.loads(row["messages"]),
            "profile": json.loads(row["profile"])
        }
    return {"messages": [], "profile": {}}

def save_memory(session_id: str, messages: list, profile: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO memory (session_id, messages, profile) VALUES (?, ?, ?)',
        (session_id, json.dumps(messages), json.dumps(profile))
    )
    conn.commit()
    conn.close()

# ── Order functions ──────────────────────────────
def save_order(order_id, session_id, items, total):
    conn = get_connection()
    cursor = conn.cursor()
    from datetime import datetime, timedelta
    now = datetime.now()
    delivery = (now + timedelta(days=5)).strftime("%B %d, %Y")
    tracking_steps = json.dumps([
        {"step": "Order Confirmed", "done": True, "time": now.strftime("%I:%M %p")},
        {"step": "Processing", "done": False, "time": ""},
        {"step": "Shipped", "done": False, "time": ""},
        {"step": "Out for Delivery", "done": False, "time": ""},
        {"step": "Delivered", "done": False, "time": ""}
    ])
    cursor.execute('''
        INSERT INTO orders
        (id, session_id, items, total, status, created_at, estimated_delivery, tracking_steps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_id, session_id, json.dumps(items),
        total, "confirmed", now.isoformat(),
        delivery, tracking_steps
    ))
    conn.commit()
    conn.close()

def get_order(order_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "items": json.loads(row["items"]),
            "total": row["total"],
            "status": row["status"],
            "created_at": row["created_at"],
            "estimated_delivery": row["estimated_delivery"],
            "tracking_steps": json.loads(row["tracking_steps"])
        }
    return None

def get_orders_by_session(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE session_id=? ORDER BY created_at DESC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r["id"], "total": r["total"],
        "status": r["status"], "created_at": r["created_at"],
        "estimated_delivery": r["estimated_delivery"],
        "items": json.loads(r["items"]),
        "tracking_steps": json.loads(r["tracking_steps"])
    } for r in rows]

# ── Style Profile functions ──────────────────────────────
def get_style_profile(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM style_profiles WHERE session_id=?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "session_id": row["session_id"],
            "body_type": row["body_type"],
            "height": row["height"],
            "preferred_colors": json.loads(row["preferred_colors"]),
            "avoided_colors": json.loads(row["avoided_colors"]),
            "occasions": json.loads(row["occasions"]),
            "style_keywords": json.loads(row["style_keywords"]),
            "budget_min": row["budget_min"],
            "budget_max": row["budget_max"],
            "preferred_sizes": json.loads(row["preferred_sizes"]),
            "updated_at": row["updated_at"]
        }
    return None

def save_style_profile(session_id: str, profile: dict):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO style_profiles
        (session_id, body_type, height, preferred_colors, avoided_colors,
         occasions, style_keywords, budget_min, budget_max,
         preferred_sizes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        profile.get("body_type", ""),
        profile.get("height", ""),
        json.dumps(profile.get("preferred_colors", [])),
        json.dumps(profile.get("avoided_colors", [])),
        json.dumps(profile.get("occasions", [])),
        json.dumps(profile.get("style_keywords", [])),
        profile.get("budget_min", 0),
        profile.get("budget_max", 200),
        json.dumps(profile.get("preferred_sizes", {})),
        now, now
    ))
    conn.commit()
    conn.close()

# ── Wishlist functions ──────────────────────────────
def add_to_wishlist(session_id: str, product_id: str, ai_note: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    import uuid
    wid = str(uuid.uuid4())
    cursor.execute('''
        INSERT OR REPLACE INTO wishlists (id, session_id, product_id, ai_note, added_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (wid, session_id, product_id, ai_note, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_wishlist(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM wishlists WHERE session_id=? ORDER BY added_at DESC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    items = []
    for row in rows:
        product = get_product_by_id(row["product_id"])
        if product:
            product["ai_note"] = row["ai_note"]
            product["wishlist_id"] = row["id"]
            items.append(product)
    return items

def remove_from_wishlist(wishlist_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlists WHERE id=?", (wishlist_id,))
    conn.commit()
    conn.close()

# ── Review functions ──────────────────────────────
def add_review(product_id, session_id, rating, review_text, ai_summary=""):
    conn = get_connection()
    cursor = conn.cursor()
    import uuid
    rid = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO reviews
        (id, product_id, session_id, rating, review_text, ai_summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (rid, product_id, session_id, rating, review_text,
          ai_summary, datetime.now().isoformat()))
    cursor.execute('''
        UPDATE products SET
        rating = (SELECT AVG(rating) FROM reviews WHERE product_id=?),
        review_count = (SELECT COUNT(*) FROM reviews WHERE product_id=?)
        WHERE id=?
    ''', (product_id, product_id, product_id))
    conn.commit()
    conn.close()

def get_reviews(product_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reviews WHERE product_id=? ORDER BY created_at DESC",
        (product_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r["id"], "rating": r["rating"],
        "review_text": r["review_text"],
        "ai_summary": r["ai_summary"],
        "created_at": r["created_at"]
    } for r in rows]

# ── Outfit functions ──────────────────────────────
def save_outfit(session_id, name, product_ids, occasion, ai_description, total_price):
    conn = get_connection()
    cursor = conn.cursor()
    import uuid
    oid = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO outfit_combos
        (id, session_id, name, product_ids, occasion, ai_description, total_price, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        oid, session_id, name,
        json.dumps(product_ids), occasion,
        ai_description, total_price,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    return oid

def get_outfits(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM outfit_combos WHERE session_id=? ORDER BY created_at DESC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    outfits = []
    for row in rows:
        pids = json.loads(row["product_ids"])
        products = [get_product_by_id(pid) for pid in pids if get_product_by_id(pid)]
        outfits.append({
            "id": row["id"],
            "name": row["name"],
            "occasion": row["occasion"],
            "ai_description": row["ai_description"],
            "total_price": row["total_price"],
            "products": products,
            "created_at": row["created_at"]
        })
    return outfits

# ── Analytics functions ──────────────────────────────
def track_event(session_id, event_type, product_id=None, data={}):
    conn = get_connection()
    cursor = conn.cursor()
    import uuid
    cursor.execute('''
        INSERT INTO analytics (id, session_id, event_type, product_id, data, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        str(uuid.uuid4()), session_id, event_type,
        product_id, json.dumps(data),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()