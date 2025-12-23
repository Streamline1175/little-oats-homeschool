# Shopping Cart Checkout System - Implementation Guide

## Overview

You now have a complete shopping cart system that allows users to:
1. Browse products on your website
2. Add multiple items to a cart
3. Review their cart in a beautiful sidebar
4. Checkout all items at once via Lemon Squeezy

## How It Works

### Frontend Flow
1. User clicks "Add to Cart" on a product
2. Product is added to localStorage cart
3. Cart sidebar opens showing all items
4. User can add more items, remove items, or proceed to checkout
5. On checkout, cart data is sent to your FastAPI backend
6. Backend creates a bundled Lemon Squeezy checkout
7. User is redirected to Lemon Squeezy to complete payment

### Backend Flow
1. Receives cart items from frontend
2. Calculates total price
3. Creates itemized description of all products
4. Uses Lemon Squeezy API to create a custom checkout with:
   - Custom price (sum of all items)
   - Custom product name ("Your Order (X items)")
   - Custom description (itemized list of products)
5. Returns checkout URL to frontend

## Files Modified

### 1. `/css/styles.css`
**Added:** Complete cart UI styling (450+ lines)
- Floating cart button
- Cart sidebar modal
- Cart items list
- Checkout button
- Mobile responsive design

### 2. `/curriculum.html`
**Added:** Cart UI elements
- Cart overlay
- Cart sidebar structure
- Floating cart button
- All necessary HTML for cart functionality

### 3. `/js/main.js`
**Modified:** Cart system (replaced simple cart with full system)
- Cart state management
- Add/remove items
- Calculate totals
- Render cart UI
- Checkout via API
- Product card creation with "Add to Cart" buttons

## Setup Instructions for Raspberry Pi

### Step 1: Create a Bundle Product in Lemon Squeezy

1. Log into your Lemon Squeezy dashboard
2. Go to Products → Create Product
3. Create a product called "Cart Bundle" or "Custom Order"
4. Set any default price (it will be overridden)
5. Save the product
6. Note the **Variant ID** (you'll need this)

**To find your Variant ID:**
```bash
curl -X GET "https://api.lemonsqueezy.com/v1/variants?filter[product_id]=YOUR_PRODUCT_ID" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/vnd.api+json"
```

Or check the URL when editing the product variant in your dashboard.

### Step 2: Update Your .env File

Add this line to your `.env` file on the RPI:
```bash
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id_here
```

Your complete `.env` should have:
```bash
LEMON_SQUEEZY_API_KEY=your_api_key
LEMON_SQUEEZY_STORE_ID=your_store_id
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_bundle_variant_id
NGROK_DOMAIN=your_ngrok_domain (optional)
```

### Step 3: Add the Checkout Endpoint to main.py

Open your `main.py` on the RPI and add the code from `RPI_BACKEND_CART_CHECKOUT.py`:

1. Add the new models at the top (after your existing imports):
```python
class CartItem(BaseModel):
    id: str
    title: str
    price: str
    priceValue: float
    image: Optional[str] = None

class CheckoutRequest(BaseModel):
    items: List[CartItem]

class CheckoutResponse(BaseModel):
    checkout_url: str
    total: float
    item_count: int
```

2. Add the checkout endpoint (after your `/api/products` endpoint):
```python
@app.post("/api/checkout", response_model=CheckoutResponse)
async def create_checkout(request: CheckoutRequest):
    # ... (copy the entire function from RPI_BACKEND_CART_CHECKOUT.py)
```

### Step 4: Restart Your FastAPI Service

```bash
# If running with systemd
sudo systemctl restart your-fastapi-service

# Or if running manually
# Stop the current process (Ctrl+C) and restart:
python main.py
```

### Step 5: Test the System

1. **Test the checkout endpoint directly:**
```bash
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
```

Expected response:
```json
{
  "checkout_url": "https://little-oat-learners.lemonsqueezy.com/checkout/...",
  "total": 29.00,
  "item_count": 1
}
```

2. **Test on your website:**
   - Open `curriculum.html`
   - Add a product to cart
   - Click the floating cart button
   - Review items in cart
   - Click "Proceed to Checkout"
   - Should redirect to Lemon Squeezy checkout

## Features

### ✅ What's Included

- **Persistent Cart:** Cart saved in localStorage, persists across page reloads
- **Beautiful UI:** Premium design matching your existing site
- **Add to Cart:** Visual feedback when adding items
- **Remove Items:** Easy removal from cart
- **Clear Cart:** One-click cart clearing with confirmation
- **Item Count Badge:** Shows number of items in cart
- **Total Calculation:** Automatic price calculation
- **Bundled Checkout:** All items in one transaction
- **Itemized Receipt:** Lemon Squeezy checkout shows all items
- **Mobile Responsive:** Works perfectly on all devices
- **Error Handling:** Graceful error messages
- **Loading States:** Visual feedback during checkout

### 🎨 User Experience

1. **Adding Items:**
   - Click "Add to Cart"
   - Button shows checkmark and "Added to Cart!"
   - Cart sidebar opens automatically
   - Item appears in cart list

2. **Managing Cart:**
   - Click floating cart button to open/close
   - See all items with images and prices
   - Remove individual items with trash icon
   - Clear entire cart with "Clear Cart" button
   - See live total calculation

3. **Checkout:**
   - Click "Proceed to Checkout"
   - Button shows loading spinner
   - Redirected to Lemon Squeezy
   - Cart cleared after successful redirect

## Customization Options

### Change Cart Button Position
In `/css/styles.css`, find `.cart-button` and modify:
```css
.cart-button {
  bottom: 2rem;  /* Change this */
  right: 2rem;   /* Change this */
}
```

### Change Checkout Redirect URL
In `RPI_BACKEND_CART_CHECKOUT.py`, modify:
```python
"redirect_url": "https://littleoatlearners.com/thank-you",
```

### Customize Cart Colors
In `/css/styles.css`, modify the CSS variables or specific cart styles.

## Troubleshooting

### Cart button not appearing
- Check browser console for errors
- Ensure `curriculum.html` has the cart button HTML
- Verify CSS is loaded

### Checkout fails
- Check RPI logs: `journalctl -u your-service -f`
- Verify `.env` has all required variables
- Test API endpoint directly with curl
- Check Lemon Squeezy API key permissions

### Items not persisting
- Check browser localStorage (DevTools → Application → Local Storage)
- Ensure JavaScript is enabled
- Check for console errors

### Checkout URL not opening
- Verify Lemon Squeezy script is loaded
- Check network tab for API response
- Ensure variant ID is correct

## API Reference

### POST /api/checkout

**Request:**
```json
{
  "items": [
    {
      "id": "prod_123",
      "title": "Product Name",
      "price": "$29.00",
      "priceValue": 29.00,
      "image": "https://..."
    }
  ]
}
```

**Response:**
```json
{
  "checkout_url": "https://...",
  "total": 29.00,
  "item_count": 1
}
```

**Errors:**
- `400`: Cart is empty
- `500`: Lemon Squeezy configuration missing or API error

## Next Steps

1. ✅ Deploy frontend changes to GitHub Pages
2. ✅ Update RPI backend with checkout endpoint
3. ✅ Create bundle product in Lemon Squeezy
4. ✅ Add variant ID to .env
5. ✅ Test end-to-end flow
6. 📝 Consider adding:
   - Email confirmation with itemized list
   - Discount codes
   - Quantity selection
   - Save cart for later
   - Guest checkout tracking

## Support

If you encounter issues:
1. Check browser console for frontend errors
2. Check RPI logs for backend errors
3. Verify all environment variables are set
4. Test API endpoint directly
5. Check Lemon Squeezy dashboard for checkout creation

---

**Built with ❤️ for Little Oat Learners**
