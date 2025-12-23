(function () {
  const navLinks = document.getElementById('nav-links');
  const menuToggle = document.querySelector('.menu-toggle');
  const dropdown = document.querySelector('.has-dropdown');
  const dropdownToggle = document.querySelector('.dropdown-toggle');

  function closeMenus() {
    navLinks.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
    dropdown.classList.remove('open');
    dropdownToggle.setAttribute('aria-expanded', 'false');
  }

  menuToggle?.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
  });

  dropdownToggle?.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.toggle('open');
    dropdownToggle.setAttribute('aria-expanded', String(isOpen));
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove('open');
      dropdownToggle.setAttribute('aria-expanded', 'false');
    }
  });

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        closeMenus();
      }
    });
  });

  const form = document.querySelector('.contact-form');
  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Thanks for reaching out! We will reply soon.');
  });

  // ==================== Shopping Cart System ====================
  const CART_STORAGE_KEY = 'little-oat-cart';
  const FASTAPI_CHECKOUT_URL = 'https://api.littleoatlearners.com/api/checkout';

  // Cart state
  let cart = [];

  // DOM elements
  const cartButton = document.getElementById('cart-button');
  const cartSidebar = document.getElementById('cart-sidebar');
  const cartOverlay = document.getElementById('cart-overlay');
  const cartClose = document.getElementById('cart-close');
  const cartBody = document.getElementById('cart-body');
  const cartFooter = document.getElementById('cart-footer');
  const cartCount = document.getElementById('cart-count');
  const cartItemsCount = document.getElementById('cart-items-count');
  const cartTotal = document.getElementById('cart-total');
  const cartCheckoutBtn = document.getElementById('cart-checkout-btn');
  const cartClearBtn = document.getElementById('cart-clear-btn');

  /**
   * Load cart from localStorage
   */
  function loadCart() {
    try {
      const stored = localStorage.getItem(CART_STORAGE_KEY);
      cart = stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('Error loading cart:', e);
      cart = [];
    }
    renderCart();
  }

  /**
   * Save cart to localStorage
   */
  function saveCart() {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
    } catch (e) {
      console.error('Error saving cart:', e);
    }
    renderCart();
  }

  /**
   * Add item to cart
   */
  function addToCart(product) {
    // Check if item already exists
    const existingIndex = cart.findIndex(item => item.id === product.id);

    if (existingIndex >= 0) {
      // Item already in cart - show feedback
      return false;
    }

    cart.push({
      id: product.id,
      title: product.title,
      price: product.price,
      priceValue: parsePrice(product.price),
      image: product.image || 'assets/placeholder.png'
    });

    saveCart();
    return true;
  }

  /**
   * Remove item from cart
   */
  function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    saveCart();
  }

  /**
   * Clear entire cart
   */
  function clearCart() {
    if (cart.length === 0) return;

    if (confirm('Are you sure you want to clear your cart?')) {
      cart = [];
      saveCart();
    }
  }

  /**
   * Parse price string to number
   */
  function parsePrice(priceStr) {
    // Remove currency symbols and parse
    const cleaned = priceStr.replace(/[^0-9.]/g, '');
    return parseFloat(cleaned) || 0;
  }

  /**
   * Calculate cart total
   */
  function calculateTotal() {
    return cart.reduce((sum, item) => sum + item.priceValue, 0);
  }

  /**
   * Format price for display
   */
  function formatPrice(value) {
    return `$${value.toFixed(2)}`;
  }

  /**
   * Render cart UI
   */
  function renderCart() {
    // Update cart count badges
    const itemCount = cart.length;
    if (cartCount) cartCount.textContent = itemCount;
    if (cartItemsCount) cartItemsCount.textContent = itemCount;

    // Update total
    const total = calculateTotal();
    if (cartTotal) cartTotal.textContent = formatPrice(total);

    // Show/hide footer
    if (cartFooter) {
      cartFooter.style.display = itemCount > 0 ? 'block' : 'none';
    }

    // Render cart items
    if (!cartBody) return;

    if (itemCount === 0) {
      cartBody.innerHTML = `
        <div class="cart-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          <h3>Your cart is empty</h3>
          <p>Add some products to get started!</p>
        </div>
      `;
      return;
    }

    // Render cart items
    cartBody.innerHTML = `
      <div class="cart-list">
        ${cart.map(item => `
          <div class="cart-item" data-product-id="${item.id}">
            <div class="cart-item-image">
              <img src="${item.image}" alt="${item.title}" onerror="this.src='assets/placeholder.png'">
            </div>
            <div class="cart-item-details">
              <div class="cart-item-title">${item.title}</div>
              <div class="cart-item-price">${item.price}</div>
            </div>
            <button class="cart-item-remove" data-remove-id="${item.id}" aria-label="Remove ${item.title}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        `).join('')}
      </div>
    `;

    // Add event listeners to remove buttons
    cartBody.querySelectorAll('[data-remove-id]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const productId = e.currentTarget.getAttribute('data-remove-id');
        removeFromCart(productId);
      });
    });
  }

  /**
   * Toggle cart sidebar
   */
  function toggleCart(open) {
    if (open) {
      cartSidebar?.classList.add('open');
      cartOverlay?.classList.add('open');
      document.body.style.overflow = 'hidden';
    } else {
      cartSidebar?.classList.remove('open');
      cartOverlay?.classList.remove('open');
      document.body.style.overflow = '';
    }
  }

  /**
   * Checkout - Send cart to backend and open Lemon Squeezy checkout
   */
  async function checkout() {
    if (cart.length === 0) {
      alert('Your cart is empty!');
      return;
    }

    // Disable checkout button and show loading
    if (cartCheckoutBtn) {
      cartCheckoutBtn.disabled = true;
      cartCheckoutBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        Processing...
      `;
    }

    try {
      // Send cart to backend
      const response = await fetch(FASTAPI_CHECKOUT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: cart })
      });

      if (!response.ok) {
        throw new Error(`Checkout failed: ${response.status}`);
      }

      const data = await response.json();

      if (!data.checkout_url) {
        throw new Error('No checkout URL received from server');
      }

      // Open Lemon Squeezy checkout in new tab (avoids overlay redirect issues)
      window.open(data.checkout_url, '_blank');

      // Clear cart after successful checkout
      cart = [];
      saveCart();
      toggleCart(false);

    } catch (error) {
      console.error('Checkout error:', error);
      alert('Sorry, there was an error processing your checkout. Please try again or contact support.');
    } finally {
      // Re-enable checkout button
      if (cartCheckoutBtn) {
        cartCheckoutBtn.disabled = false;
        cartCheckoutBtn.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          Proceed to Checkout
        `;
      }
    }
  }

  // Event listeners for cart
  cartButton?.addEventListener('click', () => toggleCart(true));
  cartClose?.addEventListener('click', () => toggleCart(false));
  cartOverlay?.addEventListener('click', () => toggleCart(false));
  cartClearBtn?.addEventListener('click', clearCart);
  cartCheckoutBtn?.addEventListener('click', checkout);

  // Initialize cart on page load
  loadCart();


  function initSlider({ rootSelector, slideSelector = '.slide', dotsSelector = '.slider-dots', interval = 2000 }) {
    const root = document.querySelector(rootSelector);
    if (!root) return;

    const slides = Array.from(root.querySelectorAll(slideSelector));
    const dotsContainer = root.parentElement?.querySelector(dotsSelector) || root.querySelector(dotsSelector);
    if (!slides.length) return;

    let activeIndex = 0;
    let autoplayId;

    function setActiveSlide(nextIndex) {
      slides[activeIndex]?.classList.remove('is-active');
      dotsContainer?.children[activeIndex]?.classList.remove('is-active');
      activeIndex = nextIndex;
      slides[activeIndex]?.classList.add('is-active');
      dotsContainer?.children[activeIndex]?.classList.add('is-active');
    }

    function nextSlide() {
      const nextIndex = (activeIndex + 1) % slides.length;
      setActiveSlide(nextIndex);
      startAutoplay(); // Restart with potentially different duration
    }

    function stopAutoplay() {
      if (autoplayId) {
        clearInterval(autoplayId);
        autoplayId = undefined;
      }
    }

    function startAutoplay() {
      stopAutoplay();
      // Check if current slide has custom duration
      const currentSlide = slides[activeIndex];
      const customDuration = currentSlide?.getAttribute('data-duration');
      const duration = customDuration ? parseInt(customDuration, 10) : interval;
      autoplayId = setInterval(nextSlide, duration);
    }

    slides.forEach((_, index) => {
      const dot = document.createElement('button');
      dot.type = 'button';
      if (index === activeIndex) dot.classList.add('is-active');
      dot.addEventListener('click', () => {
        setActiveSlide(index);
        startAutoplay();
      });
      dotsContainer?.appendChild(dot);
    });

    root.addEventListener('pointerenter', stopAutoplay);
    root.addEventListener('pointerleave', startAutoplay);

    startAutoplay();
  }

  initSlider({ rootSelector: '.story-slider .slides', interval: 2000 });
  initSlider({ rootSelector: '.hero-slider', dotsSelector: '.hero-slider-dots', interval: 2600 });

  // ==================== Dynamic Product Loading ====================
  // Configuration - UPDATE THIS VALUE
  const FASTAPI_URL = 'https://api.littleoatlearners.com/api/products';

  /**
   * Fetch products from FastAPI backend
   */
  async function fetchProducts() {
    try {
      const response = await fetch(FASTAPI_URL); // Already includes full path
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Your API returns an array directly or wrapped in {products: [...]}
      return Array.isArray(data) ? data : (data.products || data);
    } catch (error) {
      console.error('Error fetching products:', error);
      return null;
    }
  }

  /**
   * Create a product card element from product data
   */
  function createProductCard(product) {
    const article = document.createElement('article');
    article.className = 'product-card';

    // Add badge if product has category or is featured
    let badgeHTML = '';
    if (product.category) {
      badgeHTML = `<div class="product-badge">${product.category}</div>`;
    }

    // Build features list (if your API adds this later, otherwise skip)
    const featuresHTML = product.features
      ? product.features.map(feature => `<li>${feature}</li>`).join('')
      : '';

    // Build pricing section using the price field from API
    const pricingHTML = `
      <div class="product-pricing">
        <div class="price-option featured">
          <span class="price">${product.price}</span>
          <span class="period">one-time</span>
        </div>
      </div>
    `;

    article.innerHTML = `
      ${badgeHTML}
      <div class="product-image">
        <img src="${product.image || 'assets/placeholder.png'}" alt="${product.title}" loading="lazy">
      </div>
      <div class="product-content">
        <h3>${product.title}</h3>
        <p class="product-description">${product.description}</p>
        ${featuresHTML ? `<ul class="product-features">${featuresHTML}</ul>` : ''}
        ${pricingHTML}
        <button class="btn primary full add-to-cart-btn" data-product-id="${product.id}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          Add to Cart
        </button>
      </div>
    `;

    // Add click handler for Add to Cart button
    const addButton = article.querySelector('.add-to-cart-btn');
    addButton.addEventListener('click', () => {
      const added = addToCart(product);

      if (added) {
        // Show success feedback
        addButton.classList.add('added');
        addButton.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            <path d="M5 13l4 4L19 7"/>
          </svg>
          Added to Cart!
        `;

        // Open cart sidebar
        setTimeout(() => toggleCart(true), 300);

        // Reset button after delay
        setTimeout(() => {
          addButton.classList.remove('added');
          addButton.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
              <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
            Add to Cart
          `;
        }, 2000);
      } else {
        // Item already in cart
        addButton.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
          Already in Cart
        `;

        // Open cart to show it's already there
        setTimeout(() => toggleCart(true), 300);

        // Reset button
        setTimeout(() => {
          addButton.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
              <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
            Add to Cart
          `;
        }, 2000);
      }
    });

    return article;
  }

  /**
   * Load and display products dynamically
   */
  async function loadProducts() {
    const productGrid = document.querySelector('.product-grid');
    if (!productGrid) return; // Not on shop page

    // Show loading state
    productGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
        <p style="font-size: 1.125rem; color: var(--muted);">Loading products...</p>
      </div>
    `;

    // Fetch products from FastAPI
    const products = await fetchProducts();

    if (!products || products.length === 0) {
      // Show error or fallback message
      productGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
          <p style="font-size: 1.125rem; color: var(--muted);">
            Unable to load products at this time. Please try again later.
          </p>
        </div>
      `;
      return;
    }

    // Clear loading state
    productGrid.innerHTML = '';

    // Create and append product cards
    products.forEach(product => {
      const card = createProductCard(product);
      productGrid.appendChild(card);
    });

    // Initialize Lemon Squeezy buttons for the new cards
    initLemonSqueezy();
  }

  // ==================== Lemon Squeezy Integration ====================
  /**
   * Initialize Lemon Squeezy checkout buttons
   */
  function initLemonSqueezy() {
    // Load Lemon Squeezy script if not already loaded
    if (!window.createLemonSqueezy) {
      const script = document.createElement('script');
      script.src = 'https://app.lemonsqueezy.com/js/lemon.js';
      script.defer = true;
      document.head.appendChild(script);
    }

    // Handle all Lemon Squeezy buttons (remove old listeners first)
    document.querySelectorAll('.lemonsqueezy-button').forEach(button => {
      // Clone and replace to remove old event listeners
      const newButton = button.cloneNode(true);
      button.parentNode.replaceChild(newButton, button);

      newButton.addEventListener('click', function (e) {
        e.preventDefault();

        // Get checkout URL from data attribute (provided by backend)
        const checkoutUrl = this.getAttribute('data-checkout-url');

        if (!checkoutUrl) {
          console.error('No checkout URL found for product');
          return;
        }

        // Open checkout in overlay (recommended) or new tab
        if (window.createLemonSqueezy) {
          window.createLemonSqueezy();
          window.LemonSqueezy.Url.Open(checkoutUrl);
        } else {
          // Fallback: open in new tab if script hasn't loaded yet
          window.open(checkoutUrl, '_blank');
        }
      });
    });
  }

  // ==================== Initialize ====================
  // Load products if on shop page, otherwise just init Lemon Squeezy for static buttons
  if (document.querySelector('.product-grid')) {
    loadProducts();
  } else {
    initLemonSqueezy();
  }
})();
