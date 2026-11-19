/* ==========================================================================
   Paul Walczok GmbH — Bewegung
   Wenig, dafuer gezielt. Drei Bewegungen tragen die Seite:
     1. Hero-Intro (Zeilen der H1 aus der Maske, Rest in einer Timeline)
     2. Bildschieber: jede Bildbox oeffnet sich einmal von oben nach unten
     3. Masslinien der Vorteile ziehen sich auf
   Dazu die Bildmarke im Kopf, der Branchen-Ring (nur Drehung) und der Film
   im Block Laserschweissen. Text,
   Listen, Ueberschriften und Karten stehen einfach da. Kein Pinning, kein
   Preloader. Nur transform, opacity und clip-path. Ohne GSAP bleibt die Seite
   vollstaendig sichtbar.
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

  /* Bildboxen fuer den Schieber: Rahmen (.frame) und die Fotoflaeche der
     Leistungskarten (.svc__top). Nur die aeusserste Box bekommt die Klasse,
     damit verschachtelte Rahmen nicht doppelt aufgehen. Den Startzustand
     (zu) setzt das CSS ueber .gsap .wipe — also nur fuer genau die Boxen,
     die weiter unten auch wieder geoeffnet werden. */
  var boxen = [];
  if (hasGsap && !reduce) {
    Array.prototype.forEach.call(document.querySelectorAll('.frame, .svc__top'), function (el) {
      if (el.parentElement && el.parentElement.closest('.frame, .svc__top')) return;
      el.classList.add('wipe');
      boxen.push(el);
    });
  }

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
  var mainEl = document.querySelector('main');
  var ftrEl  = document.querySelector('.ftr');
  function sperreSeite(an) {
    document.body.style.overflow = an ? 'hidden' : '';
    /* Inhalt hinter dem Menue fuer Tastatur und Vorlesefunktion sperren:
       Tab bleibt in Kopfzeile und Menue. */
    if (mainEl) mainEl.inert = an;
    if (ftrEl) ftrEl.inert = an;
    if (lenis) { if (an) lenis.stop(); else lenis.start(); }
    /* Das offene Menue muss selbst scrollen koennen (Querformat). Der
       gestoppte Lenis wuerde Rad und Wischen sonst auch dort abfangen. */
    if (nav) { if (an) nav.setAttribute('data-lenis-prevent', ''); else nav.removeAttribute('data-lenis-prevent'); }
  }
  function navOffen() { return !!(nav && nav.classList.contains('is-open')); }
  function closeNav() {
    if (!nav || !burger) return;
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
    /* Ein Tipp ausserhalb von Menue und Burger (etwa auf die Kopfzeile)
       schliesst das Menue ebenfalls. */
    document.addEventListener('click', function (e) {
      if (navOffen() && !e.target.closest('#nav, #burger')) closeNav();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navOffen()) { closeNav(); burger.focus(); }
    });
    /* Wechselt die Breite ueber die Menue-Grenze (Drehen des Tablets, groesseres
       Fenster), verschwindet der Burger. Ein offenes Menue samt Seitensperre
       bliebe sonst haengen und die Seite scrollte nicht mehr. Der Wert muss
       zum Umschaltpunkt in css/styles.css passen. */
    var mqNav = window.matchMedia('(max-width: 1259px)');
    var aufBreite = function (e) { if (!e.matches && navOffen()) closeNav(); };
    if (mqNav.addEventListener) mqNav.addEventListener('change', aufBreite);
    else if (mqNav.addListener) mqNav.addListener(aufBreite);
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

  /* Ankerspruenge: Kopfzeilenhoehe beruecksichtigen. Ein offenes Menue wird
     zuerst geschlossen — sonst ist Lenis noch gestoppt und ignoriert den
     Sprung. Die Adresse bekommt den Anker, damit Links teilbar sind und die
     Zurueck-Taste funktioniert. */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href');
    if (!id || id === '#') return;
    var t = document.querySelector(id);
    if (!t) return;
    if (navOffen()) closeNav();
    var off = -(hdr ? hdr.offsetHeight : 0) - 8;
    if (lenis) {
      e.preventDefault();
      /* Ziel absolut aus der echten Scrollposition (siehe insBild) */
      lenis.scrollTo(Math.max(0, t.getBoundingClientRect().top + window.pageYOffset + off), { duration: 1.1 });
      if (window.history && history.pushState && location.hash !== id) history.pushState(null, '', id);
      /* preventDefault nimmt dem Browser auch den Fokuswechsel. Ohne ihn
         bliebe der Tastaturfokus am Link, und der naechste Tab spraenge
         zurueck (Sprunglink wirkungslos). Das Ziel bekommt den Fokus, ohne
         dass es selbst scrollt; der Rahmen bleibt per CSS aus. */
      if (!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
      t.focus({ preventScroll: true });
    }
  });

  /* Der Bilderlauf haengt an keiner Bibliothek und laeuft deshalb vor dem
     GSAP-Zweig los. Faellt der Vendor-Stack aus, bleibt er trotzdem bedienbar. */
  initGal();
  initJobs();
  initFilme();

  /* ============================================================== LOGO ==
     DREHUNG. Die Bildmarke besteht aus Buegel und Bolzen (Vektordatei des
        Kunden). Beim Scrollen schwenkt der Buegel um die senkrechte Achse, wie
        das Bauteil in der SOLIDWORKS-Aufnahme des Kunden auf dem Drehteller;
        der Bolzen ist ein Drehteil und bleibt stehen.

        Runde 3 (19.11.2026, Kunde: beim Drehen "duenn wie Papier"): Der
        Buegel ist jetzt eine Platte mit Dicke. baueMarke() ersetzt das flache
        Rueckfallbild durch 23 Schichten (Vorder- und Rueckseite als Bild,
        dazwischen die Silhouette in der Kantenfarbe), je als linke und rechte
        Haelfte, plus Bolzen und Stirnseite in einem gemeinsamen 3D-Raum. Die
        Tiefenreihenfolge (Bolzen vor oder hinter einer Haelfte) macht der
        Browser selbst; das fruehere data-vorn entfaellt. Aufbau im CSS.
        Gesetzt werden nur --dreh (Winkel) und --kante (Deckkraft der
        Stirnseite, nur nahe 90 und 270 Grad), dazu .is-ruhe bei 0 Grad.

        Die Drehung folgt dem Scrollweg (eine halbe Umdrehung je
        Bildschirmhoehe; abwaerts vorwaerts, aufwaerts rueckwaerts), gedaempft,
        damit nichts springt. Wird 1,2 s lang nicht gescrollt, laeuft die Marke
        in 1,5 s mit weichem Auslauf zur naechsten vollen Umdrehung zurueck: in
        Ruhe und beim Laden zeigt sie genau die Ansicht des Kunden. Bei
        reduzierter Bewegung wird nichts aufgebaut, die Marke steht still.

        window.__markHold (Grad) friert einen Winkel ein, nur fuer
        Bildschirmfotos. */
  function baueMarke(m) {
    var SCHICHTEN = 22;                       /* Abstaende; 23 Lagen von 0 bis -dicke */
    var d = m.dataset;
    if (!d.buegel || !d.kante || !d.bolzen) return false;
    function el(tag, cls) { var e = document.createElement(tag); e.className = cls; return e; }
    function bild(src, cls) {
      var i = el('img', cls); i.src = src; i.alt = ''; i.decoding = 'async';
      i.width = 139; i.height = 90; return i;
    }
    var raum = el('span', 'mark__raum'), welt = el('span', 'mark__welt'), dreh = el('span', 'mark__dreh');
    for (var i = 0; i <= SCHICHTEN; i++) {
      var aussen = i === 0 || i === SCHICHTEN;
      ['l', 'r'].forEach(function (seite) {
        var s = bild(aussen ? d.buegel : d.kante, 'mark__s mark__s--' + seite + (i === 0 ? ' mark__s--vorn' : ''));
        s.style.setProperty('--i', i);
        dreh.appendChild(s);
      });
    }
    welt.appendChild(dreh);
    welt.appendChild(bild(d.bolzen, 'mark__z'));
    welt.appendChild(el('span', 'mark__kante'));
    raum.appendChild(welt);
    var flach = m.querySelector('.mark__flach');
    if (flach) flach.remove();
    m.style.setProperty('--n', SCHICHTEN);
    m.appendChild(raum);
    m.classList.add('is-3d', 'is-ruhe');
    return true;
  }

  var mark = document.getElementById('mark');
  if (mark && !reduce && baueMarke(mark)) {
    var RUHE_MS = 1200, RUECKKEHR_MS = 1500;
    var jetzt = function () { return (window.performance && performance.now) ? performance.now() : Date.now(); };
    var zielGrad = 0, grad = 0, gesetzt = null, tVor = null, letzterScroll = -1e9;
    var ruheStart = null, ruheVon = 0, laeuft = false;
    var letzterY = window.pageYOffset || 0;

    /* Der Takt laeuft nur, solange sich etwas bewegt, und wird vom naechsten
       Scrollen wieder geweckt. */
    var wecken = function () {
      if (laeuft) return;
      laeuft = true;
      tVor = null;            /* sonst ist dt der ganze Schlafzeitraum */
      requestAnimationFrame(takt);
    };

    window.addEventListener('scroll', function () {
      var y = window.pageYOffset || 0;
      zielGrad += (y - letzterY) * (180 / Math.max(320, window.innerHeight));
      letzterY = y;
      letzterScroll = jetzt();
      wecken();
    }, { passive: true });

    var takt = function (t) {
      t = t || jetzt();
      if (tVor === null) tVor = t;
      var dt = Math.min(0.1, (t - tVor) / 1000); tVor = t;   /* s, gedeckelt (Tab-Wechsel) */
      var ruht = false;
      if (t - letzterScroll > RUHE_MS) {
        if (ruheStart === null) {
          ruheStart = t; ruheVon = grad;
          zielGrad = Math.round(zielGrad / 360) * 360;
        }
        var p = Math.min(1, (t - ruheStart) / RUECKKEHR_MS);
        p = 1 - Math.pow(1 - p, 3);
        grad = ruheVon + (zielGrad - ruheVon) * p;
        ruht = p >= 1;
      } else {
        ruheStart = null;
        grad += (zielGrad - grad) * Math.min(1, dt * 7);   /* Daempfung ~140 ms */
      }
      var g = ruht ? zielGrad : grad;
      if (typeof window.__markHold === 'number') g = window.__markHold;
      g = ((g % 360) + 360) % 360;
      g = Math.round(g * 2) / 2;                           /* halbe Grad reichen */
      if (g !== gesetzt) {
        gesetzt = g;
        mark.style.setProperty('--dreh', g + 'deg');
        /* Stirnseite nur nahe 90 und 270 Grad: dort sind alle Schichten
           hauchduenn. Deckkraft faehrt mit |sin| von 0,992 (rund 83 Grad)
           bis 0,9994 (rund 88 Grad) hoch; bei 85 Grad bilden die Schichten
           das Band noch selbst, die Stirnseite liegt deckungsgleich darauf. */
        var sn = Math.abs(Math.sin(g * Math.PI / 180));
        var k = Math.max(0, Math.min(1, (sn - 0.992) / 0.0074));
        mark.style.setProperty('--kante', k.toFixed(3));
        mark.classList.toggle('is-ruhe', g === 0);
        /* Bis rund 2 Grad um 90/270 nur die Stirnseite, die Schichten sind
           dort reine Kanten (helle Haarstriche ueber dem Bolzen). */
        mark.classList.toggle('is-seitlich', Math.abs(Math.cos(g * Math.PI / 180)) < 0.035);
      }
      if (ruht) {
        grad = zielGrad;
        laeuft = false;
        return;               /* Takt anhalten, bis wieder gescrollt wird */
      }
      requestAnimationFrame(takt);
    };
    if (typeof window.__markHold === 'number') wecken();
  }

  if (!hasGsap || reduce) { initForm(); return; }

  initForm();

  /* Schriften abwarten: SplitText darf erst teilen, wenn die Webfonts stehen,
     sonst stimmen die Zeilenumbrueche nicht (und GSAP warnt). Hero-Intro und
     Scroll-Aufbau starten deshalb gemeinsam nach document.fonts.ready; Kicker,
     Sub und Act laufen so weiterhin in einer Timeline mit der Ueberschrift.
     Sicherheitsnetz: spaetestens nach 1,5 s geht es auch ohne Aufloesung los;
     fehlt document.fonts, sofort. Stehen die Schriften dann noch nicht,
     blendet die H1 nur ein, ohne SplitText (heroIntro prueft das). */
  var gestartet = false;
  function startAnim() {
    if (gestartet) return;
    gestartet = true;
    try { heroIntro(); }
    catch (e) { root.classList.remove('gsap'); root.classList.add('no-anim'); }
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
    /* Zeilen erst teilen, wenn die Webfonts stehen: sonst stimmen die
       Umbrueche nicht und GSAP warnt ("SplitText called before fonts loaded"). */
    var schriftenDa = !document.fonts || document.fonts.status === 'loaded';

    if (Split && h1 && schriftenDa) {
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

  /* ======================================================== SCROLL-AUFBAU ==
     Gebuendelt ueber ScrollTrigger.batch — ein Trigger je Gruppe, nicht je
     Element. Alles nur einmal (once). Ueberschriften, Fliesstext, Listen und
     Karten bekommen bewusst keinen Auftritt: wenn alles einschwebt, wirkt
     nichts mehr besonders, und beim Scrollen stuenden staendig halb
     durchsichtige Absaetze im Bild. Die Mitarbeiterzahl zaehlt nicht mehr
     hoch, sie steht fertig im HTML. */
  function initScroll() {

  /* Hero-Video faehrt beim Verlassen ruhig mit (leichte Parallax). Der Text
     bleibt stehen und voll deckend. Nur transform, kein Filter. */
  var heroMedia = document.querySelector('.hero__media');
  if (heroMedia) {
    G.to(heroMedia, {
      yPercent: 16, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true, invalidateOnRefresh: true }
    });
  }

  /* Masslinien der Vorteile: ziehen sich von links auf wie eine Bemassung */
  ST.batch('.adv__rule', {
    start: 'top 92%',
    once: true,
    onEnter: function (els) {
      G.to(els, { scaleX: 1, duration: .9, ease: 'power2.out', stagger: 0.08 });
    }
  });

  /* ========================================================= BILDSCHIEBER ==
     Jede Bildbox oeffnet sich einmal von oben nach unten, wie ein Schieber an
     der Maschine: clip-path inset(0 0 100% 0) -> inset(0), 0,9 s, weich ein-
     und auslaufend. Gesetzt am Rahmen, nicht am Bild — das Bild selbst bleibt
     frei fuer den Hover-Zoom per CSS. Danach faellt die Klasse weg und
     clip-path ist wieder none: nichts bleibt dauerhaft beschnitten. */
  if (boxen.length) {
    var ZU = 'inset(0% 0% 100% 0%)', AUF = 'inset(0% 0% 0% 0%)';
    ST.batch(boxen, {
      start: 'top 92%',
      once: true,
      batchMax: 4,
      onEnter: function (els) {
        G.fromTo(els, { clipPath: ZU }, {
          clipPath: AUF, duration: .9, ease: 'power2.inOut', stagger: 0.08, overwrite: true,
          onComplete: function () {
            els.forEach(function (el) { el.classList.remove('wipe'); el.style.clipPath = ''; });
          }
        });
      }
    });
  }

  /* ================================================== BRANCHEN-ZYLINDER ==
     14 Ringplaetze, sechs davon belegt — die uebrigen bleiben leer, damit die
     Karten einen offenen Bogen bilden statt eines geschlossenen Rads. Der Ring
     dreht beim Scrollen, waehrend die Bilder in den Karten gegenlaeufig
     wandern. Er faehrt NICHT mehr nach unten: die Abwaertsfahrt liess oben
     einen leeren Block stehen. Erst ab 768 px; darunter (und ohne GSAP) bleibt
     die Sektion ein schlichtes Raster. */
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
      root.classList.add('gsap-cyl');   /* Ringhoehe kommt aus dem CSS */

      /* Der Ring laeuft jetzt mit der Seite mit. Die Drehung beginnt wie
         frueher, wenn seine Oberkante bei 75 % der Fensterhoehe steht, und
         endet, wenn seine Unterkante bei 25 % steht. Damit zeigt jede
         Ringlage im Fenster dasselbe Bild wie vorher, nur ohne Abwaertsfahrt.
         Linear statt power1.inOut: gleichmaessige Drehung ohne Spitze in der
         Bildmitte. */
      function weg(start, end) {
        return { trigger: cylWrap, start: start, end: end, scrub: true, invalidateOnRefresh: true };
      }
      var imgs = cyl.querySelectorAll('.cyl__img');
      var ringWeg = weg('top 75%', 'bottom 25%');
      ringWeg.onToggle = function (self) { cyl.style.willChange = self.isActive ? 'transform' : ''; };

      /* Startwinkel: Die Referenz startet mit vier belegten Ringplaetzen bei
         -102 Grad. Wir haben sechs, also 51,4 Grad mehr Bogen (25,7 je Platz) —
         der gleiche Bildeindruck beim Eintritt ergibt sich deshalb bei -153:
         links stehen zweieinhalb Karten, die rechte Haelfte ist frei, dann
         schwenken sie ein. Bis -25 wandert jede Karte genau einmal durch die
         Bildmitte. */
      G.fromTo(cyl, { rotateY: -153 }, {
        rotateY: -25, ease: 'none',
        scrollTrigger: ringWeg
      });
      /* Bilder wandern in den Karten gegenlaeufig: waagrecht mit der Drehung,
         senkrecht ueber die ganze Sichtzeit. */
      G.fromTo(imgs, { x: 100 }, {
        x: -100, ease: 'none',
        scrollTrigger: weg('top 75%', 'bottom 25%')
      });
      G.fromTo(imgs, { y: -100 }, {
        y: 100, ease: 'none',
        scrollTrigger: weg('top bottom', 'bottom top')
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

    /* Passen alle Bilder ohne Lauf in die Bahn (drei Hallenbilder ab 981 px),
       gibt es nichts zu schieben: dann sind beide Pfeile weg statt blass. */
    var pfeile = prev.parentElement;
    function stand() {
      var max = maximum();
      prev.setAttribute('aria-disabled', track.scrollLeft <= 2 ? 'true' : 'false');
      next.setAttribute('aria-disabled', track.scrollLeft >= max - 2 ? 'true' : 'false');
      if (pfeile) pfeile.classList.toggle('is-leer', max <= 2);
    }

    function schiebe(weite) {
      var max = maximum();
      var ziel = Math.max(0, Math.min(max, track.scrollLeft + weite));
      /* Restwege unter einem halben Schritt gleich mitnehmen: sonst schiebt der
         letzte Klick nur noch ein paar Pixel und das Ende fluchtet nicht. */
      var halb = Math.abs(weite) / 2;
      if (weite > 0 && max - ziel < halb) ziel = max;
      if (weite < 0 && ziel < halb) ziel = 0;
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

  /* =============================================================== FILME ==
     19.11.2026: Film im Block Laserschweissen (video[data-film]). Er laeuft
     stumm in Schleife, aber nur, solange er im Bild ist: IntersectionObserver
     startet ihn ab einem Drittel Sichtbarkeit und haelt ihn an, wenn er
     hinauslaeuft (spart Akku und Datenvolumen; preload="none" laedt erst
     beim ersten Start). Unter dem Film steht ein Knopf "Film anhalten", er
     ist per Tastatur erreichbar; wer anhaelt, bekommt den Film nicht
     ungefragt zurueck (WCAG 2.2.2). Bei reduzierter Bewegung oder ohne
     IntersectionObserver startet nichts von selbst; dann traegt der Film die
     Bedienleiste des Browsers und der Knopf bleibt versteckt.
     Haengt an keiner Bibliothek und laeuft deshalb vor dem GSAP-Zweig. */
  function initFilme() {
    Array.prototype.forEach.call(document.querySelectorAll('video[data-film]'), function (v) {
      var fig = v.closest('figure');
      var knopf = fig ? fig.querySelector('[data-film-btn]') : null;
      if (reduce || !('IntersectionObserver' in window)) {
        v.controls = true;
        return;
      }
      var angehalten = false, imBild = false;
      function abspielen() {
        var p = v.play();
        if (p && typeof p.catch === 'function') p.catch(function () { v.controls = true; if (knopf) knopf.hidden = true; });
      }
      function beschriften() {
        /* Der Knopf zeigt, was ein Klick tut: ausserhalb des Bildes ruht der
           Film von selbst, das zaehlt nicht als "angehalten". */
        if (knopf) knopf.textContent = angehalten ? 'Film abspielen' : 'Film anhalten';
      }
      new IntersectionObserver(function (eintraege) {
        eintraege.forEach(function (e) {
          imBild = e.isIntersecting;
          if (imBild && !angehalten) abspielen();
          else if (!imBild && !v.paused) v.pause();
          beschriften();
        });
      }, { threshold: 0.35 }).observe(v);
      if (knopf) {
        knopf.hidden = false;
        knopf.addEventListener('click', function () {
          angehalten = !angehalten;
          if (angehalten) v.pause(); else abspielen();
          beschriften();
        });
      }
    });
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
     Versand ueber Netlify Forms. Geprueft wird hier mit einer eigenen Meldung
     je Feld (novalidate setzt erst dieses Skript; ohne Skript prueft der
     Browser selbst und schickt das Formular normal per POST).
     Gesendet wird per fetch als application/x-www-form-urlencoded an "/".
     Netlify erkennt die Anfrage am versteckten Feld form-name. Die
     Erfolgsmeldung kommt NUR, wenn Netlify mit 2xx antwortet; sonst bleibt
     alles Getippte stehen und die Meldung nennt Telefon und E-Mail. */
  function initForm() {
    var form = document.getElementById('form');
    var note = document.getElementById('formNote');
    if (!form || !note) return;
    form.noValidate = true;

    var knopf  = form.querySelector('button[type="submit"]');
    var fields = form.querySelectorAll('[required]');
    var LEER = {
      fName: 'Bitte geben Sie Ihren Namen an.',
      fMail: 'Bitte geben Sie Ihre E-Mail-Adresse an.',
      fMsg:  'Bitte beschreiben Sie kurz Ihr Anliegen.',
      fDsg:  'Bitte bestätigen Sie, dass Sie die Datenschutzerklärung gelesen haben.'
    };
    /* Der Ausweg als eigene, mit "Oder" angebundene Moeglichkeit, nicht als
       zweiter Pflichtschritt. */
    var AUSWEG = 'Oder erreichen Sie uns direkt: Telefon <a href="tel:+49870393310">08703&nbsp;9331-0</a>, ' +
                 'E-Mail <a href="mailto:info@walczok-gmbh.de">info@walczok-gmbh.de</a>.';
    /* Zahlen bis zwoelf schreibt die Seite aus; es gibt vier Pflichtfelder. */
    var ZAHLWORT = ['', 'ein', 'zwei', 'drei', 'vier'];

    function fehlerText(f) {
      if (f.type === 'checkbox') return f.checked ? '' : LEER[f.id];
      var v = f.value.trim();
      if (!v) return LEER[f.id] || 'Bitte füllen Sie dieses Feld aus.';
      if (f.type === 'email' && (!f.checkValidity() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v))) {
        return 'Bitte geben Sie eine gültige E-Mail-Adresse an, zum Beispiel name@firma.de.';
      }
      return '';
    }
    function zeige(f, text) {
      var err = document.getElementById(f.id + 'Err');
      f.setAttribute('aria-invalid', text ? 'true' : 'false');
      if (!err) return;
      err.textContent = text;
      err.hidden = !text;
      if (text) f.setAttribute('aria-describedby', err.id);
      else f.removeAttribute('aria-describedby');
    }
    function status(html, art, sammel) {
      note.className = 'form__note' + (art ? ' is-' + art : '');
      note.innerHTML = html;
      if (sammel) note.setAttribute('data-sammel', ''); else note.removeAttribute('data-sammel');
    }
    /* Sammelmeldung ueber dem Absenden: nennt die Zahl der markierten Felder */
    function sammelText(anzahl) {
      return anzahl === 1 ? 'Bitte prüfen Sie das markierte Feld.'
                          : 'Bitte prüfen Sie die ' + (ZAHLWORT[anzahl] || anzahl) + ' markierten Felder.';
    }
    /* Ins Bild holen, mit Luft unter der Kopfzeile. Das Ziel wird absolut aus
       der echten Scrollposition gerechnet: Lenis' eigener Stand kann nach
       einem nativen Sprung (Fokus, Browser) kurz veraltet sein. */
    function insBild(el) {
      var y = Math.max(0, el.getBoundingClientRect().top + window.pageYOffset - (hdr ? hdr.offsetHeight : 0) - 72);
      if (lenis) lenis.scrollTo(y, { duration: .8 });
      else window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
    }

    /* Nach dem ersten Absendeversuch pruefen die Felder live: eine Meldung
       verschwindet, sobald die Angabe stimmt. */
    var geprueft = false;
    Array.prototype.forEach.call(fields, function (f) {
      f.addEventListener(f.type === 'checkbox' ? 'change' : 'input', function () {
        if (!geprueft) return;
        zeige(f, fehlerText(f));
        /* Die rote Sammelmeldung zaehlt mit und verschwindet, sobald kein Feld
           mehr markiert ist. Eine Versandfehler-Meldung (Telefon, E-Mail)
           bleibt dagegen stehen. */
        if (note.hasAttribute('data-sammel')) {
          var rest = form.querySelectorAll('[aria-invalid="true"]').length;
          if (rest) status(sammelText(rest), 'error', true); else status('', '');
        }
      });
    });

    var sendet = false;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (sendet) return;
      geprueft = true;

      var erstes = null, anzahl = 0;
      Array.prototype.forEach.call(fields, function (f) {
        var t = fehlerText(f);
        zeige(f, t);
        if (t) { anzahl++; if (!erstes) erstes = f; }
      });
      if (erstes) {
        status(sammelText(anzahl), 'error', true);
        insBild(erstes);
        erstes.focus({ preventScroll: true });
        return;
      }

      sendet = true;
      if (knopf) knopf.setAttribute('aria-disabled', 'true');
      status('Ihre Anfrage wird gesendet …', 'busy');

      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(form)).toString()
      }).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        status('Vielen Dank. Ihre Anfrage ist bei uns angekommen, wir melden uns zügig bei Ihnen.', 'ok');
        form.reset();
        geprueft = false;
        Array.prototype.forEach.call(fields, function (f) { f.removeAttribute('aria-invalid'); });
      }).catch(function () {
        status('Ihre Anfrage konnte gerade nicht gesendet werden. Ihre Angaben sind noch da, versuchen Sie es bitte gleich noch einmal. ' + AUSWEG, 'error');
      }).then(function () {
        sendet = false;
        if (knopf) knopf.removeAttribute('aria-disabled');
        /* Den Knopf ins Bild holen, nicht nur die Meldung: er behaelt den
           Tastaturfokus und laege sonst unter der festen Kopfzeile
           (WCAG 2.4.11). Die Meldung steht direkt darunter. */
        insBild(knopf || note);
      });
    });
  }
}());
