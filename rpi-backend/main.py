from fastapi import FastAPI, BackgroundTasks
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
import hashlib  # Required for analytics visitor hashing

# Load environment variables from .env file
load_dotenv()

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
    category: str
    purchased: bool = False
    contentPath: Optional[str] = None
    buyUrl: Optional[str] = None
    is_subscription: Optional[bool] = False
    interval: Optional[str] = None
    interval_count: Optional[int] = None

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

ANALYTICS_FILE = "analytics_data.json"

class AnalyticsEvent(BaseModel):
    visitor_id: str
    page: str

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
    try:
        with open(ANALYTICS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error writing analytics file: {e}")

@app.post("/api/analytics/track")
async def track_visit(event: AnalyticsEvent):
    """
    Track a page view.
    Stores daily view counts and unique visitor hashes.
    """
    today = time.strftime("%Y-%m-%d")
    data = load_analytics()
    
    if today not in data:
        data[today] = {
            "views": 0,
            "visitors": [] # List of unique visitor hashes
        }
    
    # Hash visitor ID for privacy (even if client sends UUID)
    visitor_hash = hashlib.sha256(event.visitor_id.encode()).hexdigest()[:16]
    
    # Update counts
    day_data = data[today]
    day_data["views"] += 1
    
    # Add unique visitor if not present
    # Note: Using list for JSON serialization, but treating as set logic
    if visitor_hash not in day_data["visitors"]:
        day_data["visitors"].append(visitor_hash)
        
    save_analytics(data)
    return {"status": "ok"}

@app.get("/api/analytics/stats")
def get_analytics():
    """
    Get analytics summary.
    Returns:
    {
        "2023-10-27": {"views": 10, "unique_visitors": 5},
        ...
    }
    """
    raw_data = load_analytics()
    summary = {}
    
    # Convert raw data (with visitor lists) to summary (counts only)
    # We don't want to expose even hashed IDs in the stats endpoint ideally,
    # or maybe we do for debugging. Let's just return counts.
    for date, info in raw_data.items():
        summary[date] = {
            "views": info.get("views", 0),
            "unique_visitors": len(info.get("visitors", []))
        }
        
    # Sort by date descending
    sorted_summary = dict(sorted(summary.items(), reverse=True))
    return sorted_summary

@app.get("/")
def read_root():
    return {"status": "online", "service": "Little Oat API"}

@app.get("/api/products", response_model=List[Product])
async def get_products():
    api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
    store_id = os.getenv("LEMON_SQUEEZY_STORE_ID")
    
    # If no credentials, return mock data
    if not api_key or not store_id:
        print("ℹ️ No Lemon Squeezy credentials found (env vars).")
        # Log keys to help debug why cron doesn't see them (security: don't log values)
        print(f"   🔍 Debug: Environment keys visible to process: {list(os.environ.keys())}")
        print("   Returning mock inventory.")
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
            live_products = []
            
            for item in data.get("data", []):
                attr = item.get("attributes", {})
                
                # Filter out "cart-bundle" or "Cart Bundle" (internal use)
                name_check = attr.get("name", "").lower()
                if "cart-bundle" in name_check or "cart bundle" in name_check:
                    continue
                
                # Fetch variant data first (needed for checkout and subscription detection)
                variant_id = None
                is_subscription = False
                interval = None
                interval_count = None
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
                            variant_attrs = variants[0].get("attributes", {})
                            # Check if this is a subscription product
                            is_subscription = variant_attrs.get("is_subscription", False)
                            if is_subscription:
                                interval = variant_attrs.get("interval", "month")  # day, week, month, year
                                interval_count = variant_attrs.get("interval_count", 1)
                except Exception as e:
                    print(f"⚠️ Failed to fetch variant for product {item['id']}: {e}")
                
                # Determine category from name AND description (keyword matching)
                name_lower = attr.get("name", "").lower()
                desc_lower = (attr.get("description", "") or "").lower()
                combined_text = name_lower + " " + desc_lower
                
                # Category detection - prioritize bundle/subscription, then subject keywords
                # Only mark as "bundle" if explicitly named as one
                if "bundle" in name_lower or "complete" in name_lower or "pack" in name_lower:
                    category = "bundle"
                elif is_subscription:
                    category = "subscription"
                elif any(kw in combined_text for kw in ["math", "arithmetic", "algebra", "geometry", "counting", "multiplication"]):
                    category = "math"
                elif any(kw in combined_text for kw in ["read", "phonics", "literacy", "comprehension", "vocabulary"]):
                    category = "reading"
                elif any(kw in combined_text for kw in ["science", "biology", "chemistry", "physics", "nature", "experiment"]):
                    category = "science"
                elif any(kw in combined_text for kw in ["writ", "composition", "essay", "grammar", "spelling"]):
                    category = "writing"
                else:
                    category = "curriculum"  # Default to curriculum instead of bundle

                live_products.append({
                    "id": str(item["id"]),
                    "variant_id": variant_id,
                    "title": attr.get("name", "Unknown Product"),
                    "description": attr.get("description", "") or "No description provided.",
                    "price": attr.get("price_formatted", "$0.00"),
                    "image": attr.get("large_thumb_url") or attr.get("thumb_url"),
                    "category": category,
                    "purchased": False,
                    "buyUrl": attr.get("buy_now_url") or attr.get("buy_url"),
                    "contentPath": None,  # Downloads handled separately
                    "is_subscription": is_subscription,
                    "interval": interval,
                    "interval_count": interval_count
                })
            
            print(f"📦 DEBUG: Fetched {len(live_products)} products from Lemon Squeezy:")
            for p in live_products:
                sub_info = f" [SUBSCRIPTION: {p['interval']}]" if p['is_subscription'] else ""
                print(f"   - {p['title']} ({p['category']}){sub_info} Image: {p['image']}")
            
            return live_products

    except Exception as e:
        print(f"❌ Error connecting to Lemon Squeezy: {e}")
        return products_db


# ==================== SYNC ENDPOINT ====================

class SyncRequest(BaseModel):
    email: str

@app.post("/api/sync-purchases")
async def sync_purchases(request: SyncRequest):
    api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
    store_id = os.getenv("LEMON_SQUEEZY_STORE_ID")
    
    if not api_key:
        return {"success": False, "error": "API misconfigured"}

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json"
        }
        
        async with httpx.AsyncClient() as client:
            # Fetch orders filtering by email AND include order-items
            response = await client.get(
                f"https://api.lemonsqueezy.com/v1/orders?filter[store_id]={store_id}&filter[user_email]={request.email}&include=order-items",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"Lemon Error: {response.text}")
                return {"success": False, "error": "Failed to fetch orders"}
                
            data = response.json()
            results = []
            
            # Map included items to look up product/variant IDs
            included = data.get("included", [])
            order_items = [obj for obj in included if obj.get("type") == "order-items"]
            
            # Also check the main data array for order IDs
            orders = data.get("data", [])
            
            for oi in order_items:
                attrs = oi.get("attributes", {})
                
                # Find the parent order ID for this item
                # Order items have a relationship to order, but here we can just map the item itself
                # Ideally we want to know WHICH order this belongs to, but for simple sync, 
                # just knowing they own 'product_id' X is enough.
                
                results.append({
                    "productId": str(attrs.get("product_id")),
                    "variantId": str(attrs.get("variant_id")),
                    "productName": attrs.get("product_name"),
                    "orderId": str(attrs.get("order_id"))
                })
                
            return {"success": True, "purchases": results}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== DOWNLOAD ENDPOINT ====================

def log_file_details(file_obj, prefix=""):
    """Helper to log detailed file object info"""
    attr = file_obj.get("attributes", {})
    file_id = file_obj.get("id", "unknown")
    print(f"{prefix}📄 FILE OBJECT DETAILS (ID: {file_id}):")
    print(f"{prefix}   ├─ variant_id: {attr.get('variant_id')}")
    print(f"{prefix}   ├─ identifier: {attr.get('identifier')}")
    print(f"{prefix}   ├─ name: {attr.get('name')}")
    print(f"{prefix}   ├─ extension: {attr.get('extension')}")
    print(f"{prefix}   ├─ size: {attr.get('size')} bytes ({attr.get('size_formatted', 'N/A')})")
    print(f"{prefix}   ├─ version: {attr.get('version')}")
    print(f"{prefix}   ├─ status: {attr.get('status')}")  # IMPORTANT: draft vs published
    print(f"{prefix}   ├─ test_mode: {attr.get('test_mode')}")  # IMPORTANT: test mode indicator
    print(f"{prefix}   ├─ sort: {attr.get('sort')}")
    print(f"{prefix}   ├─ createdAt: {attr.get('createdAt')}")
    print(f"{prefix}   ├─ updatedAt: {attr.get('updatedAt')}")
    download_url = attr.get('download_url', 'None')
    # Truncate download URL for logging (it contains sensitive signature)
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
    
    api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
    
    if not api_key:
        print("❌ Error: LEMON_SQUEEZY_API_KEY not set")
        return JSONResponse(status_code=500, content={"error": "Server misconfigured (missing API key)"})

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json"
        }
        print(f"🔑 Using headers: Accept={headers['Accept']}, Content-Type={headers['Content-Type']}")
        
        # We need a client that can potentially be closed later if streaming
        client = httpx.AsyncClient(timeout=60.0)
        
        try:
            # ==================== ATTEMPT 1: Files by Product ID ====================
            print(f"\n🔍 ATTEMPT 1: Fetching files with filter[product_id]={product_id}")
            files_url = f"https://api.lemonsqueezy.com/v1/files?filter[product_id]={product_id}"
            print(f"   URL: {files_url}")
            
            resp = await client.get(files_url, headers=headers)
            print(f"   Response Status: {resp.status_code}")
            
            if resp.status_code == 200:
                resp_data = resp.json()
                print(f"   Response JSON (truncated): {json.dumps(resp_data, indent=2)[:500]}...")
                found_files = resp_data.get("data", [])
                print(f"   Files found: {len(found_files)}")
            else:
                print(f"   ⚠️ Non-200 response: {resp.text[:300]}")
                found_files = []

            # ==================== ATTEMPT 2: Files by Variant ID ====================
            if not found_files:
                print(f"\n🔍 ATTEMPT 2: Fetching files with filter[variant_id]={product_id}")
                files_url_v = f"https://api.lemonsqueezy.com/v1/files?filter[variant_id]={product_id}"
                print(f"   URL: {files_url_v}")
                
                resp_v = await client.get(files_url_v, headers=headers)
                print(f"   Response Status: {resp_v.status_code}")
                
                if resp_v.status_code == 200:
                    resp_data = resp_v.json()
                    print(f"   Response JSON (truncated): {json.dumps(resp_data, indent=2)[:500]}...")
                    found_files = resp_data.get("data", [])
                    print(f"   Files found: {len(found_files)}")
                else:
                    print(f"   ⚠️ Non-200 response: {resp_v.text[:300]}")

            # ==================== ATTEMPT 3: Product -> Variants -> Files ====================
            if not found_files:
                print(f"\n🔍 ATTEMPT 3: Fetching variants for product {product_id}, then files")
                variants_url = f"https://api.lemonsqueezy.com/v1/variants?filter[product_id]={product_id}"
                print(f"   Variants URL: {variants_url}")
                
                v_resp = await client.get(variants_url, headers=headers)
                print(f"   Variants Response Status: {v_resp.status_code}")
                
                if v_resp.status_code == 200:
                    v_data = v_resp.json()
                    variants = v_data.get('data', [])
                    print(f"   Variants found: {len(variants)}")
                    
                    for v in variants:
                        v_id = v.get('id')
                        v_attr = v.get('attributes', {})
                        print(f"     - Variant ID: {v_id}, Name: {v_attr.get('name')}, Status: {v_attr.get('status')}")
                    
                    if variants:
                        first_variant_id = variants[0]['id']
                        print(f"\n   Fetching files for first variant: {first_variant_id}")
                        files_url_v2 = f"https://api.lemonsqueezy.com/v1/files?filter[variant_id]={first_variant_id}"
                        print(f"   Files URL: {files_url_v2}")
                        
                        resp_v2 = await client.get(files_url_v2, headers=headers)
                        print(f"   Response Status: {resp_v2.status_code}")
                        
                        if resp_v2.status_code == 200:
                            resp_data = resp_v2.json()
                            print(f"   Response JSON (truncated): {json.dumps(resp_data, indent=2)[:500]}...")
                            found_files = resp_data.get("data", [])
                            print(f"   Files found: {len(found_files)}")
                else:
                    print(f"   ⚠️ Non-200 response: {v_resp.text[:300]}")

            # ==================== NO FILES FOUND ====================
            if not found_files:
                print("\n" + "=" * 70)
                print("❌ NO FILES FOUND AFTER ALL ATTEMPTS")
                print("=" * 70)
                print("Possible reasons:")
                print("  1. No files have been uploaded to this product/variant in Lemon Squeezy")
                print("  2. The product_id provided does not match any product in the store")
                print("  3. Files exist but are in 'draft' status (not published)")
                print("  4. API key might not have permission to access files")
                await client.aclose()
                return JSONResponse(status_code=404, content={"error": "No files found"})
            
            # ==================== LOG ALL FILE DETAILS ====================
            print("\n" + "=" * 70)
            print(f"✅ FOUND {len(found_files)} FILE(S)")
            print("=" * 70)
            for i, f_obj in enumerate(found_files):
                log_file_details(f_obj, prefix=f"[{i+1}] ")
            
            # ==================== CHECK FOR TEST MODE ====================
            test_mode_files = [f for f in found_files if f.get("attributes", {}).get("test_mode")]
            if test_mode_files:
                print("\n⚠️ WARNING: Files are in TEST MODE!")
                print("   According to Lemon Squeezy docs: 'File downloads are disabled for all test mode purchases.'")
                print("   Returning test mode error to client.")
                await client.aclose()
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Test mode active",
                        "message": "File downloads are disabled in test mode. Please switch to live mode in Lemon Squeezy to enable downloads.",
                        "test_mode": True,
                        "files_found": len(found_files),
                        "file_names": [f.get("attributes", {}).get("name") for f in found_files]
                    }
                )
            
            # ==================== CHECK FOR DRAFT STATUS WARNING ====================
            draft_files = [f for f in found_files if f.get("attributes", {}).get("status") == "draft"]
            if draft_files:
                print("\n⚠️ WARNING: Some files are in DRAFT status!")
                print("   Draft files may not be downloadable. Ensure files are 'published' in Lemon Squeezy dashboard.")
            
            # ==================== SINGLE VS MULTI FILE HANDLING ====================
            print("\n" + "-" * 70)
            
            if len(found_files) == 1:
                # Single File -> Proxy Stream
                file_obj = found_files[0]
                attr = file_obj["attributes"]
                d_url = attr.get("download_url")
                fname = attr.get("name", f"{product_id}.zip")
                
                print(f"📦 SINGLE FILE MODE: Streaming '{fname}'")
                
                if not d_url:
                    print("❌ ERROR: download_url is empty/null!")
                    await client.aclose()
                    return JSONResponse(status_code=500, content={"error": "File has no download URL"})
                
                print(f"   Initiating stream from Lemon Squeezy download URL...")
                
                req = client.build_request("GET", d_url)
                r = await client.send(req, stream=True)
                
                print(f"   Upstream Response Status: {r.status_code}")
                print(f"   Content-Type: {r.headers.get('content-type')}")
                print(f"   Content-Length: {r.headers.get('content-length')}")
                
                if r.status_code != 200:
                    error_body = await r.aread()
                    print(f"   ❌ DOWNLOAD FAILED! Response body: {error_body[:500]}")
                    await r.aclose()
                    await client.aclose()
                    return JSONResponse(
                        status_code=r.status_code, 
                        content={"error": f"Upstream download failed: {r.status_code}"}
                    )
                
                async def close_proxy():
                    await r.aclose()
                    await client.aclose()
                    print(f"✅ Stream completed and resources cleaned up for '{fname}'")

                return StreamingResponse(
                    r.aiter_bytes(),
                    media_type=r.headers.get("content-type"),
                    background=BackgroundTask(close_proxy),
                    headers={
                        "Content-Disposition": f'attachment; filename="{fname}"',
                        "Content-Length": r.headers.get("content-length", "")
                    }
                )
            else:
                # Multi File -> Download & Zip
                import shutil
                import zipfile
                
                print(f"📦 MULTI FILE MODE: Bundling {len(found_files)} files into ZIP")
                
                # Cleanup task for directory
                tmp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(tempfile.gettempdir(), f"{product_id}_bundle.zip")
                
                try:
                    # Download all to tmp_dir
                    for idx, f_obj in enumerate(found_files):
                        attr = f_obj["attributes"]
                        d_url = attr.get("download_url")
                        fname = attr["name"]
                        local_path = os.path.join(tmp_dir, fname)
                        
                        print(f"   [{idx+1}/{len(found_files)}] Downloading: {fname}")
                        
                        if not d_url:
                            print(f"      ⚠️ Skipping - no download_url")
                            continue
                        
                        # Use same client
                        async with client.stream("GET", d_url) as r_sub:
                            print(f"      Upstream Status: {r_sub.status_code}")
                            if r_sub.status_code == 200:
                                with open(local_path, "wb") as f_out:
                                    async for chunk in r_sub.aiter_bytes():
                                        f_out.write(chunk)
                                file_size = os.path.getsize(local_path)
                                print(f"      ✅ Saved ({file_size} bytes)")
                            else:
                                body = await r_sub.aread()
                                print(f"      ❌ Failed to download: {body[:200]}")
                                    
                    # Create ZIP
                    print(f"\n   Creating ZIP archive: {zip_path}")
                    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', tmp_dir)
                    
                    # Ready to serve
                    final_zip_path = zip_path # make_archive adds .zip if not present, but we handled it
                    zip_size = os.path.getsize(final_zip_path)
                    print(f"   ✅ ZIP created ({zip_size} bytes)")
                    
                finally:
                    # We can close the client now, we have the files locally
                    await client.aclose()
                    # Clean the individual files dir
                    shutil.rmtree(tmp_dir)
                    print(f"   Cleaned up temp directory: {tmp_dir}")

                # Background task to remove the zip file after serving
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
            await client.aclose()
            print(f"\n❌ ERROR in download logic: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})

    except Exception as e:
        print(f"\n❌ OUTER DOWNLOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ==================== DEBUG ENDPOINT: List All Files ====================

@app.get("/api/debug/files")
async def debug_list_all_files():
    """Debug endpoint to list ALL files in the store to verify what's available."""
    print("=" * 70)
    print("🔍 DEBUG: Listing ALL files in store")
    print("=" * 70)
    
    api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
    
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "No API key"})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.lemonsqueezy.com/v1/files", headers=headers)
        
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
            return JSONResponse(status_code=resp.status_code, content={"error": resp.text})
        
        data = resp.json()
        files = data.get("data", [])
        
        print(f"Found {len(files)} total files:")
        result = []
        for f in files:
            attr = f.get("attributes", {})
            file_info = {
                "id": f.get("id"),
                "variant_id": attr.get("variant_id"),
                "name": attr.get("name"),
                "extension": attr.get("extension"),
                "size": attr.get("size"),
                "size_formatted": attr.get("size_formatted"),
                "status": attr.get("status"),
                "test_mode": attr.get("test_mode"),
                "has_download_url": bool(attr.get("download_url"))
            }
            result.append(file_info)
            print(f"  - {file_info['name']} (ID: {file_info['id']}, variant: {file_info['variant_id']}, status: {file_info['status']}, test_mode: {file_info['test_mode']})")
        
        return {"files": result, "total": len(files)}


if __name__ == "__main__":
    import uvicorn
    
    # Auto-start ngrok tunnel for convenience
    try:
        from pyngrok import ngrok
        
        # Attempt to open a tunnel with the custom domain
        # Note: This relies on 'ngrok config add-authtoken' having been run on the system
        print("🔗 Attempting to auto-start ngrok tunnel...")
        tunnel = ngrok.connect(8000, domain="api.littleoatlearners.com")
        public_url = tunnel.public_url
        print(f"🚀 Ngrok Tunnel Live at: {public_url}")
        
    except ImportError:
        print("⚠️ 'pyngrok' not found. Install it with: pip install pyngrok")
    except Exception as e:
        print(f"⚠️ Could not auto-start ngrok: {e}")
        print("   (Ensure you have run 'ngrok config add-authtoken' and reserved the domain)")

    # Wait a moment for network to stabilize if running at boot
    time.sleep(5)

    # Run on 0.0.0.0 to be accessible from network
    uvicorn.run(app, host="0.0.0.0", port=8000)
