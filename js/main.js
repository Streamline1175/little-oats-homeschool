(function() {
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
    anchor.addEventListener('click', function(e) {
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

  // Simple client-side cart handling for shop pages
  const cartStorageKey = 'little-oat-cart';
  const cartList = document.querySelector('.cart-list');
  const clearCartBtn = document.getElementById('clear-cart');
  const cartCountEls = document.querySelectorAll('.cart-count');

  function getCart() {
    try {
      return JSON.parse(localStorage.getItem(cartStorageKey)) || [];
    } catch (e) {
      return [];
    }
  }

  function saveCart(items) {
    localStorage.setItem(cartStorageKey, JSON.stringify(items));
    renderCart();
  }

  function renderCart() {
    const items = getCart();
    cartCountEls.forEach((el) => (el.textContent = items.length));

    if (!cartList) return;

    cartList.innerHTML = '';
    if (!items.length) {
      cartList.innerHTML = '<p class="cart-empty">Your cart is empty.</p>';
      return;
    }

    items.forEach((item, index) => {
      const row = document.createElement('div');
      row.className = 'cart-row';
      row.innerHTML = `
        <div>
          <strong>${item.name}</strong>
          <span class="price">${item.price}</span>
        </div>
        <button class="remove-btn" data-remove-index="${index}">Remove</button>
      `;
      cartList.appendChild(row);
    });
  }

  document.querySelectorAll('[data-add-to-cart]').forEach((button) => {
    button.addEventListener('click', () => {
      const name = button.getAttribute('data-product');
      const price = button.getAttribute('data-price');
      const cart = getCart();
      cart.push({ name, price });
      saveCart(cart);
      button.textContent = 'Added!';
      setTimeout(() => (button.textContent = 'Add to cart'), 1200);
    });
  });

  cartList?.addEventListener('click', (e) => {
    const target = e.target;
    if (target instanceof HTMLElement && target.dataset.removeIndex) {
      const cart = getCart();
      cart.splice(Number(target.dataset.removeIndex), 1);
      saveCart(cart);
    }
  });

  clearCartBtn?.addEventListener('click', () => {
    saveCart([]);
  });

  renderCart();
})();
