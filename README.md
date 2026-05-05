# Clothing-store-agent
What Is This Project?
It's an online clothing store where instead of manually searching and filtering products, customers chat with an AI stylist that understands natural language, remembers preferences, and gives personalized recommendations — all running locally with no API costs.

How It Works — Simple Flow
Customer types: "I need a casual outfit under $50 for a beach trip"
        ↓
AI Agent understands the intent
        ↓
Searches product catalog using semantic search
        ↓
Checks stock, sizes, prices
        ↓
Replies with matching products + styling advice
        ↓
Customer says "add the blue one to cart"
        ↓
Agent remembers context and adds correct item

The 3 Big Parts

Part 1 — The AI Brain (Pydantic AI + Ollama)
This is the heart of the project. Instead of simple keyword search, the AI understands meaning.
Pydantic AI is a Python framework that lets you build AI agents with:

Structured, validated outputs — the AI always returns proper typed data, never random text
Tool calling — the AI can call functions like search, add to cart, check stock
Type safety — every input and output is validated by Pydantic models

Ollama + Llama 3 is the actual AI model running on your machine. It's like having ChatGPT but fully offline and free.
Together they work like this:

Customer sends a message
Pydantic AI sends it to Llama 3 via Ollama
Llama 3 decides which tools to call
Pydantic AI validates the response
Structured result is sent back to the customer


Part 2 — The Product Intelligence (RAG + ChromaDB)
This is how the AI finds relevant products smartly.
RAG (Retrieval Augmented Generation) means the AI searches your actual product database before answering, instead of making things up.
How it works:

Every product description is converted into a vector embedding (a list of numbers that represents meaning) using nomic-embed-text
These embeddings are stored in ChromaDB (a local vector database)
When a customer asks for something, their query is also converted to an embedding
ChromaDB finds products whose embeddings are mathematically closest to the query
Those products are given to the AI to formulate a helpful response

Example:

Customer asks: "something flowy for hot weather"
System finds: linen dresses, chiffon tops, breathable fabrics
Even though the customer never said those exact words


Part 3 — The Memory System
This makes the experience feel personal and continuous.
Within a session (conversation memory):

Stored in SQLite locally
AI remembers what was said earlier in the chat
So customer can say "add the second one" and AI knows what "the second one" means

Across sessions (long-term memory):

Customer profile stored in SQLite
Remembers preferred size, style preferences, past purchases
Next visit: AI already knows "you usually wear medium and prefer minimalist styles"


The Agent Tools
These are functions the AI can call on its own when needed:
ToolWhat It Doessearch_productsSemantic search across catalogget_product_detailsFull info on a specific itemcheck_stockIs size M available right now?get_recommendationsPersonalized picks for this customeradd_to_cartAdd item to shopping cartget_outfit_suggestionsWhat goes well with this top?process_orderFinalize and place the order
The AI decides on its own which tools to call based on the conversation. You don't hardcode the logic.

The Data Models (Pydantic)
Pydantic ensures every piece of data is valid and typed:
Product        → name, price, sizes, colors, stock, description
CustomerProfile → name, size, style preferences, order history  
Order          → items, total, status, delivery address
ChatMessage    → who said what and when
AgentResponse  → AI reply + matched products + detected intent
