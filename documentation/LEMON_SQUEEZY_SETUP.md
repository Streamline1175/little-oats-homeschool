# Lemon Squeezy Integration Guide

## 🎯 What We've Built

You now have a beautiful, dedicated shop page (`curriculum.html`) with:
- 6 product cards ready for your Lemon Squeezy products
- Professional pricing displays
- Trust badges for security
- Responsive design that looks great on all devices
- Automatic Lemon Squeezy checkout integration

## 🔧 How to Connect Your Products

### Step 1: Get Your Lemon Squeezy Product IDs

1. Log into your Lemon Squeezy dashboard
2. Go to **Products** → Select a product
3. Click on **Variants** 
4. Copy the **Variant ID** (it looks like: `123456`)

### Step 2: Update the Product Cards

Open `curriculum.html` and find each product card. Replace `YOUR_PRODUCT_ID` with your actual variant ID:

```html
<!-- BEFORE -->
<a href="#" class="btn primary full lemonsqueezy-button" data-product-id="YOUR_PRODUCT_ID">
    Buy Now
</a>

<!-- AFTER (example with variant ID 123456) -->
<a href="#" class="btn primary full lemonsqueezy-button" data-product-id="123456">
    Buy Now
</a>
```

### Step 3: Update Your Store Name in JavaScript

Open `js/main.js` and find this line (around line 206):

```javascript
const checkoutUrl = `https://YOUR_STORE.lemonsqueezy.com/checkout/buy/${productId}`;
```

Replace `YOUR_STORE` with your actual Lemon Squeezy store name:

```javascript
const checkoutUrl = `https://littleoat.lemonsqueezy.com/checkout/buy/${productId}`;
```

### Step 4: Customize Product Information

For each product card in `curriculum.html`, update:
- **Product name** (`<h3>` tag)
- **Description** (`.product-description` paragraph)
- **Features** (list items in `.product-features`)
- **Price** (`.price` span)
- **Images** (update `src` attribute to your product images)

## 📝 Product Card Template

Here's a template for adding new products:

```html
<article class="product-card">
    <!-- Optional badge -->
    <div class="product-badge">Most Popular</div>
    
    <div class="product-image">
        <img src="assets/your-image.png" alt="Product Name" loading="lazy">
    </div>
    
    <div class="product-content">
        <h3>Your Product Name</h3>
        <p class="product-description">Your product description goes here.</p>
        
        <ul class="product-features">
            <li>Feature 1</li>
            <li>Feature 2</li>
            <li>Feature 3</li>
            <li>Feature 4</li>
        </ul>
        
        <div class="product-pricing">
            <div class="price-option featured">
                <span class="price">$XX.XX</span>
                <span class="period">one-time</span>
            </div>
        </div>
        
        <a href="#" class="btn primary full lemonsqueezy-button" data-product-id="YOUR_VARIANT_ID">
            Buy Now
        </a>
    </div>
</article>
```

## 🎨 Pricing Options

### Single Price
```html
<div class="product-pricing">
    <div class="price-option featured">
        <span class="price">$49.99</span>
        <span class="period">one-time</span>
    </div>
</div>
```

### Multiple Price Options (Monthly vs Lifetime)
```html
<div class="product-pricing">
    <div class="price-options">
        <div class="price-option">
            <span class="price">$9.99</span>
            <span class="period">/month</span>
        </div>
        <div class="price-option featured">
            <span class="price">$79.99</span>
            <span class="period">lifetime</span>
            <span class="savings">Save 33%</span>
        </div>
    </div>
</div>
```

## 🚀 Testing

1. Open `curriculum.html` in your browser
2. Click a "Buy Now" button
3. You should see the Lemon Squeezy checkout overlay open
4. If it opens in a new tab instead, the Lemon Squeezy script is still loading (this is normal on first load)

## 📱 What's Already Working

- ✅ Responsive design (looks great on mobile, tablet, desktop)
- ✅ Hover effects and animations
- ✅ Trust badges for security
- ✅ Navigation between pages
- ✅ Lemon Squeezy checkout integration
- ✅ Professional product cards

## 🎯 Next Steps

1. Replace all `YOUR_PRODUCT_ID` placeholders with real variant IDs
2. Update product names, descriptions, and prices
3. Add your own product images
4. Update the store name in `main.js`
5. Test the checkout flow
6. Go live! 🎉

## 💡 Tips

- The "Most Popular" and "Best Value" badges are optional - remove the `<div class="product-badge">` if you don't want them
- You can add as many products as you want - just copy the product card template
- The trust section at the bottom builds confidence with customers
- All styling is in `css/styles.css` if you want to customize colors or spacing

## 🔗 Useful Links

- [Lemon Squeezy Documentation](https://docs.lemonsqueezy.com/)
- [Lemon Squeezy Checkout Overlay](https://docs.lemonsqueezy.com/help/checkout/checkout-overlay)
- [Getting Variant IDs](https://docs.lemonsqueezy.com/api/variants)

---

Need help? Check the comments in the code or reach out!
