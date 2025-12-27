# Simplified Lemon Squeezy Integration Plan

## Current Situation
- Cart Bundle approach doesn't work for file downloads
- Custom emails are complex to maintain
- Download links not available in test mode

## ✅ Recommended Solution: Use Lemon Squeezy's Built-In System

### What This Means:
1. **Remove** custom email sending code
2. **Use** Lemon Squeezy's default order confirmation emails
3. **Direct** customers to Lemon Squeezy's "My Orders" page for downloads
4. **Keep** your custom cart and thank-you page for branding

### Implementation Options:

#### **Option A: Single Product Checkouts** (Simplest)
- Each product purchased separately
- Customer completes multiple checkouts (one per item)
- Each order has files attached
- Lemon Squeezy sends separate emails for each

**Pros:**
- ✅ Simple to implement
- ✅ Files work correctly
- ✅ No custom code needed

**Cons:**
- ❌ Multiple checkout steps
- ❌ Multiple emails

#### **Option B: Use Buy Now URLs** (Recommended)
- Use each product's `buy_now_url` from Lemon Squeezy
- For single items: redirect directly
- For multiple items: create a multi-checkout page

**Pros:**
- ✅ Uses Lemon Squeezy's built-in system
- ✅ No API calls needed
- ✅ Files work correctly

**Cons:**
- ❌ Need to create multi-checkout page
- ❌ Multiple purchases for cart

#### **Option C: Keep Cart Bundle, Remove Custom Email**
- Keep current cart bundle approach
- Remove custom email code
- Let Lemon Squeezy send default email
- Accept that downloads won't work in test mode

**Pros:**
- ✅ Single checkout
- ✅ Minimal code changes

**Cons:**
- ❌ No file downloads (Cart Bundle has no files)
- ❌ Not a real solution

## 🎯 My Recommendation: Option B

### Implementation Steps:
1. Update products API to include `buy_now_url`
2. For single item: Use buy_now_url directly
3. For multiple items: Create `multi-checkout.html` page that:
   - Shows all items
   - Has "Buy" button for each
   - Tracks which ones are purchased
   - Redirects to thank-you page when all done

### Code Changes Needed:
- ✅ Products API: Already returns `buyUrl`
- ✅ Checkout endpoint: Simplified (done)
- ⏳ Frontend: Update to handle buy_now_urls
- ⏳ Create: `multi-checkout.html` page
- ❌ Remove: Custom email code
- ❌ Remove: Webhook email sending

### Customer Experience:
1. Add 3 items to cart
2. Click "Checkout"
3. Redirected to multi-checkout page
4. Click "Buy" for each product (3 separate Lemon Squeezy checkouts)
5. Lemon Squeezy sends 3 order confirmation emails
6. Customer accesses downloads from "My Orders" page
7. Thank-you page shows summary

## Next Steps:
1. Decide on approach
2. I'll implement the chosen solution
3. Test with real products
4. Deploy

