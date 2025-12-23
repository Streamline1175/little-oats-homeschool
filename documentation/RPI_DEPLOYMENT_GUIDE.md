# 🚀 RPI Deployment Guide - Cart Checkout System

## Overview
This guide will help you deploy the updated `main.py` to your Raspberry Pi with the new cart checkout functionality.

---

## 📋 Pre-Deployment Checklist

### 1. Create Bundle Product in Lemon Squeezy

**Steps:**
1. Go to https://app.lemonsqueezy.com
2. Navigate to **Products** → **Create Product**
3. Fill in the details:
   - **Name:** "Cart Bundle" or "Custom Order"
   - **Price:** Any amount (will be overridden by custom_price)
   - **Description:** "Bundle product for cart checkouts"
4. Click **Save**
5. Note the **Variant ID**

**Finding Your Variant ID:**

**Option A - From Dashboard:**
- Click on the product you just created
- Look at the URL: `https://app.lemonsqueezy.com/products/PRODUCT_ID/variants/VARIANT_ID`
- The last number is your variant ID

**Option B - Using API:**
```bash
curl "https://api.lemonsqueezy.com/v1/variants?filter[product_id]=YOUR_PRODUCT_ID" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/vnd.api+json"
```

Look for the variant `id` in the response.

---

## 🔧 Deployment Steps

### Step 1: Backup Current Code

SSH into your RPI:
```bash
ssh pi@your-rpi-address
```

Backup your current main.py:
```bash
cd /path/to/your/fastapi/project
cp main.py main.py.backup
```

### Step 2: Update main.py

Replace your current `main.py` with the new version from `rpi-backend/main.py`:

**Option A - Copy/Paste:**
```bash
nano main.py
```
- Delete all content (Ctrl+K repeatedly)
- Paste the new code from `rpi-backend/main.py`
- Save (Ctrl+O, Enter, Ctrl+X)

**Option B - Upload via SCP:**
From your local machine:
```bash
scp rpi-backend/main.py pi@your-rpi-address:/path/to/your/fastapi/project/main.py
```

### Step 3: Update .env File

Edit your `.env` file:
```bash
nano .env
```

Add the new environment variable:
```bash
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id_here
```

Your complete `.env` should look like:
```bash
LEMON_SQUEEZY_API_KEY=lemon_api_xxxxxxxxxxxxx
LEMON_SQUEEZY_STORE_ID=12345
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=67890
NGROK_DOMAIN=your-domain.ngrok-free.app  # Optional
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

### Step 4: Verify Dependencies

Make sure you have all required packages:
```bash
pip install fastapi uvicorn httpx python-dotenv pydantic pyngrok
```

Or if using a virtual environment:
```bash
source venv/bin/activate  # Activate your venv
pip install fastapi uvicorn httpx python-dotenv pydantic pyngrok
```

### Step 5: Test the Code Locally

Before restarting the service, test the code:
```bash
python main.py
```

You should see:
```
🚀 Ngrok Tunnel Live at: https://your-domain.ngrok-free.app
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press Ctrl+C to stop.

### Step 6: Restart Your Service

If running as a systemd service:
```bash
sudo systemctl restart your-fastapi-service
```

Check status:
```bash
sudo systemctl status your-fastapi-service
```

If running manually:
```bash
# Stop the current process (if running)
# Then start it again:
python main.py
```

Or run in background:
```bash
nohup python main.py > output.log 2>&1 &
```

---

## ✅ Testing

### Test 1: Check API is Running

```bash
curl http://localhost:8000/
```

Expected response:
```json
{"status":"online","service":"Little Oat API"}
```

### Test 2: Check Products Endpoint

```bash
curl http://localhost:8000/api/products
```

Should return your products list.

### Test 3: Test Checkout Endpoint (Local)

```bash
curl -X POST http://localhost:8000/api/checkout \
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

### Test 4: Test from Public URL

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
      }
    ]
  }'
```

### Test 5: Test from Website

1. Open https://littleoatlearners.com/curriculum.html
2. Click "Add to Cart" on a product
3. Cart sidebar should open
4. Add more products if desired
5. Click "Proceed to Checkout"
6. Should redirect to Lemon Squeezy checkout
7. Verify the checkout shows:
   - Correct total
   - Itemized list of products
   - "Your Order (X items)" as product name

---

## 🔍 Troubleshooting

### Issue: "Lemon Squeezy configuration missing"

**Cause:** Missing environment variables

**Fix:**
```bash
nano .env
# Verify all three variables are set:
# LEMON_SQUEEZY_API_KEY
# LEMON_SQUEEZY_STORE_ID
# LEMON_SQUEEZY_BUNDLE_VARIANT_ID
```

Restart service after updating.

### Issue: "Failed to create checkout: 404"

**Cause:** Invalid variant ID

**Fix:**
1. Verify the variant ID is correct
2. Check that the product exists in Lemon Squeezy
3. Ensure the variant belongs to your store

### Issue: Service won't start

**Check logs:**
```bash
sudo journalctl -u your-fastapi-service -n 50
```

**Common issues:**
- Syntax error in main.py
- Missing dependencies
- Port 8000 already in use

### Issue: Checkout URL not opening on website

**Check:**
1. Browser console for errors (F12)
2. Network tab - is the POST request succeeding?
3. Is the response valid JSON?
4. Is CORS configured correctly? (should be with `allow_origins=["*"]`)

---

## 📊 Monitoring

### View Logs in Real-Time

```bash
# If using systemd
sudo journalctl -u your-fastapi-service -f

# If running manually
tail -f output.log
```

### Check for Errors

```bash
# Last 100 lines
sudo journalctl -u your-fastapi-service -n 100

# Errors only
sudo journalctl -u your-fastapi-service -p err
```

---

## 🔄 Rollback (If Needed)

If something goes wrong, restore the backup:

```bash
cd /path/to/your/fastapi/project
cp main.py.backup main.py
sudo systemctl restart your-fastapi-service
```

---

## 📝 What Changed

### New Models Added
- `CartItem` - Represents an item in the cart
- `CheckoutRequest` - Request body for checkout
- `CheckoutResponse` - Response with checkout URL

### New Endpoint Added
- `POST /api/checkout` - Creates bundled Lemon Squeezy checkout

### Environment Variables Added
- `LEMON_SQUEEZY_BUNDLE_VARIANT_ID` - Variant ID for bundle product

### No Breaking Changes
- All existing endpoints still work
- `/api/products` unchanged
- Backward compatible

---

## ✨ Success Indicators

You'll know everything is working when:

- ✅ Service starts without errors
- ✅ `/api/products` returns products
- ✅ `/api/checkout` returns checkout URL
- ✅ Website can add items to cart
- ✅ Checkout redirects to Lemon Squeezy
- ✅ Lemon Squeezy shows correct total and items

---

## 📞 Support

If you encounter issues:

1. **Check logs first:**
   ```bash
   sudo journalctl -u your-fastapi-service -n 100
   ```

2. **Verify environment variables:**
   ```bash
   cat .env
   ```

3. **Test endpoints directly:**
   ```bash
   curl http://localhost:8000/api/products
   ```

4. **Check Lemon Squeezy dashboard:**
   - Verify product exists
   - Verify variant ID is correct
   - Check API key permissions

---

## 🎉 Post-Deployment

After successful deployment:

1. **Test the full flow:**
   - Add multiple products to cart
   - Proceed to checkout
   - Complete a test purchase

2. **Monitor for a few hours:**
   - Watch logs for errors
   - Test from different devices
   - Verify cart persistence

3. **Update documentation:**
   - Note the variant ID for future reference
   - Document any custom changes

---

## 📁 File Locations

```
Your RPI Project Structure:
├── main.py              ← Updated with cart checkout
├── .env                 ← Add LEMON_SQUEEZY_BUNDLE_VARIANT_ID
├── main.py.backup       ← Backup of old version
└── output.log           ← Logs (if running manually)
```

---

**Deployment Time Estimate:** 10-15 minutes

**Ready to deploy?** Follow the steps above in order, and you'll have the cart checkout system running in no time! 🚀
