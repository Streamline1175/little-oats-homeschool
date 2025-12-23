# Dynamic Product Loading - Complete Setup Guide

## 🎯 Overview

Your GitHub Pages site can now dynamically load products from your FastAPI backend! Here's how it all works together:

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Pages (Static Site)                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  curriculum.html                                      │  │
│  │  - Empty product grid with loading state             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  main.js                                              │  │
│  │  - Fetches from FastAPI on page load                 │  │
│  │  - Dynamically creates product cards                 │  │
│  │  - Initializes Lemon Squeezy buttons                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ fetch()
┌─────────────────────────────────────────────────────────────┐
│  Your FastAPI Backend                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GET /api/products                                    │  │
│  │  - Fetches from Lemon Squeezy API                    │  │
│  │  - Transforms data for frontend                      │  │
│  │  - Returns JSON product array                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓ API call
┌─────────────────────────────────────────────────────────────┐
│  Lemon Squeezy API                                          │
│  - Returns all your products and variants                   │
└─────────────────────────────────────────────────────────────┘
```

## ✅ What's Already Done

### 1. **Frontend (GitHub Pages)**
- ✅ `curriculum.html` - Empty product grid ready for dynamic content
- ✅ `main.js` - Complete product loading and rendering logic
- ✅ `styles.css` - All product card styling
- ✅ Loading states and error handling
- ✅ Lemon Squeezy checkout integration

### 2. **Documentation**
- ✅ `FASTAPI_BACKEND_EXAMPLE.md` - Complete FastAPI code example
- ✅ `LEMON_SQUEEZY_SETUP.md` - Original setup guide

## 🚀 Quick Start

### Step 1: Configure Frontend

Edit `js/main.js` (lines 184-185):

```javascript
const FASTAPI_URL = 'https://your-backend-url.com'; // Your FastAPI URL
const LEMON_SQUEEZY_STORE = 'your-store-name';      // Your Lemon Squeezy store
```

### Step 2: Set Up FastAPI Backend

See `FASTAPI_BACKEND_EXAMPLE.md` for complete code. Quick version:

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# IMPORTANT: Allow your GitHub Pages domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourusername.github.io"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/products")
async def get_products():
    # Fetch from Lemon Squeezy
    # Transform data
    # Return JSON
    return {"products": [...]}
```

### Step 3: Deploy FastAPI

Choose one:
- **Railway** (Easiest): `railway up`
- **Render**: Connect GitHub repo
- **Fly.io**: `fly deploy`
- **Your existing server**: Add endpoint to current FastAPI

### Step 4: Test

1. Open `curriculum.html` in browser
2. Check browser console for any errors
3. Products should load automatically!

## 📋 Product Data Format

Your FastAPI must return products in this format:

```json
{
  "products": [
    {
      "id": "prod_123",
      "variant_id": "456789",
      "name": "Premium License",
      "description": "Unlock all interactive learning tools",
      "image": "https://your-cdn.com/image.png",
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

## 🔧 Customization

### Add Custom Product Metadata

In your FastAPI, you can add custom logic to set badges, features, etc:

```python
def transform_product(product):
    # Check product tags or metadata
    badge = None
    if "popular" in product.get("tags", []):
        badge = "Most Popular"
    elif "best-value" in product.get("tags", []):
        badge = "Best Value"
    
    return {
        "badge": badge,
        # ... rest of product data
    }
```

### Change Loading Message

Edit `main.js` line ~290:

```javascript
productGrid.innerHTML = `
  <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
    <p style="font-size: 1.125rem; color: var(--muted);">
      Your custom loading message...
    </p>
  </div>
`;
```

### Add Caching

In your FastAPI (recommended for production):

```python
from datetime import datetime, timedelta

_cache = {"products": None, "timestamp": None}
CACHE_DURATION = timedelta(minutes=5)

async def get_cached_products():
    now = datetime.now()
    if (_cache["products"] is None or 
        now - _cache["timestamp"] > CACHE_DURATION):
        _cache["products"] = await fetch_lemon_squeezy_products()
        _cache["timestamp"] = now
    return _cache["products"]
```

## 🐛 Troubleshooting

### Products Not Loading

1. **Check browser console** for errors
2. **Verify CORS** - Your FastAPI must allow your GitHub Pages domain
3. **Test API directly** - Visit `https://your-backend.com/api/products`
4. **Check network tab** - See if request is being made

### CORS Errors

```python
# In your FastAPI, make sure you have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourusername.github.io",  # Your actual GitHub Pages URL
        "http://localhost:8000",           # For local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Products Show But Checkout Doesn't Work

1. **Check `LEMON_SQUEEZY_STORE`** in `main.js`
2. **Verify variant IDs** are correct in your API response
3. **Check browser console** for Lemon Squeezy errors

## 🎨 Benefits of This Approach

1. ✅ **No manual HTML editing** - Add products in Lemon Squeezy, they appear automatically
2. ✅ **Centralized management** - One place to manage all products
3. ✅ **Still fast** - Static site loads instantly, products load ~100ms later
4. ✅ **Secure** - API keys never exposed to frontend
5. ✅ **Flexible** - Easy to add filtering, sorting, categories, etc.
6. ✅ **Scalable** - Works with 1 product or 1000 products

## 🔐 Security Notes

- ✅ API keys stay on backend (never in frontend code)
- ✅ CORS restricts which domains can access your API
- ✅ GitHub Pages serves over HTTPS
- ✅ Lemon Squeezy handles all payment security

## 📈 Next Steps

1. **Deploy your FastAPI backend**
2. **Update `FASTAPI_URL` in `main.js`**
3. **Test locally first** (use localhost for FastAPI)
4. **Push to GitHub Pages**
5. **Add products in Lemon Squeezy**
6. **Watch them appear automatically!** 🎉

## 💡 Pro Tips

- Use product tags in Lemon Squeezy to control badges
- Store product images in Lemon Squeezy or a CDN
- Add caching to reduce API calls
- Consider adding product categories/filtering
- Monitor your FastAPI logs for errors

## 🆘 Need Help?

- Check `FASTAPI_BACKEND_EXAMPLE.md` for complete backend code
- Check `LEMON_SQUEEZY_SETUP.md` for Lemon Squeezy integration
- Look at browser console for frontend errors
- Check FastAPI logs for backend errors

---

**You're all set!** Your static GitHub Pages site can now dynamically load products from your FastAPI backend. 🚀
