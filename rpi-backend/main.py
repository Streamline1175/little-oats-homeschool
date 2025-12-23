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

# Import email sender
from email_sender import send_order_confirmation_email

# Load environment variables from .env file
load_dotenv()

# JSON file for storing pending orders (persists across restarts)
PENDING_ORDERS_FILE = "pending_orders.json"

def load_pending_orders() -> Dict[str, List[Dict]]:
    """Load pending orders from JSON file"""
    try:
        if os.path.exists(PENDING_ORDERS_FILE):
            with open(PENDING_ORDERS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading pending orders: {e}")
    return {}

def save_pending_orders(orders: Dict[str, List[Dict]]):
    """Save pending orders to JSON file"""
    try:
        with open(PENDING_ORDERS_FILE, 'w') as f:
            json.dump(orders, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving pending orders: {e}")

def store_order(order_identifier: str, items: List[Dict]):
    """Store order items for later retrieval"""
    orders = load_pending_orders()
    orders[order_identifier] = items
    save_pending_orders(orders)
    print(f"💾 Stored {len(items)} items for order #{order_identifier}")

def retrieve_order(order_identifier: str) -> List[Dict]:
    """Retrieve and remove order items"""
    orders = load_pending_orders()
    items = orders.pop(order_identifier, [])
    if items:
        save_pending_orders(orders)
        print(f"✅ Retrieved {len(items)} stored items for order #{order_identifier}")
    return items

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

class CartItem(BaseModel):
    """Item in the shopping cart"""
    id: str
    title: str
    price: str
    priceValue: float
    image: Optional[str] = None

class CheckoutRequest(BaseModel):
    """Request body for creating a checkout"""
    items: List[CartItem]

class CheckoutResponse(BaseModel):
    """Response containing the Lemon Squeezy checkout URL"""
    checkout_url: str
    total: float
    item_count: int

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

                live_products.append({
                    "id": str(item["id"]),
                    "title": product_name,
                    "description": attr.get("description", "") or "No description provided.",
                    "price": attr.get("price_formatted", "$0.00"),
                    "image": attr.get("large_thumb_url") or attr.get("thumb_url"),
                    "category": category,
                    "purchased": False,
                    "buyUrl": attr.get("buy_now_url"),
                    "contentPath": None # Downloads handled separately
                })

            
            return live_products

    except Exception as e:
        print(f"❌ Error connecting to Lemon Squeezy: {e}")
        return products_db

@app.post("/api/checkout", response_model=CheckoutResponse)
async def create_checkout(request: CheckoutRequest):
    """
    Create a bundled Lemon Squeezy checkout for multiple cart items.
    
    This endpoint:
    1. Receives cart items from the frontend
    2. Calculates the total price
    3. Creates a custom Lemon Squeezy checkout with all items bundled
    4. Returns the checkout URL to the frontend
    """
    
    if not request.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Get Lemon Squeezy credentials
    api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
    store_id = os.getenv("LEMON_SQUEEZY_STORE_ID")
    variant_id = os.getenv("LEMON_SQUEEZY_BUNDLE_VARIANT_ID")
    
    if not all([api_key, store_id, variant_id]):
        raise HTTPException(
            status_code=500, 
            detail="Lemon Squeezy configuration missing. Please set LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID, and LEMON_SQUEEZY_BUNDLE_VARIANT_ID in .env"
        )
    
    # Calculate total
    total = sum(item.priceValue for item in request.items)
    total_cents = int(total * 100)  # Convert to cents
    
    # Build itemized description
    item_list = "\n".join([
        f"• {item.title} - {item.price}"
        for item in request.items
    ])
    
    description = f"Your Order:\n\n{item_list}\n\nTotal: ${total:.2f}"
    
    # Create custom checkout via Lemon Squeezy API
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json"
        }
        
        checkout_data = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "custom_price": total_cents,
                    "product_options": {
                        "name": f"Your Order ({len(request.items)} items)",
                        "description": description,
                        "redirect_url": f"https://littleoatlearners.com/thank-you.html?checkout_id={checkout_id}&items={len(request.items)}&total={total:.2f}",
                    },
                    "checkout_data": {
                        "custom": {
                            "item_count": str(len(request.items)),  # Convert to string
                            "items": json.dumps([  # Convert to JSON string
                                {
                                    "id": item.id,
                                    "title": item.title,
                                    "price": item.price
                                }
                                for item in request.items
                            ])
                        }
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": store_id
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": variant_id
                        }
                    }
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.lemonsqueezy.com/v1/checkouts",
                headers=headers,
                json=checkout_data,
                timeout=30.0
            )
            
            if response.status_code != 201:
                print(f"❌ Lemon Squeezy Error {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create checkout: {response.text}"
                )
            
            result = response.json()
            checkout_url = result["data"]["attributes"]["url"]
            checkout_id = result["data"]["id"]
            
            # Prepare items for storage
            items_to_store = [
                {
                    "id": item.id,
                    "title": item.title,
                    "price": item.price
                }
                for item in request.items
            ]
            
            # Store items using checkout_id
            # We'll also need to match this in the webhook somehow
            store_order(checkout_id, items_to_store)
            
            print(f"✅ Created checkout for ${total:.2f} ({len(request.items)} items)")
            print(f"🔗 Checkout URL: {checkout_url}")
            
            return CheckoutResponse(
                checkout_url=checkout_url,
                total=total,
                item_count=len(request.items)
            )
    
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error creating checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/api/order/{checkout_id}")
async def get_order_details(checkout_id: str):
    """
    Get order details for thank-you page
    Returns the stored items for a checkout
    """
    orders = load_pending_orders()
    items = orders.get(checkout_id, [])
    
    if items:
        return {
            "success": True,
            "items": items,
            "item_count": len(items)
        }
    else:
        return {
            "success": False,
            "items": [],
            "item_count": 0
        }

@app.post("/webhooks/lemon-squeezy")
async def lemon_squeezy_webhook(request: Request):
    """
    Handle Lemon Squeezy webhooks for order events.
    
    This endpoint:
    1. Verifies the webhook signature
    2. Processes order_created events
    3. Logs order information with itemized details
    4. Can be extended to send custom emails
    """
    
    # Get webhook signing secret from environment
    webhook_secret = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET")
    
    if not webhook_secret:
        print("⚠️ LEMON_SQUEEZY_WEBHOOK_SECRET not set. Webhook signature verification disabled.")
        # Continue anyway for testing, but log warning
    
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("X-Signature")
    
    # Verify signature if secret is set
    if webhook_secret and signature:
        # Compute HMAC
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
        
        # Debug: Log all available keys to find checkout reference
        print(f"🔍 Debug - attributes keys: {list(attributes.keys())}")
        
        # Extract order details
        order_id = order_data.get("id")
        customer_email = attributes.get("user_email")
        customer_name = attributes.get("user_name")
        total = attributes.get("total_formatted")
        
        # Extract custom data (contains itemized list)
        first_order_item = attributes.get("first_order_item", {})
        meta_data = first_order_item.get("meta", {})
        custom_data = meta_data.get("custom_data", {})
        
        # Debug: Log the full first_order_item to see its structure
        print(f"🔍 Debug - first_order_item keys: {list(first_order_item.keys())}")
        print(f"🔍 Debug - product_name: {first_order_item.get('product_name')}")
        print(f"🔍 Debug - variant_name: {first_order_item.get('variant_name')}")
        print(f"🔍 Debug - custom_data: {json.dumps(custom_data, indent=2)}")
        
        # Also check if there's a description in attributes
        checkout_description = attributes.get("first_order_item", {}).get("product", {}).get("description", "")
        print(f"🔍 Debug - checkout description: {checkout_description}")
        
        # Since custom_data is empty, parse items from the product description
        product_name = first_order_item.get("product_name", "")
        
        # Extract item count from product name (e.g., "Your Order (3 items)")
        import re
        count_match = re.search(r'\((\d+) items?\)', product_name)
        item_count = int(count_match.group(1)) if count_match else 0
        
        # Try to find stored items using various identifiers
        # The webhook doesn't give us the checkout_id directly, so we need to try different approaches
        order_identifier = attributes.get("identifier")  # Order identifier
        order_id_str = str(order_id)  # Order ID
        
        print(f"🔍 Debug - order_identifier: {order_identifier}")
        print(f"🔍 Debug - order_id: {order_id_str}")
        
        # Load all pending orders to see what we have
        all_orders = load_pending_orders()
        print(f"🔍 Debug - available order keys: {list(all_orders.keys())}")
        
        # Try to retrieve items using different identifiers
        items = retrieve_order(order_identifier) or retrieve_order(order_id_str)
        
        # If still no items, try matching by checking all stored orders
        if not items and all_orders:
            # Just use the first/oldest stored order as fallback
            # This works if there's only one pending order
            first_key = list(all_orders.keys())[0]
            print(f"⚠️ Using fallback: retrieving order #{first_key}")
            items = retrieve_order(first_key)
        
        item_count = len(items) if items else 0
        
        if not items:
            # Final fallback: create a simple item from the order
            print(f"⚠️ No stored items found")
            items = [{
                "title": product_name or "Your Order",
                "price": total
            }]
            item_count = 1
        
        # Extract download URLs from order
        urls = attributes.get("urls", {})
        download_url = urls.get("download", "")  # Main download page URL
        
        print(f"📦 Order #{order_id} created")
        print(f"👤 Customer: {customer_name} ({customer_email})")
        print(f"💰 Total: {total}")
        print(f"📋 Items: {item_count}")
        if download_url:
            print(f"📥 Download URL: {download_url}")
        
        # Log itemized list
        if items:
            print("📝 Order contains:")
            for item in items:
                print(f"   • {item.get('title')} - {item.get('price')}")
        
        # Send custom email with itemized list and download link
        if customer_email and customer_name:
            email_sent = await send_order_confirmation_email(
                to_email=customer_email,
                customer_name=customer_name,
                order_id=str(order_id),
                items=items,
                total=total,
                download_url=download_url  # Pass download URL
            )
            
            if email_sent:
                print(f"📧 Custom order confirmation email sent to {customer_email}")
            else:
                print(f"⚠️ Failed to send custom email to {customer_email}")
        
        print(f"✅ Order #{order_id} processed successfully")
    
    # Handle other events
    elif event_name == "subscription_created":
        print("📬 Subscription created (not handling in this implementation)")
    
    # Return success
    return {"status": "success", "event": event_name}

if __name__ == "__main__":
    import uvicorn
    
    # Ngrok tunnel is started/stopped in FastAPI startup/shutdown events when running under uvicorn/systemd.
    # When running this file directly (python main.py) the startup events will also run under uvicorn.

    # Run on 0.0.0.0 to be accessible from network
    uvicorn.run(app, host="0.0.0.0", port=8000)
