# 🛒 Cart Bundle Product Setup Guide

## 🎯 Overview

The "Cart Bundle" product is a **special technical product** used only by your backend to create custom checkouts. It should **never be shown to customers** on your website or desktop app.

---

## 📝 **Lemon Squeezy Product Setup**

### **Step 1: Create the Product**

Go to your Lemon Squeezy dashboard → Products → Create Product

### **Step 2: Fill Out the Form**

#### **Basic Information**

| Field | Value | Notes |
|-------|-------|-------|
| **Product Name** | `Cart Bundle` | ⚠️ Must contain "cart bundle" for filtering |
| **Description** | `Internal use only - for cart checkout system. Do not delete.` | Helps you remember its purpose |
| **Status** | ✅ **Published** | Must be published for API access |

#### **Pricing**

| Field | Value | Notes |
|-------|-------|-------|
| **Price** | `$1.00` | Doesn't matter - overridden by `custom_price` |
| **Pricing Type** | One-time payment | Required |
| **Currency** | USD (or your currency) | Match your other products |

#### **Media**

| Field | Value | Notes |
|-------|-------|-------|
| **Product Image** | Leave blank or use placeholder | Customers never see this |
| **Thumbnail** | Leave blank | Not needed |

#### **Product Files/Downloads**

| Field | Value | Notes |
|-------|-------|-------|
| **Files** | ❌ **Leave empty** | This product doesn't deliver files |
| | | Actual cart items have their own files |

#### **Additional Settings**

| Field | Value | Notes |
|-------|-------|-------|
| **Visibility** | Published | API needs access |
| **Category** | (Optional) "System" | For your organization |
| **Tags** | `internal`, `system` | Helps identify it |

---

## 🔑 **Get the Variant ID**

After creating the product:

### **Option A: From URL**
1. Click on the product
2. Look at the URL: `https://app.lemonsqueezy.com/products/PRODUCT_ID/variants/VARIANT_ID`
3. Copy the **VARIANT_ID** (the last number)

### **Option B: From API**
```bash
curl "https://api.lemonsqueezy.com/v1/variants?filter[product_id]=YOUR_PRODUCT_ID" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/vnd.api+json"
```

Look for the variant `id` in the response.

### **Add to .env**
```bash
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id_here
```

---

## 🚫 **Filtering from Website & Desktop App**

The Cart Bundle product is automatically filtered out by the updated backend code.

### **How It Works:**

The `/api/products` endpoint now skips products with these keywords in the name:
- `"cart bundle"`
- `"custom order"`
- `"internal"`
- `"system"`

### **Code (Already Updated):**

```python
# Skip internal/system products
if any(keyword in name_lower for keyword in ["cart bundle", "custom order", "internal", "system"]):
    print(f"⏭️  Skipping internal product: {product_name}")
    continue
```

### **What This Means:**

✅ **Website:** Cart Bundle won't appear in product grid  
✅ **Desktop App:** Cart Bundle won't appear in shop  
✅ **Backend:** Can still use it for checkout API  
✅ **Logs:** You'll see "⏭️ Skipping internal product: Cart Bundle"

---

## ✅ **Verification Checklist**

### **In Lemon Squeezy Dashboard:**
- [ ] Product created with name "Cart Bundle"
- [ ] Status is "Published"
- [ ] Price is set (any amount)
- [ ] Variant ID copied
- [ ] No files attached

### **In RPI .env:**
- [ ] `LEMON_SQUEEZY_BUNDLE_VARIANT_ID` added
- [ ] Value is the variant ID (not product ID)
- [ ] Service restarted after adding

### **On Website:**
- [ ] Visit curriculum.html
- [ ] Cart Bundle does NOT appear
- [ ] Only real products are shown
- [ ] Cart functionality works

### **In Desktop App:**
- [ ] Open shop section
- [ ] Cart Bundle does NOT appear
- [ ] Only real products are shown

### **In Logs:**
- [ ] See "⏭️ Skipping internal product: Cart Bundle"
- [ ] Other products load normally

---

## 🧪 **Testing**

### **Test 1: Verify Filtering**

```bash
# Check RPI logs when products load
ssh pi@your-rpi
sudo journalctl -u your-service -f
```

You should see:
```
⏭️  Skipping internal product: Cart Bundle
```

### **Test 2: Check Website**

1. Open https://littleoatlearners.com/curriculum.html
2. Verify Cart Bundle is NOT visible
3. Verify real products ARE visible

### **Test 3: Check API Response**

```bash
curl https://api.littleoatlearners.com/api/products
```

Response should NOT include Cart Bundle.

### **Test 4: Verify Checkout Still Works**

1. Add products to cart
2. Click "Proceed to Checkout"
3. Should create checkout successfully
4. Cart Bundle is used behind the scenes

---

## 🎯 **Product Naming Guidelines**

To ensure proper filtering, follow these rules:

### **✅ Good Names (Will be filtered):**
- `Cart Bundle`
- `Custom Order`
- `Internal - Cart System`
- `System Product`

### **❌ Bad Names (Won't be filtered):**
- `Bundle` (too generic)
- `Special Offer` (doesn't contain keywords)
- `Multi-Item` (doesn't contain keywords)

### **Recommended:**
Use **"Cart Bundle"** - it's clear, descriptive, and will be filtered.

---

## 🔧 **Troubleshooting**

### **Problem: Cart Bundle appears on website**

**Cause:** Product name doesn't contain filter keywords

**Fix:** 
1. Rename product in Lemon Squeezy to "Cart Bundle"
2. Wait a few seconds for cache to clear
3. Refresh website

### **Problem: Checkout fails with "variant not found"**

**Cause:** Wrong variant ID in `.env`

**Fix:**
1. Verify variant ID in Lemon Squeezy dashboard
2. Update `.env` with correct ID
3. Restart service

### **Problem: Product not published**

**Cause:** Product status is "Draft"

**Fix:**
1. Go to Lemon Squeezy dashboard
2. Edit Cart Bundle product
3. Change status to "Published"
4. Save

---

## 📊 **How It's Used**

### **Normal Product Flow:**
```
Customer → Clicks "Buy Now" → Lemon Squeezy Checkout → Purchase
```

### **Cart Bundle Flow:**
```
Customer → Adds to cart → Clicks "Proceed to Checkout"
    ↓
Backend creates custom checkout using Cart Bundle
    ↓
Sets custom_price = total of cart items
    ↓
Sets description = itemized list
    ↓
Customer → Lemon Squeezy Checkout → Purchase
```

**Key Point:** Cart Bundle is just a "container" - the actual products and prices come from the cart.

---

## 💡 **Why This Approach?**

### **Lemon Squeezy Limitation:**
- Can't create checkout for multiple different products at once
- Each checkout must be for a single product/variant

### **Our Solution:**
- Create one "bundle" product
- Use `custom_price` to set the total
- Use `product_options.description` to show itemized list
- Store actual items in `checkout_data.custom`

### **Result:**
- ✅ Customers can buy multiple items at once
- ✅ Single transaction
- ✅ Itemized list visible
- ✅ Professional experience

---

## 📝 **Quick Reference**

### **Product Settings:**
```
Name: Cart Bundle
Description: Internal use only - for cart checkout system
Status: Published
Price: $1.00 (any amount)
Files: None
```

### **Environment Variable:**
```bash
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id
```

### **Filter Keywords:**
```python
["cart bundle", "custom order", "internal", "system"]
```

---

## ✅ **Summary**

1. **Create** "Cart Bundle" product in Lemon Squeezy
2. **Set** status to Published
3. **Copy** variant ID
4. **Add** to `.env` as `LEMON_SQUEEZY_BUNDLE_VARIANT_ID`
5. **Verify** it's filtered from website/app
6. **Test** cart checkout works

**Result:** Backend can create custom checkouts, but customers never see the Cart Bundle product!

---

## 🎉 **You're Done!**

The Cart Bundle product is now:
- ✅ Created in Lemon Squeezy
- ✅ Configured correctly
- ✅ Filtered from customer view
- ✅ Ready for cart checkouts

**Next:** Test the complete cart flow to verify everything works!

---

**Questions?** Check the logs for "⏭️ Skipping internal product" to verify filtering is working!
