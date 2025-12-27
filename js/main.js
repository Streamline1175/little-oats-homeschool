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
        <a href="${product.buyUrl || '#'}" 
           class="btn primary full buy-now-btn" 
           target="_blank"
           rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
            <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          Buy Now
        </a>
      </div>
  `;

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

  // ==================== Download Count Logic ====================
  async function fetchGitHubDownloads() {
    const winBadge = document.getElementById('download-win');
    const macBadge = document.getElementById('download-mac');
    const linuxBadge = document.getElementById('download-linux');

    // Only proceed if elements exist
    if (!winBadge && !macBadge && !linuxBadge) return;

    try {
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
      console.error('Error fetching download counts:', error);
      // Fallback or hide
      if (winBadge) winBadge.style.display = 'none';
      if (macBadge) macBadge.style.display = 'none';
      if (linuxBadge) linuxBadge.style.display = 'none';
    }
  }

  // Init download counts
  fetchGitHubDownloads();
})();
