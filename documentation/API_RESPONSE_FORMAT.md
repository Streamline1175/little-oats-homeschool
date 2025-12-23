# FastAPI Product Response Format

## ✅ What Your FastAPI Should Return

Your `/api/products` endpoint should return products in this format:

```json
{
  "products": [
    {
      "id": "prod_123",
      "name": "Premium License",
      "description": "Unlock all interactive learning tools",
      "image": "https://your-cdn.com/image.png",
      "checkout_url": "https://little-oat-learners.lemonsqueezy.com/checkout/buy/456789",
      "pricing": [
        {
          "amount": "$9.99",
          "period": "/month",
          "featured": false
        },
        {
          "amount": "$79.99",
          "period": "lifetime",
          "featured": true,
          "savings": "Save 33%"
        }
      ],
      "features": [
        "9 Interactive Activities",
        "Unlimited Students",
        "Lifetime Updates"
      ],
      "badge": "Most Popular"
    }
  ]
}
```

## 🔑 Key Field: `checkout_url`

The most important field is **`checkout_url`** - this is the full Lemon Squeezy checkout URL that your backend builds.

### Example in Python (FastAPI):

```python
from fastapi import FastAPI
import httpx
import os

app = FastAPI()

LEMON_SQUEEZY_API_KEY = os.getenv("LEMON_SQUEEZY_API_KEY")
LEMON_SQUEEZY_STORE_ID = os.getenv("LEMON_SQUEEZY_STORE_ID")
LEMON_SQUEEZY_STORE_NAME = "little-oat-learners"  # Your store subdomain

@app.get("/api/products")
async def get_products():
    # Fetch products from Lemon Squeezy API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.lemonsqueezy.com/v1/products",
            headers={
                "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}",
                "Accept": "application/vnd.api+json",
            },
            params={"filter[store_id]": LEMON_SQUEEZY_STORE_ID}
        )
        
        lemon_products = response.json()
    
    # Transform for frontend
    products = []
    for product in lemon_products.get("data", []):
        attrs = product.get("attributes", {})
        
        # Get first variant (or loop through all variants)
        variant_id = "YOUR_VARIANT_ID"  # Get from variants API
        
        # BUILD THE CHECKOUT URL HERE
        checkout_url = f"https://{LEMON_SQUEEZY_STORE_NAME}.lemonsqueezy.com/checkout/buy/{variant_id}"
        
        products.append({
            "id": product["id"],
            "name": attrs.get("name"),
            "description": attrs.get("description"),
            "image": attrs.get("thumb_url"),
            "checkout_url": checkout_url,  # ← IMPORTANT!
            "pricing": [
                {
                    "amount": "$79.99",
                    "period": "lifetime",
                    "featured": True
                }
            ],
            "features": [
                "Feature 1",
                "Feature 2",
                "Feature 3"
            ],
            "badge": None
        })
    
    return {"products": products}
```

## 📋 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `checkout_url` | string | **REQUIRED** - Full Lemon Squeezy checkout URL |
| `name` | string | Product name |
| `description` | string | Product description |
| `image` | string | Product image URL |
| `pricing` | array | Array of pricing options |
| `features` | array | Array of feature strings |
| `badge` | string/null | Optional badge text ("Most Popular", "Best Value", etc.) |

## 🎯 Why This Approach is Better

1. ✅ **Backend controls checkout URLs** - You can change store name without touching frontend
2. ✅ **No hardcoded store info in frontend** - More secure and maintainable
3. ✅ **Easier to test** - Backend can return different URLs for testing
4. ✅ **Supports custom checkout flows** - You can add discount codes, affiliates, etc.
5. ✅ **Single source of truth** - All Lemon Squeezy config stays on backend

## 🔧 Quick Test

Test your endpoint:

```bash
curl https://api.littleoatlearners.com/api/products | jq
```

Should return products with `checkout_url` field!

## ✅ Frontend Changes Complete

The frontend now:
- ✅ Fetches products from your FastAPI
- ✅ Uses `checkout_url` from your API response
- ✅ No longer needs store name or variant ID
- ✅ Just clicks → opens Lemon Squeezy checkout

---

**That's it!** Just make sure your FastAPI returns the `checkout_url` field for each product. 🚀
