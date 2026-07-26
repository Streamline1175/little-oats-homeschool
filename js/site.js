/* Little Oat LLC — shared nav behavior (mobile toggle + dropdown accordions)
   plus privacy-first page-view tracking. */
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var menu   = document.getElementById('site-menu');

  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  /* On mobile, tapping a dropdown's top-level label opens/closes it
     instead of navigating (desktop uses hover). */
  var mq = window.matchMedia('(max-width: 820px)');
  document.querySelectorAll('.nav-menu > li.has-dropdown > a').forEach(function (link) {
    link.addEventListener('click', function (e) {
      if (!mq.matches) return;            // desktop: follow the link
      e.preventDefault();
      link.parentElement.classList.toggle('open');
    });
  });

  /* ---- Privacy-first analytics ----
     Lives here (not main.js) so every page that loads the shared nav is
     counted. Guarded so pages loading both site.js and main.js only fire once. */
  if (window.__loTracked) return;
  window.__loTracked = true;

  var visitorId = localStorage.getItem('lol_visitor_id');
  if (!visitorId) {
    visitorId = (window.crypto && crypto.randomUUID)
      ? crypto.randomUUID()
      : 'v-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem('lol_visitor_id', visitorId);
  }

  fetch('https://api.littleoatlearners.com/api/analytics/track', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ visitor_id: visitorId, page: window.location.pathname })
  }).catch(function () { /* analytics is best-effort — never block the page */ });
})();
