# Raspberry Pi FastAPI Integration - Quick Setup

Since you already have a FastAPI backend running on your Raspberry Pi with a products endpoint, here's exactly what you need to do:

## ✅ Required Changes

### 1. Update `js/main.js` (Lines 186-187)

Replace these two values:

```javascript
const FASTAPI_URL = 'http://your-rpi-ip:port';
const LEMON_SQUEEZY_STORE = 'YOUR_STORE';
```

**With your actual values:**

```javascript
const FASTAPI_URL = 'http://YOUR_RPI_IP:YOUR_PORT';  // e.g., http://192.168.1.100:8000
const LEMON_SQUEEZY_STORE = 'your-actual-store-name'; // Your Lemon Squeezy store name
```

### 2. Enable CORS on Your Raspberry Pi FastAPI

Your FastAPI needs to allow requests from GitHub Pages. Add this to your FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourusername.github.io",  # Your GitHub Pages URL
        "http://localhost:8000",           # For local testing
        "*"                                 # Or use "*" for development (not recommended for production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📋 Expected API Response Format

Your existing endpoint should return products in this format:

```json
{
  "products": [
    {
      "id": "prod_123",
      "variant_id": "456789",
      "name": "Premium License",
      "description": "Unlock all interactive learning tools",
      "image": "https://url-to-image.png",
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
      "badge": "Most Popular"  // Optional
    }
  ]
}
```

## 🔍 What the Frontend Expects

The JavaScript in `main.js` will:

1. **Fetch** from `${FASTAPI_URL}/api/products`
2. **Parse** the JSON response
3. **Extract** `data.products` or just `data` (handles both formats)
4. **Create** product cards for each product
5. **Initialize** Lemon Squeezy checkout buttons

## 🛠️ If Your API Format is Different

If your existing endpoint returns data in a different format, you have two options:

### Option A: Adjust Your FastAPI (Recommended)

Make sure your endpoint returns the format above.

### Option B: Modify the Frontend Parser

Edit `js/main.js` around line 200:

```javascript
async function fetchProducts() {
  try {
    const response = await fetch(`${FASTAPI_URL}/api/products`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    // MODIFY THIS LINE to match your API response structure
    return data.products || data;  // Change based on your format
    
  } catch (error) {
    console.error('Error fetching products:', error);
    return null;
  }
}
```

## 🌐 Network Considerations

### If Your RPI is on Local Network:

**Problem**: GitHub Pages (HTTPS) can't fetch from local HTTP URLs due to mixed content security.

**Solutions**:

1. **Use HTTPS** on your RPI (recommended):
   - Set up Let's Encrypt with a domain
   - Or use a reverse proxy like Cloudflare Tunnel

2. **Use ngrok** (quick testing):
   ```bash
   ngrok http 8000
   ```
   Then use the ngrok HTTPS URL in `FASTAPI_URL`

3. **Test locally first**:
   - Open `curriculum.html` as a local file
   - Browser will allow HTTP requests

### If Your RPI has a Public Domain/IP:

Just use that URL directly:
```javascript
const FASTAPI_URL = 'https://yourdomain.com';
// or
const FASTAPI_URL = 'http://your-public-ip:8000';
```

## ✅ Testing Checklist

1. **Test your API directly**:
   ```bash
   curl http://your-rpi-ip:port/api/products
   ```
   Should return JSON with products.

2. **Check CORS**:
   Open browser console on GitHub Pages and look for CORS errors.

3. **Verify product format**:
   Make sure your API returns the expected structure.

4. **Test Lemon Squeezy**:
   Click "Buy Now" buttons to ensure checkout opens.

## 🐛 Common Issues

### Issue: "Mixed Content" Error
**Cause**: GitHub Pages (HTTPS) can't fetch from HTTP URLs  
**Fix**: Use HTTPS for your RPI or test locally

### Issue: CORS Error
**Cause**: Your FastAPI doesn't allow GitHub Pages domain  
**Fix**: Add CORS middleware (see step 2 above)

### Issue: Products Not Loading
**Cause**: Wrong URL or API format  
**Fix**: Check browser console, verify URL and response format

### Issue: Checkout Not Working
**Cause**: Wrong store name or variant IDs  
**Fix**: Update `LEMON_SQUEEZY_STORE` and verify variant IDs in API response

## 🚀 Quick Start Commands

1. **Update `js/main.js`** with your RPI URL and store name
2. **Add CORS** to your FastAPI
3. **Restart** your FastAPI server
4. **Test** by opening `curriculum.html`
5. **Push** to GitHub Pages
6. **Done!** 🎉

## 📝 Example Values

If your setup is:
- RPI IP: `192.168.1.100`
- FastAPI Port: `8000`
- Store Name: `littleoat`

Then update `main.js` to:

```javascript
const FASTAPI_URL = 'http://192.168.1.100:8000';
const LEMON_SQUEEZY_STORE = 'littleoat';
```

---

**That's it!** Just update those 2 values and ensure CORS is enabled. Your products will load automatically! 🌾
