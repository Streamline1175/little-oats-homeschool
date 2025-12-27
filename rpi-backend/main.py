from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import httpx
from dotenv import load_dotenv
import time
import sys
import hmac
import hashlib
import json

# Load environment variables from .env file
load_dotenv()

# Optional ngrok auto-start support via pyngrok. When running under uvicorn/systemd,
# the __main__ block is not executed, so we start ngrok in FastAPI startup event.
try:
    from pyngrok import ngrok
except Exception:
    ngrok = None

app = FastAPI()

# Allow interactions from the desktop app (which might be localhost or another IP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup/shutdown events to manage pyngrok tunnel when running under uvicorn/systemd.
@app.on_event("startup")
async def _startup_ngrok():
    if not ngrok:
        print("⚠️ 'pyngrok' not available. Skipping ngrok startup.")
        return
    domain = os.getenv("NGROK_DOMAIN")

    # If there are already tunnels, prefer reusing a matching one
    try:
        existing = ngrok.get_tunnels()
        if existing:
            # if domain is set, try to find a tunnel for it
            if domain:
                match = next((t for t in existing if domain in t.public_url), None)
                if match:
                    app.state.ngrok_tunnel = match
                    print(f"🔁 Reusing existing ngrok tunnel: {match.public_url}")
                    return
            # otherwise just reuse the first
            app.state.ngrok_tunnel = existing[0]
            print(f"🔁 Reusing existing ngrok tunnel: {existing[0].public_url}")
            return
    except Exception:
        # Non-fatal — proceed to try to create a tunnel
        pass

    try:
        print(f"🔗 Starting ngrok tunnel (domain={domain})...")
        tunnel = ngrok.connect(8000, domain=domain) if domain else ngrok.connect(8000)
        app.state.ngrok_tunnel = tunnel
        print(f"🚀 Ngrok Tunnel Live at: {tunnel.public_url}")
    except Exception as e:
        # If the tunnel creation failed, attempt to read existing tunnels again
        err_str = str(e)
        print(f"⚠️ Could not auto-start ngrok: {err_str}")

        # Common cause: an endpoint for the requested domain is already online.
        if "already online" in err_str.lower() or "err_ngrok_334" in err_str.lower():
            print("⚠️ A tunnel for that address is already online. Stop the existing endpoint or start both endpoints with '--pooling-enabled' to load balance between them.")

        try:
            existing = ngrok.get_tunnels()
            if existing:
                # show what existing tunnels we found
                for t in existing:
                    print(f"🔁 Found existing tunnel: {t.public_url} (proto={t.proto})")
                app.state.ngrok_tunnel = existing[0]
                print(f"🔁 Using existing ngrok tunnel after error: {existing[0].public_url}")
                return
        except Exception as e2:
            print(f"⚠️ Error listing existing tunnels: {e2}")

        print("⚠️ Ngrok unavailable — continuing without a public tunnel.")

@app.on_event("shutdown")
async def _shutdown_ngrok():
    tunnel = getattr(app.state, "ngrok_tunnel", None)
    if tunnel:
        try:
            ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
            print("🔗 Ngrok tunnel stopped.")
        except Exception as e:
            print(f"⚠️ Error stopping ngrok: {e}")

# ==================== MODELS ====================

class Product(BaseModel):
    id: str
    title: str
    description: str
    price: str
    image: Optional[str] = None
    category: str
    purchased: bool = False
    contentPath: Optional[str] = None
    buyUrl: Optional[str] = None

# Mock Data (matches desktop app)
products_db = [
    {
        "id": "prod_123_math_g1",
        "title": "Grade 1 Math Mastery Bundle",
        "description": "Complete curriculum for Grade 1 Math. Includes 50+ worksheets, interactive quizzes, and progress tracking.",
        "price": "$29.00",
        "category": "math",
        "purchased": False,
        "contentPath": "bundles/math-grade-1.zip"
    },
    {
        "id": "prod_456_read_g1",
        "title": "Early Readers Phonics Pack",
        "description": "Comprehensive phonics and reading comprehension worksheets for beginners.",
        "price": "$24.00",
        "category": "reading",
        "purchased": False,
        "contentPath": "bundles/reading-grade-1.zip"
    },
    {
        "id": "prod_789_full_g1",
        "title": "Complete Grade 1 Curriculum",
        "description": "Get everything! Math, Reading, Writing, and Science for Grade 1. Best value.",
        "price": "$79.00",
        "category": "bundle",
        "purchased": False,
        "contentPath": "bundles/grade-1-complete.zip"
    }
]

# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {"status": "online", "service": "Little Oat API"}

@app.get("/api/products", response_model=List[Product])
async def get_products():
    api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
    store_id = os.getenv("LEMON_SQUEEZY_STORE_ID")
    
    # If no credentials, return mock data
    if not api_key or not store_id:
        print("ℹ️ No Lemon Squeezy credentials found (env vars). Returning mock inventory.")
        return products_db

    # Fetch from Lemon Squeezy
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.lemonsqueezy.com/v1/products?filter[store_id]={store_id}",
                headers=headers
            )
            if response.status_code != 200:
                print(f"⚠️ Lemon Squeezy Error {response.status_code}: {response.text}")
                return products_db # Fallback

            data = response.json()
            print(data)
            live_products = []
            
            for item in data.get("data", []):
                attr = item.get("attributes", {})
                
                # Get product name
                product_name = attr.get("name", "")
                name_lower = product_name.lower()
                
                # Skip internal/system products (Cart Bundle, etc.)
                # These are used by the backend but should never be shown to customers
                if any(keyword in name_lower for keyword in ["cart bundle", "custom order", "internal", "system"]):
                    print(f"⏭️  Skipping internal product: {product_name}")
                    continue
                
                # Determine category from name (simple heuristic)
                category = "bundle"
                if "math" in name_lower: category = "math"
                elif "read" in name_lower: category = "reading"
                elif "science" in name_lower: category = "science"
                elif "writ" in name_lower: category = "writing"
                
                # Fetch variant ID for this product (needed for checkout)
                variant_id = None
                try:
                    variant_response = await client.get(
                        f"https://api.lemonsqueezy.com/v1/products/{item['id']}/variants",
                        headers=headers,
                        timeout=10.0
                    )
                    if variant_response.status_code == 200:
                        variants = variant_response.json().get("data", [])
                        if variants:
                            variant_id = str(variants[0]["id"])  # Use first variant
                except Exception as e:
                    print(f"⚠️ Failed to fetch variant for product {item['id']}: {e}")

                live_products.append({
                    "id": str(item["id"]),
                    "variant_id": variant_id,  # Add variant ID
                    "title": product_name,
                    "description": attr.get("description", "") or "No description provided.",
                    "price": attr.get("price_formatted", "$0.00"),
                    "image": attr.get("large_thumb_url") or attr.get("thumb_url"),
                    "category": category,
                    "purchased": False,
                    "buyUrl": attr.get("buy_now_url"),
                    "contentPath": None # Downloads handled by Lemon Squeezy
                })

            
            return live_products

    except Exception as e:
        print(f"❌ Error connecting to Lemon Squeezy: {e}")
        return products_db

@app.post("/webhooks/lemon-squeezy")
async def lemon_squeezy_webhook(request: Request):
    """
    Handle Lemon Squeezy webhooks (optional - just for logging).
    
    Lemon Squeezy handles:
    - Sending order confirmation emails
    - Providing download links
    - Customer notifications
    
    This webhook is just for your own tracking/logging.
    """
    
    # Get webhook signing secret from environment
    webhook_secret = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET")
    
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("X-Signature")
    
    # Verify signature if secret is set
    if webhook_secret and signature:
        computed_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, computed_signature):
            print("❌ Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse webhook data
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Get event type
    event_name = data.get("meta", {}).get("event_name")
    
    print(f"📬 Received webhook: {event_name}")
    
    # Handle order_created event
    if event_name == "order_created":
        order_data = data.get("data", {})
        attributes = order_data.get("attributes", {})
        
        # Extract order details
        order_id = order_data.get("id")
        customer_email = attributes.get("user_email")
        customer_name = attributes.get("user_name")
        total = attributes.get("total_formatted")
        
        # Log order details
        print(f"� Order #{order_id} created")
        print(f"� Customer: {customer_name} ({customer_email})")
        print(f"� Total: {total}")
        print(f"✅ Lemon Squeezy will send order confirmation email with download links")
    
    # Handle other events
    elif event_name:
        print(f"ℹ️ Received {event_name} event (no action needed)")
    
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    
    # Ngrok tunnel is started/stopped in FastAPI startup/shutdown events when running under uvicorn/systemd.
    # When running this file directly (python main.py) the startup events will also run under uvicorn.

    # Run on 0.0.0.0 to be accessible from network
    uvicorn.run(app, host="0.0.0.0", port=8000)
