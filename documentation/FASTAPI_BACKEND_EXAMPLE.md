# FastAPI Backend Example for Lemon Squeezy Integration

This is an example FastAPI endpoint that fetches products from Lemon Squeezy
and serves them to your GitHub Pages frontend.

## Installation

```bash
pip install fastapi uvicorn httpx python-dotenv
```

## Environment Variables

Create a `.env` file:

```env
LEMON_SQUEEZY_API_KEY=your_api_key_here
LEMON_SQUEEZY_STORE_ID=your_store_id_here
```

## FastAPI Code

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

app = FastAPI()

# CORS configuration - IMPORTANT for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourusername.github.io",  # Replace with your GitHub Pages URL
        "http://localhost:8000",  # For local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LEMON_SQUEEZY_API_KEY = os.getenv("LEMON_SQUEEZY_API_KEY")
LEMON_SQUEEZY_STORE_ID = os.getenv("LEMON_SQUEEZY_STORE_ID")
LEMON_SQUEEZY_API_URL = "https://api.lemonsqueezy.com/v1"


async def fetch_lemon_squeezy_products() -> List[Dict[str, Any]]:
    """Fetch all products from Lemon Squeezy API"""
    headers = {
        "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }
    
    async with httpx.AsyncClient() as client:
        # Fetch products
        response = await client.get(
            f"{LEMON_SQUEEZY_API_URL}/products",
            headers=headers,
            params={"filter[store_id]": LEMON_SQUEEZY_STORE_ID}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch products")
        
        products_data = response.json()
        
        # Fetch variants for each product
        products_with_variants = []
        for product in products_data.get("data", []):
            product_id = product["id"]
            
            # Fetch variants for this product
            variants_response = await client.get(
                f"{LEMON_SQUEEZY_API_URL}/variants",
                headers=headers,
                params={"filter[product_id]": product_id}
            )
            
            if variants_response.status_code == 200:
                variants_data = variants_response.json()
                product["variants"] = variants_data.get("data", [])
            else:
                product["variants"] = []
            
            products_with_variants.append(product)
        
        return products_with_variants


def transform_product_for_frontend(product: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Lemon Squeezy product data into frontend-friendly format"""
    attributes = product.get("attributes", {})
    variants = product.get("variants", [])
    
    # Get the first variant (or you can handle multiple variants)
    variant_id = variants[0]["id"] if variants else None
    
    # Parse pricing from variants
    pricing = []
    for variant in variants:
        variant_attrs = variant.get("attributes", {})
        pricing.append({
            "amount": f"${variant_attrs.get('price', 0) / 100:.2f}",  # Convert cents to dollars
            "period": "one-time",  # Adjust based on your product type
            "featured": variant_attrs.get("is_subscription", False),
            "savings": None  # Calculate if you have multiple price points
        })
    
    # Extract features from description or custom fields
    # You might want to use custom product metadata for this
    features = [
        "Feature 1",  # Replace with actual features from your product data
        "Feature 2",
        "Feature 3",
    ]
    
    return {
        "id": product["id"],
        "variant_id": variant_id,
        "name": attributes.get("name", ""),
        "description": attributes.get("description", ""),
        "image": attributes.get("thumb_url") or attributes.get("large_thumb_url"),
        "pricing": pricing,
        "features": features,
        "badge": None,  # Set based on product metadata or tags
    }


@app.get("/api/products")
async def get_products():
    """
    Endpoint to fetch and return products in a format ready for the frontend
    """
    try:
        lemon_products = await fetch_lemon_squeezy_products()
        
        # Transform products for frontend
        frontend_products = [
            transform_product_for_frontend(product)
            for product in lemon_products
        ]
        
        return {"products": frontend_products}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """
    Get a single product by ID
    """
    try:
        products = await fetch_lemon_squeezy_products()
        product = next((p for p in products if p["id"] == product_id), None)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return transform_product_for_frontend(product)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Running the Server

```bash
uvicorn main:app --reload
```

## Testing the Endpoint

```bash
curl http://localhost:8000/api/products
```

## Deployment Options

### 1. **Railway** (Recommended - Easy & Free Tier)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 2. **Render** (Free Tier Available)
- Push your code to GitHub
- Connect Render to your repo
- Deploy as a Web Service

### 3. **Fly.io** (Free Tier Available)
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### 4. **Your Existing Server**
If you already have a server running your desktop app's FastAPI:
- Just add this endpoint to your existing FastAPI app
- Make sure CORS is configured to allow your GitHub Pages domain

## Frontend Configuration

After deploying, update `js/main.js`:

```javascript
const FASTAPI_URL = 'https://your-deployed-backend.railway.app'; // Your actual URL
const LEMON_SQUEEZY_STORE = 'your-store-name';
```

## Product Data Format

Your FastAPI should return products in this format:

```json
{
  "products": [
    {
      "id": "123",
      "variant_id": "456",
      "name": "Premium License",
      "description": "Unlock all features",
      "image": "https://...",
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

## Caching (Optional but Recommended)

Add caching to reduce API calls to Lemon Squeezy:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache
_cache = {"products": None, "timestamp": None}
CACHE_DURATION = timedelta(minutes=5)

async def get_cached_products():
    now = datetime.now()
    
    if (_cache["products"] is None or 
        _cache["timestamp"] is None or 
        now - _cache["timestamp"] > CACHE_DURATION):
        
        # Refresh cache
        _cache["products"] = await fetch_lemon_squeezy_products()
        _cache["timestamp"] = now
    
    return _cache["products"]
```

## Security Notes

1. **Never expose your Lemon Squeezy API key** in frontend code
2. **Always use CORS** to restrict which domains can access your API
3. **Rate limiting** - Consider adding rate limiting to prevent abuse
4. **Environment variables** - Keep sensitive data in `.env` files

## Next Steps

1. Deploy your FastAPI backend
2. Update `FASTAPI_URL` in `js/main.js`
3. Test the integration
4. Products will now load dynamically! 🎉
