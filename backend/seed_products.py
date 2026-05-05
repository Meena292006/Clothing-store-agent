
import sqlite3
import json
from database import init_db, get_connection

products = [
    {
        "id": "prod_001",
        "name": "Floral Summer Dress",
        "category": "dresses",
        "price": 45.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["blue", "pink", "white"],
        "stock": 50,
        "description": "Lightweight floral summer dress perfect for beach trips and casual outings. Made from breathable cotton fabric with a flowy silhouette.",
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400",
        "tags": ["floral", "summer", "beach", "casual", "dress"]
    },
    {
        "id": "prod_002",
        "name": "Denim Shorts",
        "category": "bottoms",
        "price": 29.99,
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["blue", "black", "white"],
        "stock": 75,
        "description": "Classic denim shorts with a relaxed fit. Great for casual summer days, beach walks, and outdoor activities.",
        "image_url": "https://images.unsplash.com/photo-1591195853828-11db59a44f43?w=400",
        "tags": ["denim", "shorts", "casual", "summer"]
    },
    {
        "id": "prod_003",
        "name": "Striped Bikini Set",
        "category": "swimwear",
        "price": 38.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["red", "blue", "black"],
        "stock": 40,
        "description": "Stylish striped bikini set with UV protection. Perfect for beach days and pool parties. Includes top and bottom.",
        "image_url": "https://images.unsplash.com/photo-1570976447640-ac859083963f?w=400",
        "tags": ["bikini", "swimwear", "striped", "beach"]
    },
    {
        "id": "prod_004",
        "name": "Linen Wide Leg Pants",
        "category": "bottoms",
        "price": 49.99,
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["beige", "white", "olive"],
        "stock": 35,
        "description": "Elegant wide leg linen pants ideal for summer evenings and beach dinners. Breathable and comfortable all day long.",
        "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4b4c4e?w=400",
        "tags": ["linen", "pants", "elegant", "summer"]
    },
    {
        "id": "prod_005",
        "name": "Crop Tank Top",
        "category": "tops",
        "price": 19.99,
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["white", "black", "yellow", "pink"],
        "stock": 100,
        "description": "Versatile crop tank top that pairs well with anything. Made from soft cotton blend fabric perfect for hot summer days.",
        "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=400",
        "tags": ["crop", "top", "tank", "basic", "summer"]
    },
    {
        "id": "prod_006",
        "name": "Boho Maxi Skirt",
        "category": "bottoms",
        "price": 42.99,
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["orange", "purple", "green"],
        "stock": 30,
        "description": "Beautiful bohemian maxi skirt with floral print. Flowy and elegant for beach evenings and casual summer outings.",
        "image_url": "https://images.unsplash.com/photo-1583496661160-fb5218ees4b5?w=400",
        "tags": ["boho", "maxi", "skirt", "floral", "summer"]
    },
    {
        "id": "prod_007",
        "name": "Light Cardigan",
        "category": "tops",
        "price": 34.99,
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["beige", "white", "grey"],
        "stock": 45,
        "description": "Soft lightweight cardigan perfect for cool beach evenings. Pairs beautifully with dresses and shorts.",
        "image_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400",
        "tags": ["cardigan", "layering", "light", "evening"]
    },
    {
        "id": "prod_008",
        "name": "Wrap Sundress",
        "category": "dresses",
        "price": 52.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["yellow", "coral", "blue"],
        "stock": 25,
        "description": "Elegant wrap sundress with adjustable fit. Perfect for beach weddings, brunches, and summer parties.",
        "image_url": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400",
        "tags": ["wrap", "sundress", "elegant", "party", "wedding"]
    },
    {
        "id": "prod_009",
        "name": "Oversized Beach Shirt",
        "category": "tops",
        "price": 24.99,
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "colors": ["white", "blue", "pink"],
        "stock": 60,
        "description": "Relaxed oversized beach shirt made from lightweight linen. Great as a swimwear coverup or casual top.",
        "image_url": "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=400",
        "tags": ["oversized", "beach", "shirt", "coverup", "linen"]
    },
    {
        "id": "prod_010",
        "name": "High Waist Bikini Bottom",
        "category": "swimwear",
        "price": 22.99,
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["black", "red", "green"],
        "stock": 55,
        "description": "Flattering high waist bikini bottom with tummy control. Mix and match with any bikini top for a stylish beach look.",
        "image_url": "https://images.unsplash.com/photo-1581338834647-b0fb40704e21?w=400",
        "tags": ["bikini", "high-waist", "swimwear", "mix-match"]
    },
    {
        "id": "prod_011",
        "name": "Straw Sun Hat",
        "category": "accessories",
        "price": 18.99,
        "sizes": ["one-size"],
        "colors": ["beige", "brown"],
        "stock": 80,
        "description": "Classic straw sun hat with wide brim for UV protection. The perfect beach accessory for any summer outfit.",
        "image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "tags": ["hat", "straw", "sun-protection", "accessory", "beach"]
    },
    {
        "id": "prod_012",
        "name": "Strappy Sandals",
        "category": "footwear",
        "price": 36.99,
        "sizes": ["36", "37", "38", "39", "40", "41"],
        "colors": ["tan", "white", "black"],
        "stock": 40,
        "description": "Elegant strappy sandals with cushioned sole. Perfect for beach walks, dinners, and summer events.",
        "image_url": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400",
        "tags": ["sandals", "strappy", "footwear", "elegant", "summer"]
    },
    {
        "id": "prod_013",
        "name": "Flowy Palazzo Pants",
        "category": "bottoms",
        "price": 44.99,
        "sizes": ["S", "M", "L", "XL"],
        "colors": ["white", "navy", "coral"],
        "stock": 30,
        "description": "Ultra flowy palazzo pants in lightweight fabric. Comfortable and stylish for beach resorts and summer travel.",
        "image_url": "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400",
        "tags": ["palazzo", "pants", "flowy", "resort", "travel"]
    },
    {
        "id": "prod_014",
        "name": "Tube Top",
        "category": "tops",
        "price": 16.99,
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["black", "white", "red", "blue"],
        "stock": 90,
        "description": "Simple and chic tube top that goes with everything. Great for layering or wearing on its own on hot days.",
        "image_url": "https://images.unsplash.com/photo-1485462537746-965f33f7f6a7?w=400",
        "tags": ["tube", "top", "chic", "basic", "layering"]
    },
    {
        "id": "prod_015",
        "name": "Beach Tote Bag",
        "category": "accessories",
        "price": 27.99,
        "sizes": ["one-size"],
        "colors": ["beige", "blue", "pink"],
        "stock": 50,
        "description": "Spacious beach tote bag made from durable canvas. Fits towels, sunscreen, and all your beach essentials.",
        "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=400",
        "tags": ["tote", "bag", "beach", "canvas", "accessory"]
    }
]

def seed_products():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    for product in products:
        cursor.execute('''
            INSERT OR REPLACE INTO products
            (id, name, category, price, sizes, colors, stock, description, image_url, tags, rating, review_count, trending)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product["id"], product["name"], product["category"],
            product["price"], json.dumps(product["sizes"]),
            json.dumps(product["colors"]), product["stock"],
            product["description"], product["image_url"],
            json.dumps(product.get("tags", [])),
            product.get("rating", 4.0),
            product.get("review_count", 10),
            product.get("trending", 0)
        ))
    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(products)} products!")

if __name__ == "__main__":
    seed_products()