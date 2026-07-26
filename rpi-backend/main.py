from fastapi import FastAPI, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse, FileResponse
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import httpx
from dotenv import load_dotenv
import time
import sys
import json
import tempfile
import asyncio  # Required for the analytics write lock
import hashlib  # Required for analytics visitor hashing
from polar_sdk import Polar

# Load environment variables from .env file
load_dotenv()

# Initialize Polar SDK client
def is_sandbox_mode():
    """Check if Polar sandbox mode is enabled"""
    return os.getenv("POLAR_SANDBOX_MODE", "false").lower() == "true"

def get_polar_client():
    """Get Polar client configured for sandbox or production based on env settings"""
    sandbox = is_sandbox_mode()

    if sandbox:
        access_token = os.getenv("POLAR_SANDBOX_TOKEN")
        if not access_token:
            print("⚠️ POLAR_SANDBOX_MODE is enabled but POLAR_SANDBOX_TOKEN is not set")
            return None
        print("🧪 Using Polar SANDBOX mode")
        return Polar(server="sandbox", access_token=access_token)
    else:
        access_token = os.getenv("POLAR_PRODUCTION_TOKEN")
        if not access_token:
            print("⚠️ POLAR_PRODUCTION_TOKEN is not set")
            return None
        print("🚀 Using Polar PRODUCTION mode")
        return Polar(access_token=access_token)

def get_polar_api_config():
    """Get API base URL and token for direct httpx calls"""
    sandbox = is_sandbox_mode()
    if sandbox:
        return {
            "base_url": "https://sandbox-api.polar.sh",
            "token": os.getenv("POLAR_SANDBOX_TOKEN")
        }
    else:
        return {
            "base_url": "https://api.polar.sh",
            "token": os.getenv("POLAR_PRODUCTION_TOKEN")
        }

app = FastAPI()

# Allow interactions from the desktop app (which might be localhost or another IP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Product(BaseModel):
    id: str
    title: str
    description: str
    price: str
    image: Optional[str] = None
    images: Optional[List[str]] = None  # Array of images for gallery
    category: str
    purchased: bool = False
    contentPath: Optional[str] = None
    buyUrl: Optional[str] = None
    is_subscription: Optional[bool] = False
    interval: Optional[str] = None
    interval_count: Optional[int] = None
    hasFiles: Optional[bool] = None  # Whether product has downloadable files
    licenseKey: Optional[str] = None  # License key for this purchase (if applicable)

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

# ==================== ANALYTICS ====================

# Absolute path: the data file must not depend on the process working directory.
# If WorkingDirectory ever changes, a relative path would silently begin a
# second, empty analytics file instead of appending to the real one.
ANALYTICS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics_data.json")

# /api/analytics/track is public and unauthenticated, so client-supplied page
# values are normalized and bounded. Without this a stray "?utm_source=..."
# fragments one page into many keys, and a spoofed flood of unique paths would
# grow the pages dict without limit.
MAX_PAGE_LEN = 128
MAX_PAGES_PER_DAY = 250

# Serializes the read-modify-write below. uvicorn runs this app in a single
# process (see uvicorn.run at the bottom of this file), so an asyncio lock is
# sufficient. Without it, concurrent requests each load the same snapshot and
# the last save wins, silently dropping view counts -- which matters now that
# every page loads the tracker instead of just two.
_analytics_lock = asyncio.Lock()


class AnalyticsEvent(BaseModel):
    visitor_id: str
    page: str


def _normalize_page(raw: str) -> str:
    """Reduce a client-supplied path to a stable, bounded key."""
    page = (raw or "").split("?", 1)[0].split("#", 1)[0].strip()
    if not page:
        return ""
    if not page.startswith("/"):
        page = "/" + page
    return page[:MAX_PAGE_LEN]


def load_analytics() -> Dict[str, Any]:
    if not os.path.exists(ANALYTICS_FILE):
        return {}
    try:
        with open(ANALYTICS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading analytics file: {e}")
        return {}


def save_analytics(data: Dict[str, Any]):
    """Write to a temp file and atomically rename over the target, so an
    interrupted write cannot truncate or corrupt the existing data."""
    tmp_path = None
    try:
        directory = os.path.dirname(ANALYTICS_FILE) or "."
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".analytics-", suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, ANALYTICS_FILE)
        tmp_path = None
    except Exception as e:
        print(f"⚠️ Error writing analytics file: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.post("/api/analytics/track")
async def track_visit(event: AnalyticsEvent):
    today = time.strftime("%Y-%m-%d")

    async with _analytics_lock:
        data = load_analytics()

        # setdefault on each key so days written by the older format (which had
        # no "pages") keep working instead of raising.
        day_data = data.setdefault(today, {})
        day_data.setdefault("views", 0)
        day_data.setdefault("visitors", [])
        day_data.setdefault("pages", {})

        visitor_hash = hashlib.sha256(event.visitor_id.encode()).hexdigest()[:16]

        day_data["views"] += 1

        if visitor_hash not in day_data["visitors"]:
            day_data["visitors"].append(visitor_hash)

        page = _normalize_page(event.page)
        if page:
            pages = day_data["pages"]
            # Only admit a new key while under the cap; existing keys always count.
            if page in pages or len(pages) < MAX_PAGES_PER_DAY:
                pages[page] = pages.get(page, 0) + 1

        save_analytics(data)

    return {"status": "ok"}


@app.get("/api/analytics/stats")
def get_analytics():
    raw_data = load_analytics()
    summary = {}

    for date, info in raw_data.items():
        pages = info.get("pages", {})
        top_page = max(pages, key=pages.get) if pages else ""
        summary[date] = {
            "views": info.get("views", 0),
            "unique_visitors": len(info.get("visitors", [])),
            "top_pages": dict(sorted(pages.items(), key=lambda x: x[1], reverse=True)),
            "top_page": top_page,
        }

    return dict(sorted(summary.items(), reverse=True))

@app.get("/dashboard")
def analytics_dashboard():
    return FileResponse("templates/dashboard.html", media_type="text/html")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Little Oat API",
        "polar_mode": "sandbox" if is_sandbox_mode() else "production"
    }

@app.get("/api/health")
async def health_check():
    """Health endpoint for the desktop app to verify the API and Polar connection."""
    polar = get_polar_client()

    if not polar:
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "polar_connected": False,
            "reason": "No Polar credentials configured"
        })

    try:
        products_response = polar.products.list()
        product_count = len(products_response.result.items) if products_response and products_response.result else 0
        return {
            "status": "healthy",
            "polar_connected": True,
            "polar_mode": "sandbox" if is_sandbox_mode() else "production",
            "product_count": product_count
        }
    except Exception as e:
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "polar_connected": False,
            "polar_mode": "sandbox" if is_sandbox_mode() else "production",
            "reason": str(e)
        })

@app.get("/api/products", response_model=List[Product])
async def get_products():
    polar = get_polar_client()

    # If no credentials, return mock data
    if not polar:
        print("ℹ️ No Polar credentials found (env vars).")
        print(f"   🔍 Debug: Environment keys visible to process: {list(os.environ.keys())}")
        print("   Returning mock inventory.")
        return products_db

    # Fetch from Polar
    try:
        live_products = []

        # List all products from Polar
        products_response = polar.products.list()

        if products_response and products_response.result:
            for product in products_response.result.items:
                # Filter out archived and internal products
                if getattr(product, 'is_archived', False):
                    continue
                name_check = product.name.lower() if product.name else ""
                if "cart-bundle" in name_check or "cart bundle" in name_check:
                    continue

                # Determine if this is a subscription product using product-level is_recurring
                is_subscription = getattr(product, 'is_recurring', False)
                interval = getattr(product, 'recurring_interval', None)
                interval_count = getattr(product, 'recurring_interval_count', 1)

                # Get price info from the first price if available
                price_formatted = "$0.00"
                if hasattr(product, 'prices') and product.prices:
                    first_price = product.prices[0]
                    if hasattr(first_price, 'price_amount'):
                        price_formatted = f"${first_price.price_amount / 100:.2f}"
                    # Get interval from price if not set at product level
                    if not interval and hasattr(first_price, 'recurring_interval'):
                        interval = first_price.recurring_interval
                        interval_count = getattr(first_price, 'recurring_interval_count', 1)

                # Determine category from name AND description (keyword matching)
                name_lower = (product.name or "").lower()
                desc_lower = (product.description or "").lower()
                combined_text = name_lower + " " + desc_lower

                # Category detection - based on content keywords (subscription is NOT a category)
                # Subscription status is tracked via is_subscription field instead
                if "bundle" in name_lower or "complete" in name_lower or "pack" in name_lower:
                    category = "bundle"
                elif any(kw in combined_text for kw in ["math", "arithmetic", "algebra", "geometry", "counting", "multiplication"]):
                    category = "math"
                elif any(kw in combined_text for kw in ["read", "phonics", "literacy", "comprehension", "vocabulary"]):
                    category = "reading"
                elif any(kw in combined_text for kw in ["science", "biology", "chemistry", "physics", "nature", "experiment"]):
                    category = "science"
                elif any(kw in combined_text for kw in ["writ", "composition", "essay", "grammar", "spelling"]):
                    category = "writing"
                elif any(kw in combined_text for kw in ["premium", "license", "subscription", "membership"]):
                    category = "premium"
                else:
                    category = "curriculum"

                # Get product images if available (collect all for gallery)
                images = []
                image_url = None  # Keep for backwards compatibility
                if hasattr(product, 'medias') and product.medias:
                    for media in product.medias:
                        if hasattr(media, 'public_url') and media.public_url:
                            images.append(media.public_url)
                    if images:
                        image_url = images[0]  # First image for backwards compat

                # Determine hasFiles and isLicenseProduct from benefits array
                has_files = False
                is_license_product = False
                file_count = 0
                
                # Debug: Print product attributes to understand SDK structure
                print(f"\n   🔍 DEBUG: Product '{product.name}' structure:")
                print(f"      - Type: {type(product)}")
                print(f"      - Has 'benefits' attr: {hasattr(product, 'benefits')}")
                
                # Try to get benefits multiple ways
                benefits = None
                if hasattr(product, 'benefits'):
                    benefits = product.benefits
                    print(f"      - benefits from attr: {benefits}")
                elif isinstance(product, dict) and 'benefits' in product:
                    benefits = product['benefits']
                    print(f"      - benefits from dict: {benefits}")
                
                # If still no benefits, try to list all attributes
                if benefits is None:
                    try:
                        attrs = dir(product) if not isinstance(product, dict) else product.keys()
                        benefit_related = [a for a in attrs if 'benefit' in str(a).lower()]
                        print(f"      - Benefit-related attrs: {benefit_related}")
                    except:
                        pass
                
                if benefits:
                    print(f"      - Benefits count: {len(benefits)}")
                    for i, benefit in enumerate(benefits):
                        # SDK uses TYPE (uppercase), not type
                        benefit_type = getattr(benefit, 'TYPE', None)
                        if benefit_type is None:
                            benefit_type = getattr(benefit, 'type', None)
                        
                        print(f"      - Benefit {i}: TYPE={benefit_type}")
                        
                        if benefit_type == 'downloadables':
                            has_files = True
                            # Count files from benefit properties
                            props = getattr(benefit, 'properties', None)
                            if props:
                                files_list = getattr(props, 'files', None)
                                if files_list:
                                    file_count = len(files_list)
                                    print(f"        - 📁 {file_count} downloadable file(s)")
                        elif benefit_type == 'license_keys':
                            is_license_product = True
                            print(f"        - 🔑 License key product")
                else:
                    print(f"      - ⚠️ No benefits found")

                live_products.append({
                    "id": str(product.id),
                    "title": product.name or "Unknown Product",
                    "description": product.description or "No description provided.",
                    "price": price_formatted,
                    "image": image_url,  # Single image for backwards compat
                    "images": images,    # All images for gallery
                    "category": category,
                    "purchased": False,
                    "buyUrl": None,  # Polar uses checkout sessions instead of static URLs
                    "contentPath": None,
                    "is_subscription": is_subscription,
                    "interval": interval,
                    "interval_count": interval_count,
                    "hasFiles": has_files,
                    "fileCount": file_count,  # Number of downloadable files
                    "isLicenseProduct": is_license_product,
                    "licenseKey": None,  # Will be populated on sync for purchased products
                })

            print(f"📦 DEBUG: Fetched {len(live_products)} products from Polar:")
            for p in live_products:
                sub_info = f" [SUBSCRIPTION: {p['interval']}]" if p['is_subscription'] else ""
                files_info = "📁" if p.get('hasFiles') else "📄"
                license_info = "🔑" if p.get('isLicenseProduct') else ""
                print(f"   - {p['title']} ({p['category']}){sub_info} {files_info}{license_info} | Images: {len(p.get('images', []))}")

            return live_products

        return products_db  # Fallback if no products found

    except Exception as e:
        print(f"❌ Error connecting to Polar: {e}")
        import traceback
        traceback.print_exc()
        return products_db


# ==================== CHECKOUT ENDPOINT ====================

class CheckoutRequest(BaseModel):
    product_id: str

@app.post("/api/checkout")
async def create_checkout(request: CheckoutRequest):
    """
    Create a Polar checkout session and return the checkout URL.
    The desktop app will open this URL in a webview for payment.
    """
    polar = get_polar_client()

    if not polar:
        print("❌ Error: Polar credentials not configured")
        return JSONResponse(status_code=500, content={"error": "Payment system not configured"})

    try:
        print(f"🛒 Creating checkout session for product: {request.product_id}")
        
        # Create a checkout session with Polar
        # The SDK uses request= dict pattern, not keyword arguments
        checkout = polar.checkouts.create(request={
            "products": [request.product_id]
        })
        
        checkout_url = checkout.url
        print(f"✅ Checkout created: {checkout_url}")
        
        return {"success": True, "checkoutUrl": checkout_url}
        
    except Exception as e:
        print(f"❌ Error creating checkout: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ==================== LICENSE VALIDATION ENDPOINT ====================

# Desktop app subscription product ID (for product-specific validation)
DESKTOP_SUBSCRIPTION_PRODUCT_ID = os.getenv("POLAR_DESKTOP_PRODUCT_ID", "")

class ValidateLicenseRequest(BaseModel):
    license_key: str
    product_id: Optional[str] = None  # If provided, validates license is for this specific product

@app.post("/api/validate-license")
async def validate_license(request: ValidateLicenseRequest):
    """
    Validate a Polar license key.
    This endpoint validates license keys using Polar's customer portal API.
    If product_id is provided, also verifies the license belongs to that specific product.
    """
    print(f"🔑 Validating license key: {request.license_key[:8]}...")
    if request.product_id:
        print(f"   Product filter: {request.product_id}")

    # Test license bypass — set TEST_LICENSE_KEY in .env to enable production testing
    test_key = os.getenv("TEST_LICENSE_KEY", "")
    if test_key and request.license_key == test_key:
        print(f"   ✅ Test license key matched — bypassing Polar validation")
        return {
            "success": True,
            "valid": True,
            "license": {
                "type": "lifetime",
                "expiresAt": None,
                "email": "test@test.com",
                "customerName": "Test User",
                "features": ["premium", "content-updates"]
            }
        }

    api_config = get_polar_api_config()
    
    if not api_config['token']:
        print("❌ Error: Polar credentials not configured")
        return JSONResponse(status_code=500, content={"error": "License validation not configured"})

    # Get organization ID from env
    org_id = os.getenv("POLAR_ORGANIZATION_ID")
    if not org_id:
        print("❌ Error: POLAR_ORGANIZATION_ID not set")
        return JSONResponse(status_code=500, content={"error": "License validation not configured"})

    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Use the customer portal license key validation endpoint
        # This endpoint doesn't require authentication (public-facing)
        validate_url = f"{api_config['base_url']}/v1/customer-portal/license-keys/validate"
        
        payload = {
            "key": request.license_key,
            "organization_id": org_id
        }
        
        print(f"   Calling: {validate_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(validate_url, json=payload, headers=headers)
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ License key is valid")
                
                # If product_id filter is provided, verify the license belongs to that product
                # Use license key prefix to determine product type since subscription benefits 
                # don't include benefit ID in the validation response
                if request.product_id:
                    print(f"   Checking product association via prefix...")
                    
                    # Desktop App Subscription keys start with LOHSCD-
                    expected_prefix = "LOHSCD-"
                    if request.product_id == DESKTOP_SUBSCRIPTION_PRODUCT_ID:
                        if not request.license_key.upper().startswith(expected_prefix):
                            print(f"   ❌ License key doesn't have expected prefix {expected_prefix}")
                            return {
                                "success": False, 
                                "valid": False, 
                                "error": f"This license key is for a different product. Desktop App subscription keys start with {expected_prefix}"
                            }
                        print(f"   ✅ License key prefix matches Desktop App subscription")
                    # Add other product prefixes here as needed
                    # e.g., elif request.product_id == PREMIUM_CONTENT_PRODUCT_ID:
                    #          expected_prefix = "LOL-"
                
                # Extract customer info
                customer = data.get("customer", {})
                benefit = data.get("benefit", {})
                
                # Determine license type based on benefit or default to lifetime
                license_type = "lifetime"
                expires_at = data.get("expires_at")
                
                if expires_at:
                    # Check if it's a subscription based on expiration
                    from datetime import datetime
                    try:
                        exp_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                        now = datetime.now(exp_date.tzinfo)
                        days_til_expiry = (exp_date - now).days
                        if days_til_expiry <= 35:
                            license_type = "monthly"
                        elif days_til_expiry <= 380:
                            license_type = "yearly"
                    except:
                        pass
                
                return {
                    "success": True,
                    "valid": True,
                    "license": {
                        "type": license_type,
                        "expiresAt": expires_at,
                        "email": customer.get("email", ""),
                        "customerName": customer.get("name", ""),
                        "features": ["premium", "content-updates"]
                    }
                }
            elif response.status_code == 404 or response.status_code == 422:
                print(f"   ❌ Invalid license key")
                return {"success": False, "valid": False, "error": "Invalid license key"}
            else:
                error_text = response.text[:200] if response.text else "Unknown error"
                print(f"   ❌ Validation failed: {error_text}")
                return {"success": False, "valid": False, "error": "License validation failed"}
                
    except Exception as e:
        print(f"❌ Error validating license: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ==================== SYNC ENDPOINT ====================

class SyncRequest(BaseModel):
    email: str

@app.post("/api/sync-purchases")
async def sync_purchases(request: SyncRequest):
    polar = get_polar_client()

    if not polar:
        return {"success": False, "error": "API misconfigured"}

    try:
        results = []

        # First, find customer by email
        customers_response = polar.customers.list()
        customer_id = None

        if customers_response and customers_response.result:
            for customer in customers_response.result.items:
                if hasattr(customer, 'email') and customer.email == request.email:
                    customer_id = customer.id
                    print(f"✅ Found customer: {customer_id} for email: {request.email}")
                    break

        if not customer_id:
            print(f"ℹ️ No customer found with email: {request.email}")
            return {"success": True, "purchases": [], "count": 0}

        # Fetch ALL license keys for this customer
        # First, we need to build a benefit_id -> product_id map from products
        # This allows us to associate license keys (which have benefit_id) with products
        
        benefit_to_product = {}  # benefit_id -> product_id
        try:
            products_response = polar.products.list()
            if products_response and products_response.result:
                for prod in products_response.result.items:
                    prod_id = str(prod.id)
                    if hasattr(prod, 'benefits') and prod.benefits:
                        for benefit in prod.benefits:
                            benefit_id = str(getattr(benefit, 'id', ''))
                            benefit_type = getattr(benefit, 'TYPE', None) or getattr(benefit, 'type', None)
                            if benefit_id:
                                benefit_to_product[benefit_id] = {
                                    'product_id': prod_id,
                                    'product_name': prod.name,
                                    'benefit_type': benefit_type
                                }
            print(f"\n   📋 Built benefit->product map: {len(benefit_to_product)} benefits")
            for bid, info in benefit_to_product.items():
                print(f"      - {bid[:8]}... -> {info['product_name']} ({info['benefit_type']})")
        except Exception as e:
            print(f"⚠️ Could not build benefit->product map: {e}")
        
        # Now fetch license keys and map them to products
        license_keys_by_product = {}  # product_id -> license_key
        
        try:
            org_id = os.getenv("POLAR_ORGANIZATION_ID")
            if org_id:
                license_keys_response = polar.license_keys.list(
                    organization_id=org_id
                )
                if license_keys_response and license_keys_response.result:
                    for lk in license_keys_response.result.items:
                        # Check if this license belongs to our customer
                        lk_customer_id = getattr(lk, 'customer_id', None)
                        if lk_customer_id == customer_id:
                            key_value = getattr(lk, 'key', None)
                            benefit_id = str(getattr(lk, 'benefit_id', ''))
                            
                            print(f"\n   🔑 Found license key: {key_value[:12] if key_value else 'N/A'}...")
                            print(f"      - benefit_id: {benefit_id}")
                            
                            # Use the benefit_to_product map to find which product this license belongs to
                            if benefit_id in benefit_to_product and key_value:
                                prod_info = benefit_to_product[benefit_id]
                                prod_id = prod_info['product_id']
                                license_keys_by_product[prod_id] = key_value
                                print(f"      - ✅ Mapped to product: {prod_info['product_name']} (id: {prod_id})")
                            else:
                                print(f"      - ⚠️ No product mapping found for this benefit")
                                
                    print(f"\n   📊 License keys by product: {len(license_keys_by_product)}")
                    for pid, key in license_keys_by_product.items():
                        print(f"      - {pid} -> {key[:12]}...")
        except Exception as e:
            print(f"⚠️ Could not fetch license keys: {e}")
            import traceback
            traceback.print_exc()

        # Fetch orders for this customer
        orders_response = polar.orders.list()

        if orders_response and orders_response.result:
            for order in orders_response.result.items:
                # Check if this order belongs to the customer
                if hasattr(order, 'customer_id') and order.customer_id == customer_id:
                    product = order.product if hasattr(order, 'product') else None
                    product_id = str(product.id) if product and hasattr(product, 'id') else str(getattr(order, 'product_id', ''))
                    product_name = product.name if product and hasattr(product, 'name') else "Unknown"

                    # Note: order.product typically doesn't include full benefits info
                    # hasFiles and isLicenseProduct should come from /api/products, not sync
                    # We only try to match license keys here
                    has_files = None  # None = use value from products API
                    is_license_product = None  # None = use value from products API
                    product_benefit_ids = []
                    
                    print(f"\n   🔍 Processing order for: {product_name} (id: {product_id})")
                    
                    # Try to get benefits if available on order.product
                    if product and hasattr(product, 'benefits') and product.benefits:
                        print(f"      - Benefits found on order.product: {len(product.benefits)}")
                        for benefit in product.benefits:
                            benefit_type = getattr(benefit, 'TYPE', None) or getattr(benefit, 'type', None)
                            benefit_id = str(getattr(benefit, 'id', ''))
                            print(f"      - Benefit: TYPE={benefit_type}, id={benefit_id[:8]}...")
                            
                            if benefit_type == 'downloadables':
                                has_files = True
                            elif benefit_type == 'license_keys':
                                is_license_product = True
                                product_benefit_ids.append(benefit_id)
                    else:
                        print(f"      - No benefits on order.product (will use values from products API)")

                    # Try to find a license key for this product (via product_id lookup)
                    license_key = None
                    
                    if product_id in license_keys_by_product:
                        license_key = license_keys_by_product[product_id]
                        is_license_product = True  # Override since we found a key
                        print(f"      - ✅ Found license key for this product!")
                    else:
                        print(f"      - ℹ️ No license key for this product")

                    results.append({
                        "productId": product_id,
                        "variantId": None,
                        "productName": product_name,
                        "orderId": str(order.id),
                        "hasFiles": has_files,  # None = frontend should use products API value
                        "isLicenseProduct": is_license_product,  # None = frontend should use products API value
                        "licenseKey": license_key,
                    })

        print(f"📦 Found {len(results)} purchases for {request.email}")
        for r in results:
            files_info = "📁 Has files" if r.get('hasFiles') else "📄 No files"
            key_info = f"🔑 {r.get('licenseKey', '')[:8]}..." if r.get('licenseKey') else "🔓 No key"
            print(f"   - {r['productName']}: {files_info} | {key_info}")

        return {"success": True, "purchases": results, "count": len(results)}

    except Exception as e:
        print(f"❌ Error syncing purchases: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ==================== DOWNLOAD ENDPOINT ====================

def log_file_details(file_obj, prefix=""):
    """Helper to log detailed file object info for Polar downloads"""
    print(f"{prefix}📄 FILE OBJECT DETAILS:")
    print(f"{prefix}   ├─ id: {getattr(file_obj, 'id', 'unknown')}")
    print(f"{prefix}   ├─ name: {getattr(file_obj, 'name', 'unknown')}")
    print(f"{prefix}   ├─ size: {getattr(file_obj, 'size', 'unknown')} bytes")
    print(f"{prefix}   ├─ checksum_sha256: {getattr(file_obj, 'checksum_sha256', 'N/A')}")
    download_url = getattr(file_obj, 'download_url', None)
    if download_url and len(download_url) > 80:
        download_url = download_url[:80] + "..."
    print(f"{prefix}   └─ download_url: {download_url}")


@app.get("/api/download")
async def download_product(product_id: str = "", email: str = ""):
    print("=" * 70)
    print(f"📥 DOWNLOAD REQUEST RECEIVED")
    print(f"   Product ID: {product_id}")
    print(f"   Email: {email}")
    print("=" * 70)

    polar = get_polar_client()

    if not polar:
        print("❌ Error: POLAR_ACCESS_TOKEN not set")
        return JSONResponse(status_code=500, content={"error": "Server misconfigured (missing API key)"})

    try:
        # Step 1: Find customer by email
        customer_id = None
        customers_response = polar.customers.list()

        if customers_response and customers_response.result:
            for customer in customers_response.result.items:
                if hasattr(customer, 'email') and customer.email == email:
                    customer_id = customer.id
                    print(f"   ✅ Found customer: {customer_id}")
                    break

        if not customer_id:
            print(f"⚠️ No customer found with email: {email}")
            return JSONResponse(status_code=404, content={"error": "Customer not found"})

        # Step 2: Verify customer has purchased this product
        orders_response = polar.orders.list()
        has_order = False
        
        if orders_response and orders_response.result:
            for order in orders_response.result.items:
                if hasattr(order, 'customer_id') and order.customer_id == customer_id:
                    order_product_id = None
                    if hasattr(order, 'product') and hasattr(order.product, 'id'):
                        order_product_id = str(order.product.id)
                    elif hasattr(order, 'product_id'):
                        order_product_id = str(order.product_id)
                    
                    if order_product_id == product_id:
                        has_order = True
                        print(f"   ✅ Found matching order: {order.id}")
                        break

        if not has_order:
            print(f"❌ No orders found for product {product_id} and customer {email}")
            return JSONResponse(status_code=404, content={"error": "No purchase found for this product"})

        # Step 3: Create a customer session to access Customer Portal API
        # Using httpx since the SDK's customer_sessions.create() has different params
        print(f"\n🔐 Creating customer session...")
        api_config = get_polar_api_config()
        session_token = None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as session_client:
                session_url = f"{api_config['base_url']}/v1/customer-sessions/"
                headers = {
                    "Authorization": f"Bearer {api_config['token']}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                body = {"customer_id": str(customer_id)}
                
                print(f"   POST {session_url}")
                print(f"   Body: {body}")
                
                resp = await session_client.post(session_url, json=body, headers=headers)
                print(f"   Response Status: {resp.status_code}")
                
                if resp.status_code == 201 or resp.status_code == 200:
                    resp_data = resp.json()
                    session_token = resp_data.get("token")
                    print(f"   ✅ Customer session created: {session_token[:20] if session_token else 'N/A'}...")
                else:
                    print(f"   ❌ Session creation failed: {resp.text[:500]}")
                    return JSONResponse(status_code=500, content={"error": f"Failed to create customer session: {resp.text}"})
            
        except Exception as e:
            print(f"   ❌ Failed to create customer session: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": f"Failed to create customer session: {str(e)}"})

        # Step 4: Use the session token to fetch downloadables from Customer Portal API
        api_config = get_polar_api_config()
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Customer Portal API uses the session token for auth
            portal_headers = {
                "Authorization": f"Bearer {session_token}",
                "Accept": "application/json"
            }
            
            # Fetch downloadables for this customer
            downloadables_url = f"{api_config['base_url']}/v1/customer-portal/downloadables"
            print(f"\n🔍 Fetching downloadables: {downloadables_url}")
            
            resp = await client.get(downloadables_url, headers=portal_headers)
            print(f"   Response Status: {resp.status_code}")
            
            if resp.status_code != 200:
                print(f"   ❌ Error response: {resp.text[:500]}")
                return JSONResponse(status_code=resp.status_code, content={"error": f"Failed to fetch downloadables: {resp.text}"})
            
            resp_data = resp.json()
            items = resp_data.get("items", [])
            print(f"   📦 Total downloadables found: {len(items)}")
            
            # Filter to only files for the requested product
            # We need to match by benefit_id - find benefit_ids for this product first
            found_files = []
            
            # Get product benefits to know which benefit_ids belong to this product
            product_benefit_ids = set()
            try:
                products_response = polar.products.list()
                if products_response and products_response.result:
                    for prod in products_response.result.items:
                        if str(prod.id) == product_id:
                            if hasattr(prod, 'benefits') and prod.benefits:
                                for benefit in prod.benefits:
                                    bid = str(getattr(benefit, 'id', ''))
                                    if bid:
                                        product_benefit_ids.add(bid)
                            break
                print(f"   📋 Product benefit IDs: {product_benefit_ids}")
            except Exception as e:
                print(f"   ⚠️ Could not fetch product benefits: {e}")
            
            # Filter downloadables to only those matching our product
            for item in items:
                item_benefit_id = item.get("benefit_id", "")
                file_info = item.get("file", {})
                
                # If we have product_benefit_ids, filter; otherwise include all
                if product_benefit_ids and item_benefit_id not in product_benefit_ids:
                    continue
                
                download_info = file_info.get("download", {})
                found_files.append({
                    "id": file_info.get("id"),
                    "name": file_info.get("name"),
                    "size": file_info.get("size"),
                    "mime_type": file_info.get("mime_type"),
                    "download_url": download_info.get("url"),
                    "expires_at": download_info.get("expires_at")
                })
            
            print(f"   ✅ Files for this product: {len(found_files)}")
            
            if not found_files:
                print("\n" + "=" * 70)
                print("❌ NO FILES FOUND FOR THIS PRODUCT")
                print("=" * 70)
                return JSONResponse(status_code=404, content={"error": "No files found for this product"})

            # ==================== LOG ALL FILE DETAILS ====================
            print("\n" + "=" * 70)
            print(f"✅ FOUND {len(found_files)} FILE(S)")
            print("=" * 70)
            for i, f_obj in enumerate(found_files):
                print(f"[{i+1}] 📄 {f_obj.get('name')} ({f_obj.get('size')} bytes)")

            # ==================== SINGLE VS MULTI FILE HANDLING ====================
            print("\n" + "-" * 70)

            if len(found_files) == 1:
                # Single File -> Proxy Stream
                file_obj = found_files[0]
                d_url = file_obj.get("download_url")
                fname = file_obj.get("name", f"{product_id}.zip")

                print(f"📦 SINGLE FILE MODE: Streaming '{fname}'")

                if not d_url:
                    print("❌ ERROR: download_url is empty/null!")
                    return JSONResponse(status_code=500, content={"error": "File has no download URL"})

                print(f"   Initiating stream from Polar download URL...")
                print(f"   URL: {d_url[:100]}...")

                # Download to temp file first since we can't stream across contexts
                import tempfile
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(fname)[1])
                tmp_path = tmp_file.name
                
                try:
                    r = await client.get(d_url)
                    print(f"   Upstream Response Status: {r.status_code}")
                    print(f"   Content-Type: {r.headers.get('content-type')}")
                    
                    if r.status_code != 200:
                        print(f"   ❌ DOWNLOAD FAILED! Response: {r.text[:500]}")
                        return JSONResponse(
                            status_code=r.status_code,
                            content={"error": f"Upstream download failed: {r.status_code}"}
                        )
                    
                    tmp_file.write(r.content)
                    tmp_file.close()
                    
                    file_size = os.path.getsize(tmp_path)
                    print(f"   ✅ Downloaded {file_size} bytes to temp file")
                    
                except Exception as e:
                    print(f"   ❌ Download error: {e}")
                    tmp_file.close()
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return JSONResponse(status_code=500, content={"error": f"Download failed: {str(e)}"})

                def cleanup_file():
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                        print(f"🗑️ Cleaned up temp file: {tmp_path}")

                return FileResponse(
                    tmp_path,
                    filename=fname,
                    media_type=file_obj.get("mime_type", "application/octet-stream"),
                    background=BackgroundTask(cleanup_file)
                )
            else:
                # Multi File -> Download & Zip
                import shutil
                import zipfile

                print(f"📦 MULTI FILE MODE: Bundling {len(found_files)} files into ZIP")

                tmp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(tempfile.gettempdir(), f"{product_id}_bundle.zip")

                try:
                    for idx, f_obj in enumerate(found_files):
                        d_url = f_obj.get("download_url")
                        fname = f_obj.get("name", f"file_{idx}")
                        local_path = os.path.join(tmp_dir, fname)

                        print(f"   [{idx+1}/{len(found_files)}] Downloading: {fname}")

                        if not d_url:
                            print(f"      ⚠️ Skipping - no download_url")
                            continue

                        r_sub = await client.get(d_url)
                        print(f"      Upstream Status: {r_sub.status_code}")
                        if r_sub.status_code == 200:
                            with open(local_path, "wb") as f_out:
                                f_out.write(r_sub.content)
                            file_size = os.path.getsize(local_path)
                            print(f"      ✅ Saved ({file_size} bytes)")
                        else:
                            print(f"      ❌ Failed to download: {r_sub.text[:200]}")

                    print(f"\n   Creating ZIP archive: {zip_path}")
                    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', tmp_dir)

                    final_zip_path = zip_path
                    zip_size = os.path.getsize(final_zip_path)
                    print(f"   ✅ ZIP created ({zip_size} bytes)")

                finally:
                    shutil.rmtree(tmp_dir)
                    print(f"   Cleaned up temp directory: {tmp_dir}")

                def cleanup_zip():
                    if os.path.exists(final_zip_path):
                        os.remove(final_zip_path)
                        print(f"🗑️ Deleted temp zip: {final_zip_path}")

                return FileResponse(
                    final_zip_path,
                    filename=f"{product_id}_bundle.zip",
                    media_type="application/zip",
                    background=BackgroundTask(cleanup_zip)
                )

    except Exception as e:
        print(f"\n❌ OUTER DOWNLOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ==================== DEBUG ENDPOINT: List All Files ====================

@app.get("/api/debug/files")
async def debug_list_all_files():
    """Debug endpoint to list ALL files in Polar to verify what's available."""
    print("=" * 70)
    print("🔍 DEBUG: Listing ALL files in Polar")
    print("=" * 70)

    api_config = get_polar_api_config()

    if not api_config['token']:
        return JSONResponse(status_code=500, content={"error": "No API key configured"})

    print(f"   Mode: {'SANDBOX' if is_sandbox_mode() else 'PRODUCTION'}")
    print(f"   API Base: {api_config['base_url']}")

    headers = {
        "Authorization": f"Bearer {api_config['token']}",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{api_config['base_url']}/v1/files", headers=headers)

        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
            return JSONResponse(status_code=resp.status_code, content={"error": resp.text})

        data = resp.json()
        files = data.get("items", [])

        print(f"Found {len(files)} total files:")
        result = []
        for f in files:
            file_info = {
                "id": f.get("id"),
                "name": f.get("name"),
                "size": f.get("size"),
                "mime_type": f.get("mime_type"),
                "checksum_sha256": f.get("checksum_sha256"),
                "has_download_url": bool(f.get("download"))
            }
            result.append(file_info)
            print(f"  - {file_info['name']} (ID: {file_info['id']}, size: {file_info['size']}, mime: {file_info['mime_type']})")

        return {"files": result, "total": len(files)}

# ==================== FEEDBACK EMAIL ENDPOINT ====================

class FeedbackRequest(BaseModel):
    subject: str
    body: str
    type: str  # 'bug', 'feature', 'general'
    app_version: Optional[str] = None
    platform: Optional[str] = None

@app.post("/api/send-feedback")
async def send_feedback(request: FeedbackRequest):
    """Send feedback email from the desktop app."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    feedback_to = os.getenv("FEEDBACK_EMAIL", "support@littleoatlearners.com")
    
    if not smtp_user or not smtp_pass:
        print("❌ SMTP credentials not configured")
        return {"success": False, "error": "Email service not configured"}
    
    try:
        # Build email
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = feedback_to
        msg["Subject"] = f"[{request.type.upper()}] {request.subject}"
        
        # Build body with metadata
        full_body = f"""
Feedback Type: {request.type}
App Version: {request.app_version or 'Unknown'}
Platform: {request.platform or 'Unknown'}

---

{request.body}
"""
        msg.attach(MIMEText(full_body, "plain"))
        
        # Send
        print(f"📧 Sending feedback email: {request.subject}")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        print("✅ Feedback email sent successfully")
        return {"success": True, "message": "Feedback sent successfully"}
        
    except Exception as e:
        print(f"❌ Failed to send feedback: {e}")
        return {"success": False, "error": str(e)}

# ==================== MOBILE FEEDBACK ENDPOINT ====================

@app.post("/mobile-feedback", status_code=201)
async def submit_mobile_feedback(
    feedback_type: str = Form(...),
    message: str = Form(...),
    app_version: str = Form(...),
    device: str = Form(...),
    os_name: str = Form(..., alias="os"),
    images: Optional[List[UploadFile]] = File(None),
):
    import uuid
    import shutil
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from datetime import datetime, timezone

    submission_id = uuid.uuid4().hex[:8]
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    recipient = os.getenv("FEEDBACK_EMAIL", "support@littleoatlearners.com")

    if not smtp_user or not smtp_pass:
        print("❌ SMTP credentials not configured for mobile feedback")
        raise HTTPException(status_code=500, detail="Failed to send feedback email")

    image_data = []
    tmp_dir = None
    try:
        if images:
            tmp_dir = tempfile.mkdtemp()
            for i, img in enumerate(images):
                ext = (img.filename or "image.jpg").rsplit(".", 1)[-1].lower()
                dest = os.path.join(tmp_dir, f"attachment_{i + 1}.{ext}")
                with open(dest, "wb") as f:
                    f.write(await img.read())
                image_data.append((dest, ext))

        photo_line = f"{len(image_data)} photo(s) attached" if image_data else "No photos attached"
        submitted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        html_body = f"""
        <html><body style="font-family: sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #5b8a5e; border-bottom: 2px solid #e8f0e9; padding-bottom: 8px;">
            New Feedback — Daily Homeschool Tracker
          </h2>
          <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px 0; color: #888; width: 140px;">Type</td>
                <td style="padding: 8px 0; font-weight: 600;">{feedback_type}</td></tr>
            <tr><td style="padding: 8px 0; color: #888;">Submission ID</td>
                <td style="padding: 8px 0; font-family: monospace;">#{submission_id}</td></tr>
            <tr><td style="padding: 8px 0; color: #888;">App Version</td>
                <td style="padding: 8px 0;">v{app_version}</td></tr>
            <tr><td style="padding: 8px 0; color: #888;">Device</td>
                <td style="padding: 8px 0;">{device}</td></tr>
            <tr><td style="padding: 8px 0; color: #888;">OS</td>
                <td style="padding: 8px 0;">{os_name}</td></tr>
            <tr><td style="padding: 8px 0; color: #888;">Photos</td>
                <td style="padding: 8px 0;">{photo_line}</td></tr>
            <tr><td style="padding: 8px 0; color: #888;">Submitted</td>
                <td style="padding: 8px 0;">{submitted_at}</td></tr>
          </table>
          <h3 style="margin-top: 24px; color: #555;">Message</h3>
          <div style="background: #f7f7f7; border-radius: 8px; padding: 16px; white-space: pre-wrap;">{message}</div>
        </body></html>
        """

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = f"[{feedback_type}] Daily Homeschool Tracker v{app_version} — #{submission_id}"
        msg.attach(MIMEText(html_body, "html"))

        total_size = 0
        for dest, ext in image_data:
            with open(dest, "rb") as f:
                img_bytes = f.read()
            file_size = len(img_bytes)
            total_size += file_size
            print(f"   📎 Attaching {os.path.basename(dest)}: {file_size / 1024:.1f} KB")
            mime_subtype = "png" if ext == "png" else "jpeg"
            attachment = MIMEImage(img_bytes, _subtype=mime_subtype)
            fname = os.path.basename(dest)
            attachment.add_header("Content-Disposition", "attachment", filename=fname)
            msg.attach(attachment)

        if image_data:
            print(f"   📦 Total attachment size: {total_size / 1024:.1f} KB")

        print(f"📧 Sending mobile feedback #{submission_id} ({len(image_data)} image(s))")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print(f"✅ Mobile feedback email sent: #{submission_id}")
        return {"status": "received", "id": submission_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Mobile feedback failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send feedback email") from e

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ==================== RELEASES ENDPOINT ====================

GITHUB_RELEASES_API = "https://api.github.com/repos/Streamline1175/homeschool-releases/releases"

def _group_assets_by_os(assets):
    mac, win, linux = [], [], []
    for a in assets:
        n = a["label"].lower()
        if ".dmg" in n or "mac" in n or "darwin" in n:
            mac.append({"label": a["label"], "size": a["size"], "url": a["url"]})
        elif ".exe" in n or ".msi" in n or "win" in n:
            win.append({"label": a["label"], "size": a["size"], "url": a["url"]})
        elif ".appimage" in n or ".deb" in n or ".tar.gz" in n or "linux" in n:
            linux.append({"label": a["label"], "size": a["size"], "url": a["url"]})
    return {"mac": mac, "win": win, "linux": linux}

@app.get("/api/releases")
async def get_releases():
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            GITHUB_RELEASES_API,
            headers={"Accept": "application/vnd.github+json"}
        )

    if r.status_code != 200:
        return JSONResponse(status_code=r.status_code, content={"error": "Failed to fetch releases from GitHub"})

    data = r.json()
    releases = []

    for rel in data:
        body = rel.get("body") or ""
        notes = [
            line.lstrip("- ").strip()
            for line in body.splitlines()
            if line.strip().startswith("-")
        ]
        assets = [
            {
                "label": a["name"],
                "size": f"{round(a['size'] / 1_048_576)} MB",
                "url": a["browser_download_url"],
                "downloads": a["download_count"],
            }
            for a in rel.get("assets", [])
        ]
        releases.append({
            "version": rel["tag_name"].lstrip("v"),
            "summary": rel["name"],
            "released": rel["published_at"][:10],
            "url": rel["html_url"],
            "notes": notes,
            "assets": assets,
        })

    current = releases[0] if releases else {}

    history = []
    for rel in data[1:5]:
        body = rel.get("body") or ""
        history.append({
            "version": rel["tag_name"].lstrip("v"),
            "summary": rel["name"],
            "released": rel["published_at"][:10],
            "url": rel["html_url"],
            "body": body,
            "notes": [
                line.replace("-", "", 1).strip()
                for line in body.splitlines()
                if line.strip().startswith(("-", "*"))
            ],
        })

    return {
        "current": {
            "version": current.get("version", ""),
            "released": current.get("released", ""),
            "notes": current.get("notes", []),
            "body": data[0].get("body", "") if data else "",
            "assets": _group_assets_by_os(current.get("assets", [])),
        },
        "history": history,
    }


# ============================================================================
# ADMIN KEY VALIDATION + CONTENT PROXY (added 2026-07-25)
# ============================================================================
# Env vars used (set in the .env next to main.py):
#   ADMIN_KEYS            comma-separated admin license keys (server-side only)
#   GITHUB_CONTENT_TOKEN  fine-grained PAT with read access to the content repo
#   CONTENT_REPO          owner/repo (default Streamline1175/homeschool-content)
#   CONTENT_BRANCH        branch (default main)

import hmac as _hmac
from urllib.parse import quote as _urlquote
from fastapi.responses import Response as _RawResponse


class AdminKeyRequest(BaseModel):
    key: str
    device_id: Optional[str] = None


@app.post("/api/validate-admin-key")
async def validate_admin_key(request: AdminKeyRequest):
    """Validate an admin license key against the server-side ADMIN_KEYS list.

    The desktop app calls this for admin-format keys so no key material has
    to ship inside the public binaries. Comparison is constant-time and the
    key is never echoed back or fully logged.
    """
    admin_keys = [k.strip().upper() for k in os.getenv("ADMIN_KEYS", "").split(",") if k.strip()]
    supplied = (request.key or "").strip().upper()

    valid = any(_hmac.compare_digest(supplied, k) for k in admin_keys)
    print(f"🔐 Admin key check: {supplied[:6]}*** -> {'VALID' if valid else 'invalid'} (device: {(request.device_id or 'unknown')[:8]})")

    return {"valid": valid}


def _content_repo_config():
    return {
        "repo": os.getenv("CONTENT_REPO", "Streamline1175/homeschool-content"),
        "branch": os.getenv("CONTENT_BRANCH", "main"),
        "token": os.getenv("GITHUB_CONTENT_TOKEN", ""),
    }


@app.get("/api/content/file")
async def get_content_file(path: str = ""):
    """Proxy a file from the private content repo to the desktop app.

    The GitHub token lives only on this server, never in shipped binaries.
    Path is validated against traversal; only repo-relative paths allowed.
    """
    # Path validation: no empty, no absolute, no traversal, no backslashes
    parts = path.split("/")
    if (not path or path.startswith("/") or "\\" in path
            or any(p in ("", ".", "..") for p in parts)):
        return JSONResponse(status_code=400, content={"error": "Invalid path"})

    cfg = _content_repo_config()
    if not cfg["token"]:
        print("❌ /api/content/file: GITHUB_CONTENT_TOKEN not set")
        return JSONResponse(status_code=503, content={"error": "Content service not configured"})

    encoded_path = "/".join(_urlquote(p) for p in parts)
    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{encoded_path}?ref={cfg['branch']}"
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "LittleOatLearners-Backend",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            r = await client.get(url, headers=headers)
    except Exception as e:
        print(f"❌ /api/content/file: upstream error for {path}: {e}")
        return JSONResponse(status_code=502, content={"error": "Upstream fetch failed"})

    if r.status_code == 404:
        return JSONResponse(status_code=404, content={"error": f"File not found: {path}"})
    if r.status_code != 200:
        print(f"❌ /api/content/file: GitHub returned {r.status_code} for {path}")
        return JSONResponse(status_code=502, content={"error": f"Upstream returned {r.status_code}"})

    media_type = r.headers.get("content-type", "application/octet-stream")
    return _RawResponse(content=r.content, media_type=media_type)


if __name__ == "__main__":
    import uvicorn

    # Auto-start ngrok tunnel for convenience.
    # At boot, DNS/network may not be ready when this runs, so retry with backoff
    # instead of giving up on the first failure (which leaves the public endpoint dead).
    try:
        from pyngrok import ngrok

        # Relies on 'ngrok config add-authtoken' having been run on the system.
        print("🔗 Attempting to auto-start ngrok tunnel...")
        public_url = None
        for attempt in range(1, 13):
            try:
                tunnel = ngrok.connect(8000, domain="api.littleoatlearners.com")
                public_url = tunnel.public_url
                print(f"🚀 Ngrok Tunnel Live at: {public_url}")
                break
            except Exception as e:
                print(f"⚠️ Ngrok attempt {attempt} failed: {e}")
                try:
                    ngrok.kill()  # clear any half-started agent before retrying
                except Exception:
                    pass
                time.sleep(min(5 * attempt, 30))
        if public_url is None:
            print("⚠️ Could not establish ngrok tunnel after retries; serving locally only.")
            print("   (Ensure you have run 'ngrok config add-authtoken' and reserved the domain)")

    except ImportError:
        print("⚠️ 'pyngrok' not found. Install it with: pip install pyngrok")

    # Run on 0.0.0.0 to be accessible from network
    uvicorn.run(app, host="0.0.0.0", port=8000)
