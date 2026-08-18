/* ═══════════════════════════════════════════════════════════════════════════
   Paul Walczok GmbH — main.js
   GSAP + ScrollTrigger + SplitText + Lenis (alles lokal aus js/vendor/)

   01 Setup & Helfer        02 Lenis (Smooth Scroll)   03 Header & Navigation
   04 Rotierende Bildmarke  05 Hero-Intro & Parallax   06 Scroll-Reveals
   07 Headline-Reveals      08 Zähler                  09 Marquee
   10 Vorher/Nachher        11 Bild-Parallax           12 Leistungs-Vorschau
   13 Magnet-Buttons        14 Formular                15 Kleinkram

   Performance: animiert werden ausschließlich transform und opacity.
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ───────────────────────── 01 · SETUP & HELFER ───────────────────────── */

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasGSAP = typeof window.gsap !== 'undefined';
  var canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  var $  = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  if (hasGSAP) {
    gsap.registerPlugin(ScrollTrigger);
    if (window.SplitText) { gsap.registerPlugin(SplitText); }
    ScrollTrigger.config({ ignoreMobileResize: true });
    gsap.defaults({ ease: 'power3.out', duration: .9 });
  }

  /* Kopfhöhe als px-Wert (für Sprungziele) */
  function headerOffset() {
    var h = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--hdr-h'), 10);
    return isNaN(h) ? 84 : h;
  }

  /* ───────────────────── 02 · LENIS · SMOOTH SCROLL ────────────────────── */

  var lenis = null;

  if (!reduce && hasGSAP && typeof window.Lenis !== 'undefined') {
    lenis = new Lenis({
      lerp: .085,
      wheelMultiplier: 1,
      smoothWheel: true,
      touchMultiplier: 1.6
    });

    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(function (time) { lenis.raf(time * 1000); });
    gsap.ticker.lagSmoothing(0);
  }

  /* Anker-Links laufen über Lenis, damit Smooth-Scroll und ScrollTrigger synchron bleiben */
  function scrollToTarget(target) {
    if (!target) return;
    if (lenis) { lenis.scrollTo(target, { offset: -(headerOffset() - 10), duration: 1.2 }); }
    else { target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' }); }
  }

  $$('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (!id || id === '#') return;
      var target = id === '#top' ? document.body : document.getElementById(id.slice(1));
      if (!target) return;
      e.preventDefault();
      closeMenu();
      if (id === '#top') { lenis ? lenis.scrollTo(0, { duration: 1.2 }) : window.scrollTo(0, 0); }
      else { scrollToTarget(target); }
      history.replaceState(null, '', id);
    });
  });

  /* ─────────────────── 03 · HEADER & MOBILE-NAVIGATION ─────────────────── */

  var hdr     = $('#hdr');
  var burger  = $('#burger');
  var mobile  = $('#mobilenav');
  var menuOpen = false;

  function onScrollHeader() {
    hdr.classList.toggle('is-stuck', (window.scrollY || window.pageYOffset) > 30);
  }
  onScrollHeader();
  window.addEventListener('scroll', onScrollHeader, { passive: true });

  function openMenu() {
    menuOpen = true;
    mobile.hidden = false;
    burger.setAttribute('aria-expanded', 'true');
    burger.querySelector('.u-sr').textContent = 'Menü schließen';
    document.body.classList.add('is-locked');
    if (lenis) lenis.stop();

    if (hasGSAP && !reduce) {
      gsap.fromTo(mobile, { opacity: 0 }, { opacity: 1, duration: .35, ease: 'power2.out' });
      gsap.fromTo($$('.mnav__in a, .mnav__foot', mobile),
        { yPercent: 60, opacity: 0 },
        { yPercent: 0, opacity: 1, duration: .55, stagger: .045, ease: 'power3.out', delay: .06 });
    }
  }

  function closeMenu() {
    if (!menuOpen) return;
    menuOpen = false;
    burger.setAttribute('aria-expanded', 'false');
    burger.querySelector('.u-sr').textContent = 'Menü öffnen';
    document.body.classList.remove('is-locked');
    if (lenis) lenis.start();

    if (hasGSAP && !reduce) {
      gsap.to(mobile, {
        opacity: 0, duration: .28, ease: 'power2.in',
        onComplete: function () { mobile.hidden = true; gsap.set(mobile, { clearProps: 'opacity' }); }
      });
    } else {
      mobile.hidden = true;
    }
  }

  burger.addEventListener('click', function () { menuOpen ? closeMenu() : openMenu(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });

  /* ────────────────── 04 · ROTIERENDE BILDMARKE (NAVBAR) ───────────────── */
  /* Endlosrotation um die eigene Achse; Tempo und Richtung folgen dem Scrollen. */

  var mark = $('#spinMark');

  if (mark && hasGSAP && !reduce) {
    var spin = gsap.to(mark, {
      rotation: 360,
      duration: 24,
      ease: 'none',
      repeat: -1,
      transformOrigin: '50% 50%'
    });

    var idleTimer = null;

    ScrollTrigger.create({
      start: 0,
      end: 'max',
      invalidateOnRefresh: true,
      onUpdate: function (self) {
        var v   = self.getVelocity();               // px/s
        var dir = v < 0 ? -1 : 1;                   // Richtung folgt dem Scrollen
        var boost = gsap.utils.clamp(0, 8, Math.abs(v) / 320);

        gsap.to(spin, {
          timeScale: dir * (1 + boost),
          duration: .45,
          ease: 'power2.out',
          overwrite: true
        });

        clearTimeout(idleTimer);
        idleTimer = setTimeout(function () {
          gsap.to(spin, { timeScale: 1, duration: 1.4, ease: 'power2.out', overwrite: true });
        }, 160);
      }
    });
  }

  /* ────────────────── 05 · HERO · INTRO UND PARALLAX ───────────────────── */

  var heroVideo = $('#heroVideo');

  /* Bei reduzierter Bewegung kein Autoplay — das Poster bleibt stehen. */
  if (reduce && heroVideo) {
    heroVideo.removeAttribute('autoplay');
    heroVideo.autoplay = false;
    heroVideo.pause();
  }

  if (hasGSAP && !reduce) {

    /* Intro: Badge → Headline (zeilenweise) → Sub → CTAs → Scroll-Cue */
    var heroTl = gsap.timeline({ delay: .15 });

    heroTl
      .fromTo('.hero__kicker', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .7 }, 0)
      .add(revealHeadline($('.hero__title')), .12)
      .fromTo('.hero__sub',  { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: .8 }, .55)
      .fromTo('.hero__cta',  { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: .7 }, .7)
      .fromTo('.hero__foot', { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .8 }, .85);

    /* Video-Parallax: langsames Wegdriften beim Scrollen */
    if (heroVideo) {
      gsap.to(heroVideo, {
        yPercent: 12,
        scale: 1.16,
        ease: 'none',
        scrollTrigger: {
          trigger: '.hero',
          start: 'top top',
          end: 'bottom top',
          scrub: true,
          invalidateOnRefresh: true
        }
      });
    }

    /* Hero-Inhalt fährt beim Verlassen leicht mit */
    gsap.to('.hero__body', {
      yPercent: -14,
      opacity: .35,
      ease: 'none',
      scrollTrigger: {
        trigger: '.hero',
        start: 'top top',
        end: 'bottom top',
        scrub: true,
        invalidateOnRefresh: true
      }
    });
  }

  /* ───────────────────── 06 · GENERISCHE SCROLL-REVEALS ────────────────── */

  if (hasGSAP && !reduce) {

    /* Gruppen: gestaffelt, ein Trigger für alle Kinder */
    $$('[data-reveal-group]').forEach(function (group) {
      var items = $$('[data-reveal]', group);
      if (!items.length) return;
      gsap.to(items, {
        y: 0, opacity: 1, duration: .9, stagger: .085, ease: 'power3.out',
        scrollTrigger: { trigger: group, start: 'top 84%', once: true, invalidateOnRefresh: true }
      });
    });

    /* Einzelne Elemente außerhalb einer Gruppe */
    $$('[data-reveal]').forEach(function (el) {
      if (el.closest('[data-reveal-group]')) return;
      gsap.to(el, {
        y: 0, opacity: 1, duration: .9, ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 88%', once: true, invalidateOnRefresh: true }
      });
    });
  }

  /* ──────────────── 07 · HEADLINE-REVEALS (SplitText + Maske) ──────────── */
  /* Jede Zeile fährt aus einer Maske hoch. Fällt ohne SplitText auf ein
     einfaches Einblenden der vorhandenen .l-Zeilen zurück.                */

  function revealHeadline(el) {
    if (!el || !hasGSAP) return null;

    var lines = null;

    if (window.SplitText) {
      try {
        var split = new SplitText(el, { type: 'lines', linesClass: 'sline' });
        lines = split.lines;
        /* Maske je Zeile: oben etwas Luft für Umlaute, unten sauber abgeschnitten */
        lines.forEach(function (line) {
          var wrap = document.createElement('span');
          wrap.className = 'smask';
          line.parentNode.insertBefore(wrap, line);
          wrap.appendChild(line);
        });
      } catch (err) { lines = null; }
    }

    /* .l-Zeilen sind per CSS unsichtbar gestartet — jetzt freigeben */
    gsap.set($$('.l', el), { opacity: 1 });

    if (!lines || !lines.length) {
      lines = $$('.l', el);
      if (!lines.length) lines = [el];
      return gsap.from(lines, { y: 40, opacity: 0, duration: .9, stagger: .08 });
    }

    return gsap.from(lines, {
      yPercent: 118,
      duration: 1.05,
      stagger: .085,
      ease: 'power4.out'
    });
  }

  if (hasGSAP && !reduce) {
    $$('[data-split]').forEach(function (el) {
      if (el.closest('.hero')) return;                 /* Hero läuft über die Intro-Timeline */
      ScrollTrigger.create({
        trigger: el,
        start: 'top 86%',
        once: true,
        invalidateOnRefresh: true,
        onEnter: function () { revealHeadline(el); }
      });
    });
  } else {
    /* Ohne Animation: Zeilen sofort sichtbar machen */
    $$('[data-split] .l').forEach(function (l) { l.style.opacity = 1; });
  }

  /* ───────────────────────────── 08 · ZÄHLER ──────────────────────────── */

  var nf = new Intl.NumberFormat('de-DE');

  $$('[data-count]').forEach(function (el) {
    var end   = parseFloat(el.getAttribute('data-count'));
    var plain = el.hasAttribute('data-plain');
    var fmt   = function (v) { return plain ? String(Math.round(v)) : nf.format(Math.round(v)); };

    if (!hasGSAP || reduce) { el.textContent = fmt(end); return; }

    var obj = { v: 0 };
    gsap.to(obj, {
      v: end,
      duration: 1.6,
      ease: 'power2.out',
      onUpdate: function () { el.textContent = fmt(obj.v); },
      scrollTrigger: { trigger: el, start: 'top 92%', once: true }
    });
  });

  /* ──────────────────────────── 09 · MARQUEE ──────────────────────────── */

  $$('[data-marquee]').forEach(function (box) {
    var track = $('.marquee__track', box);
    if (!track) return;

    /* Inhalt verdoppeln → nahtloser Loop bei xPercent -50 */
    track.innerHTML += track.innerHTML;

    if (!hasGSAP || reduce) return;

    var rev = box.getAttribute('data-dir') === '-1';
    gsap.fromTo(track,
      { xPercent: rev ? -50 : 0 },
      { xPercent: rev ? 0 : -50, duration: 34, ease: 'none', repeat: -1 });
  });

  /* ──────────────── 10 · VORHER/NACHHER-VERGLEICH (2×) ─────────────────── */

  $$('[data-cmp]').forEach(function (box) {
    var handle = $('[data-cmp-handle]', box);
    if (!handle) return;

    var dragging = false;

    function setPos(pct, announce) {
      pct = Math.max(0, Math.min(100, pct));
      box.style.setProperty('--pos', pct + '%');
      handle.setAttribute('aria-valuenow', Math.round(pct));
      if (announce !== false) {
        handle.setAttribute('aria-valuetext', Math.round(pct) + ' % ' +
          ($('.cmp__label--b', box) ? $('.cmp__label--b', box).textContent : 'Nachher'));
      }
    }

    function fromEvent(e) {
      var r = box.getBoundingClientRect();
      setPos(((e.clientX - r.left) / r.width) * 100);
    }

    box.addEventListener('pointerdown', function (e) {
      dragging = true;
      box.setPointerCapture(e.pointerId);
      fromEvent(e);
    });
    box.addEventListener('pointermove', function (e) { if (dragging) fromEvent(e); });
    box.addEventListener('pointerup', function (e) {
      dragging = false;
      if (box.hasPointerCapture(e.pointerId)) box.releasePointerCapture(e.pointerId);
    });
    box.addEventListener('pointercancel', function () { dragging = false; });

    /* Tastatur: Pfeile ±3 %, mit Shift ±10 %, Pos1/Ende auf die Extreme */
    handle.addEventListener('keydown', function (e) {
      var cur = parseFloat(handle.getAttribute('aria-valuenow')) || 50;
      var step = e.shiftKey ? 10 : 3;
      var next = null;

      if (e.key === 'ArrowLeft'  || e.key === 'ArrowDown') next = cur - step;
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp')   next = cur + step;
      if (e.key === 'Home') next = 0;
      if (e.key === 'End')  next = 100;

      if (next !== null) { e.preventDefault(); setPos(next); }
    });

    setPos(50);
  });

  /* ─────────────────────── 11 · BILD-PARALLAX (scrub) ──────────────────── */
  /* Bilder sind per CSS auf 1.14 überskaliert; wir bewegen max. ±7 %.      */

  if (hasGSAP && !reduce) {
    $$('[data-parallax]').forEach(function (img) {
      gsap.fromTo(img,
        { yPercent: -7, scale: 1.14 },
        {
          yPercent: 7, scale: 1.14, ease: 'none',
          scrollTrigger: {
            trigger: img.closest('figure, .frame, .stage, .tile') || img,
            start: 'top bottom',
            end: 'bottom top',
            scrub: true,
            invalidateOnRefresh: true
          }
        });
    });

    /* Betriebs-Bühne: der Hallenblick zieht etwas langsamer mit */
    var stageImg = $('.stage__img');
    if (stageImg) gsap.set(stageImg, { transformOrigin: '50% 50%' });
  }

  /* ──────────── 12 · LEISTUNGEN · VORSCHAUBILD AM CURSOR (Desktop) ─────── */

  (function () {
    var list = $('#svcList');
    var peek = $('#svcPeek');
    var peekImg = $('#svcPeekImg');
    if (!list || !peek || !hasGSAP || reduce || !canHover) return;
    if (!window.matchMedia('(min-width: 1001px)').matches) return;

    var xTo = gsap.quickTo(peek, 'x', { duration: .5, ease: 'power3' });
    var yTo = gsap.quickTo(peek, 'y', { duration: .5, ease: 'power3' });
    var visible = false;

    list.addEventListener('pointermove', function (e) {
      var r = list.getBoundingClientRect();
      xTo(e.clientX - r.left - 135);
      yTo(e.clientY - r.top - 101);
    });

    $$('.svc__row', list).forEach(function (row) {
      row.addEventListener('pointerenter', function () {
        var src = row.getAttribute('data-peek');
        if (src && peekImg.getAttribute('src') !== src) peekImg.setAttribute('src', src);
        if (!visible) {
          visible = true;
          gsap.to(peek, { opacity: 1, duration: .35, ease: 'power2.out' });
        }
      });
    });

    list.addEventListener('pointerleave', function () {
      visible = false;
      gsap.to(peek, { opacity: 0, duration: .3, ease: 'power2.out' });
    });
  }());

  /* ───────────────────────── 13 · MAGNET-BUTTONS ───────────────────────── */

  if (hasGSAP && !reduce && canHover) {
    $$('[data-magnet]').forEach(function (el) {
      var xTo = gsap.quickTo(el, 'x', { duration: .45, ease: 'power3' });
      var yTo = gsap.quickTo(el, 'y', { duration: .45, ease: 'power3' });

      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        xTo((e.clientX - (r.left + r.width / 2)) * .22);
        yTo((e.clientY - (r.top + r.height / 2)) * .32);
      });
      el.addEventListener('pointerleave', function () { xTo(0); yTo(0); });
    });
  }

  /* ──────────────────────────── 14 · FORMULAR ─────────────────────────── */
  /* Reines Frontend — es gibt kein Backend. Wir bestätigen freundlich und
     verweisen auf Telefon und E-Mail.                                      */

  var form = $('#kontaktForm');
  var note = $('#formNote');

  if (form && note) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      if (!form.checkValidity()) {
        note.classList.add('is-error');
        note.textContent = 'Bitte prüfen Sie die markierten Felder — Name, E-Mail, Nachricht und die Einwilligung brauchen wir.';
        var firstInvalid = form.querySelector(':invalid');
        if (firstInvalid) firstInvalid.focus();
        return;
      }

      var name = (form.elements.name && form.elements.name.value.trim().split(' ')[0]) || '';
      note.classList.remove('is-error');
      note.textContent = (name ? name + ', vielen ' : 'Vielen ') +
        'Dank für Ihre Anfrage. Wir melden uns zügig zurück. Wenn es eilt: 0 87 03 / 93 31 - 0 oder info@walczok-gmbh.de.';

      form.reset();
      if (hasGSAP && !reduce) {
        gsap.fromTo(note, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: .5 });
      }
    });
  }

  /* ───────────────────────────── 15 · KLEINKRAM ───────────────────────── */

  var year = $('#year');
  if (year) year.textContent = new Date().getFullYear();

  /* will-change nach dem Intro wieder abräumen */
  window.setTimeout(function () {
    $$('.btn').forEach(function (b) { b.style.willChange = 'auto'; });
  }, 4000);

  /* Layout nach dem Laden von Schriften und Bildern neu vermessen */
  if (hasGSAP) {
    window.addEventListener('load', function () { ScrollTrigger.refresh(); });
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { ScrollTrigger.refresh(); });
    }
  }

}());
