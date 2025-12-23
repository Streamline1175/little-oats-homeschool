# 🛒 Shopping Cart System - Quick Start Guide

## ✅ What's Been Done

### Frontend (Your Website)
- ✅ Added beautiful cart UI with floating button
- ✅ Added cart sidebar with item list
- ✅ Changed "Buy Now" to "Add to Cart" buttons
- ✅ Added cart management (add/remove items)
- ✅ Added checkout functionality
- ✅ Mobile responsive design

### Files Modified
1. **`css/styles.css`** - Added 450+ lines of cart styling
2. **`curriculum.html`** - Added cart UI elements
3. **`js/main.js`** - Replaced simple cart with full system

### Files Created
1. **`CART_SYSTEM_DOCUMENTATION.md`** - Complete documentation
2. **`RPI_CODE_TO_ADD.py`** - Code to add to your RPI
3. **`RPI_BACKEND_CART_CHECKOUT.py`** - Full backend implementation reference

---

## 🚀 Next Steps (What You Need to Do)

### Step 1: Create Bundle Product in Lemon Squeezy
1. Go to https://app.lemonsqueezy.com
2. Navigate to Products → Create Product
3. Name it "Cart Bundle" or "Custom Order"
4. Set any price (will be overridden)
5. Save and note the **Variant ID**

**Finding Variant ID:**
- Option A: Check the URL when editing the variant
- Option B: Use the API:
  ```bash
  curl "https://api.lemonsqueezy.com/v1/variants?filter[product_id]=YOUR_PRODUCT_ID" \
    -H "Authorization: Bearer YOUR_API_KEY"
  ```

### Step 2: Update .env on RPI
SSH into your RPI and edit `.env`:
```bash
nano .env
```

Add this line:
```
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id_here
```

Save and exit (Ctrl+X, Y, Enter)

### Step 3: Update main.py on RPI
Open `main.py`:
```bash
nano main.py
```

Copy the code from `RPI_CODE_TO_ADD.py` and add it to your `main.py`:
1. Add the new models after your existing `Product` model
2. Add the `/api/checkout` endpoint after your `/api/products` endpoint

Save and exit.

### Step 4: Restart FastAPI Service
```bash
sudo systemctl restart your-fastapi-service
# Or if running manually: python main.py
```

### Step 5: Test It!
1. Open your website: https://littleoatlearners.com/curriculum.html
2. Click "Add to Cart" on a product
3. Cart sidebar should open
4. Add more products if desired
5. Click "Proceed to Checkout"
6. Should redirect to Lemon Squeezy checkout

---

## 📋 Quick Test Checklist

- [ ] Bundle product created in Lemon Squeezy
- [ ] Variant ID added to .env
- [ ] Code added to main.py
- [ ] FastAPI service restarted
- [ ] Can add items to cart
- [ ] Can remove items from cart
- [ ] Cart total calculates correctly
- [ ] Checkout button works
- [ ] Redirects to Lemon Squeezy
- [ ] Lemon Squeezy shows correct total
- [ ] Lemon Squeezy shows itemized list

---

## 🎨 How It Looks

### Cart Button (Bottom Right)
- Floating green button with cart icon
- Badge showing number of items
- Hover effect scales up

### Cart Sidebar (Slides from Right)
- Header with "Your Cart" title
- List of items with images and prices
- Remove button for each item
- Total price at bottom
- "Proceed to Checkout" button
- "Clear Cart" button

### Add to Cart Flow
1. Click "Add to Cart" → Button shows checkmark
2. Cart sidebar opens automatically
3. Item appears in cart list
4. Button resets after 2 seconds

---

## 🔧 Troubleshooting

### Cart button not visible
**Check:** Is `curriculum.html` loaded?
**Fix:** Refresh page, check browser console

### Checkout fails
**Check:** RPI logs
```bash
journalctl -u your-service -f
```
**Common issues:**
- Missing variant ID in .env
- Wrong API key
- Variant ID doesn't exist

### Items disappear on refresh
**Check:** Browser localStorage
**Fix:** Check browser console for errors

---

## 📞 Testing the Backend Directly

Before testing on the website, verify the backend works:

```bash
curl -X POST https://api.littleoatlearners.com/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": "test-1",
        "title": "Test Product",
        "price": "$29.00",
        "priceValue": 29.00
      },
      {
        "id": "test-2",
        "title": "Another Product",
        "price": "$19.00",
        "priceValue": 19.00
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "checkout_url": "https://little-oat-learners.lemonsqueezy.com/checkout/...",
  "total": 48.00,
  "item_count": 2
}
```

---

## 🎯 Key Features

✅ **Persistent Cart** - Saved in browser, survives page reloads
✅ **Beautiful UI** - Matches your existing design
✅ **Mobile Friendly** - Works on all devices
✅ **Bundled Checkout** - All items in one transaction
✅ **Itemized Receipt** - Customer sees all items
✅ **Error Handling** - Graceful error messages
✅ **Loading States** - Visual feedback

---

## 📚 Documentation Files

1. **`CART_SYSTEM_DOCUMENTATION.md`** - Full documentation
2. **`RPI_CODE_TO_ADD.py`** - Exact code for RPI
3. **`QUICK_START.md`** - This file

---

## 🎉 You're Almost Done!

Just need to:
1. Create bundle product in Lemon Squeezy (5 min)
2. Add variant ID to .env (1 min)
3. Copy code to main.py (5 min)
4. Restart service (1 min)
5. Test! (5 min)

**Total time: ~15-20 minutes**

---

**Questions?** Check `CART_SYSTEM_DOCUMENTATION.md` for detailed troubleshooting and customization options.
