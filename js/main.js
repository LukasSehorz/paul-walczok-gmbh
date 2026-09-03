/* ==========================================================================
   Paul Walczok GmbH — Bewegung
   Sparsam und strukturstuetzend: 3D-Logo, Hero-Intro mit leichter Parallax,
   Zeilenmasken der Ueberschriften, gebuendelte Reveals, Zaehler, Bild-Reveal,
   Stellen-Schalter. Kein Pinning, kein Preloader, keine Parallax-Schwaerme.
   Nur transform und opacity. Ohne GSAP bleibt die Seite vollstaendig sichtbar.
   ========================================================================== */
(function () {
  'use strict';

  var root  = document.documentElement;
  var G     = window.gsap;
  var ST    = window.ScrollTrigger;
  var Split = window.SplitText;
  var LenisC = window.Lenis;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasGsap = !!(G && ST);

  /* Erst jetzt — nach nachweislich geladenem Stack — duerfen die versteckten
     Startzustaende greifen. main.js laeuft vor dem ersten Paint. */
  if (hasGsap && !reduce) root.classList.add('gsap');
  root.classList.add('anim-ready');

  /* ------------------------------------------------------------ Jahreszahl */
  var yr = document.getElementById('year');
  if (yr) yr.textContent = new Date().getFullYear();

  /* --------------------------------------------------------- Kopfzeile fix */
  var hdr = document.getElementById('hdr');
  var stuck = false;
  function onScrollHdr() {
    var s = (window.scrollY || window.pageYOffset) > 24;
    if (s !== stuck) { stuck = s; hdr.classList.toggle('is-stuck', s); }
  }
  onScrollHdr();
  window.addEventListener('scroll', onScrollHdr, { passive: true });

  /* -------------------------------------------------------------- Mobilmenu */
  var burger = document.getElementById('burger');
  var nav    = document.getElementById('nav');
  /* Bei offenem Menue steht die Seite dahinter still. Ohne die Sperre scrollt
     das Dokument unter dem Menue weiter, sobald man ueber die Liste wischt. */
  function sperreSeite(an) {
    document.body.style.overflow = an ? 'hidden' : '';
    if (lenis) { if (an) lenis.stop(); else lenis.start(); }
  }
  function closeNav() {
    nav.classList.remove('is-open');
    if (hdr) hdr.classList.remove('is-navopen');
    burger.setAttribute('aria-expanded', 'false');
    sperreSeite(false);
  }
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      if (hdr) hdr.classList.toggle('is-navopen', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      sperreSeite(open);
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeNav();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) { closeNav(); burger.focus(); }
    });
  }

  /* ---------------------------------------------------- Sanftes Scrollen */
  var lenis = null;
  if (LenisC && hasGsap && !reduce) {
    lenis = new LenisC({ duration: 1.05, smoothWheel: true, wheelMultiplier: 1, touchMultiplier: 1.6 });
    root.style.scrollBehavior = 'auto';
    lenis.on('scroll', ST.update);
    G.ticker.add(function (t) { lenis.raf(t * 1000); });
    G.ticker.lagSmoothing(0);
  }

  /* Ankerspruenge: Kopfzeilenhoehe beruecksichtigen */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href');
    if (!id || id === '#') return;
    var t = document.querySelector(id);
    if (!t) return;
    var off = -(hdr ? hdr.offsetHeight : 0) - 8;
    if (lenis) { e.preventDefault(); lenis.scrollTo(t, { offset: off, duration: 1.1 }); }
  });

  /* Der Bilderlauf haengt an keiner Bibliothek und laeuft deshalb vor dem
     GSAP-Zweig los. Faellt der Vendor-Stack aus, bleibt er trotzdem bedienbar. */
  initGal();
  initJobs();

  /* ============================================================== LOGO ==
     Die Schraube steht fest, der Messbuegel dreht sich in der Bildebene um die
     Schraubenachse (Bildmitte der Ebene). Beim Scrollen folgt der Winkel dem
     Scrollweg (eine halbe Umdrehung je Bildschirmhoehe; abwaerts vorwaerts,
     aufwaerts rueckwaerts), gedaempft, damit nichts springt. Wird 1,2 s lang
     nicht gescrollt, kehrt der Buegel in 1,5 s mit weichem Auslauf (kubisches
     Ease-out, ohne Ueberschwingen) zum naechsten Vielfachen von 360 Grad
     zurueck, also in die Originallage, und bleibt dort stehen: in Ruhe ist
     das Logo exakt die Kundendatei. Beim
     Laden steht er bei 0 Grad. Bei reduzierter Bewegung passiert nichts.
     window.__markHold (Zahl) friert einen Winkel ein, nur fuer Bildschirmfotos. */
  var markFrame = document.getElementById('markFrame');
  if (markFrame && !reduce) {
    var RUHE_MS = 1200, RUECKKEHR_MS = 1500;
    var jetzt = function () { return (window.performance && performance.now) ? performance.now() : Date.now(); };
    var scrollWinkel = 0, winkel = 0, gesetzt = null, tVor = null, letzterScroll = -1e9;
    var ruheStart = null, ruheVon = 0;
    var letzterY = window.pageYOffset || 0;

    window.addEventListener('scroll', function () {
      var y = window.pageYOffset || 0;
      scrollWinkel += (y - letzterY) * (180 / Math.max(320, window.innerHeight));
      letzterY = y;
      letzterScroll = jetzt();
    }, { passive: true });

    (function takt(t) {
      t = t || jetzt();
      if (tVor === null) tVor = t;
      var dt = Math.min(0.1, (t - tVor) / 1000); tVor = t;   /* s, gedeckelt (Tab-Wechsel) */
      if (t - letzterScroll > RUHE_MS) {
        /* Ruhe: Ziel auf die Originallage einrasten und in RUECKKEHR_MS mit
           kubischem Ease-out dorthin laufen (endet exakt, kein Ueberschwingen) */
        if (ruheStart === null) {
          ruheStart = t; ruheVon = winkel;
          scrollWinkel = Math.round(scrollWinkel / 360) * 360;
        }
        var p = Math.min(1, (t - ruheStart) / RUECKKEHR_MS);
        p = 1 - Math.pow(1 - p, 3);
        winkel = ruheVon + (scrollWinkel - ruheVon) * p;
      } else {
        ruheStart = null;
        winkel += (scrollWinkel - winkel) * Math.min(1, dt * 7);   /* Daempfung ~140 ms */
      }
      var w = Math.round(winkel * 10) / 10;
      if (typeof window.__markHold === 'number') w = window.__markHold;  /* nur fuer Bildschirmfotos */
      if (w !== gesetzt) {
        gesetzt = w;
        markFrame.style.transform = 'rotate(' + w + 'deg)';
      }
      requestAnimationFrame(takt);
    }());
  }

  if (!hasGsap || reduce) { initForm(); return; }

  initForm();

  /* Schriften abwarten: SplitText darf erst teilen, wenn die Webfonts stehen,
     sonst stimmen die Zeilenumbrueche nicht (und GSAP warnt). Hero-Intro und
     Scroll-Aufbau starten deshalb gemeinsam nach document.fonts.ready; Kicker,
     Sub und Act laufen so weiterhin in einer Timeline mit der Ueberschrift.
     Sicherheitsnetz: spaetestens nach 1,5 s geht es auch ohne Aufloesung los;
     fehlt document.fonts, sofort. */
  var gestartet = false;
  function startAnim() {
    if (gestartet) return;
    gestartet = true;
    heroIntro();
    /* Der Scroll-Aufbau haengt sich hinter den ersten Bildwechsel: so faellt
       der Intro-Aufbau nicht in eine einzige lange Aufgabe, und die
       Hero-Bewegung laeuft auf schwachen Geraeten von Anfang an sauber. */
    if (window.requestAnimationFrame) {
      requestAnimationFrame(function () { requestAnimationFrame(safeInitScroll); });
    } else {
      safeInitScroll();
    }
  }
  var fontsReady = document.fonts && document.fonts.ready;
  if (fontsReady && typeof fontsReady.then === 'function') {
    fontsReady.then(startAnim, startAnim);
    setTimeout(startAnim, 1500);
  } else {
    startAnim();
  }
  return;

  /* ========================================================== HERO-INTRO == */
  function heroIntro() {
    var h1 = document.querySelector('.hero__h1');
    var tl = G.timeline({ defaults: { ease: 'power3.out' }, delay: 0.12 });

    if (Split && h1) {
      var split = new Split(h1, { type: 'lines', mask: 'lines', linesClass: 'hl' });
      G.set(h1, { opacity: 1 });
      tl.from(split.lines, { yPercent: 112, duration: 1.0, stagger: 0.09 }, 0.1);
    } else if (h1) {
      tl.fromTo(h1, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: .9 }, 0.1);
    }

    tl.fromTo('.hero__kicker', { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: .7 }, 0)
      .fromTo('.hero__sub',    { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .8 }, 0.5)
      .fromTo('.hero__act',    { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: .8 }, 0.62)
      .fromTo('.hero__proof',  { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: .8 }, 0.8);
  }

  /* Ausfallschutz: bricht der Scroll-Aufbau ab, faellt die Seite auf den
     sichtbaren Zustand zurueck, statt mit unsichtbaren Sektionen stehenzubleiben. */
  function safeInitScroll() {
    try { initScroll(); }
    catch (e) { root.classList.remove('gsap'); root.classList.add('no-anim'); }
  }

  /* ======================================================= SCROLL-REVEALS ==
     Gebuendelt ueber ScrollTrigger.batch — ein Trigger je Gruppe, nicht je
     Element. Alles nur einmal (once). */
  function initScroll() {

  /* Hero-Video faehrt beim Verlassen langsam mit, der Text etwas schneller.
     Nur transform, kein Filter. */
  var heroMedia = document.querySelector('.hero__media');
  if (heroMedia) {
    G.to(heroMedia, {
      yPercent: 16, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true, invalidateOnRefresh: true }
    });
    G.to('.hero__in', {
      yPercent: -8, opacity: .25, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: '40% top', end: 'bottom top', scrub: true, invalidateOnRefresh: true }
    });
  }

  /* Sektionsueberschriften: jede Zeile faehrt aus einer eigenen Maske hoch.
     autoSplit teilt bei Breitenwechsel neu und ruft onSplit erneut auf. Ohne
     SplitText bleibt die Ueberschrift einfach sichtbar, der umgebende .rv-Block
     blendet sie dann mit ein. */
  var h2s = document.querySelectorAll('.h2');
  if (Split && h2s.length) {
    h2s.forEach(function (h) {
      G.set(h, { opacity: 1 });
      Split.create(h, {
        type: 'lines', mask: 'lines', linesClass: 'hl', autoSplit: true,
        onSplit: function (self) {
          return G.from(self.lines, {
            yPercent: 110, duration: .95, ease: 'power3.out', stagger: .09,
            scrollTrigger: { trigger: h, start: 'top 88%', once: true }
          });
        }
      });
    });
  } else {
    G.set(h2s, { opacity: 1 });
  }

  ST.batch('.rv', {
    start: 'top 88%',
    once: true,
    batchMax: 6,
    onEnter: function (els) {
      G.fromTo(els,
        { opacity: 0, y: 26 },
        { opacity: 1, y: 0, duration: .85, ease: 'power3.out', stagger: 0.08, overwrite: true });
    }
  });

  /* Akzentlinien der Vorteile-Spalten wachsen von links auf */
  ST.batch('.adv__rule', {
    start: 'top 92%',
    once: true,
    onEnter: function (els) {
      G.to(els, { scaleX: 1, duration: .9, ease: 'power2.out', stagger: 0.08 });
    }
  });

  /* ========================================================= BILD-REVEAL ==
     Leichte Skalierung 1.04 -> 1, hoechstens drei gleichzeitig. */
  ST.batch('.frame > img', {
    start: 'top 92%',
    once: true,
    batchMax: 3,
    onEnter: function (els) {
      els.forEach(function (el) { el.style.willChange = 'transform'; });
      G.to(els, {
        scale: 1, duration: 1.25, ease: 'power2.out', stagger: 0.1, overwrite: true,
        onComplete: function () { els.forEach(function (el) { el.style.willChange = ''; }); }
      });
    }
  });

  /* ============================================================= ZAEHLER ==
     Maschinendaten und Gruendungsjahr werden NICHT gezaehlt — waehrend des
     Hochlaufens stuenden sonst plausibel aussehende, aber falsche Angaben
     ueber den Betrieb auf dem Bildschirm. Nur die Mitarbeiterzahl laeuft an,
     und die in 0,6 s. */
  var nums = document.querySelectorAll('[data-count]');
  if (nums.length) {
    var stats = document.querySelector('.stats');
    ST.create({
      trigger: stats,
      start: 'top 78%',
      once: true,
      onEnter: function () {
        nums.forEach(function (el) {
          var target = parseInt(el.getAttribute('data-count'), 10);
          if (isNaN(target)) return;
          var obj = { v: 0 };
          el.textContent = '0';
          G.to(obj, {
            v: target, duration: 0.6, ease: 'power2.out',
            onUpdate: function () { el.textContent = String(Math.round(obj.v)); },
            onComplete: function () { el.textContent = String(target); }
          });
        });
      }
    });
  }

  /* ================================================== BRANCHEN-ZYLINDER ==
     14 Ringplaetze, sechs davon belegt — die uebrigen bleiben leer, damit die
     Karten einen offenen Bogen bilden statt eines geschlossenen Rads. Der Ring
     dreht beim Scrollen von -102 auf -25 Grad und schiebt sich nach unten,
     waehrend die Bilder in den Karten gegenlaeufig wandern. Erst ab 768 px;
     darunter (und ohne GSAP) bleibt die Sektion ein schlichtes Raster. */
  var cyl      = document.getElementById('cyl');
  var cylWrap  = document.getElementById('cylWrap');
  var cylStage = document.getElementById('cylStage');

  if (cyl && cylWrap && cylStage) {
    var TOTAL = 14;
    for (var ci = cyl.children.length; ci < TOTAL; ci++) {
      var slot = document.createElement('li');
      slot.className = 'cyl__c';
      slot.setAttribute('data-empty', '');
      slot.setAttribute('aria-hidden', 'true');
      cyl.appendChild(slot);
    }
    Array.prototype.forEach.call(cyl.children, function (card, i) {
      card.style.setProperty('--index', i + 1);
    });

    G.matchMedia().add('(min-width: 768px)', function () {
      root.classList.add('gsap-cyl');   /* Hoehe des Scrollwegs kommt aus dem CSS */

      var base = {
        trigger: cylWrap, start: 'top 75%', end: 'bottom 25%',
        scrub: true, invalidateOnRefresh: true,
        onToggle: function (self) { cyl.style.willChange = self.isActive ? 'transform' : ''; }
      };
      var imgs = cyl.querySelectorAll('.cyl__img');

      /* Startwinkel: die Vorlage beginnt bei -102 Grad, hat aber nur vier belegte
         Ringplaetze. Sechs Karten spannen einen Bogen von 5 x 25,7 = 128,6 Grad
         und stuenden bei -102 schon quer ueber den Schirm. Bei -180 liegt die
         letzte Karte links der Mitte, die rechte Bildhaelfte ist frei, und die
         Karten schwenken beim Scrollen dort hinein. Bis -25 Grad wandert damit
         jede der sechs Karten genau einmal durch die Bildmitte. */
      /* Startwinkel: Die Referenz startet mit vier belegten Ringplätzen bei -102°.
         Wir haben sechs, also 51,4° mehr Bogen (25,7° je Platz) — der gleiche
         Bildeindruck beim Eintritt ergibt sich deshalb bei -153°: links stehen
         zweieinhalb Karten, die rechte Hälfte ist frei, dann schwenken sie ein. */
      G.fromTo(cyl, { rotateY: -153 }, {
        rotateY: -25, yPercent: 100, ease: 'power1.inOut',
        scrollTrigger: base
      });
      G.fromTo(imgs, { x: 100 }, {
        x: -100, ease: 'power1.inOut',
        scrollTrigger: { trigger: cylWrap, start: 'top 75%', end: 'bottom 25%', scrub: true, invalidateOnRefresh: true }
      });
      G.fromTo(imgs, { y: -100 }, {
        y: 100, ease: 'none',
        scrollTrigger: { trigger: cylWrap, start: 'top bottom', end: 'bottom top', scrub: true, invalidateOnRefresh: true }
      });

      return function () {
        root.classList.remove('gsap-cyl');
        cylWrap.style.height = '';
        cyl.style.willChange = '';
        G.set(cyl, { clearProps: 'transform' });
        G.set(imgs, { clearProps: 'transform' });
      };
    });
  }

  ST.refresh();
  window.addEventListener('load', function () { ST.refresh(); });
  }

  /* ====================================================== BILDERLAUF ==
     Anwendungsbeispiele der Eigenentwicklungen. Gescrollt wird nativ ueber
     overflow-x mit Scroll-Snap, die beiden Pfeile schieben um genau eine
     Kartenbreite. Kein Timer, kein Autoplay, keine Bibliothek.

     Am Ende bekommen die Pfeile `aria-disabled` statt `disabled`. Ein Knopf mit
     `disabled` faellt aus dem Tab-Lauf, und wer ihn per Tastatur ausloest,
     verliert im selben Moment den Fokus an `body` und steht wieder am Anfang
     des Dokuments. So bleiben beide Knoepfe erreichbar und laufen am Anschlag
     nur folgenlos. Zusaetzlich bedienen Pfeiltasten, Pos1 und Ende den Lauf,
     alle mit derselben Schrittweite wie die Knoepfe. */
  function initGal() {
    var gal = document.querySelector('[data-gal]');
    if (!gal) return;

    var track = gal.querySelector('[data-gal-track]');
    var prev  = gal.querySelector('[data-gal-prev]');
    var next  = gal.querySelector('[data-gal-next]');
    if (!track || !prev || !next) return;

    function schritt() {
      var karte = track.firstElementChild;
      if (!karte) return track.clientWidth * 0.8;
      var lueckeRoh = parseFloat(getComputedStyle(track).columnGap || '0');
      var luecke = isNaN(lueckeRoh) ? 0 : lueckeRoh;
      return karte.getBoundingClientRect().width + luecke;
    }

    function maximum() { return track.scrollWidth - track.clientWidth; }

    function stand() {
      var max = maximum();
      prev.setAttribute('aria-disabled', track.scrollLeft <= 2 ? 'true' : 'false');
      next.setAttribute('aria-disabled', track.scrollLeft >= max - 2 ? 'true' : 'false');
    }

    function schiebe(weite) {
      var ziel = Math.max(0, Math.min(maximum(), track.scrollLeft + weite));
      if (Math.abs(ziel - track.scrollLeft) < 1) return;   /* am Anschlag folgenlos */
      track.scrollTo({ left: ziel, behavior: 'smooth' });
    }
    function springe(ziel) {
      track.scrollTo({ left: Math.max(0, Math.min(maximum(), ziel)), behavior: 'smooth' });
    }

    prev.addEventListener('click', function () { schiebe(-schritt()); });
    next.addEventListener('click', function () { schiebe( schritt()); });

    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight')      { e.preventDefault(); schiebe( schritt()); }
      else if (e.key === 'ArrowLeft')  { e.preventDefault(); schiebe(-schritt()); }
      else if (e.key === 'Home')       { e.preventDefault(); springe(0); }
      else if (e.key === 'End')        { e.preventDefault(); springe(maximum()); }
    });

    var warten;
    track.addEventListener('scroll', function () {
      clearTimeout(warten);
      warten = setTimeout(stand, 80);
    }, { passive: true });
    window.addEventListener('resize', stand, { passive: true });
    stand();
  }

  /* ============================================================= STELLEN ==
     Der Kunde blendet Stellen selbst aus, indem er dem <li class="job"> das
     Attribut `hidden` gibt. Sind alle Stellen versteckt, erscheint der Hinweis
     statt der leeren Liste. Die Initiativbewerbung steht ausserhalb der Liste
     und bleibt immer sichtbar. */
  function initJobs() {
    var jobs = document.getElementById('jobs');
    var none = document.getElementById('jobsNone');
    if (!jobs || !none) return;
    var offen = jobs.querySelectorAll('.job:not([hidden])').length;
    none.hidden = offen > 0;
    jobs.hidden = offen === 0;
  }

  /* ============================================================ FORMULAR ==
     Rein im Frontend, ohne Uebertragung. */
  function initForm() {
    var form = document.getElementById('form');
    var note = document.getElementById('formNote');
    if (!form || !note) return;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var bad = null;
      var fields = form.querySelectorAll('[required]');
      Array.prototype.forEach.call(fields, function (f) {
        var ok = f.type === 'checkbox' ? f.checked : f.checkValidity() && f.value.trim() !== '';
        f.setAttribute('aria-invalid', ok ? 'false' : 'true');
        if (!ok && !bad) bad = f;
      });
      if (bad) {
        note.textContent = 'Bitte füllen Sie die Pflichtfelder aus.';
        bad.focus();
        return;
      }
      note.textContent = 'Vielen Dank. Wir melden uns zügig bei Ihnen.';
      form.reset();
      Array.prototype.forEach.call(fields, function (f) { f.removeAttribute('aria-invalid'); });
    });
  }
}());
