# ==================== ADD THESE IMPORTS TO YOUR EXISTING main.py ====================
# (Add to the top of the file with your other imports)

from typing import List  # If not already imported
from pydantic import BaseModel  # If not already imported


# ==================== ADD THESE MODELS AFTER YOUR EXISTING Product MODEL ====================

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


# ==================== ADD THIS ENDPOINT AFTER YOUR /api/products ENDPOINT ====================

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
    variant_id = os.getenv("LEMON_SQUEEZY_BUNDLE_VARIANT_ID")  # NEW: Add this to your .env
    
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
                        "redirect_url": "https://littleoatlearners.com/thank-you",  # Optional: customize this
                    },
                    "checkout_data": {
                        "custom": {
                            "item_count": len(request.items),
                            "items": [
                                {
                                    "id": item.id,
                                    "title": item.title,
                                    "price": item.price
                                }
                                for item in request.items
                            ]
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


# ==================== UPDATE YOUR .env FILE ====================
# Add this line to your .env file on the RPI:
# LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id_here

# To get your variant ID:
# 1. Create a product in Lemon Squeezy called "Cart Bundle"
# 2. Get the variant ID from the API or dashboard
# 3. Add it to your .env file


# ==================== TESTING ====================
# After adding the code and restarting your service, test with:
"""
curl -X POST https://api.littleoatlearners.com/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": "test-1",
        "title": "Test Product",
        "price": "$29.00",
        "priceValue": 29.00,
        "image": "https://example.com/image.jpg"
      }
    ]
  }'
"""
