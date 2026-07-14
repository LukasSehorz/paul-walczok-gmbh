/* ============================================================
   Paul Walczok GmbH — Landingpage V2
   Entrance-Reveals (einmalig), Count-up, Navigation, Formular
   ============================================================ */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Header-Zustand ---------- */
  var header = document.querySelector('.site-header');

  function onScroll() {
    header.classList.toggle('scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile Navigation ---------- */
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('mainNav');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Menü schließen' : 'Menü öffnen');
    });

    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        document.body.classList.remove('nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- Count-up für Statistiken ---------- */
  function countUp(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    if (isNaN(target) || prefersReduced) {
      el.textContent = target;
      return;
    }
    var duration = 1400;
    var start = null;

    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * target);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ---------- Entrance-Reveals (einmalig beim Erscheinen) ---------- */
  var revealEls = document.querySelectorAll('[data-reveal]');

  if ('IntersectionObserver' in window && !prefersReduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('revealed');
        entry.target.querySelectorAll('[data-count]').forEach(countUp);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -40px 0px' });

    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add('revealed');
      el.querySelectorAll('[data-count]').forEach(function (c) {
        c.textContent = c.getAttribute('data-count');
      });
    });
  }

  /* ---------- Kontaktformular (Demo: öffnet E-Mail-Entwurf) ---------- */
  var form = document.getElementById('contactForm');
  var note = document.getElementById('formNote');

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var name = form.name.value.trim();
      var firma = form.firma.value.trim();
      var email = form.email.value.trim();
      var msg = form.nachricht.value.trim();

      var body =
        'Name: ' + name + '\n' +
        (firma ? 'Firma: ' + firma + '\n' : '') +
        'E-Mail: ' + email + '\n\n' +
        'Projekt:\n' + msg;

      var link =
        'mailto:info@walczok-gmbh.de' +
        '?subject=' + encodeURIComponent('Projektanfrage über die Website') +
        '&body=' + encodeURIComponent(body);

      window.location.href = link;

      if (note) {
        note.textContent = 'Ihr E-Mail-Programm öffnet sich mit der vorbereiteten Anfrage. Vielen Dank!';
      }
    });
  }
})();
