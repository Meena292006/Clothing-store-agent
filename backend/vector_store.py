import chromadb
import os
import json
from chromadb.utils import embedding_functions
from database import get_all_products

# Local Ollama embeddings
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text"
)

client = chromadb.Client()

# Two separate collections
# 1. Products — for product search
product_collection = client.get_or_create_collection(
    name="clothing_products",
    embedding_function=ollama_ef
)

# 2. Knowledge base — for RAG
knowledge_collection = client.get_or_create_collection(
    name="knowledge_base",
    embedding_function=ollama_ef
)

# ── Knowledge Base Documents ──────────────────────────────
KNOWLEDGE_DOCS = {
    "style_guide": """
    STYLE GUIDE — Complete Fashion Rules

    Color Coordination Rules:
    Neutral colors like white, black, beige and grey go with everything.
    Complementary colors sit opposite each other on the color wheel and create vibrant looks.
    Analogous colors sit next to each other and create harmonious outfits.
    The 60-30-10 rule: 60% dominant color, 30% secondary, 10% accent.
    Avoid matching exact same colors head to toe — it looks flat.
    Navy and white is a timeless classic combination.
    Black and white always works for any occasion.
    Earth tones like brown, rust, olive pair beautifully together.

    Body Type Dressing:
    Hourglass figures: wrap dresses, belted styles, fitted tops highlight curves.
    Pear shapes: A-line skirts, wide leg pants, statement tops draw attention upward.
    Apple shapes: empire waistlines, flowy fabrics, V-necks elongate the torso.
    Rectangle shapes: ruffles, peplums, crop tops with high waist create curves.
    Petite frames: vertical stripes, monochrome outfits, high waists create length.
    Tall frames: bold prints, horizontal stripes, wide leg pants all work beautifully.

    Proportion Rules:
    If wearing loose top, wear fitted bottom and vice versa.
    Crop tops pair best with high waist bottoms.
    Oversized pieces need one fitted piece to balance.
    Maxi skirts work with tucked in tops to avoid looking swamped.

    Occasion Dressing:
    Beach: lightweight fabrics, bright colors, cover-ups over swimwear.
    Wedding guest: avoid white, ivory and black. Opt for jewel tones or pastels.
    Casual brunch: smart casual, linen, cotton, comfortable yet polished.
    Date night: fitted silhouettes, rich colors, elegant fabrics like satin or silk.
    Work casual: clean lines, neutral palettes, minimal accessories.
    """,

    "size_guide": """
    SIZE GUIDE — How to Find Your Perfect Fit

    How to Take Your Measurements:
    Bust: Measure around the fullest part of your chest, keeping tape parallel to ground.
    Waist: Measure around the narrowest part of your waist, usually 1 inch above belly button.
    Hips: Measure around the fullest part of your hips, usually 7-9 inches below waist.
    Inseam: Measure from crotch to ankle for pants length.

    Size Chart:
    XS: Bust 30-32 inches, Waist 22-24 inches, Hips 32-34 inches
    S: Bust 32-34 inches, Waist 24-26 inches, Hips 34-36 inches
    M: Bust 34-36 inches, Waist 26-28 inches, Hips 36-38 inches
    L: Bust 36-38 inches, Waist 28-30 inches, Hips 38-40 inches
    XL: Bust 38-40 inches, Waist 30-32 inches, Hips 40-42 inches
    XXL: Bust 40-42 inches, Waist 32-34 inches, Hips 42-44 inches

    Fit Tips:
    Always size up if between sizes for comfort.
    Dresses: measure bust and hips, use larger measurement to select size.
    Pants: measure waist and hips, use hips for size selection.
    Tops: measure bust for best fit.
    Swimwear: measure bust, waist and hips. Tops and bottoms can be mixed in different sizes.
    Wrap styles are very forgiving and fit multiple sizes.
    Linen and cotton fabrics shrink slightly, consider sizing up.
    Stretch fabrics like jersey fit true to size or you can size down.

    When to Size Up:
    If you are between sizes always size up for comfort.
    For fitted dresses size up if bust is larger than chart.
    For active or beach wear, true to size is usually best.
    """,

    "fabric_guide": """
    FABRIC GUIDE — Understanding Clothing Materials

    Cotton:
    Soft, breathable, and durable natural fabric.
    Perfect for everyday wear and hot climates.
    Easy to wash and maintain.
    May shrink slightly in first wash — wash in cold water.
    Best for: casual tops, dresses, basics, beachwear coverups.

    Linen:
    Made from flax plant, extremely breathable and lightweight.
    Gets softer with every wash.
    Wrinkles easily but this is part of its natural charm.
    Perfect for hot weather, beach, and resort wear.
    Best for: summer dresses, palazzo pants, shirts, beach outfits.

    Chiffon:
    Lightweight, sheer, and floaty synthetic or silk fabric.
    Creates beautiful drape and movement.
    Delicate — hand wash or dry clean only.
    Best for: evening wear, flowy dresses, layering pieces.

    Jersey:
    Stretchy, soft knit fabric that moves with your body.
    Very comfortable and wrinkle resistant.
    Easy to care for — machine washable.
    Best for: casual dresses, tops, activewear.

    Denim:
    Durable cotton twill fabric.
    Gets better with age and wear.
    Machine washable — wash inside out to preserve color.
    Best for: shorts, jackets, casual everyday wear.

    Mesh:
    Open weave fabric with UV protection properties.
    Breathable and quick drying.
    Perfect for beach and activewear.
    Best for: swimwear coverups, beach tops, activewear.

    Care Instructions:
    Always check the label before washing.
    Cold water preserves color and prevents shrinking.
    Hang dry delicate fabrics instead of using dryer.
    Iron linen and cotton when slightly damp for best results.
    Store swimwear flat or rolled, never folded with creases.
    """,

    "occasion_guide": """
    OCCASION STYLE GUIDE — What to Wear Where

    Beach Day:
    Must have: swimsuit or bikini as base layer.
    Layer with: lightweight coverup, linen shirt, or oversized tee.
    Bottoms: denim shorts, linen shorts, or beach pants.
    Footwear: sandals, flip flops, or espadrilles.
    Accessories: sun hat, sunglasses, beach tote bag.
    Colors: brights, tropical prints, classic navy and white.
    Fabrics: linen, cotton, mesh, quick-dry materials.
    Budget tip: invest in a quality swimsuit, keep coverups simple.

    Beach Wedding:
    Avoid white and ivory — leave those for the bride.
    Opt for: floral midi dresses, elegant maxi dresses, chic jumpsuits.
    Colors: coral, sage, dusty rose, sky blue, champagne.
    Fabrics: chiffon, linen, light satin, jersey.
    Footwear: strappy heeled sandals, elegant flat sandals.
    Avoid: heavy fabrics, dark colors, overly casual pieces.
    Budget: $45-80 for the dress, $30-50 for sandals.

    Casual Brunch:
    Smart casual is the code — elevated but comfortable.
    Options: sundresses, linen sets, crop top with wide leg pants.
    Colors: pastels, neutrals, soft prints.
    Footwear: sandals, mules, clean sneakers.
    Budget: full outfit under $70.

    Date Night:
    Aim for: polished, confident, and slightly elevated.
    Options: wrap dress, fitted midi dress, chic two-piece set.
    Colors: deep red, cobalt blue, emerald green, classic black.
    Fabrics: satin, jersey, chiffon for movement.
    Footwear: heeled sandals, block heels, strappy flats.
    Accessories: minimal jewelry, small bag.
    Budget: $50-100 for dress, $30-60 for shoes.

    Summer Party:
    Fun, festive, and comfortable to dance in.
    Options: mini dress, printed maxi, crop top with skirt.
    Colors: bold and bright — yellow, orange, hot pink.
    Fabrics: breathable cotton, jersey, chiffon.
    Budget: $35-70 for complete look.

    Everyday Casual:
    Comfort is key but still put together.
    Options: jeans with nice top, casual dress, shorts set.
    Colors: whatever you love — no rules for casual.
    Budget: $20-50 per item.
    """,

    "trend_report": """
    CURRENT FASHION TRENDS 2025-2026

    Color Trends:
    Butter yellow is the color of the season — warm, soft, universally flattering.
    Cobalt blue making a strong comeback — bold and confident.
    Earthy terracotta and rust tones continuing to dominate.
    Sage green for its calming, natural appeal.
    Cream and off-white replacing pure white for a softer look.

    Silhouette Trends:
    Oversized everything — blazers, shirts, trousers.
    But also: fitted and body-con for evenings.
    Asymmetric hemlines on dresses and skirts.
    Wide leg and palazzo pants at peak popularity.
    Maxi skirts making a massive comeback.
    Cutout details on dresses and tops.

    Fabric Trends:
    Linen is dominating summer — sustainable and breathable.
    Satin finishes for elevated casual looks.
    Sheer and semi-transparent layers.
    Textured fabrics — crochet, broderie anglaise, eyelet.

    Style Trends:
    Coastal grandmother aesthetic — linen, neutrals, relaxed elegance.
    Barbiecore influence — pinks, playful and unapologetically feminine.
    Quiet luxury — understated, high quality, minimal branding.
    Boho revival — flowy fabrics, earthy tones, natural textures.
    Y2K influence — low waist, butterfly prints, denim.

    Shopping Trends:
    Investment pieces over fast fashion.
    Mixing high and low price points.
    Capsule wardrobe building.
    Sustainable and natural fabrics preferred.
    Versatile pieces that work multiple ways.
    """,

    "return_policy": """
    STORE POLICIES — Returns, Exchanges and Customer Care

    Return Policy:
    Items can be returned within 30 days of delivery.
    Items must be unworn, unwashed, with original tags attached.
    Swimwear can only be returned if hygiene liner is intact.
    Sale items are final sale and cannot be returned.
    To initiate a return, contact customer support with order ID.

    Exchange Policy:
    Size exchanges are free within 14 days.
    Color exchanges subject to availability.
    Exchange shipping is covered by the store for first exchange.

    Refund Policy:
    Refunds processed within 5-7 business days.
    Refunds issued to original payment method.
    Shipping fees are non-refundable unless item was defective.

    Damaged or Defective Items:
    Contact support within 48 hours of receiving damaged item.
    Photo evidence required for damage claims.
    Full refund or replacement provided for defective items.

    Shipping Policy:
    Standard shipping: 5-7 business days.
    Express shipping: 2-3 business days.
    Free standard shipping on orders over $50.
    International shipping available to selected countries.

    Customer Support:
    Email: support@bellafashion.com
    Response time: within 24 hours.
    Live chat available Monday to Friday 9am-6pm.
    """
}

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    """Split text into overlapping chunks for better retrieval"""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def build_knowledge_base():
    """Chunk all knowledge docs and store in ChromaDB"""
    print("Building RAG knowledge base...")
    all_chunks = []
    all_ids = []
    all_metadatas = []

    for doc_name, content in KNOWLEDGE_DOCS.items():
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_name}_chunk_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "source": doc_name,
                "chunk_index": i,
                "doc_type": "knowledge"
            })

    # Add to ChromaDB
    if all_chunks:
        knowledge_collection.add(
            documents=all_chunks,
            metadatas=all_metadatas,
            ids=all_ids
        )
    print(f"Knowledge base built: {len(all_chunks)} chunks from {len(KNOWLEDGE_DOCS)} documents")

def build_product_index():
    """Index all products for semantic search"""
    from database import get_all_products
    products = get_all_products()
    documents = []
    metadatas = []
    ids = []

    for p in products:
        doc = (
            f"Product: {p['name']}. "
            f"Category: {p['category']}. "
            f"Description: {p['description']} "
            f"Colors available: {', '.join(p['colors'])}. "
            f"Sizes: {', '.join(p['sizes'])}. "
            f"Price: ${p['price']}. "
            f"Tags: {', '.join(p.get('tags', []))}."
        )
        documents.append(doc)
        metadatas.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"]
        })
        ids.append(p["id"])

    if documents:
        product_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    print(f"Product index built: {len(products)} products indexed")

def build_vector_store():
    """Build both product index and knowledge base"""
    build_product_index()
    build_knowledge_base()

def search_products(query: str, n_results: int = 4):
    """Semantic search over product catalog"""
    results = product_collection.query(
        query_texts=[query],
        n_results=min(n_results, product_collection.count() or 1)
    )
    if not results["metadatas"][0]:
        return []
    product_ids = [m["id"] for m in results["metadatas"][0]]
    from database import get_product_by_id
    products = []
    for pid in product_ids:
        p = get_product_by_id(pid)
        if p:
            products.append(p)
    return products

def retrieve_knowledge(query: str, n_results: int = 3):
    """
    TRUE RAG — Retrieve relevant knowledge chunks for a query
    Returns chunks with source attribution
    """
    if knowledge_collection.count() == 0:
        return []

    results = knowledge_collection.query(
        query_texts=[query],
        n_results=min(n_results, knowledge_collection.count())
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i] if "distances" in results else 0
        chunks.append({
            "content": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "relevance_score": round(1 - distance, 3)
        })

    return chunks