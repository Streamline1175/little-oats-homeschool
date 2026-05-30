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


  // ==================== Product Display System ====================

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
        throw new Error(`HTTP error! status: ${response.status} `);
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

    // Build pricing section - handle subscriptions vs one-time purchases
    let periodText = 'one-time';
    if (product.is_subscription && product.interval) {
      // Format interval (e.g., "month" -> "/month", "year" -> "/year")
      const intervalLabel = product.interval_count > 1
        ? `every ${product.interval_count} ${product.interval}s`
        : `/${product.interval}`;
      periodText = intervalLabel;
    }

    const pricingHTML = `
      <div class="product-pricing">
        <div class="price-option featured">
          <span class="price">${product.price}</span>
          <span class="period">${periodText}</span>
        </div>
      </div>
    `;

    // Generate unique ID for the description toggle
    const descriptionId = `desc-${product.id}`;

    article.innerHTML = `
      ${badgeHTML}
      <div class="product-image">
        <img src="${product.image || 'assets/placeholder.png'}" alt="${product.title}" loading="lazy">
      </div>
      <div class="product-content">
        <h3>${product.title}</h3>
        <div class="product-description-wrapper collapsed">
          <div class="product-description" id="${descriptionId}">${product.description}</div>
          <button type="button" class="description-toggle" aria-expanded="false" aria-controls="${descriptionId}">
            <span class="show-more">Show more</span>
            <span class="show-less">Show less</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
        ${featuresHTML ? `<ul class="product-features">${featuresHTML}</ul>` : ''}
        ${pricingHTML}
        <button type="button" class="btn primary full add-to-cart-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          Add to Cart
        </button>
      </div>
  `;

    // Add click handler for description toggle
    const toggleBtn = article.querySelector('.description-toggle');
    const wrapper = article.querySelector('.product-description-wrapper');
    if (toggleBtn && wrapper) {
      toggleBtn.addEventListener('click', () => {
        const isCollapsed = wrapper.classList.toggle('collapsed');
        toggleBtn.setAttribute('aria-expanded', String(!isCollapsed));
      });
    }

    // Add click handler for Add to Cart button
    const addToCartBtn = article.querySelector('.add-to-cart-btn');
    if (addToCartBtn) {
      addToCartBtn.addEventListener('click', () => {
        Cart.addItem(product);
      });
    }

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
      // Show maintenance state
      productGrid.innerHTML = `
        <div style="grid-column: 1 / -1; display: flex; flex-direction: column; align-items: center; text-align: center; padding: 4rem 2rem; background: rgba(122, 139, 111, 0.05); border-radius: 24px; border: 1px solid rgba(139, 115, 85, 0.12);">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--sage-deep)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1.5rem;">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
          </svg>
          <h3 style="color: var(--sage-deep); margin-bottom: 0.75rem;">Shop Maintenance</h3>
          <p style="font-size: 1.125rem; color: var(--muted); max-width: 400px; margin: 0 auto;">
            The shop is currently undergoing scheduled maintenance. Please check back shortly.
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
  }

  // ==================== Shopping Cart System ====================
  const Cart = {
    items: [],

    init() {
      // Load cart items from localStorage
      try {
        const storedCart = localStorage.getItem('lol_cart');
        if (storedCart) {
          this.items = JSON.parse(storedCart);
        }
      } catch (e) {
        console.error('Failed to load cart from localStorage:', e);
      }
      this.updateUI();
      this.bindEvents();
    },

    save() {
      try {
        localStorage.setItem('lol_cart', JSON.stringify(this.items));
      } catch (e) {
        console.error('Failed to save cart to localStorage:', e);
      }
      this.updateUI();
    },

    addItem(product) {
      // Check if product already in cart
      const existing = this.items.find(item => item.id === product.id);
      if (existing) {
        alert(`${product.title} is already in your cart.`);
        this.openDrawer();
        return;
      }
      
      // Parse numeric price value (e.g. "$29.00" -> 29.0)
      const priceVal = parseFloat(product.price.replace(/[^0-9.]/g, '')) || 0.0;

      this.items.push({
        id: product.id,
        title: product.title,
        price: product.price,
        priceValue: priceVal,
        image: product.image
      });
      
      this.save();
      this.openDrawer();
    },

    removeItem(id) {
      this.items = this.items.filter(item => item.id !== id);
      this.save();
    },

    clear() {
      this.items = [];
      this.save();
    },

    getTotal() {
      return this.items.reduce((sum, item) => sum + item.priceValue, 0.0);
    },

    getItemCount() {
      return this.items.length;
    },

    openDrawer() {
      document.getElementById('cart-sidebar')?.classList.add('open');
      document.getElementById('cart-overlay')?.classList.add('open');
      document.body.style.overflow = 'hidden'; // Lock background scrolling
    },

    closeDrawer() {
      document.getElementById('cart-sidebar')?.classList.remove('open');
      document.getElementById('cart-overlay')?.classList.remove('open');
      document.body.style.overflow = ''; // Unlock background scrolling
    },

    updateUI() {
      const count = this.getItemCount();
      const badge = document.getElementById('cart-badge');
      const emptyState = document.getElementById('cart-empty-state');
      const itemsList = document.getElementById('cart-items-list');
      const cartFooter = document.getElementById('cart-footer');
      const subtotalEl = document.getElementById('cart-subtotal');
      const totalEl = document.getElementById('cart-total');

      // Update badge
      if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
      }

      if (count === 0) {
        emptyState && (emptyState.style.display = 'block');
        itemsList && (itemsList.style.display = 'none');
        cartFooter && (cartFooter.style.display = 'none');
      } else {
        emptyState && (emptyState.style.display = 'none');
        itemsList && (itemsList.style.display = 'flex');
        cartFooter && (cartFooter.style.display = 'block');

        // Populate items list
        if (itemsList) {
          itemsList.innerHTML = '';
          this.items.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'cart-item';
            itemEl.innerHTML = `
              <div class="cart-item-image">
                <img src="${item.image || 'assets/placeholder.png'}" alt="${item.title}">
              </div>
              <div class="cart-item-details">
                <div class="cart-item-title" title="${item.title}">${item.title}</div>
                <div class="cart-item-price">${item.price}</div>
              </div>
              <button class="cart-item-remove" data-id="${item.id}" aria-label="Remove ${item.title}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  <line x1="10" y1="11" x2="10" y2="17"></line>
                  <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
              </button>
            `;
            // Add click listener to remove button
            itemEl.querySelector('.cart-item-remove').addEventListener('click', () => {
              this.removeItem(item.id);
            });
            itemsList.appendChild(itemEl);
          });
        }

        // Update subtotals
        const total = this.getTotal();
        const formattedTotal = `$${total.toFixed(2)}`;
        if (subtotalEl) subtotalEl.textContent = formattedTotal;
        if (totalEl) totalEl.textContent = formattedTotal;
      }
      
      // Update checkouts button text
      const checkoutBtn = document.getElementById('cart-checkout-btn');
      if (checkoutBtn) {
        checkoutBtn.disabled = count === 0;
      }
    },

    bindEvents() {
      // Toggle cart sidebar drawer
      document.getElementById('cart-btn')?.addEventListener('click', () => this.openDrawer());
      document.getElementById('cart-close-btn')?.addEventListener('click', () => this.closeDrawer());
      document.getElementById('cart-overlay')?.addEventListener('click', () => this.closeDrawer());

      // Keyboard Esc close drawer
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.closeDrawer();
        }
      });

      // Clear cart action
      document.getElementById('cart-clear-btn')?.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your cart?')) {
          this.clear();
        }
      });

      // Checkout submit action
      document.getElementById('cart-checkout-btn')?.addEventListener('click', async () => {
        await this.handleCheckout();
      });
    },

    async handleCheckout() {
      const checkoutBtn = document.getElementById('cart-checkout-btn');
      if (!checkoutBtn || this.items.length === 0) return;

      // Disable button & show loading state
      const originalHTML = checkoutBtn.innerHTML;
      checkoutBtn.disabled = true;
      checkoutBtn.innerHTML = `
        <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite; width: 20px; height: 20px;">
          <circle cx="12" cy="12" r="10" stroke-dasharray="162" stroke-dashoffset="100"></circle>
        </svg>
        Preparing Checkout...
      `;

      const customerEmail = localStorage.getItem('lol_visitor_email') || null;

      const payload = {
        items: this.items,
        customer_email: customerEmail
      };

      const API_BASE = 'https://api.littleoatlearners.com';

      try {
        const response = await fetch(`${API_BASE}/api/checkout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errText = await response.text();
          throw new Error(`Checkout creation failed: ${errText}`);
        }

        const data = await response.json();
        
        if (data.checkout_url) {
          this.clear();
          window.location.href = data.checkout_url;
        } else {
          throw new Error('Did not receive a valid checkout URL from backend API');
        }

      } catch (err) {
        console.error('Checkout error:', err);
        alert(`Sorry, we couldn't initiate checkout at this moment.\n\nError: ${err.message || err}`);
        // Reset checkout button
        checkoutBtn.disabled = false;
        checkoutBtn.innerHTML = originalHTML;
      }
    }
  };

  // ==================== Initialize ====================
  // Initialize Shopping Cart System
  Cart.init();

  if (document.querySelector('.product-grid')) {
    loadProducts();
  }

  // ==================== Download Links & Count Logic ====================
  async function fetchGitHubDownloads() {
    const winBadge = document.getElementById('download-win');
    const macBadge = document.getElementById('download-mac');
    const linuxBadge = document.getElementById('download-linux');
    const winLink = document.getElementById('download-win-link');
    const macLink = document.getElementById('download-mac-link');
    const linuxLink = document.getElementById('download-linux-link');

    // Only proceed if elements exist
    if (!winBadge && !macBadge && !linuxBadge) return;

    try {
      // Fetch the latest release to get correct download URLs
      const latestResponse = await fetch('https://api.github.com/repos/Streamline1175/homeschool-releases/releases/latest');
      if (!latestResponse.ok) throw new Error('Failed to fetch latest release');

      const latestRelease = await latestResponse.json();

      // Find download URLs from latest release assets
      let downloadUrls = {
        windows: null,
        mac: null,
        linux: null
      };

      latestRelease.assets.forEach(asset => {
        const name = asset.name.toLowerCase();
        // Prefer setup exe for Windows (installer)
        if (name.includes('setup') && name.endsWith('.exe')) {
          downloadUrls.windows = asset.browser_download_url;
        } else if (name.endsWith('.dmg')) {
          downloadUrls.mac = asset.browser_download_url;
        } else if (name.endsWith('.appimage')) {
          downloadUrls.linux = asset.browser_download_url;
        }
      });

      // Fallback: if no setup exe found, use any exe
      if (!downloadUrls.windows) {
        const exeAsset = latestRelease.assets.find(a => a.name.toLowerCase().endsWith('.exe'));
        if (exeAsset) downloadUrls.windows = exeAsset.browser_download_url;
      }

      // Update download links
      if (winLink && downloadUrls.windows) winLink.href = downloadUrls.windows;
      if (macLink && downloadUrls.mac) macLink.href = downloadUrls.mac;
      if (linuxLink && downloadUrls.linux) linuxLink.href = downloadUrls.linux;

      // Fetch all releases for download counts
      const response = await fetch('https://api.github.com/repos/Streamline1175/homeschool-releases/releases');
      if (!response.ok) throw new Error('Failed to fetch releases');

      const releases = await response.json();

      let counts = {
        windows: 0,
        mac: 0,
        linux: 0
      };

      releases.forEach(release => {
        release.assets.forEach(asset => {
          const name = asset.name.toLowerCase();
          const count = asset.download_count;

          if (name.endsWith('.exe')) {
            counts.windows += count;
          } else if (name.endsWith('.dmg')) {
            counts.mac += count;
          } else if (name.endsWith('.appimage') || name.endsWith('.deb') || name.endsWith('.rpm')) {
            counts.linux += count;
          }
        });
      });

      // Format numbers (e.g., 1.2k)
      const formatCount = (num) => {
        if (num >= 1000) {
          return (num / 1000).toFixed(1) + 'k downloads';
        }
        return num + ' downloads';
      };

      if (winBadge) winBadge.textContent = formatCount(counts.windows);
      if (macBadge) macBadge.textContent = formatCount(counts.mac);
      if (linuxBadge) linuxBadge.textContent = formatCount(counts.linux);

    } catch (error) {
      console.error('Error fetching download info:', error);
      // Fallback to releases page
      const fallbackUrl = 'https://github.com/Streamline1175/homeschool-releases/releases/latest';
      if (winLink) winLink.href = fallbackUrl;
      if (macLink) macLink.href = fallbackUrl;
      if (linuxLink) linuxLink.href = fallbackUrl;
      // Hide badges on error
      if (winBadge) winBadge.style.display = 'none';
      if (macBadge) macBadge.style.display = 'none';
      if (linuxBadge) linuxBadge.style.display = 'none';
    }
  }

  // ==================== Age Verification Modal ====================
  const ageModalOverlay = document.getElementById('age-modal-overlay');
  const dobMonthSelect = document.getElementById('dob-month');
  const dobDaySelect = document.getElementById('dob-day');
  const dobYearSelect = document.getElementById('dob-year');
  const ageVerifyBtn = document.getElementById('age-verify-btn');
  const ageCancelBtn = document.getElementById('age-cancel-btn');
  const ageError = document.getElementById('age-error');

  let pendingDownloadUrl = null;

  // Populate day dropdown (1-31)
  function populateDays() {
    if (!dobDaySelect) return;
    for (let i = 1; i <= 31; i++) {
      const opt = document.createElement('option');
      opt.value = i;
      opt.textContent = i;
      dobDaySelect.appendChild(opt);
    }
  }

  // Populate year dropdown (current year - 100 to current year)
  function populateYears() {
    if (!dobYearSelect) return;
    const currentYear = new Date().getFullYear();
    for (let year = currentYear; year >= currentYear - 100; year--) {
      const opt = document.createElement('option');
      opt.value = year;
      opt.textContent = year;
      dobYearSelect.appendChild(opt);
    }
  }

  // Calculate age from date of birth
  function calculateAge(birthDate) {
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    const dayDiff = today.getDate() - birthDate.getDate();

    // Adjust age if birthday hasn't occurred yet this year
    if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
      age--;
    }
    return age;
  }

  // Show the age verification modal
  function showAgeModal(downloadUrl) {
    if (!ageModalOverlay) return false;
    pendingDownloadUrl = downloadUrl;
    // Reset form
    if (dobMonthSelect) dobMonthSelect.value = '';
    if (dobDaySelect) dobDaySelect.value = '';
    if (dobYearSelect) dobYearSelect.value = '';
    if (ageError) ageError.textContent = '';
    ageModalOverlay.setAttribute('aria-hidden', 'false');
    return true;
  }

  // Hide the age verification modal
  function hideAgeModal() {
    if (!ageModalOverlay) return;
    ageModalOverlay.setAttribute('aria-hidden', 'true');
    pendingDownloadUrl = null;
  }

  // Verify age and proceed with download if valid
  function verifyAge() {
    const month = dobMonthSelect?.value;
    const day = dobDaySelect?.value;
    const year = dobYearSelect?.value;

    // Validate all fields are filled
    if (month === '' || day === '' || year === '') {
      if (ageError) ageError.textContent = 'Please select your complete date of birth.';
      return;
    }

    const birthDate = new Date(parseInt(year), parseInt(month), parseInt(day));
    const age = calculateAge(birthDate);

    if (age >= 18) {
      // Age verified - proceed with download
      const downloadUrl = pendingDownloadUrl;
      hideAgeModal();
      if (downloadUrl) {
        window.location.href = downloadUrl;
      }
    } else {
      // Under 18 - block download
      if (ageError) {
        ageError.textContent = 'Sorry, you must be 18 years or older to download this application.';
      }
    }
  }

  // Initialize age verification system
  function initAgeVerification() {
    if (!ageModalOverlay) return; // Elements don't exist on this page

    populateDays();
    populateYears();

    // Verify button click
    ageVerifyBtn?.addEventListener('click', verifyAge);

    // Cancel button click
    ageCancelBtn?.addEventListener('click', hideAgeModal);

    // Click outside modal to close
    ageModalOverlay.addEventListener('click', (e) => {
      if (e.target === ageModalOverlay) {
        hideAgeModal();
      }
    });

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && ageModalOverlay.getAttribute('aria-hidden') === 'false') {
        hideAgeModal();
      }
    });

    // Intercept download link clicks using event delegation
    // This captures clicks even on nested elements inside the links
    document.addEventListener('click', (e) => {
      const downloadLink = e.target.closest('#download-win-link, #download-mac-link, #download-linux-link, .resource-card .btn');
      if (downloadLink) {
        e.preventDefault();
        e.stopPropagation();
        const downloadUrl = downloadLink.href;
        showAgeModal(downloadUrl);
      }
    }, true); // Use capture phase to intercept before default behavior
  }

  // Init age verification
  initAgeVerification();

  // Init download links and counts
  fetchGitHubDownloads();

  // ==================== Privacy-First Analytics ====================
  async function trackVisit() {
    // 1. Get or create anonymous visitor ID
    let visitorId = localStorage.getItem('lol_visitor_id');
    if (!visitorId) {
      visitorId = crypto.randomUUID();
      localStorage.setItem('lol_visitor_id', visitorId);
    }

    // 2. Prepare payload
    const payload = {
      visitor_id: visitorId,
      page: window.location.pathname
    };

    // 3. Send to backend
    // Note: Use a separate base URL if needed, but here we assume same domain or previously defined FASTAPI_URL (base)
    // The previous FASTAPI_URL variable might be scoped inside the IIFE or block, so let's re-declare a base or use relative if proxied.
    // For safety, let's use the hardcoded base for now matching existing code.
    const API_BASE = 'https://api.littleoatlearners.com';

    try {
      await fetch(`${API_BASE}/api/analytics/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      // Fail silently for analytics
      console.debug('Analytics skipped', e);
    }
  }

  // ==================== Pointer Glow Effect for Glass Cards ====================
  function initPointerGlow() {
    document.addEventListener('pointermove', (e) => {
      const card = e.target.closest('.glass-widget, .service-card, .product-card');
      if (!card) return;
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  }
  initPointerGlow();

  // Run tracking once per page load
  trackVisit();
})();
