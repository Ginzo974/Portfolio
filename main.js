document.documentElement.classList.add('booted');   // même tard (CDN lent) : les commandes restent affichées (style.css)
(() => {
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  // appareil sans survol (doigt) : même requête que .only-touch / .only-fine dans
  // style.css, suivie en direct (raccourcis, adresse mail)
  const noHover = matchMedia('(hover: none)');
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const pad = n => String(n).padStart(2, '0');
  /* Deux éditions, un seul code : « ux » (racine) et « brand » (/brand/, data-edition
     sur <html>). data-root : préfixe des chemins d'images (« / » depuis /brand/).
     Ordre : window.PROJECT_ORDER[édition] s'il existe (projects.js), sinon les
     projets sans « only », ou réservés à cette édition, dans l'ordre du fichier. */
  const EDITION = root.dataset.edition || 'ux';
  const ROOT = root.dataset.root || '';
  const ALL = window.PROJECTS || [];
  const ORDER = (window.PROJECT_ORDER || {})[EDITION];
  const PROJECTS = ORDER ? ORDER.map(id => ALL.find(p => p.id === id)).filter(Boolean) : ALL.filter(p => !p.only || p.only === EDITION);
  // une seule famille d'icônes : flèches de 14 × 14 au trait de 1,5 px (style.css, .ic)
  const ICON_PATHS = { out: 'M3 11 11 3M5 3h6v6', left: 'M13 7H1.5M6.5 2 1.5 7l5 5', right: 'M1 7h11.5M7.5 2l5 5-5 5', up: 'M7 13V1.5M2 6.5l5-5 5 5' };
  const icon = k => `<svg class="ic ${k}" viewBox="0 0 14 14" aria-hidden="true" focusable="false"><path d="${ICON_PATHS[k]}"/></svg>`;
  const ARROW = icon('out');

  /* ---------- Liste des travaux ----------
     Seuls les sites en ligne portent une mention. Au doigt (pas de survol),
     chaque ligne montre sa vignette et une ligne « type · année ». */
  const list = $('.work-list');
  const peekIn = $('.peek-in');
  const touchList = noHover.matches;
  // titres affichés : « WEI & GO » et « e-sport » ne se coupent pas (espaces
  // insécables, gluon après le trait d'union). Pas dans les noms lus ni partagés
  const glue = s => s.replace(/ & /g, '\u00a0&\u00a0').replace(/-/g, '-\u2060');
  // grille de cartes (édition brand, classe posée dans le HTML) : ni aperçu au
  // curseur, ni vignettes au doigt, ni ajustement des titres
  const gridList = list.classList.contains('work-list--grid');
  list.classList.toggle('work-list--thumbs', touchList && !gridList);

  /* Images des projets (projects.js) : WebP dans assets/projects/<id>/, un
     fichier par largeur (« <nom>-<largeur>.webp »). width et height donnent le
     ratio avant le chargement (pas de décalage de mise en page). */
  const attr = s => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const plain = s => String(s).replace(/<[^>]*>/g, '');   // libellé HTML -> texte (aria-label)
  const dirOf = p => `${ROOT}assets/projects/${p.id}/`;
  const srcsetOf = (p, m) => m.widths.map(w => `${dirOf(p)}${m.src}-${w}.webp ${w}w`).join(', ');
  const srcOf = (p, m) => `${dirOf(p)}${m.src}-${m.widths[0]}.webp`;
  // eager : le visuel du haut de la fiche, seul chargé tout de suite ; tout le reste attend le défilement
  const pic = (p, m, sizes, eager = false) => `<img src="${srcOf(p, m)}" srcset="${srcsetOf(p, m)}" sizes="${sizes}" width="${m.w}" height="${m.h}" alt="${attr(m.alt)}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
  // couverture en 4:5 (aperçu, vignettes, projet suivant) : décorative, le titre est écrit à côté
  const coverSet = p => [200, 400, p.cover.w].map(w => `${dirOf(p)}cover-${w}.webp ${w}w`).join(', ');
  const coverImg = (p, sizes, extra = '') => `<img src="${dirOf(p)}cover-400.webp" srcset="${coverSet(p)}" sizes="${sizes}" width="800" height="1000" alt="" decoding="async" style="background-color:${p.cover.tint}"${extra}>`;
  const liveTag = p => p.tag === 'Live' ? '<span class="live-tag"><span aria-hidden="true"></span>en ligne</span>' : '';
  // carte de la grille : couverture 4:5 (décorative), numéro, titre, « type · année »,
  // et la mention « en ligne » au bout de cette ligne (le titre garde toute la largeur)
  const card = (p, i) => `
    <li><button class="work-row" type="button" data-i="${i}" style="--d:${(i % 3) * 80}ms">
      <span class="card-cover" aria-hidden="true">${coverImg(p, '(max-width: 760px) calc(100vw - 32px), (max-width: 1100px) calc(50vw - 40px), min(calc(33vw - 40px), 540px)', ' loading="lazy"')}</span>
      <span class="card-txt">
        <span class="n mono" aria-hidden="true">${pad(i + 1)}</span>
        <span class="ttl">${glue(p.title)}</span>
        <span class="meta mono"><span>${p.kind}</span><span class="sep"> · </span><span class="meta-yr">${p.year}</span></span>${liveTag(p)}
      </span>
      <span class="sr-only"> Ouvrir la fiche</span>
    </button></li>`;
  // nom de la ligne : son texte visible, puis « Ouvrir la fiche » (WCAG 2.5.3)
  if (PROJECTS.length && gridList) list.innerHTML = PROJECTS.map(card).join('');
  else if (PROJECTS.length) list.innerHTML = PROJECTS.map((p, i) => `
    <li><button class="work-row" type="button" data-i="${i}" style="--d:${(i % 4) * 70}ms">
      <span class="n mono" aria-hidden="true">${pad(i + 1)}</span>
      <span class="ttl">${glue(p.title)}${liveTag(p)}</span>
      ${touchList
        ? `<span class="meta mono"><span>${p.kind}</span><span class="sep"> · </span><span class="meta-yr">${p.year}</span></span>
      <span class="thumb" aria-hidden="true">${coverImg(p, '(max-width: 760px) 56px, 96px', ' loading="lazy"')}</span>`
        : `<span class="sr-only">Type : </span><span class="kind mono">${p.kind}</span>
      <span class="sr-only">, rôle : </span><span class="role mono">${p.role}</span>
      <span class="sr-only">, année </span><span class="yr mono">${p.year}${ARROW}</span>`}
      <span class="sr-only"> Ouvrir la fiche</span>
    </button></li>`).join('');
  // projects.js absent ou en erreur : la liste statique (noscript) prend la place
  else { const ns = $('#travaux noscript'); if (ns && !$('.work-list--static')) ns.insertAdjacentHTML('afterend', ns.textContent); }

  /* ---------- Lenis ----------
     Créé après la première image : le défilement doux n'est pas nécessaire
     pour afficher la page. Jusque-là, le scroll natif suffit.
     La boucle d'images ne tourne que pendant un défilement doux (molette,
     saut d'ancre) : au repos, la page ne demande aucune image. Clavier, barre
     de défilement et doigt restent natifs dans Lenis 1.1 : pas de boucle. */
  let lenis = null, lenisRaf = 0;
  // animate.isRunning et time : champs internes de Lenis 1.1.13, à revoir si la version change
  const lenisTick = t => {
    lenis.raf(t);
    lenisRaf = lenis.animate.isRunning ? requestAnimationFrame(lenisTick) : 0;
    // arrêt : le prochain départ repart d'un pas normal, pas du temps passé au repos
    if (!lenisRaf) lenis.time = 0;
  };
  const lenisKick = () => { if (lenis && !lenisRaf) lenisRaf = requestAnimationFrame(lenisTick); };
  function initLenis() {
    if (reduce || !window.Lenis) return;
    lenis = new Lenis({ lerp: .085, wheelMultiplier: 1 });
    window.__lenis = lenis;
    // chaque molette passe par virtual-scroll avant d'être traitée
    lenis.on('virtual-scroll', lenisKick);
    // tout défilement animé demandé à Lenis (ici ou ailleurs) relance la boucle
    const lenisScrollTo = lenis.scrollTo.bind(lenis);
    lenis.scrollTo = (...a) => { lenisScrollTo(...a); lenisKick(); };
    // le scroll est lu dans la même image que celle où Lenis l'écrit
    window.removeEventListener('scroll', queueScroll);
    lenis.on('scroll', onScroll);
    if (!caseEl.hidden) lenis.stop();
  }
  requestAnimationFrame(() => setTimeout(initLenis, 0));
  const scrollToEl = (el, instant) => {
    // hauteur réelle de la barre du haut : zone sûre de l'encoche comprise (style.css, --top-h)
    const off = el === document.body ? 0 : -($('.topbar').offsetHeight || 60) + 1;
    if (lenis) lenis.scrollTo(el, { offset: off, duration: instant ? 0 : 1.5, immediate: !!instant });
    // sans Lenis (mouvement réduit) : même calage sous la barre du haut
    else window.scrollTo({ top: el === document.body ? 0 : el.getBoundingClientRect().top + scrollY + off, behavior: instant || reduce ? 'auto' : 'smooth' });
  };
  // le focus suit le défilement : Tab repart de la section atteinte (#top : main).
  // Liens internes et touches 1 à 4 (Clavier)
  let dockHold = 0;   // fin du saut d'ancre : la barre du bas ne s'efface pas avant (voir onScroll)
  function goTo(id) {
    const target = $(id);
    if (!target) return false;
    dockHold = performance.now() + 1600;   // durée du défilement doux (1,5 s)
    scrollToEl(id === '#top' ? document.body : target);
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    history.replaceState(null, '', id === '#top' ? location.pathname + location.search : id);
    return true;
  }
  $$('a[href^="#"]').forEach(a => a.addEventListener('click', e => {
    if (goTo(a.getAttribute('href'))) e.preventDefault();
  }));

  /* ---------- Découpage en lettres ---------- */
  $$('[data-split]').forEach(el => {
    const txt = el.textContent.trim();
    el.textContent = '';
    [...txt].forEach(c => {
      const s = document.createElement('span');
      s.className = 'ch';
      s.textContent = c === ' ' ? ' ' : c;
      el.appendChild(s);
    });
  });
  // rang de chaque lettre dans sa ligne : décalage de l'entrée
  $$('.name-line').forEach(l => $$('.ch', l).forEach((c, i) => c.style.setProperty('--i', i)));

  const splitLines = h => {
    const parts = h.innerHTML.split(/<br\s*\/?>/i);
    h.innerHTML = parts.map((p, i) => `<span class="ln"><span style="--d:${i * 90}ms">${p.trim()}</span></span>`).join('');
  };
  $$('.sec-title').forEach(splitLines);

  /* ---------- Texte ajusté à la largeur ----------
     QUENTIN et ÉCRIVEZ-MOI remplissent exactement leur conteneur.
     La photo prend l'espace restant à gauche de LOUIS. */
  const name = $('.name');
  const line1Word = $('.name-line--1 .name-word');
  const mailTxt = $('.mail-txt');
  let capRatio = .7;
  function measureCap() {
    try {
      const ctx = document.createElement('canvas').getContext('2d');
      ctx.font = '850 100px Anybody';
      const m = ctx.measureText('H');
      if (m.actualBoundingBoxAscent) capRatio = m.actualBoundingBoxAscent / 100;
    } catch (e) {}
    name.style.setProperty('--cap', capRatio.toFixed(3) + 'em');
  }
  /* Alignement optique : un mot ajusté s'aligne sur son encre, pas sur sa boîte.
     Approches (espace entre la boîte et le dessin) de la première et de la
     dernière lettre, en em, au repos (largeur 100) : lues une fois au canevas,
     quand Anybody est chargée. r tient compte de l'interlettrage (-.02em) */
  let bear = null;
  function bearings() {
    if (bear || (document.fonts && !document.fonts.check(NAME_FONT))) return bear;
    try {
      const ctx = document.createElement('canvas').getContext('2d');
      ctx.font = NAME_FONT;
      const ls = parseFloat(getComputedStyle(name).letterSpacing) / parseFloat(getComputedStyle(name).fontSize) || 0;
      const side = chars => {
        const a = ctx.measureText(chars[0].textContent.toUpperCase()), z = ctx.measureText(chars.at(-1).textContent.toUpperCase());
        return { l: -a.actualBoundingBoxLeft / 100, r: (z.width - z.actualBoundingBoxRight) / 100 + ls };
      };
      bear = { name: side($$('.ch', line1Word)), louis: side($$('.name-line--2 .ch')), mail: side($$('.ch', mailTxt)) };
    } catch (e) {}
    return bear;
  }
  // maxH : hauteur à ne pas dépasser (bloc entier, marges du Q comprises) ;
  // b : approches, le dessin (et non la boîte) remplit target, la ligne est décalée de -b.l (style.css)
  function fitTo(el, target, word, maxH = Infinity, b = null) {
    const chars = $$('.ch', word);
    el.style.setProperty('--fs', '100px');
    // largeur réelle du texte (du bord de la 1re lettre au bord de la dernière), moins les approches
    const w = chars[chars.length - 1].getBoundingClientRect().right - chars[0].getBoundingClientRect().left - (b ? (b.l + b.r) * 100 : 0);
    if (b) { el.style.setProperty('--lsb', b.l.toFixed(4) + 'em'); el.style.setProperty('--rsb', b.r.toFixed(4) + 'em'); }
    if (w) el.style.setProperty('--fs', (100 * Math.min(target / w, maxH / el.getBoundingClientRect().height)).toFixed(2) + 'px');
  }
  // téléphone à l'horizontale : le nom laisse voir le Poste du brief dans le premier
  // écran (66 px : filet, libellé, première réponse et marges), 58 % de la hauteur au plus
  const landscape = matchMedia('(orientation: landscape) and (max-height: 520px)');
  const landscapeCap = () => Math.max(innerHeight * .35, Math.min(innerHeight * .58, innerHeight - (name.getBoundingClientRect().top + scrollY) - 66));
  // mesure lettres au repos (largeur 100), puis mise en cache des centres.
  // Tant que la police du nom n'est pas là, la taille en cqi de style.css (le
  // même rapport, mesuré avec Anybody) reste en place : ajuster une police de
  // secours décalerait la page deux fois.
  const canFit = () => !document.fonts || document.fonts.check(NAME_FONT) || isNamed;
  // mail : faux au démarrage quand ÉCRIVEZ-MOI est hors de l'écran (ajusté juste après, voir boot)
  function fitAll(mail = true) {
    heroStretch.forEach(s => s.settle());
    if (canFit()) {
      const b = bearings();
      fitTo(name, name.clientWidth, line1Word, landscape.matches ? landscapeCap() : Infinity, b && b.name);
      if (b) name.style.setProperty('--rsb2', b.louis.r.toFixed(4) + 'em');
      // téléphone à l'horizontale (nom borné par la hauteur) : la ligne 2 finit où
      // finit QUENTIN, jamais plus large ; la photo reste un bandeau, plus court
      if (landscape.matches) {
        const c = $$('.ch', line1Word), fs = parseFloat(getComputedStyle(name).fontSize);
        const w1 = c.at(-1).getBoundingClientRect().right - c[0].getBoundingClientRect().left - (b ? (b.name.l + b.name.r - b.louis.r) * fs : 0);
        name.style.setProperty('--l1w', w1.toFixed(1) + 'px');
      } else name.style.removeProperty('--l1w');
    }
    heroStretch.forEach(s => s.measure());
    if (mail) fitMail();
  }
  // is-fitting : ÉCRIVEZ-MOI mesuré à pleine largeur, où qu'en soit son ouverture au scroll
  function fitMail() {
    mailStretch.settle();
    root.classList.add('is-fitting');
    if (canFit()) {
      const b = bearings();
      fitTo(mailTxt, $('.mail').clientWidth, mailTxt, Infinity, b && b.mail);   // encre bord à bord, au pixel près
    }
    mailStretch.measure();
    root.classList.remove('is-fitting');
  }

  /* ---------- Étirement au curseur ----------
     Les lettres proches s'élargissent, les autres se resserrent juste assez
     pour garder la même largeur de ligne (moyenne ramenée à 100). Bornes
     douces : jamais en dessous de 86, pour ne plus écraser les extrémités.
     Les centres des lettres sont mesurés une fois au repos (relatifs à leur
     ligne) : pendant le mouvement, une seule lecture de position par ligne.
     --w ne reçoit que des entiers, et seulement quand la valeur change.
     intro() : entrée en largeur (58 -> 100). */
  // base : largeur de repos des lettres (100 par défaut)
  class Stretch {
    constructor(chars, { min = 86, max = 134, gain = 34, spread = .95 } = {}) {
      Object.assign(this, { chars, min, max, gain, spread });
      this.base = 100;
      this.cur = chars.map(() => 100);
      this.tgt = chars.map(() => 100);
      this.out = chars.map(() => 100);
      this.line = chars[0].closest('.name-line, .mail-txt');
      this.cx = []; this.cy = [];
      this.raf = 0;
      this.tween = 0;
      this.fs = 100;
      this.hold = false;   // pendant une onde (clic sur ÉCRIVEZ-MOI), le pointeur n'agit plus
    }
    measure() {
      this.fs = parseFloat(getComputedStyle(this.chars[0]).fontSize) || 100;
      // offsetLeft/Top ignorent les transforms (entrée des lettres, écart au scroll)
      this.cx = this.chars.map(c => c.offsetLeft + c.offsetWidth / 2);
      this.cy = this.chars.map(c => c.offsetTop + c.offsetHeight / 2);
    }
    point(x, y) {
      const sigma = this.fs * this.spread;
      const r = this.line.getBoundingClientRect();
      const raw = this.cx.map((cx, i) => {
        const dx = x - (r.left + cx), dy = (y - (r.top + this.cy[i])) * .8;
        return 100 + this.gain * Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma));
      });
      this.setRaw(raw);
    }
    // moyenne ramenée à la base ; bornes proportionnelles à la base, 150 au plus (limite de la police)
    setRaw(raw) {
      const mean = raw.reduce((a, b) => a + b, 0) / raw.length;
      const k = this.base / 100;
      this.tgt = raw.map(v => clamp(v * this.base / mean, this.min * k, Math.min(150, this.max * k)));
      this.kick();
    }
    rest() { this.tgt = this.chars.map(() => this.base); this.kick(); }
    // retour immédiat au repos, avant une mesure. Pendant l'entrée, les lettres ont
    // déjà leur largeur de repos (en em) : leur dessin n'est pas remis à 100, sinon il
    // clignoterait une image (police arrivée pendant l'entrée)
    settle() {
      cancelAnimationFrame(this.raf); this.raf = 0;
      this.cur = this.chars.map(() => this.base);
      this.tgt = this.chars.map(() => this.base);
      if (!this.tween) this.chars.forEach((_, i) => this.write(i, this.base));
    }
    // seul point d'écriture de --w : valeur arrondie, écrite seulement si elle change
    write(i, v) {
      const r = Math.round(v);
      if (r !== this.out[i]) { this.chars[i].style.setProperty('--w', r); this.out[i] = r; }
    }
    // pendant l'entrée, la cible (pointeur, balayage) est gardée et suivie à la fin
    kick() { if (!this.tween && !this.raf) this.raf = requestAnimationFrame(() => this.step()); }
    step() {
      let moving = false;
      this.cur = this.cur.map((v, i) => {
        const n = v + (this.tgt[i] - v) * .14;
        if (Math.abs(this.tgt[i] - n) > .05) moving = true;
        this.write(i, n);
        return n;
      });
      this.raf = moving ? requestAnimationFrame(() => this.step()) : 0;
    }
    // chaque lettre s'élargit de `from` à 100 (easeOutExpo), décalée de `stagger` ms.
    // Les lettres gardent leur largeur de repos (en em, suit un recalage) : seul
    // le dessin s'élargit dans sa case, le mot ne bouge pas (aucun décalage de
    // mise en page).
    intro({ from, dur, stagger, delay }) {
      this.settle();
      const fs = parseFloat(getComputedStyle(this.chars[0]).fontSize);
      this.chars.forEach(c => { c.style.width = (c.getBoundingClientRect().width / fs).toFixed(4) + 'em'; });
      const t0 = performance.now();
      const frame = now => {
        let done = true;
        this.chars.forEach((_, i) => {
          const t = clamp((now - t0 - delay - i * stagger) / dur, 0, 1);
          if (t < 1) done = false;
          this.write(i, from + (this.base - from) * (1 - 2 ** (-10 * t)));
        });
        if (!done) { this.tween = requestAnimationFrame(frame); return; }
        this.tween = 0;
        this.chars.forEach((c, i) => { c.style.width = ''; this.write(i, this.base); });
        this.cur = this.chars.map(() => this.base);
        this.kick();
      };
      this.chars.forEach((_, i) => this.write(i, from));
      this.tween = requestAnimationFrame(frame);
    }
  }
  const heroStretch = $$('.name-line').map(l => new Stretch($$('.ch', l)));
  const mailStretch = new Stretch($$('.ch', mailTxt), { gain: 30, spread: 1.1 });

  // pointeur : on garde la dernière position, un seul calcul par image
  let ptrX = 0, ptrY = 0, ptrRaf = 0, ptrTargets = [];
  const aim = (targets, e) => {
    ptrX = e.clientX; ptrY = e.clientY; ptrTargets = targets;
    if (!ptrRaf) ptrRaf = requestAnimationFrame(() => { ptrRaf = 0; ptrTargets.forEach(s => s.hold || s.point(ptrX, ptrY)); });
  };
  const release = targets => {
    cancelAnimationFrame(ptrRaf); ptrRaf = 0;
    targets.forEach(s => s.hold || s.rest());
  };

  // balayage unique du nom sur écran tactile (QUENTIN, puis LOUIS 250 ms après)
  function sweep() {
    const dur = 1400, t0 = performance.now();
    const frame = now => {
      heroStretch.forEach((s, li) => {
        const e = now - t0 - li * 250;
        if (e < 0) return;
        const c = -2 + clamp(e / dur, 0, 1) * (s.chars.length + 4);
        s.setRaw(s.chars.map((_, i) => 100 + 22 * Math.exp(-((i - c) ** 2) / 2)));
      });
      if (now - t0 < dur + 250) requestAnimationFrame(frame);
      else heroStretch.forEach(s => s.rest());
    };
    requestAnimationFrame(frame);
  }

  // Décidé par le type de pointeur de chaque événement, pas par ce que l'écran
  // annonce (hover/pointer) : un PC avec un périphérique tactile se déclare parfois
  // « tactile » alors qu'on s'y sert d'une souris.
  // Souris ou stylet : les lettres suivent le survol (tout le hero, ou ÉCRIVEZ-MOI).
  // Doigt : elles suivent le doigt tant qu'il glisse à l'horizontale sur le mot ;
  // un glissement vertical devient un scroll (pointercancel) : retour au repos.
  if (!reduce) {
    [[$('.hero'), name, heroStretch], [$('.mail'), $('.mail'), [mailStretch]]].forEach(([zone, word, targets]) => {
      let touching = false;
      word.addEventListener('pointerdown', e => { if (e.pointerType === 'touch') touching = true; });
      zone.addEventListener('pointermove', e => {
        if (e.pointerType === 'touch' ? touching : true) aim(targets, e);
      });
      zone.addEventListener('pointerleave', () => { touching = false; release(targets); });
      ['pointerup', 'pointercancel'].forEach(t => word.addEventListener(t, e => {
        if (e.pointerType === 'touch' && touching) { touching = false; release(targets); }
      }));
    });
  }

  /* ---------- Aperçu calé sur la grille (souris) ----------
     Colonnes 9 à 11, face à la ligne survolée ou atteinte au clavier : seule
     la position verticale glisse, et la boucle s'arrête à l'arrivée. Les
     visuels, en bande verticale, ne sont injectés qu'au premier survol de la
     liste : rien n'est téléchargé sur mobile ni avant d'en avoir besoin. */
  const peek = $('.peek');
  const cols = $$('.grid-overlay .grid12 > span');
  let track = null, peekRow = null, peekX = 0, peekMin = 0, peekMax = 0;
  let py = 0, ty = 0, px = 0, tx = 0, peekRaf = 0;
  let peekMuted = null;   // ligne dont l'aperçu a été fermé par Échap, jusqu'à ce que le pointeur ou le focus change de ligne
  let peekKbd = false;    // aperçu ouvert par le focus clavier : posé hors de la ligne (aimPeek)
  const placePeek = () => { peek.style.transform = `translate3d(${px.toFixed(1)}px, ${py.toFixed(1)}px, 0)`; };
  // la bande des huit couvertures : posée dès que la souris entre dans la section
  // (images prêtes quand l'aperçu s'ouvre), jamais au doigt
  function buildTrack() {
    if (track || !PROJECTS.length) return;
    peekIn.innerHTML = `<div class="peek-track">${PROJECTS.map(p => coverImg(p, 'min(23vw, 390px)', ' fetchpriority="low"')).join('')}</div>`;
    track = peekIn.firstElementChild;
  }
  const peekLoop = () => {
    py += (ty - py) * .15; px += (tx - px) * .15;
    if (Math.abs(ty - py) < .3 && Math.abs(tx - px) < .3) { py = ty; px = tx; peekRaf = 0; } else peekRaf = requestAnimationFrame(peekLoop);
    placePeek();
  };
  // largeur : 3 colonnes et 2 gouttières ; hauteur en 4:5, plafonnée par la fenêtre
  function measurePeek() {
    if (!fine) return;
    const a = cols[8].getBoundingClientRect(), b = cols[10].getBoundingClientRect();
    const top = parseFloat(getComputedStyle(root).getPropertyValue('--topbar')) || 60;
    const h = Math.min((b.right - a.left) * 5 / 4, innerHeight - top - 48);
    peekX = a.left;
    peek.style.width = h * 4 / 5 + 'px';
    peekMin = top + 24 + h / 2;
    peekMax = innerHeight - 24 - h / 2;
    if (peekRow) aimPeek(peekRow, true);
  }
  // centre de la ligne, gardé dans la fenêtre sous la barre du haut, et sous
  // l'en-tête de la liste (la note de la section reste lisible) ; si les deux
  // se contredisent, la fenêtre l'emporte. Mouvement réduit : saut direct.
  // Au clavier, l'aperçu ne couvre pas la ligne focalisée (titre, type et rôle
  // restent lisibles) : mêmes colonnes, 12 px au-dessus d'elle, sinon au-dessous ;
  // sinon face à elle, entre la fin du titre et la colonne Type si la place y
  // est ; en dernier recours, du côté où il y a le plus de place.
  const workHead = $('.work-head');
  const ttlRange = document.createRange();
  function aimPeek(row, jump) {
    const r = row.getBoundingClientRect();
    const w = parseFloat(peek.style.width) || 0, half = w * 5 / 8;
    const minC = Math.max(peekMin, workHead.getBoundingClientRect().bottom + 8 + half);
    const mid = Math.min(Math.max(r.top + r.height / 2, minC), peekMax);
    ty = mid; tx = peekX;
    if (peekKbd) {
      const above = r.top - 12 - half, below = r.bottom + 12 + half;
      ttlRange.selectNodeContents($('.ttl', row));
      const from = ttlRange.getBoundingClientRect().right + 24, to = $('.kind', row).getBoundingClientRect().left - 24;
      if (above >= minC) ty = above;
      else if (below <= peekMax) ty = below;
      else if (to - from >= w) tx = (from + to - w) / 2;
      else ty = r.top - minC > peekMax - r.bottom ? minC : peekMax;
    }
    if (jump || reduce) { cancelAnimationFrame(peekRaf); peekRaf = 0; py = ty; px = tx; placePeek(); }
    else if (!peekRaf) peekRaf = requestAnimationFrame(peekLoop);
  }
  function showPeek(row, kbd = false) {
    if (kbd !== peekKbd && row === peekRow && row !== peekMuted) {
      // même ligne, autre source (souris qui part, clavier qui reste) : l'aperçu glisse à sa place
      peekKbd = kbd;
      row.classList.toggle('is-peeked', !kbd);
      return aimPeek(row);
    }
    if (row === peekRow || row === peekMuted || root.classList.contains('is-inspect')) return;
    peekKbd = kbd;
    buildTrack();
    const first = !peekRow;
    // à l'ouverture, la bande est déjà sur le bon visuel : pas de défilement
    if (first) track.style.transition = 'none';
    track.style.setProperty('--pi', row.dataset.i);
    if (first) { void track.offsetHeight; track.style.transition = ''; }
    if (peekRow) peekRow.classList.remove('is-peeked');
    peekRow = row;
    row.classList.toggle('is-peeked', !kbd);   // souris : type et rôle s'effacent sous l'aperçu (style.css)
    aimPeek(row, first);
    rowRO.disconnect();
    rowRO.observe(row);
    peek.classList.add('is-on');
  }
  function hidePeek() {
    if (peekRow) peekRow.classList.remove('is-peeked');
    peekRow = null;
    rowRO.disconnect();
    peek.classList.remove('is-on');
  }
  /* Titres de la liste (souris) : au survol, la chasse monte vers 118 sans
     jamais faire passer le titre sur deux lignes (la liste ne bouge pas). Pour
     chaque ligne, la plus grande chasse où le titre, sa mention et le décalage
     du survol tiennent dans sa colonne devient --tw-max (entier, 90 à 118 ;
     style.css). Un titre trop long même au repos garde le retour à la ligne. */
  function fitTitles() {
    if (touchList || gridList) return;
    $$('.work-row .ttl', list).forEach(t => {
      t.style.removeProperty('--tw-max');
      t.style.whiteSpace = 'nowrap';
      t.style.transition = 'none';
      const avail = t.clientWidth, fs = parseFloat(getComputedStyle(t).fontSize);
      const r = document.createRange();
      r.selectNodeContents(t);
      const fits = w => {
        t.style.fontVariationSettings = `"wdth" ${w}`;
        return r.getBoundingClientRect().width + fs * .12 <= avail;
      };
      // trop long même au repos (fenêtre étroite) : retour à la ligne permis
      const wrap = !fits(90);
      let max = 118;
      if (!wrap && !fits(118)) {
        let lo = 90, hi = 118;   // lo tient, hi déborde : recherche par moitiés
        while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (fits(mid)) lo = mid; else hi = mid; }
        max = lo;
      }
      if (wrap) t.dataset.wrap = ''; else delete t.dataset.wrap;
      t.style.setProperty('--tw-max', max);
      t.style.fontVariationSettings = t.style.whiteSpace = '';
      void t.offsetWidth;
      t.style.transition = '';
    });
  }
  // la ligne bouge sans scroll (entrée qui se termine, largeur de la fenêtre) :
  // l'aperçu la rejoint
  const rowRO = new ResizeObserver(() => { if (peekRow) aimPeek(peekRow); });
  // ligne tenue par le clavier, que l'aperçu retrouve quand la souris s'en va
  const keyRow = () => {
    const a = document.activeElement;
    return a && a.classList.contains('work-row') && a.matches(':focus-visible') ? a : null;
  };
  if (fine) {
    if (!gridList) $('#travaux').addEventListener('pointerenter', buildTrack, { once: true });
    // 150 ms sur une ligne (ou le focus) : le visuel du haut de sa fiche se charge, l'ouverture est immédiate
    let heroT = 0;
    list.addEventListener('pointerover', e => {
      const row = e.target.closest('.work-row');
      clearTimeout(heroT);
      if (row) heroT = setTimeout(() => preloadHero(+row.dataset.i), 150);
    });
    list.addEventListener('focusin', e => { const row = e.target.closest('.work-row'); if (row) preloadHero(+row.dataset.i); });
  }
  // aperçu au curseur : liste seulement (la grille montre déjà ses couvertures)
  if (fine && !gridList) {
    list.addEventListener('pointerover', e => {
      const row = e.target.closest('.work-row');
      if (row && row !== peekMuted) peekMuted = null;
      if (row) showPeek(row);
    });
    list.addEventListener('pointerleave', () => { const k = keyRow(); hidePeek(); if (k !== peekMuted) peekMuted = null; if (k) showPeek(k, true); });
    list.addEventListener('focusin', () => { const k = keyRow(); if (k !== peekMuted) peekMuted = null; if (k) showPeek(k, true); });
    list.addEventListener('focusout', e => {
      if (list.contains(e.relatedTarget)) return;
      peekMuted = null;
      if (!list.matches(':hover')) hidePeek();
    });
    list.addEventListener('transitionend', e => { if (e.target === peekRow && e.propertyName === 'transform') aimPeek(peekRow); });
    // la bande pleine largeur entre et sort par le bord que la souris a franchi
    const side = (row, e) => {
      const r = row.getBoundingClientRect();
      row.dataset.from = e.clientY < r.top + r.height / 2 ? 'top' : 'bottom';
    };
    $$('.work-row', list).forEach(row => {
      row.addEventListener('pointerenter', e => side(row, e));
      row.addEventListener('pointerleave', e => side(row, e));
    });
    // au scroll, l'aperçu suit sa ligne ; il se ferme quand la liste n'est plus sous
    // la souris, ou quand sa ligne passe sous l'en-tête de la liste ou sort de l'écran
    window.addEventListener('scroll', () => {
      if (!peekRow) return;
      const r = peekRow.getBoundingClientRect();
      const inView = r.bottom > Math.max(workHead.getBoundingClientRect().bottom, 0) && r.top < innerHeight;
      if (inView && (list.matches(':hover') || peekRow === keyRow())) aimPeek(peekRow);
      else hidePeek();
    }, { passive: true });
  }

  /* ---------- Au doigt : la ligne au centre de l'écran ----------
     La ligne qui traverse la bande centrale (8 % de la hauteur) depuis
     120 ms est mise en avant, une seule à la fois. */
  if (touchList && !gridList) {
    const band = new Set();
    let focusRow = null, dwell = 0;
    const pick = () => {
      const mid = innerHeight / 2;
      let best = null, gap = Infinity;
      band.forEach(row => {
        const r = row.getBoundingClientRect(), d = Math.abs(r.top + r.height / 2 - mid);
        if (d < gap) { gap = d; best = row; }
      });
      if (best === focusRow) return;
      focusRow && focusRow.classList.remove('is-focus');
      focusRow = best;
      best && best.classList.add('is-focus');
    };
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => band[e.isIntersecting ? 'add' : 'delete'](e.target));
      clearTimeout(dwell);
      dwell = setTimeout(pick, 120);
    }, { rootMargin: '-46% 0px -46% 0px' });
    $$('.work-row', list).forEach(row => io.observe(row));
  }

  /* ---------- Fiche projet (avec lien direct #id) ----------
     .case.is-open fait monter la fiche et le voile ; .case-body.is-in fait
     entrer le contenu (titre dans son masque, puis le reste en cascade). */
  const caseEl = $('.case');
  const sheet = $('.case-sheet');
  const scrim = $('.case-scrim');
  const caseBar = $('.case-bar');
  const caseBody = $('.case-body');
  const shareBtn = $('.case-share');
  const MAIL = $('.mail').dataset.mail;
  // fiche ouverte : le reste de la page sort de la tabulation et des lecteurs d'écran
  const behind = $$('.skip, .topbar, main, .foot, .dock');
  let current = -1, target = -1, lastFocus = null, pushed = false, hideT = 0, openY = 0;
  const DOC_TITLE = document.title;   // rendu à la fermeture de la fiche

  /* Visuel du haut de la fiche : un cadre posé comme dans Figma (nom au-dessus à
     gauche, dimensions en direct en dessous à droite). Un site : sa page dans une
     fenêtre de navigateur, sur le canevas à points ; au téléphone, sa version
     mobile dans un téléphone. Sinon l'image elle-même, à son ratio : rien n'est
     rogné. C'est la seule image chargée tout de suite (fetchpriority high). */
  const linkName = p => p.link.includes('behance.net') ? 'Behance' : new URL(p.link).host;
  const phoneQ = matchMedia('(max-width: 760px)');
  const rmQ = matchMedia('(prefers-reduced-motion: reduce)');   // relue à chaque changement (animations de la galerie)
  const SIZES = {
    hero: '(max-width: 760px) 100vw, min(calc(100vw - 64px), 1616px)',
    heroBrowser: '(max-width: 760px) 62vw, min(calc(90vw - 280px), 1230px)',
    heroPhone: '(max-width: 760px) 50vw, 300px',
    full: '(max-width: 760px) calc(100vw - 32px), min(calc(100vw - 64px), 1616px)',
    inset: '(max-width: 1100px) calc(100vw - 48px), min(calc(83vw - 45px), 1340px)',
    pair: '(max-width: 760px) calc(100vw - 32px), min(calc(50vw - 44px), 796px)',
    aside: '(max-width: 1100px) calc(100vw - 48px), min(calc(58vw - 30px), 930px)',
    browser: '(max-width: 760px) calc(100vw - 64px), min(calc(100vw - 224px), 1100px)',
    'browser-pair': '(max-width: 760px) calc(100vw - 64px), min(calc(50vw - 140px), 700px)',
    phones: '(max-width: 760px) 62vw, clamp(160px, 20vw, 300px)'
  };
  // fenêtre de navigateur et téléphone : cadres en CSS, sans faux contenu d'interface
  const browserWin = (p, m, sizes, eager) => `<div class="browser"><div class="browser-bar" aria-hidden="true"><span class="browser-dots"><i></i><i></i><i></i></span><span class="browser-url">${linkName(p)}</span><span></span></div>${pic(p, m, sizes, eager)}</div>`;
  const phoneEl = (p, m, sizes, eager) => `<div class="phone">${pic(p, m, sizes, eager)}</div>`;
  // image animée : son image fixe d'abord, l'animation seulement quand elle est à l'écran (animSet)
  const PLAY_IC = '<svg class="g-play-ic" viewBox="0 0 10 10" aria-hidden="true" focusable="false"><path class="i-pause" d="M2 1h2v8H2zM6 1h2v8H6z"/><path class="i-play" d="M2.5 1 9 5l-6.5 4z"/></svg>';
  const media = (p, m, sizes, eager) => m.anim
    ? `<div class="g-anim" data-anim="${dirOf(p)}${m.anim}">${pic(p, m, sizes, eager)}<button type="button" class="g-play">${PLAY_IC}<span class="g-play-lbl">Pause</span><span class="sr-only"> : ${attr(m.label)}</span></button></div>`
    : pic(p, m, sizes, eager);
  function heroHTML(p) {
    const h = p.hero, site = h.type === 'browser', mob = phoneQ.matches;
    // site : les deux versions sont écrites, le CSS n'en montre qu'une ; la version cachée
    // est en lazy, donc jamais téléchargée tant qu'elle reste cachée
    const inner = site
      ? `<div class="hero-desk">${browserWin(p, h, SIZES.heroBrowser, !mob)}</div><div class="hero-mob">${phoneEl(p, h.phone, SIZES.heroPhone, mob)}</div>`
      : media(p, h, SIZES.hero, true);
    return `<div class="case-hero${site ? ' is-site' : ''}" style="--ar: ${site ? '16 / 9' : h.w + ' / ' + h.h}"><div class="frame${site ? ' is-canvas' : ''}" data-spec="Frame · ${site ? 'canevas 16:9' : h.w + ' × ' + h.h}">${inner}</div><div class="frame-label mono" aria-hidden="true"><span>${linkName(p)}</span><span class="frame-size"></span></div></div>`;
  }
  /* Galerie : une figure par groupe, légendée (role figure et aria-label, RGAA 1.9.1),
     et des titres de chapitre (h4). Au téléphone, les captures mobiles défilent de
     côté ; la rangée n'entre dans la tabulation que si elle défile (scrollRO). */
  function gallery(p) {
    return p.gallery.map(g => {
      if (g.head) return `<h4 class="g-head">${g.head}</h4>`;
      const L = g.layout, it = g.items;
      let body;
      if (L === 'browser' || L === 'browser-pair') body = `<div class="g-canvas">${it.map(m => browserWin(p, m, SIZES[L])).join('')}</div>`;
      else if (L === 'phones') body = `<div class="g-canvas g-phone-row" role="region" aria-label="Captures sur téléphone" data-scroll-x>${it.map(m => phoneEl(p, m, SIZES.phones)).join('')}</div>`;
      else body = `<div class="g-row">${it.map(m => media(p, m, SIZES[L])).join('')}</div>`;
      const cap = L === 'aside'
        ? `<figcaption><span class="g-cap mono">${g.caption}</span>${g.text ? `<span class="g-txt">${g.text}</span>` : ''}</figcaption>`
        : `<figcaption class="mono">${g.caption}</figcaption>`;
      return `<figure class="g-item g-${L}" role="figure" aria-label="${attr(plain(g.caption))}">${body}${cap}</figure>`;
    }).join('');
  }
  // dimensions du cadre, affichées comme dans Figma
  const frameRO = new ResizeObserver(([e]) => {
    const size = $('.frame-size', caseBody);
    if (size) size.textContent = `${Math.round(e.contentRect.width)} × ${Math.round(e.contentRect.height)}`;
  });
  // visuel du haut d'une fiche, chargé d'avance (survol ou focus d'une ligne, bloc « Projet suivant » en vue)
  const preloaded = new Set();
  function preloadHero(i) {
    const p = PROJECTS[i];
    if (!p || preloaded.has(i)) return;
    preloaded.add(i);
    const site = p.hero.type === 'browser', m = site && phoneQ.matches ? p.hero.phone : p.hero;
    const a = new Image();
    a.sizes = site ? (phoneQ.matches ? SIZES.heroPhone : SIZES.heroBrowser) : SIZES.hero;
    a.srcset = srcsetOf(p, m);
  }

  /* Images animées (WebP) : l'image fixe reste affichée tant que l'animation n'est
     pas décodée, puis la remplace. Animée seulement si elle est à l'écran (35 %),
     pas mise en pause, et sans mouvement réduit au départ ; sinon l'image fixe
     revient, et le processeur s'arrête. Bouton Pause / Lecture (WCAG 2.2.2). */
  let animIO = null, revealIO = null, nextIO = null;
  function animSet(el) {
    const img = $('img', el), btn = $('.g-play', el);
    const play = el._play === undefined ? !rmQ.matches : el._play;
    $('.g-play-lbl', btn).textContent = play ? 'Pause' : 'Lecture';
    btn.classList.toggle('is-paused', !play);
    if (!el._poster) el._poster = { src: img.getAttribute('src'), srcset: img.getAttribute('srcset') };
    const on = play && !!el._vis;
    if (on && !el._on) {
      el._on = true;
      const a = new Image();
      a.src = el.dataset.anim;
      (a.decode ? a.decode() : Promise.resolve()).catch(() => {}).then(() => {
        if (!el._on || !el.isConnected) return;
        img.removeAttribute('srcset');
        img.src = el.dataset.anim;
      });
    } else if (!on && el._on) {
      el._on = false;
      img.srcset = el._poster.srcset;
      img.src = el._poster.src;
    }
  }
  rmQ.addEventListener('change', () => $$('[data-anim]', caseBody).forEach(el => { el._play = undefined; animSet(el); }));
  // rangée de téléphones : dans la tabulation seulement quand elle défile (axe scrollable-region-focusable)
  const scrollRO = new ResizeObserver(es => es.forEach(({ target: el }) => {
    if (el.scrollWidth > el.clientWidth + 1) el.tabIndex = 0; else el.removeAttribute('tabindex');
  }));
  function unwatchCase() {
    [animIO, revealIO, nextIO].forEach(o => o && o.disconnect());
    scrollRO.disconnect();
    frameRO.disconnect();
  }
  function watchCase(next) {
    unwatchCase();
    frameRO.observe($('.case-hero .frame', caseBody));
    animIO = new IntersectionObserver(es => es.forEach(e => {
      e.target._vis = e.isIntersecting && e.intersectionRatio >= .35;
      animSet(e.target);
    }), { root: sheet, threshold: [0, .35] });
    $$('[data-anim]', caseBody).forEach(el => { animSet(el); animIO.observe(el); });
    // entrée des images de la galerie, une fois, en arrivant dans la vue
    revealIO = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('is-in'); revealIO.unobserve(e.target); }
    }), { root: sheet, threshold: .15, rootMargin: '0px 0px -8% 0px' });
    $$('.g-item', caseBody).forEach(el => revealIO.observe(el));
    nextIO = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { preloadHero(next); nextIO.disconnect(); } }, { root: sheet, rootMargin: '0px 0px 50% 0px' });
    nextIO.observe($('.case-next', caseBody));
    $$('[data-scroll-x]', caseBody).forEach(el => scrollRO.observe(el));
  }

  function renderCase(i) {
    const p = PROJECTS[i];
    document.title = `${p.title}, Quentin Louis`;   // titre de l'onglet : le projet ouvert (RGAA 8.6)
    const ni = (i + 1) % PROJECTS.length, next = PROJECTS[ni];
    current = target = i;
    $('.case-idx').innerHTML = `${pad(i + 1)} / ${pad(PROJECTS.length)}<span class="case-kind"> · ${p.kind}</span>`;
    // lien du site dans la barre, avant « Lien » (même ordre au clavier qu'à l'écran)
    const site = $('.case-site', caseBar);
    if (site) site.remove();
    // forme courte sous 560 px (style.css) : « Site », et « Bē », le sigle de Behance (nom lu : Behance), suivis de la flèche
    // nom lu : libellé visible, puis le domaine (le nom de Behance suffit) et « nouvel onglet »
    if (p.link) shareBtn.insertAdjacentHTML('beforebegin', `<a class="case-site" href="${p.link}" target="_blank" rel="noopener">${p.link.includes('behance.net')
      ? '<span class="case-site-lg">Behance</span><span class="case-site-sm"><span aria-hidden="true">Bē</span><span class="sr-only">Behance</span></span>'
      : `<span class="case-site-lg">Voir le site</span><span class="case-site-sm">Site</span><span class="sr-only"> ${linkName(p)}</span>`}${icon('out')}<span class="sr-only"> (nouvel onglet)</span></a>`);
    // fiche technique : les faits du projet, puis les outils, l'année (sauf date précise) et le lien
    const has = k => p.facts.some(([f]) => f === k);
    const meta = [
      ...p.facts,
      ...(p.tools && !has('Outils') ? [['Outils', p.tools]] : []),
      ...(has('Date') ? [] : [['Année', p.year]]),
      ...(p.link ? [['Lien', `<a href="${p.link}" target="_blank" rel="noopener">${linkName(p)}<span class="sr-only"> (nouvel onglet)</span></a>`]] : [])
    ];
    caseBody.innerHTML = `
      <h2 class="case-title" id="case-title" tabindex="-1">${glue(p.title)}</h2>
      ${p.subtitle ? `<p class="case-sub mono">${p.subtitle}</p>` : ''}
      <dl class="case-meta mono" style="--mc: ${meta.length % 3 === 0 && meta.length < 8 ? 3 : 4}">${meta.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>
      ${heroHTML(p)}
      <div class="case-intro grid12"><p class="pitch">${p.pitch}</p></div>
      <div class="case-cols grid12 case-cols--${p.cols.length}">${p.cols.map(([h, t]) => `<section><h3>${h}</h3><p>${t}</p></section>`).join('')}</div>
      ${p.gallery && p.gallery.length ? `<section class="case-gallery" aria-labelledby="case-gallery-h"><h3 id="case-gallery-h" class="mono">Le projet en images</h3><div class="g-grid">${gallery(p)}</div></section>` : ''}
      ${p.link
        ? `<div class="case-actions"><a class="btn btn--accent" href="${p.link}" target="_blank" rel="noopener"><span class="lbl">${p.linkLabel || 'Voir le projet sur Behance'}</span><span class="sr-only"> (nouvel onglet)</span> ${ARROW}</a></div>`
        : `<div class="case-ask"><a class="btn btn--ghost" href="mailto:${MAIL}?subject=${encodeURIComponent('Écrans du projet ' + p.title)}"><span class="lbl">Demander les écrans</span></a></div>`}
      <button class="case-next" type="button" data-go="${ni}"><span class="case-next-txt"><span class="mono">Projet suivant</span><b>${glue(next.title)}</b><span class="mono case-next-meta">${pad(ni + 1)} / ${pad(PROJECTS.length)} · ${next.kind}</span></span><span class="case-next-cover" aria-hidden="true">${coverImg(next, '(max-width: 760px) 96px, min(23vw, 390px)', ' loading="lazy"')}</span></button>
      <button class="btn btn--ghost case-back" type="button" data-close><span class="lbl">Retour aux projets</span></button>`;
    splitLines($('.case-title', caseBody));
    [...caseBody.children].forEach((c, k) => c.style.setProperty('--k', k));
    watchCase(ni);
    fitCaseTitle();
    resetShare();
    lockWidths(caseEl);
    sheet.scrollTop = 0;
  }

  /* Titre ajusté : taille maximale du CSS (clamp) et chasse 116 ; si le mot le
     plus long déborde, la chasse descend jusqu'à 76 (recherche par moitiés,
     6 mesures au plus), puis la taille, jusqu'à 40 px. En dessous, le titre
     passe à la ligne plutôt que d'être coupé par son masque. */
  function fitCaseTitle() {
    const h = $('.case-title', caseBody);
    if (!h) return;
    h.style.fontSize = h.style.fontVariationSettings = h.style.overflowWrap = '';
    const maxFs = parseFloat(getComputedStyle(h).fontSize);
    const spans = $$('.ln > span', h);
    // largeur utile : celle d'une ligne (bloc), en pixels entiers comme scrollWidth
    const avail = spans[0].clientWidth;
    const widest = w => {
      h.style.fontVariationSettings = `"wdth" ${w}`;
      return Math.max(...spans.map(s => s.scrollWidth));
    };
    let width = widest(116);
    if (width <= avail) return;
    let lo = 76, hi = 116;
    width = widest(lo);
    if (width <= avail) {
      for (let n = 0; n < 4 && hi - lo > 1; n++) {
        const mid = Math.round((lo + hi) / 2), w = widest(mid);
        if (w <= avail) { lo = mid; width = w; } else hi = mid;
      }
      h.style.fontVariationSettings = `"wdth" ${lo}`;
      return;
    }
    const fs = Math.floor(maxFs * avail / width);
    h.style.fontSize = Math.max(40, fs) + 'px';
    if (fs < 40) h.style.overflowWrap = 'anywhere';
  }

  // l'entrée de la fiche ne se pose jamais sur une adresse à ancre (#travaux) :
  // au retour, le navigateur donnerait le focus à la section au lieu de la
  // ligne qui a ouvert la fiche. L'adresse affichée ne change pas.
  const setHash = (id, push) => {
    if (push) {
      if (location.hash) history.replaceState(history.state, '', location.pathname + location.search);
      history.pushState({ case: id }, '', '#' + id); pushed = true;
    }
    else history.replaceState({ case: id }, '', '#' + id);
  };
  // morph : ouverture depuis l'aperçu, fiche posée directement ouverte (voir morphOpen)
  function openCase(i, { push = true, morph = false } = {}) {
    // déjà ouverte : changement de projet
    if (current >= 0) return swapTo(i, i < current ? -1 : 1);
    // fermée, ou en train de se fermer : ouverture complète (hors du mode Inspecter)
    setInspect(false);
    clearTimeout(hideT);
    lastFocus = document.activeElement; openY = scrollY;
    resetDrag();
    caseBody.classList.remove('is-in', 'is-step');
    caseEl.hidden = false;   // visible avant le rendu : le titre se mesure
    renderCase(i);
    setHash(PROJECTS[i].id, push);
    document.body.classList.add('no-scroll');
    behind.forEach(el => { el.inert = true; });
    lenis && lenis.stop();
    hidePeek();
    if (morph) { caseEl.classList.add('is-open'); return; }
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (current >= 0) { caseEl.classList.add('is-open'); caseBody.classList.add('is-in'); }
    }));
    $('#case-title').focus({ preventScroll: true });
  }

  /* Précédent / suivant : le contenu sort du côté opposé en 180 ms, le suivant
     entre de l'autre. Pendant un changement, seule la dernière demande compte
     (trois flèches rapides : un seul saut vers le 3e projet suivant). */
  let swapping = false, stepDir = 1;
  async function swapTo(i, dir) {
    target = i; stepDir = dir;
    if (swapping) return;
    swapping = true;
    while (current >= 0 && target !== current) {
      const out = reduce ? null : caseBody.animate(
        [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: `translateX(${-3 * stepDir}%)` }],
        { duration: 180, easing: 'cubic-bezier(.4, 0, 1, 1)', fill: 'forwards' });
      if (out) await out.finished;
      if (current >= 0 && target !== current) {
        // état de départ posé avant le rendu : le nouveau contenu naît caché,
        // décalé du côté d'où il arrive (--dir)
        caseBody.classList.remove('is-in');
        caseBody.classList.add('is-step');
        caseBody.style.setProperty('--dir', stepDir);
        renderCase(target);
        setHash(PROJECTS[target].id, false);
        void caseBody.offsetWidth;
        caseBody.classList.add('is-in');
        // le focus perdu avec l'ancien contenu (« Projet suivant ») revient au titre
        if (!caseEl.contains(document.activeElement)) $('#case-title').focus({ preventScroll: true });
      }
      if (out) out.cancel();
    }
    swapping = false;
    // focus resté dans la barre (flèches, Fermer) : le nouveau projet est annoncé.
    // Sinon le focus est sur le titre, déjà lu : l'annonce précédente est vidée
    announce(current >= 0 && document.activeElement !== $('#case-title') ? `Projet ${current + 1} sur ${PROJECTS.length} : ${PROJECTS[current].title}` : '');
  }
  // vidé puis rempli à l'image suivante : la même phrase est relue
  const announcer = $('.case-announce');
  let announceRaf = 0;
  function announce(msg) {
    cancelAnimationFrame(announceRaf);
    announcer.textContent = '';
    if (msg) announceRaf = requestAnimationFrame(() => { announcer.textContent = msg; });
  }
  const step = d => { if (current >= 0) swapTo((target + d + PROJECTS.length) % PROJECTS.length, d); };

  const hideCase = () => {
    clearTimeout(hideT);
    if (current < 0) { caseEl.hidden = true; resetDrag(); }
  };
  function doClose() {
    if (current < 0) return;
    current = target = -1;
    unwatchCase();   // animations et observateurs de la fiche : arrêtés
    document.title = DOC_TITLE;
    caseEl.classList.remove('is-open');
    caseBody.classList.remove('is-in', 'is-step');
    document.body.classList.remove('no-scroll');
    behind.forEach(el => { el.inert = false; });
    lenis && lenis.start();
    showDock();
    // masquée quand la fiche a fini de descendre (900 ms au plus)
    if (reduce) hideCase(); else hideT = setTimeout(hideCase, 900);
    if (location.hash) history.replaceState(null, '', location.pathname + location.search);
    announce('');
    lastFocus && lastFocus.focus({ preventScroll: true });
  }
  sheet.addEventListener('transitionend', e => {
    if (e.target !== sheet || e.propertyName !== 'transform') return;
    if (current < 0) hideCase();
    else sheet.style.transition = '';   // fin du retour après un glissement trop court
  });
  function requestClose() {
    if (pushed && history.state && history.state.case) { pushed = false; history.back(); }
    else doClose();
  }

  /* Glisser la barre vers le bas ferme la fiche (souris et doigt). Moins de
     6 px : un clic. Au lâcher, au-delà de 22 % de l'écran ou d'un geste rapide
     (0,5 px/ms), la fiche finit sa descente ; sinon elle revient en place. */
  let drag = null;
  function resetDrag() {
    drag = null;
    caseBar.classList.remove('is-drag');
    sheet.style.transform = sheet.style.transition = scrim.style.opacity = scrim.style.transition = '';
  }
  /* Au doigt, le geste part aussi d'un bouton : le navigateur attire vers le
     bouton voisin une touche posée sur la poignée. Le bouton garde ses taps ;
     passé 6 px, la barre prend le pointeur et le bouton ne reçoit pas de clic.
     À la souris, un bouton reste un bouton (et un lien ne se glisse pas). */
  caseBar.addEventListener('pointerdown', e => {
    const ctl = !!e.target.closest('a, button');
    if (current < 0 || e.button !== 0 || (ctl && e.pointerType !== 'touch')) return;
    drag = { id: e.pointerId, y: e.clientY, dy: 0, on: false, ctl, pts: [[e.timeStamp, e.clientY]] };
    if (!ctl) caseBar.setPointerCapture(e.pointerId);
  });
  caseBar.addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id) return;
    const dy = e.clientY - drag.y;
    if (!drag.on) {
      if (Math.abs(dy) < 6) return;
      if (drag.ctl) try { caseBar.setPointerCapture(e.pointerId); } catch (err) { /* pointeur déjà relâché */ }
      drag.on = true;
      caseBar.classList.add('is-drag');
      sheet.style.transition = scrim.style.transition = 'none';
    }
    drag.dy = dy;
    // vitesse mesurée sur les 100 dernières ms
    drag.pts.push([e.timeStamp, e.clientY]);
    while (drag.pts.length > 2 && e.timeStamp - drag.pts[0][0] > 100) drag.pts.shift();
    sheet.style.transform = `translateY(${dy > 0 ? dy : dy * .25}px)`;   // vers le haut : résistance
    scrim.style.opacity = dy > 0 ? Math.max(0, 1 - dy / (innerHeight * .6)) : 1;
  });
  function endDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    const { on, dy, pts } = drag;
    drag = null;
    caseBar.classList.remove('is-drag');
    if (!on) return;
    const [t0, y0] = pts[0];
    dropSheet(dy, e.type === 'pointerup' && e.timeStamp > t0 ? (e.clientY - y0) / (e.timeStamp - t0) : 0);
  }
  // lâcher (barre ou contenu) : dy, glissement ; v, vitesse en px/ms
  function dropSheet(dy, v) {
    if (dy > innerHeight * .22 || v > .5) {
      // la descente continue, puis la fermeture habituelle (historique compris)
      sheet.style.transition = 'transform .35s ease-out';
      scrim.style.transition = 'opacity .35s ease-out';
      sheet.style.transform = 'translateY(100%)';
      scrim.style.opacity = 0;
      requestClose();
    } else {
      sheet.style.transition = 'transform .5s var(--ease)';
      sheet.style.transform = scrim.style.opacity = scrim.style.transition = '';
    }
  }
  caseBar.addEventListener('pointerup', endDrag);
  caseBar.addEventListener('pointercancel', endDrag);

  /* Au doigt, tout le contenu se glisse aussi, quand la fiche est lue depuis son
     haut (scrollTop à 0 au contact) et que le geste part vers le bas : même
     suivi, mêmes seuils que la barre. Vers le haut ou de côté : défilement normal */
  let pull = null;
  sheet.addEventListener('touchstart', e => {
    pull = null;
    if (current < 0 || e.touches.length !== 1 || sheet.scrollTop > 0 || caseBar.contains(e.target)) return;
    const t = e.touches[0];
    pull = { x: t.clientX, y: t.clientY, dy: 0, on: false, pts: [[e.timeStamp, t.clientY]] };
  }, { passive: true });
  sheet.addEventListener('touchmove', e => {
    if (!pull) return;
    const t = e.touches[0], dx = t.clientX - pull.x, dy = t.clientY - pull.y;
    if (!pull.on) {
      // premier mouvement : le sens décide (le défilement ne se reprend plus ensuite)
      if (dy <= 0 || Math.abs(dx) > dy) { pull = null; return; }
      pull.on = true;
      sheet.style.transition = scrim.style.transition = 'none';
    }
    e.preventDefault();
    pull.dy = dy;
    pull.pts.push([e.timeStamp, t.clientY]);
    while (pull.pts.length > 2 && e.timeStamp - pull.pts[0][0] > 100) pull.pts.shift();
    sheet.style.transform = `translateY(${Math.max(0, dy)}px)`;
    scrim.style.opacity = Math.max(0, 1 - Math.max(0, dy) / (innerHeight * .6));
  }, { passive: false });
  const endPull = e => {
    if (!pull) return;
    const { on, dy, pts } = pull;
    pull = null;
    if (!on) return;
    const [t0, y0] = pts[0], [t1, y1] = pts[pts.length - 1];
    dropSheet(dy, e.type === 'touchend' && t1 > t0 ? (y1 - y0) / (t1 - t0) : 0);
  };
  sheet.addEventListener('touchend', endPull);
  sheet.addEventListener('touchcancel', endPull);

  // progression de la lecture : filet sous la barre (--cp de 0 à 1)
  let cpRaf = 0;
  sheet.addEventListener('scroll', () => {
    if (cpRaf) return;
    cpRaf = requestAnimationFrame(() => {
      cpRaf = 0;
      const max = sheet.scrollHeight - sheet.clientHeight;
      caseBar.style.setProperty('--cp', max > 0 ? (sheet.scrollTop / max).toFixed(3) : 0);
    });
  }, { passive: true });

  /* Lien vers la fiche : partage natif au doigt, sinon copié dans le
     presse-papiers ; « Lien » devient « Copié » pendant 1,6 s. */
  // nom accessible = texte visible + complément sr-only, vidé pendant « Copié » (WCAG 2.5.3)
  const shareLbl = $('.case-share-lbl');
  const shareSr = $('.case-share-sr');
  const shareMsg = $('.case-share-msg', caseBar);
  const SHARE_SR = shareSr.textContent;
  let shareT = 0;
  // presse-papiers, ou à défaut un champ caché posé après le bouton (back), qui reprend le focus
  async function copyText(text, back) {
    try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* repli ci-dessous */ }
    const f = document.createElement('textarea');
    f.value = text; f.readOnly = true; f.className = 'sr-only';
    back.after(f); f.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    f.remove();
    back.focus({ preventScroll: true });
    return ok;
  }
  shareBtn.addEventListener('click', async () => {
    const p = PROJECTS[current];
    if (!p) return;
    const url = location.origin + location.pathname + '#' + p.id;
    if (touchList && navigator.share) {
      try { await navigator.share({ title: 'Quentin Louis · ' + p.title, url }); return; }
      catch (e) { if (e.name === 'AbortError') return; }
    }
    if (!(await copyText(url, shareBtn))) return;
    shareBtn.classList.add('is-done');
    shareLbl.textContent = 'Copié';
    shareSr.textContent = '';
    shareMsg.textContent = 'Lien copié';
    clearTimeout(shareT);
    shareT = setTimeout(resetShare, 1600);
  });
  // aussi à chaque changement de projet : « Copié » ne vaut que pour la fiche copiée
  function resetShare() {
    clearTimeout(shareT);
    shareBtn.classList.remove('is-done');
    shareLbl.textContent = 'Lien';
    shareSr.textContent = SHARE_SR;
    shareMsg.textContent = '';
  }

  /* Ouverture à la souris depuis l'aperçu : le cadre de l'aperçu devient celui
     de la fiche (View Transitions, là où elles existent). Le 4:5 de l'aperçu
     s'ouvre vers le cadre de la fiche, rogné (style.css). La fiche monte dessous, puis le
     titre et le contenu entrent comme d'habitude. Clavier, lien direct, doigt,
     flèches et fermeture gardent l'ouverture habituelle. */
  const canMorph = !!document.startViewTransition && fine && !reduce;
  let morphing = false;
  function morphOpen(i) {
    let frame = null, vt;
    peekIn.style.viewTransitionName = 'case-frame';
    try {
      vt = document.startViewTransition(() => {
        peekIn.style.viewTransitionName = '';
        root.classList.add('vt');
        openCase(i, { morph: true });
        frame = $('.case-hero .frame', caseBody);
        frame.parentNode.classList.add('is-shared');
        frame.style.viewTransitionName = 'case-frame';
        sheet.style.viewTransitionName = 'case-sheet';
      });
    } catch (e) {
      peekIn.style.viewTransitionName = '';
      return openCase(i);
    }
    morphing = true;
    vt.ready.catch(() => {});   // transition sautée : la fiche s'ouvre quand même
    // le contenu entre pendant le morphing (dès que la page est à jour), pas
    // après : la fiche ne paraît jamais vide. Sans ce signal, après 350 ms
    const updated = vt.updateCallbackDone || new Promise(res => setTimeout(res, 350));
    updated.catch(() => {}).then(() => {
      // fermée entre-temps (Échap) : rien à faire entrer
      if (current >= 0) caseBody.classList.add('is-in');
    });
    vt.finished.catch(() => {}).then(() => {
      morphing = false;
      root.classList.remove('vt');
      peekIn.style.viewTransitionName = sheet.style.viewTransitionName = '';
      if (frame) frame.style.viewTransitionName = '';
      if (current < 0) return;
      caseBody.classList.add('is-in');
      $('#case-title').focus({ preventScroll: true });
    });
  }
  list.addEventListener('click', e => {
    const row = e.target.closest('.work-row');
    if (!row || morphing) return;
    // clic de souris (detail > 0) sur la ligne dont l'aperçu est affiché, fiche fermée
    if (canMorph && e.detail > 0 && row === peekRow && peek.classList.contains('is-on') && caseEl.hidden) morphOpen(+row.dataset.i);
    else openCase(+row.dataset.i);
  });
  caseEl.addEventListener('click', e => {
    if (e.target.closest('[data-close]')) return requestClose();
    const play = e.target.closest('.g-play');
    if (play) { const el = play.closest('[data-anim]'); el._play = play.classList.contains('is-paused'); return animSet(el); }
    const go = e.target.closest('[data-go]');
    if (go) return swapTo(+go.dataset.go, 1);
    const st = e.target.closest('[data-step]');
    if (st) step(+st.dataset.step);
  });
  // Tab reste dans la fiche ; depuis le titre, Tab mène à la barre
  caseEl.addEventListener('keydown', e => {
    if (e.key !== 'Tab') return;
    const f = $$('a[href], button:not([disabled]), [tabindex="0"]', caseEl).filter(el => el.offsetParent !== null);
    if (!f.length) return;
    if (!f.includes(document.activeElement)) { e.preventDefault(); (e.shiftKey ? f[f.length - 1] : f[0]).focus(); }
    else if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  });
  const fromHash = () => PROJECTS.findIndex(p => '#' + p.id === location.hash);
  window.addEventListener('popstate', () => {
    const i = fromHash();
    if (i >= 0) return openCase(i, { push: false });
    const wasOpen = current >= 0, f = lastFocus;
    pushed = false; doClose();
    // le retour vers une adresse à ancre (#methode…) fait sauter la page vers
    // cette section : la page reste là où la fiche avait été ouverte, et le
    // focus revient au bouton qui l'a ouverte (filet, voir setHash)
    if (wasOpen) requestAnimationFrame(() => {
      if (f && f.isConnected && document.activeElement !== f && !caseEl.contains(document.activeElement) && current < 0) f.focus({ preventScroll: true });
      if (Math.abs(scrollY - openY) < 2) return;
      if (lenis) lenis.scrollTo(openY, { immediate: true, force: true }); else scrollTo(0, openY);
    });
  });

  /* ---------- Mode Inspecter ----------
     La boucle du Dev Mode de Figma : survoler (cadre et fiche courte), cliquer
     ou toucher pour sélectionner, lire les propriétés en tokens dans un panneau,
     copier le CSS. Les styles calculés ne sont lus qu'au survol d'un nouvel
     élément, à la sélection ou au focus, jamais dans une boucle continue. */
  // saisie de texte en cours : les touches lui reviennent. Les curseurs du
  // playground n'en sont pas (Échap, I et T y marchent)
  const typing = el => el.closest && el.closest('input:not([type=range]):not([type=checkbox]):not([type=radio]), textarea, select, [contenteditable]:not([contenteditable="false"])');
  const inspectBtn = $('.inspect-btn');
  const inspectTouch = $('.inspect-touch');
  const probe = $('.probe');
  const probeBox = $('.probe-box');
  const probeTag = $('.probe-tag');
  const rx = $('.ruler-x .ruler-mark');
  const ry = $('.ruler-y .ruler-mark');
  const xNums = $('.ruler-nums');
  const yTrack = $('.ruler-track');
  const selBox = $('.sel-box');
  const selSize = $('.sel-size');
  const specLayer = $('.spec-layer');
  const panel = $('.inspect-panel');
  let inspecting = false, sel = null;
  let vw = 0, vh = 0, rulerTop = 0;
  cols.forEach((c, i) => c.style.setProperty('--c', i));   // cascade d'entrée des colonnes

  // interface du mode et fenêtres par-dessus la page : jamais inspectées
  const UI = '.topbar, .probe, .sel-box, .spec-layer, .inspect-panel, .inspect-chip, .toast, .dock, .case, .keys';
  // élément inspectable sous le pointeur ou le focus (un tracé SVG compte pour son icône)
  const pick = el => {
    if (!el || !el.closest || !el.closest('main, .foot') || el.closest(UI) || el.tagName === 'MAIN') return null;
    return el.closest('svg') || el;
  };
  const layerName = el => el.tagName.toLowerCase() + (el.classList[0] ? '.' + el.classList[0] : '');
  const px0 = v => Math.round(parseFloat(v)) || 0;
  const num = v => String(Math.round(parseFloat(v) * 100) / 100);
  // couleur calculée -> #rrggbb (opacité en % si besoin), via le canevas du playground
  const hex = c => {
    const [r, g, b, a] = toRgba(c);
    if (!a) return 'transparent';
    const h = '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
    return a < 255 ? `${h} ${Math.round(a / 2.55)} %` : h;
  };
  const hasText = el => el.classList.contains('ch') || [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const wdthOf = fvs => num((fvs.match(/"wdth"\s+(-?[\d.]+)/) || [0, 100])[1]);
  // relu quand ses transitions finissent : jamais une couleur intermédiaire
  // (transitions et animations qui finissent ; pas celles liées au scroll)
  const whenSettled = (el, fn) => {
    const running = el.getAnimations().filter(a => a.playState === 'running' && a.timeline === document.timeline && isFinite(a.effect.getComputedTiming().endTime));
    if (running.length) Promise.allSettled(running.map(a => a.finished)).then(fn);
  };
  function measureView() {
    vw = root.clientWidth; vh = innerHeight;
    rulerTop = parseFloat(getComputedStyle(root).getPropertyValue('--topbar')) + 18;
  }

  /* Règles : x de 100 en 100 sur la largeur de la fenêtre ; y en coordonnées
     de page, une piste d'étiquettes décalée de -(scrollY % 100), réécrite
     seulement quand la centaine change. */
  let yBase = -1, yShift = '';
  function buildRulers() {
    xNums.innerHTML = Array.from({ length: Math.floor(vw / 100) + 1 }, (_, k) => `<span style="left:${k * 100 + 3}px">${k * 100}</span>`).join('');
    const n = Math.ceil(vh / 100) + 2;
    if (yTrack.children.length !== n) yTrack.innerHTML = Array.from({ length: n }, (_, k) => `<span style="top:${k * 100 + 3}px"></span>`).join('');
    yBase = -1; placeRulerY(scrollY);
  }
  function placeRulerY(y) {
    const base = Math.floor(y / 100);
    if (base !== yBase) { yBase = base; [...yTrack.children].forEach((s, k) => { s.textContent = (base + k) * 100; }); }
    const t = `translate3d(0, ${-(y % 100).toFixed(1)}px, 0)`;
    if (t !== yShift) { yShift = t; yTrack.style.transform = t; }
  }

  /* Survol : le cadre glisse vers l'élément (lerp .35, arrêté une fois posé),
     la fiche suit le cadre. Au scroll, il reste collé à son élément. */
  const P = { x: 0, y: 0, w: 0, h: 0 }, PT = { x: 0, y: 0, w: 0, h: 0 };
  let probeEl = null, probeOn = false, probeBy = 'ptr', probeLoop = 0, pw = -1, ph = -1, tagW = 0, tagH = 0;
  let ptr = null, ptrFrame = 0;
  function describe(el) {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const lines = [`<b>${layerName(el)}</b>  ${Math.round(r.width)} × ${Math.round(r.height)}`];
    if (hasText(el)) {
      const wd = cs.fontVariationSettings.includes('wdth') ? ' · wdth ' + wdthOf(cs.fontVariationSettings) : '';
      lines.push(`${cs.fontFamily.split(',')[0].replace(/"/g, '')} ${cs.fontWeight}${wd}`);
      lines.push(`${px0(cs.fontSize)}px / ${cs.lineHeight === 'normal' ? 'auto' : px0(cs.lineHeight) + 'px'} · ${hex(cs.color)}`);
    }
    const p = [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft].map(px0);
    if (p.some(Boolean)) lines.push(`padding ${p.join(' ')}`);
    const bg = hex(cs.backgroundColor);
    if (bg !== 'transparent') lines.push(`fill ${bg}`);
    if (px0(cs.borderTopLeftRadius)) lines.push(`radius ${px0(cs.borderTopLeftRadius)}`);
    return lines.join('\n');
  }
  function describeProbe(el) {
    probeTag.innerHTML = describe(el);
    tagW = probeTag.offsetWidth; tagH = probeTag.offsetHeight;
    whenSettled(el, () => { if (probeEl === el && inspecting) { describeProbe(el); drawProbe(); } });
  }
  function drawProbe() {
    probeBox.style.transform = `translate3d(${P.x.toFixed(1)}px, ${P.y.toFixed(1)}px, 0)`;
    const w = Math.round(P.w), h = Math.round(P.h);
    if (w !== pw || h !== ph) { pw = w; ph = h; probeBox.style.width = w + 'px'; probeBox.style.height = h + 'px'; }
    // fiche sous le cadre ; au-dessus s'il n'y a plus la place ; dedans en dernier recours
    let lx = P.x, ly = P.y + P.h + 8;
    if (ly + tagH > vh - 8) ly = Math.max(8, P.y - tagH - 8);
    if (ly < rulerTop + 8) ly = Math.min(vh - tagH - 8, P.y + 8);
    lx = clamp(lx, 24, vw - tagW - 8);
    probeTag.style.transform = `translate3d(${Math.round(lx)}px, ${Math.round(ly)}px, 0)`;
  }
  function stepProbe() {
    let moving = false;
    for (const k in P) {
      const d = PT[k] - P[k];
      if (Math.abs(d) > .3) { P[k] += d * .35; moving = true; } else P[k] = PT[k];
    }
    drawProbe();
    probeLoop = moving ? requestAnimationFrame(stepProbe) : 0;
  }
  // jump : posé d'un coup (première apparition, scroll, mouvement réduit)
  function probeTo(el, r, jump) {
    if (!el) return hideProbe();
    Object.assign(PT, { x: r.left, y: r.top, w: r.width, h: r.height });
    if (el !== probeEl) { probeEl = el; describeProbe(el); showDeferred(); }
    if (!probeOn) { probeOn = jump = true; probe.classList.add('is-on'); }
    if (jump || reduce) {
      cancelAnimationFrame(probeLoop); probeLoop = 0;
      Object.assign(P, PT); drawProbe();
    } else if (!probeLoop) probeLoop = requestAnimationFrame(stepProbe);
  }
  function hideProbe() {
    if (!probeOn) return;
    probeOn = false; probeEl = null;
    cancelAnimationFrame(probeLoop); probeLoop = 0;
    probe.classList.remove('is-on');
    showDeferred();
  }
  function hoverFrame() {
    ptrFrame = 0;
    if (!inspecting || !ptr) return;
    const el = pick(document.elementFromPoint(ptr.x, ptr.y));
    const r = el && el.getBoundingClientRect();
    // repères des règles : x dans la fenêtre, y dans la page
    rx.style.transform = `translate3d(${ptr.x}px, 0, 0)`; rx.dataset.v = Math.round(ptr.x);
    ry.style.transform = `translate3d(0, ${ptr.y - rulerTop}px, 0)`; ry.dataset.v = Math.round(ptr.y + scrollY);
    probeBy = 'ptr';
    probeTo(el, r);
  }
  window.addEventListener('pointermove', e => {
    if (!inspecting || e.pointerType === 'touch') return;
    ptr = { x: e.clientX, y: e.clientY };
    if (!ptrFrame) ptrFrame = requestAnimationFrame(hoverFrame);
  }, { passive: true });
  root.addEventListener('pointerleave', () => { if (probeBy === 'ptr') { ptr = null; hideProbe(); } });
  // Tab inspecte : le cadre suit le focus clavier (pas celui d'un clic ou d'un tap)
  document.addEventListener('focusin', e => {
    if (!inspecting || !e.target.matches(':focus-visible')) return;
    const el = pick(e.target);
    probeBy = 'focus';
    probeTo(el, el && el.getBoundingClientRect());
    // après le défilement qui amène l'élément dans la fenêtre
    if (sel) requestAnimationFrame(dodgePanel);
  });

  /* Noms des blocs ([data-spec]) : des onglets dans un calque à l'origine du
     document, posés hors du bloc sans jamais couvrir un texte, une image ou un
     autre onglet : au-dessus à gauche, au-dessus à droite, puis dans la marge
     de gauche. Trop large pour l'écran, le nom prend sa forme courte
     (data-spec-short), jamais coupé. Nulle part où se poser : l'onglet attend
     le survol ou la sélection du bloc (.is-deferred). */
  let specEls = [], specT = 0;
  // position dans la page sans les transforms (révélations, nom qui s'écarte)
  const docBox = el => {
    let x = 0, y = 0;
    for (let e = el; e; e = e.offsetParent) { x += e.offsetLeft; y += e.offsetTop; }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight };
  };
  const hit = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
  // ce que les onglets ne couvrent pas : les lignes de texte et les images de la
  // page, en coordonnées de mise en page (le décalage des révélations retiré).
  // Une ligne est bornée par son bloc : l'œil d'une police à interligne serré
  // (le nom) déborde de sa boîte sans rien y dessiner
  function specObstacles() {
    const out = [], sx = scrollX, sy = scrollY;
    const blocks = new Map(), range = document.createRange();
    const blockOf = el => {
      let b = el;
      while (b.parentElement && /^(inline|contents)$/.test(getComputedStyle(b).display)) b = b.parentElement;
      return b;
    };
    const frame = el => {
      if (!blocks.has(el)) {
        const r = el.getBoundingClientRect(), d = docBox(el);
        blocks.set(el, { dx: r.left + sx - d.x, dy: r.top + sy - d.y, box: d });
      }
      return blocks.get(el);
    };
    const push = (r, f, clip) => {
      let y1 = r.top + sy - f.dy, y2 = r.bottom + sy - f.dy;
      if (clip) { y1 = Math.max(y1, f.box.y); y2 = Math.min(y2, f.box.y + f.box.h); }
      if (r.width > 0 && y2 > y1) out.push({ x: r.left + sx - f.dx, y: y1, w: r.width, h: y2 - y1 });
    };
    const skip = '.sr-only, ' + UI;
    $$('main, .foot').forEach(scope => {
      const walk = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, {
        acceptNode: n => n.textContent.trim() && !n.parentElement.closest(skip) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
      });
      for (let n = walk.nextNode(); n; n = walk.nextNode()) {
        range.selectNodeContents(n);
        const rects = range.getClientRects();
        if (!rects.length) continue;
        const f = frame(blockOf(n.parentElement));
        for (const r of rects) push(r, f, true);
      }
      // images et icônes (un svg compte en entier, pas ses tracés)
      $$('img, video, canvas, svg', scope).forEach(m => {
        if (m.parentElement.closest('svg') || m.closest(skip)) return;
        const r = m.getBoundingClientRect();
        if (r.width && r.height) push(r, frame(blockOf(m instanceof HTMLElement ? m : m.parentElement)), false);
      });
    });
    return out;
  }
  function fillLabels() {
    clearTimeout(specT);
    specEls = $$('[data-spec]').filter(el => !el.closest('.topbar, .case') && el.getClientRects().length);
    specLayer.replaceChildren(...specEls.map((el, i) => {
      const s = document.createElement('span');
      s.className = 'spec-label';
      s.textContent = el.dataset.spec;
      s.style.setProperty('--sd', Math.min(i * 30, 300) + 'ms');
      return s;
    }));
    placeLabels();
  }
  function placeLabels() {
    const tags = [...specLayer.children];
    if (!tags.length) return;
    // lectures d'abord (noms entiers, puis formes courtes), écritures ensuite
    const full = specEls.map(el => el.dataset.spec), short = specEls.map(el => el.dataset.specShort || '');
    tags.forEach((t, i) => { t.textContent = full[i]; });
    const fullSz = tags.map(t => [t.offsetWidth, t.offsetHeight]);
    tags.forEach((t, i) => { if (short[i]) t.textContent = short[i]; });
    const shortSz = tags.map((t, i) => short[i] ? [t.offsetWidth, t.offsetHeight] : null);
    const boxes = specEls.map(docBox);
    const obst = specObstacles();
    const edge = root.clientWidth - 8;
    const placed = [];
    const spots = (b, w, h) => [
      { x: b.x - 1, y: b.y - 1 - h, side: false },           // au-dessus, à gauche
      { x: b.x + b.w + 1 - w, y: b.y - 1 - h, side: false },   // au-dessus, à droite
      { x: b.x - w - 4, y: b.y, side: true }                   // dans la marge de gauche
    ].map(s => Object.assign(s, { w, h }));
    const free = r => r.x >= 0 && r.y >= 0 && r.x + r.w <= edge && !placed.some(p => hit(p, r)) && !obst.some(o => hit(o, r));
    const out = tags.map((t, i) => {
      const b = boxes[i];
      for (const [txt, sz] of [[full[i], fullSz[i]], [short[i], shortSz[i]]]) {
        if (!sz) continue;
        const r = spots(b, sz[0], sz[1]).find(free);
        if (r) { placed.push(r); return { txt, r, wait: false }; }
      }
      // en attente : montré au survol ou à la sélection, au-dessus à gauche, dans l'écran
      const long = shortSz[i] && b.x - 1 + fullSz[i][0] > edge;
      const [w, h] = long ? shortSz[i] : fullSz[i];
      const r = { x: clamp(b.x - 1, 0, Math.max(0, edge - w)), y: b.y - 1 - h, w, h, side: false };
      if (r.y < 0) r.y = b.y + 4;
      return { txt: long ? short[i] : full[i], r, wait: true };
    });
    tags.forEach((t, i) => {
      const { txt, r, wait } = out[i];
      t.textContent = txt;
      t.style.transform = `translate(${r.x}px, ${r.y}px)`;
      t.classList.toggle('is-side', r.side);
      t.classList.toggle('is-deferred', wait);
    });
    showDeferred();
  }
  // onglets en attente : celui du bloc survolé (ou focalisé) et du bloc sélectionné
  function showDeferred() {
    const tags = specLayer.children;
    specEls.forEach((el, i) => {
      const t = tags[i];
      if (t && t.classList.contains('is-deferred')) t.classList.toggle('is-shown', [probeEl, sel].some(x => x && el.contains(x)));
    });
  }

  /* Sélection : cadre à 8 poignées et taille dessous, suivi au scroll */
  let selKey = '';
  function placeSel(r) {
    selBox.style.transform = `translate3d(${r.left}px, ${r.top}px, 0)`;
    const w = Math.round(r.width), h = Math.round(r.height), key = w + ' ' + h;
    if (key === selKey) return;
    selKey = key;
    selBox.style.width = r.width + 'px'; selBox.style.height = r.height + 'px';
    selSize.textContent = `${w} × ${h}`;
  }
  // sélection annoncée aux lecteurs d'écran seulement (le focus reste sur la page :
  // Entrée et Maj+Entrée en partent). Vidée d'abord : la même sélection se relit
  const ipLive = $('.ip-live');
  let liveFrame = 0;
  function select(el) {
    sel = el; selKey = '';
    const r = el.getBoundingClientRect();
    placeSel(r);
    selBox.classList.add('is-on');
    root.classList.add('has-sel');
    showDeferred();
    renderPanel();
    showPanel();
    if (touchList) revealSel(el);
    else dodgePanel();
    ipLive.textContent = '';
    cancelAnimationFrame(liveFrame);
    liveFrame = requestAnimationFrame(() => { ipLive.textContent = `${layerName(el)} sélectionné, ${Math.round(r.width)} × ${Math.round(r.height)}`; });
  }
  /* Au doigt, le panneau monte du bas : l'élément choisi qu'il cacherait remonte
     entre la pastille (la barre du haut, à l'horizontale) et le panneau, centré
     s'il y tient, sinon son haut sous la pastille. La page a gagné 45svh en bas
     pendant la sélection (style.css) : même le pied de page peut remonter. */
  const chip = $('.inspect-chip');
  const sheetLow = matchMedia('(orientation: landscape) and (max-height: 520px)');
  function revealSel(el) {
    if (lenis) lenis.resize();
    const r = el.getBoundingClientRect();
    const top = (sheetLow.matches ? $('.topbar') : chip).getBoundingClientRect().bottom + 8;
    // haut du panneau une fois monté (il part encore de translateY(100%))
    const bottom = innerHeight - panel.offsetHeight - 8;
    if (Math.min(r.bottom, bottom) - Math.max(r.top, top) >= Math.min(24, r.height)) return;
    const to = r.height <= bottom - top ? top + (bottom - top - r.height) / 2 : top;
    const y = Math.max(0, scrollY + r.top - to);
    if (lenis) lenis.scrollTo(y, { duration: .8, force: true });
    else window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
  }
  /* Le panneau ne cache jamais l'élément focalisé (RGAA 10.7, WCAG 2.4.11), ni,
     sans focus clavier dans la page, l'élément sélectionné. À la souris, il
     glisse du bord droit au bord gauche quand il le couvrirait (le côté le moins
     couvert l'emporte), et revient à droite dès que la place est libre. Au doigt,
     le panneau monte du bas : c'est l'élément qui remonte au-dessus de lui. */
  function dodgePanel() {
    if (!sel || panel.hidden) return;
    const a = document.activeElement;
    const kbd = a && a !== document.body && pick(a) && a.matches(':focus-visible');
    const el = kbd ? a : sel;
    const r = el.getBoundingClientRect();
    if (noHover.matches) {
      if (!kbd) return;   // sélection au doigt : revealSel s'en charge
      const top = $('.topbar').getBoundingClientRect().bottom + 8;
      const bottom = innerHeight - panel.offsetHeight - 8;
      if (r.top >= top && r.bottom <= bottom) return;
      const y = Math.max(0, scrollY + r.top + r.height / 2 - (top + bottom) / 2);
      if (lenis) lenis.scrollTo(y, { duration: .6, force: true });
      else window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
      return;
    }
    // places du panneau sans son décalage (offset* ignorent le transform) : bord
    // droit, où la mise en page le pose, ou bord gauche, à 16 px
    const w = panel.offsetWidth, x = panel.offsetLeft, top = panel.offsetTop, bottom = top + panel.offsetHeight;
    // 8 px autour de l'élément : l'anneau de focus (2 px, décalé de 3) compte aussi
    const hit = x0 => Math.max(0, Math.min(r.right + 8, x0 + w) - Math.max(r.left - 8, x0)) * Math.max(0, Math.min(r.bottom + 8, bottom) - Math.max(r.top - 8, top));
    const right = hit(x), left = hit(16);
    panel.style.setProperty('--ip-dx', 16 - x + 'px');
    panel.classList.toggle('is-left', right > 0 && left < right);
  }
  function deselect() {
    if (!sel) return;
    const was = sel;
    sel = null;
    selBox.classList.remove('is-on');
    root.classList.remove('has-sel');
    showDeferred();
    // le focus ne se perd pas avec le panneau
    if (panel.contains(document.activeElement)) (was.tabIndex >= 0 ? was : touchList ? inspectTouch : inspectBtn).focus({ preventScroll: true });
    hidePanel();
  }
  // mode Inspecter : un clic (ou un tap, Entrée, Espace) dans la page sélectionne au lieu d'agir
  document.addEventListener('click', e => {
    if (!inspecting) return;
    const el = pick(e.target);
    if (!el) return;
    e.preventDefault(); e.stopPropagation();
    select(el);
    try {
      if (sessionStorage.getItem('ql-inspect-tip') !== null) return;
      sessionStorage.setItem('ql-inspect-tip', '1');
    } catch (err) { return; }
    // au clavier (detail 0), les touches qui remplacent le panneau
    toast(touchList
      ? 'En mode Inspecter, toucher un élément le sélectionne. Touchez l’icône Inspecter pour revenir.'
      : !e.detail
        ? 'Élément sélectionné. Tab pour ouvrir le panneau, Échap pour désélectionner.'
        : 'En mode Inspecter, un clic sélectionne l’élément. ' + (keysOn ? 'Touche I pour revenir.' : 'Bouton Inspecter pour revenir.'));
  }, true);

  /* Panneau : nom du calque, parents jusqu'à la section, mise en page,
     espacement, typographie, couleurs et CSS, en tokens quand la valeur en
     est un. Même contenu au doigt, dans un panneau qui monte du bas. */
  const ipName = $('.ip-name', panel);
  const ipCrumbs = $('.ip-crumbs', panel);
  const ipFields = $('.ip-fields', panel);
  const ipSpace = $('.ip-space', panel);
  const ipTypo = $('.ip-typo', panel);
  const ipAg = $('.ip-ag', panel);
  const ipRows = $('.ip-rows', panel);
  const ipColors = $('.ip-colors', panel);
  const ipCode = $('.ip-code', panel);
  let ipCss = '';   // le CSS copié, lignes comprises (le bloc affiché est en spans)
  const ipCopy = $('.ip-copy', panel);
  let crumbEls = [], panelT = 0;

  /* Tokens : les propriétés personnalisées déclarées sur :root (feuilles du
     site ; celles d'un autre domaine sont illisibles), résolues sur un témoin
     caché. Couleurs, polices, rayons (--r-*), tailles mono (--mono-*) et
     espacements, chacun dans sa table ; à valeur égale, le premier déclaré
     gagne (--accent avant --spec). Relu au changement de thème et de largeur. */
  let tokens = null, host = null;
  function readTokens() {
    const names = new Set();
    const walk = rules => {
      for (const r of rules) {
        if (r.selectorText) { if (r.selectorText.startsWith(':root')) Array.from(r.style).forEach(p => { if (p.startsWith('--')) names.add(p); }); }
        else if (r.cssRules) walk(r.cssRules);   // @media, @supports
      }
    };
    for (const s of document.styleSheets) { try { walk(s.cssRules); } catch (e) { /* feuille d'un autre domaine */ } }
    if (!host) {
      host = document.createElement('div');
      host.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;overflow:hidden;visibility:hidden;pointer-events:none';
      host.setAttribute('aria-hidden', 'true');
      host.appendChild(document.createElement('div'));
      document.body.appendChild(host);
    }
    const t = host.firstChild, cs = getComputedStyle(t), rootCs = getComputedStyle(root);
    const T = { color: new Map(), font: new Map(), radius: new Map(), type: new Map(), space: new Map() };
    const put = (map, k, n) => { if (!map.has(k)) map.set(k, n); };
    names.forEach(n => {
      const raw = rootCs.getPropertyValue(n).trim();
      if (!raw) return;
      if (n.startsWith('--f-')) { t.style.fontFamily = `var(${n})`; put(T.font, cs.fontFamily, n); }
      else if (CSS.supports('color', raw)) { t.style.color = `var(${n})`; put(T.color, cs.color, n); }
      else if (CSS.supports('width', raw)) {
        t.style.width = `var(${n})`;
        put(n.startsWith('--r-') ? T.radius : n.startsWith('--mono-') ? T.type : T.space, num(cs.width), n);
      }
    });
    t.removeAttribute('style');
    return T;
  }
  // display par défaut d'une balise (feuilles du site comprises), pour ne garder que l'utile
  const uaDisplay = {};
  const defaultDisplay = tag => {
    if (!(tag in uaDisplay)) {
      const d = host.appendChild(document.createElement(tag));
      uaDisplay[tag] = getComputedStyle(d).display;
      d.remove();
    }
    return uaDisplay[tag];
  };
  // valeur -> var(--token) quand elle en est un ; sinon la valeur (couleur opaque en hex)
  const tok = (kind, v) => {
    const n = tokens[kind].get(kind === 'color' || kind === 'font' ? v : num(v));
    if (n) return `var(${n})`;
    return kind === 'color' && !hex(v).includes(' ') ? hex(v) : v;
  };
  const len = (kind, v) => parseFloat(v) ? tok(kind, num(v) + 'px') : '0';
  const box4 = v => v[1] === v[3] ? (v[0] === v[2] ? (v[0] === v[1] ? [v[0]] : [v[0], v[1]]) : [v[0], v[1], v[2]]) : v;
  function cssOf(el, cs, text) {
    const out = [];
    const add = (p, v) => out.push(`  ${p}: ${v};`);
    const tag = el.tagName.toLowerCase();
    if (tag !== 'svg' && cs.display !== defaultDisplay(tag)) add('display', cs.display);
    if (/flex|grid/.test(cs.display) && (cs.rowGap !== 'normal' || cs.columnGap !== 'normal')) {
      const g = [cs.rowGap, cs.columnGap].map(v => v === 'normal' ? '0' : len('space', v));
      add('gap', g[0] === g[1] ? g[0] : g.join(' '));
    }
    const pad = ['Top', 'Right', 'Bottom', 'Left'].map(s => len('space', cs['padding' + s]));
    if (pad.some(v => v !== '0')) add('padding', box4(pad).join(' '));
    const rad = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map(s => len('radius', cs[`border${s}Radius`]));
    if (rad.some(v => v !== '0')) add('border-radius', box4(rad).join(' '));
    if (text) {
      add('font-family', tok('font', cs.fontFamily));
      add('font-size', tok('type', num(cs.fontSize) + 'px'));   // arrondi comme la ligne Typographie
      add('font-weight', cs.fontWeight);
      if (cs.lineHeight !== 'normal') add('line-height', num(cs.lineHeight) + 'px');
      if (cs.letterSpacing !== 'normal' && parseFloat(cs.letterSpacing)) add('letter-spacing', num(cs.letterSpacing) + 'px');
      if (cs.fontVariationSettings !== 'normal') add('font-variation-settings', cs.fontVariationSettings);
    }
    if (hex(cs.backgroundColor) !== 'transparent') add('background', tok('color', cs.backgroundColor));
    if (text || (el.parentElement && getComputedStyle(el.parentElement).color !== cs.color)) add('color', tok('color', cs.color));
    // bordures visibles seulement (une bordure transparente ne sert qu'à réserver la place)
    const bw = ['Top', 'Right', 'Bottom', 'Left'].map(s => cs[`border${s}Style`] === 'none' || hex(cs[`border${s}Color`]) === 'transparent' ? 0 : parseFloat(cs[`border${s}Width`]));
    const border = s => `${num(cs[`border${s}Width`])}px ${cs[`border${s}Style`]} ${tok('color', cs[`border${s}Color`])}`;
    if (bw.every(w => w && w === bw[0])) add('border', border('Top'));
    else ['Top', 'Right', 'Bottom', 'Left'].forEach((s, i) => { if (bw[i]) add('border-' + s.toLowerCase(), border(s)); });
    const selector = el.classList[0] ? '.' + el.classList[0] : tag;
    return `${selector} {\n${out.join('\n')}\n}`;
  }
  function renderPanel() {
    const el = sel;
    if (!el) return;
    tokens = tokens || readTokens();
    const cs = getComputedStyle(el), r = el.getBoundingClientRect(), text = hasText(el);
    ipName.textContent = layerName(el);
    // parents, de la section (ou du pied de page) jusqu'au parent direct
    const stop = el.closest('main > section, .foot') || el;
    crumbEls = [];
    for (let a = el; a !== stop; ) { a = a.parentElement; crumbEls.unshift(a); }
    // réécrits seulement s'ils changent : une relecture ne fait pas perdre le focus à un parent
    const crumbs = crumbEls.map((a, k) => `<li><button type="button" data-k="${k}">${layerName(a)}</button></li>`).join('');
    if (ipCrumbs.innerHTML !== crumbs) ipCrumbs.innerHTML = crumbs;
    ipFields.innerHTML = [['W', r.width], ['H', r.height], ['X', r.left + scrollX], ['Y', r.top + scrollY]]
      .map(([k, v]) => `<div><span>${k}</span><b>${Math.round(v)}</b></div>`).join('');
    const sides = p => ['Top', 'Right', 'Bottom', 'Left'].map(s => px0(cs[p + s]));
    const ring = v => ['t', 'r', 'b', 'l'].map((k, i) => `<span class="ip-v ${k}${v[i] ? '' : ' is-0'}">${v[i]}</span>`).join('');
    const pd = sides('padding'), bl = px0(cs.borderLeftWidth) + px0(cs.borderRightWidth), bt = px0(cs.borderTopWidth) + px0(cs.borderBottomWidth);
    ipSpace.innerHTML = `<div class="ip-m"><span class="ip-cap">margin</span>${ring(sides('margin'))}<div class="ip-p"><span class="ip-cap">padding</span>${ring(pd)}<span class="ip-c">${Math.round(r.width) - pd[1] - pd[3] - bl} × ${Math.round(r.height) - pd[0] - pd[2] - bt}</span></div></div>`;
    ipTypo.hidden = !text;
    if (text) {
      Object.assign(ipAg.style, { fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontVariationSettings: cs.fontVariationSettings });
      const ls = cs.letterSpacing === 'normal' ? '0' : num(cs.letterSpacing) + 'px';
      ipRows.innerHTML = [
        ['Police', cs.fontFamily.split(',')[0].replace(/"/g, '')],
        ['Graisse', cs.fontWeight],
        ['Taille', `${num(cs.fontSize)}px / ${cs.lineHeight === 'normal' ? 'normal' : num(cs.lineHeight) + 'px'}`],
        ['Interlettrage', ls],
        ['wdth', wdthOf(cs.fontVariationSettings)]
      ].map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
    }
    const colors = [['Texte', cs.color], ['Fond', cs.backgroundColor]];
    if (cs.borderTopStyle !== 'none' && parseFloat(cs.borderTopWidth)) colors.push(['Bordure', cs.borderTopColor]);
    ipColors.innerHTML = colors.filter(([, c]) => hex(c) !== 'transparent').map(([k, c]) => {
      const n = tokens.color.get(c);
      return `<li><span class="ip-sw" style="background:${c}"></span><span>${k}</span><b>${n || ''}</b><code>${hex(c)}</code></li>`;
    }).join('');
    // une ligne par déclaration : coupée, la suite reste en retrait sous la propriété
    ipCss = cssOf(el, cs, text);
    // un mot à trait d'union (var(--line), -5.81px) ne se coupe pas en deux
    ipCode.replaceChildren(...ipCss.split('\n').map(l => {
      const s = document.createElement('span');
      s.append(...l.split(/( +)/).map(w => {
        if (!w.includes('-')) return w;
        const n = document.createElement('span');
        n.className = 'ip-nw'; n.textContent = w;
        return n;
      }));
      return s;
    }));
    whenSettled(el, () => { if (sel === el) renderPanel(); });
  }
  // l'élément sélectionné change d'état après coup (survol quitté, focus perdu) :
  // panneau et cadre relus à la fin de sa transition, une fois par image
  let selFrame = 0;
  const reSel = e => {
    if (!inspecting || !sel || e.target !== sel || selFrame) return;
    selFrame = requestAnimationFrame(() => { selFrame = 0; if (sel) { placeSel(sel.getBoundingClientRect()); renderPanel(); } });
  };
  document.addEventListener('transitionend', reSel, true);
  document.addEventListener('animationend', reSel, true);
  ipCrumbs.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (b) select(crumbEls[+b.dataset.k]);
  });
  const ipClose = $('.ip-close', panel);
  ipClose.addEventListener('click', deselect);
  // Maj+Tab sur la croix : retour à l'élément sélectionné, ou au lien qui le porte,
  // sinon au bouton Inspecter
  ipClose.addEventListener('keydown', e => {
    if (e.key !== 'Tab' || !e.shiftKey || !sel) return;
    e.preventDefault();
    const back = sel.tabIndex >= 0 ? sel : sel.closest('a[href], button, [tabindex]:not([tabindex="-1"])');
    (back || (touchList ? inspectTouch : inspectBtn)).focus();
  });
  async function copyCss() {
    if (sel && await copyText(ipCss, ipCopy)) toast('CSS copié');
  }
  ipCopy.addEventListener('click', copyCss);
  function showPanel() {
    clearTimeout(panelT);
    if (panel.hidden) { panel.hidden = false; void panel.offsetWidth; }   // état de départ avant l'entrée
    panel.classList.add('is-on');
  }
  function hidePanel() {
    panel.classList.remove('is-on');
    clearTimeout(panelT);
    panelT = setTimeout(() => { if (!sel) { panel.hidden = true; panel.classList.remove('is-left'); } }, reduce ? 0 : 450);
  }
  // au doigt : glisser la tête du panneau de plus de 80 px vers le bas désélectionne
  const ipHead = $('.ip-head', panel);
  let sheetDrag = null;
  ipHead.addEventListener('pointerdown', e => {
    if (!touchList || e.target.closest('button')) return;
    sheetDrag = { id: e.pointerId, y0: e.clientY, dy: 0 };
    ipHead.setPointerCapture(e.pointerId);
    panel.style.transition = 'none';
  });
  ipHead.addEventListener('pointermove', e => {
    if (!sheetDrag || e.pointerId !== sheetDrag.id) return;
    sheetDrag.dy = Math.max(0, e.clientY - sheetDrag.y0);
    panel.style.transform = `translateY(${sheetDrag.dy}px)`;
  });
  const endSheet = e => {
    if (!sheetDrag || e.pointerId !== sheetDrag.id) return;
    const far = sheetDrag.dy > 80;
    sheetDrag = null;
    // la transition repart de la position glissée : vers le bas, ou retour en place
    panel.style.transition = '';
    if (far) deselect();
    panel.style.transform = '';
  };
  ipHead.addEventListener('pointerup', endSheet);
  ipHead.addEventListener('pointercancel', endSheet);

  // relu avec la mise en page : largeur, polices, hauteur de page
  function inspectMeasure() {
    measureView(); buildRulers(); placeLabels();
    tokens = null;
    if (sel) { renderPanel(); dodgePanel(); }
    queueScroll();
  }
  // au scroll (onScroll) : lectures des cadres suivis d'abord, puis écritures
  function inspectScroll(y) {
    const selR = sel && sel.isConnected ? sel.getBoundingClientRect() : null;
    let el = null;
    if (probeBy === 'ptr' && ptr && probeOn) el = pick(document.elementFromPoint(ptr.x, ptr.y));
    else if (probeBy === 'focus' && probeEl && probeEl.isConnected) el = probeEl;
    const r = el && el.getBoundingClientRect();
    placeRulerY(y);
    if (ptr) ry.dataset.v = Math.round(ptr.y + y);
    if (selR) placeSel(selR);
    if (probeOn) probeTo(el, r, true);
  }

  function setInspect(on) {
    if (on === inspecting) return;
    inspecting = on;
    inspectBtn.setAttribute('aria-pressed', on);
    inspectTouch.setAttribute('aria-pressed', on);
    if (on) {
      hidePeek();
      // calques remplis avant la classe : les noms des blocs partent bien de 0
      measureView(); buildRulers(); fillLabels();
      root.classList.add('is-inspect');
      toastEl.classList.add('toast--top');
      if (!touchList) toast('Mode Inspecter : survolez un élément ou cliquez dessus. Échap pour quitter.');
    } else {
      root.classList.remove('is-inspect');
      deselect(); hideProbe();
      ptr = null;
      toastEl.classList.remove('is-on', 'toast--top');
      specT = setTimeout(() => specLayer.replaceChildren(), 200);   // après le fondu de sortie
    }
  }
  inspectBtn.addEventListener('click', () => setInspect(!inspecting));
  inspectTouch.addEventListener('click', () => setInspect(!inspecting));
  $('.inspect-chip button').addEventListener('click', () => setInspect(false));
  // clavier, avec une sélection : Entrée descend au premier enfant (focus sur l'élément
  // sélectionné ou un parent), Maj+Entrée remonte au parent (jusqu'à la section), C copie
  // Tab depuis l'élément sélectionné (ou son lien) : le panneau, juste après lui
  // dans l'ordre de lecture (RGAA 12.8) ; Maj+Tab sur la croix y ramène
  window.addEventListener('keydown', e => {
    if (!inspecting || !sel || e.metaKey || e.ctrlKey || e.altKey || typing(e.target)) return;
    const a = document.activeElement;
    if (e.key === 'Tab' && !e.shiftKey && !panel.hidden && a !== document.body && (a === sel || sel.contains(a) || a.contains(sel))) {
      e.preventDefault();
      ipClose.focus();
      return;
    }
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      const up = pick(sel.parentElement);
      if (up) select(up);
    } else if (e.key === 'Enter' && (a === document.body || a.contains(sel))) {
      e.preventDefault();
      const down = sel.tagName.toLowerCase() === 'svg' ? null : pick(sel.firstElementChild);
      if (down) select(down);
    } else if ((e.key === 'c' || e.key === 'C') && !e.shiftKey && !e.repeat && keysOn && !noHover.matches) copyCss();   // keysOn, noHover : Clavier
  });

  /* ---------- Playground composant ----------
     Un seul état ({ radius, padx, weight, wdth, fill, state }) : le bouton, son
     contraste et le code généré (CSS, tokens DTCG en JSON, Tailwind) en découlent. */
  const demo = $('.demo-btn');
  const labOut = $('#lab-out');
  const ranges = $$('[data-token]');
  const lab = { radius: 10, padx: 26, weight: 650, wdth: 100, fill: 'ink', state: 'default' };
  let fmt = 'css';
  const units = { radius: 'px', padx: 'px', weight: '', wdth: '%' };
  const cssVar = { radius: '--radius', padx: '--pad-x', weight: '--w', wdth: '--wd' };
  // fonds : valeur posée sur le bouton (v), puis sa forme dans le CSS, le JSON et Tailwind.
  // Survol : bleu pour tous, sauf le fond Bleu qui passe au marine (style.css)
  const HOVER = { css: 'var(--accent)', token: '{color.accent}', tw: 'hover:bg-accent' };
  const FILLS = {
    ink: { v: 'var(--ink)', css: 'var(--ink)', token: '{color.ink}', tw: 'bg-[var(--ink)]' },
    accent: { v: 'var(--accent)', css: 'var(--accent)', token: '{color.accent}', tw: 'bg-accent', hover: { css: 'var(--navy)', token: '#14244d', tw: 'hover:bg-[#14244d]' } },
    navy: { v: '#14244d', css: 'var(--navy)', token: '{color.navy}', tw: 'bg-[#14244d]' },
    outline: { v: 'transparent', css: 'transparent', token: 'transparent', tw: 'bg-transparent border border-current' }
  };
  // texte : celle des trois couleurs qui contraste le plus avec le fond ; l'encre sur le contour
  const TEXTS = [
    { v: 'var(--paper)', css: 'var(--paper)', token: '{color.paper}', tw: 'text-[var(--paper)]' },
    { v: '#fff', css: '#fff', token: '#ffffff', tw: 'text-white' },
    { v: '#14244d', css: 'var(--navy)', token: '{color.navy}', tw: 'text-[#14244d]' }
  ];
  const INK = { v: 'var(--ink)', css: 'var(--ink)', token: '{color.ink}', tw: 'text-[var(--ink)]' };
  let text = TEXTS[0];

  /* Couleurs lues sur un double du bouton jamais rendu (display none, donc sans
     transition : valeurs finales tout de suite), puis peintes sur 1 px de
     canevas : rgb, color(srgb…) ou oklab reviennent tous en [r, g, b, a]. */
  const twin = demo.cloneNode(false);
  twin.style.display = 'none';
  demo.after(twin);
  const dot = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  // rgb() et rgba() lus tels quels ; le reste peint opaque, l'opacité reprise de
  // la chaîne : le canevas prémultiplie, une couleur à 12 % reviendrait faussée
  const toRgba = css => {
    const m = css.match(/^rgba?\(([^)]+)\)$/);
    if (m) {
      const v = m[1].split(/[\s,\/]+/).map(parseFloat);
      return [v[0], v[1], v[2]].map(Math.round).concat(Math.round((v.length > 3 ? v[3] : 1) * 255));
    }
    const am = css.match(/\/\s*([\d.]+)(%?)\s*\)$/);
    const a = am ? parseFloat(am[1]) / (am[2] ? 100 : 1) : 1;
    dot.clearRect(0, 0, 1, 1);
    dot.fillStyle = 'transparent'; dot.fillStyle = am ? css.replace(/\s*\/\s*[\d.]+%?\s*\)$/, ')') : css;
    dot.fillRect(0, 0, 1, 1);
    const [r, g, b, a0] = dot.getImageData(0, 0, 1, 1).data;
    return [r, g, b, a0 ? Math.round(a * 255) : 0];
  };
  // gardées par thème : une seule lecture par couleur et par thème (pastilles, texte du bouton)
  const resolved = {};
  const resolve = v => {
    const k = (root.dataset.theme || 'dark') + '|' + v;
    if (resolved[k]) return resolved[k];
    twin.style.color = v;
    const c = toRgba(getComputedStyle(twin).color);
    twin.style.color = '';
    return (resolved[k] = c);
  };
  // luminance relative et rapport de contraste WCAG 2
  const lum = c => {
    const [r, g, b] = c.slice(0, 3).map(x => { x /= 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; });
    return .2126 * r + .7152 * g + .0722 * b;
  };
  const ratio = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + .05) / (lo + .05); };
  const pickText = () => {
    if (lab.fill === 'outline') return INK;
    const bg = resolve(FILLS[lab.fill].v);
    const score = TEXTS.map(t => ratio(bg, resolve(t.v)));
    return TEXTS[score.indexOf(Math.max(...score))];
  };

  // lecture sous le bouton : tel qu'il s'affiche (état, survol compris) ;
  // sur fond transparent, c'est le fond de la scène qui compte
  const readout = $('.contrast');
  const stageBg = $('.lab-stage');
  /* live : annoncé aux lecteurs d'écran (changement fait par le visiteur) ;
     le survol et le changement de thème relisent le texte sans l'annoncer */
  function readContrast(live) {
    readout.setAttribute('aria-live', live === true ? 'polite' : 'off');
    let html;
    if (lab.state === 'disabled') html = 'Inactif · contraste non requis';   // WCAG 1.4.3 exclut les éléments inactifs
    else {
      twin.className = demo.className;
      twin.dataset.fill = demo.dataset.fill;   // survol du fond Bleu : marine (style.css)
      twin.style.cssText = demo.style.cssText + ';display:none';
      twin.classList.toggle('is-hover', demo.classList.contains('is-hover') || demo.matches(':hover'));
      const cs = getComputedStyle(twin);
      let bg = toRgba(cs.backgroundColor);
      if (bg[3] === 0) bg = toRgba(getComputedStyle(stageBg).backgroundColor);
      // au dixième ; sous un seuil, jamais affiché le seuil (4,49 reste insuffisant, 6,96 reste AA)
      const r = ratio(bg, toRgba(cs.color));
      const lvl = r >= 7 ? 'AAA' : r >= 4.5 ? 'AA' : null;
      const cap = r < 4.5 ? 4.4 : r < 7 ? 6.9 : Infinity;
      const n = Math.min(Math.round(r * 10) / 10, cap).toFixed(1).replace('.', ',');
      html = lvl ? `Contraste ${n}:1 · ${lvl}` : `Contraste ${n}:1 · <span class="contrast-fail">Insuffisant (AA 4,5:1)</span>`;
    }
    if (readout.innerHTML !== html) readout.innerHTML = html;
  }
  demo.addEventListener('pointerenter', () => readContrast());
  demo.addEventListener('pointerleave', () => readContrast());

  // code : les valeurs modifiées clignotent (.flash), dans chaque format
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const STATES = {
    default: '',
    hover: '\n.btn-primary:hover {\n  background: {HOVER};\n  color: {#fff};\n}',
    focus: '\n.btn-primary:focus-visible {\n  outline: {2px solid var(--accent-t)};\n  outline-offset: {3px};\n}',
    disabled: '\n.btn-primary:disabled {\n  opacity: {.35};\n}'
  };
  // une ligne par groupe de classes (chaque ligne clignote en entier)
  const TW_STATES = {
    default: [],
    hover: ['HOVER hover:text-white'],
    focus: ['focus-visible:outline-2', 'focus-visible:outline-offset-3', 'focus-visible:outline-[var(--accent-t)]'],
    disabled: ['disabled:opacity-35']
  };
  const JSON_KEYS = { radius: 'radius', 'padding-x': 'padx', 'font-weight': 'weight', 'font-width': 'wdth', background: 'fill', 'background-hover': 'state', text: 'text' };
  function render(changed) {
    const f = FILLS[lab.fill], hov = f.hover || HOVER;
    const b = (k, v) => `<b${changed.includes(k) ? ' class="flash"' : ''}>${esc(v)}</b>`;
    let html;
    if (fmt === 'json') {
      const tok = (type, value) => ({ $type: type, $value: value });
      const json = JSON.stringify({ button: { primary: {
        radius: tok('dimension', lab.radius + 'px'),
        'padding-x': tok('dimension', lab.padx + 'px'),
        'font-weight': tok('fontWeight', lab.weight),
        'font-width': tok('number', lab.wdth),
        background: tok('color', f.token),
        ...(lab.state === 'hover' ? { 'background-hover': tok('color', hov.token) } : {}),
        text: tok('color', text.token)
      } } }, null, 2);
      // chaque "$value" est rattachée au token ouvert juste au-dessus
      let k = '';
      html = json.split('\n').map(l => {
        const name = l.match(/^\s*"([\w-]+)": \{$/);
        if (name) k = JSON_KEYS[name[1]] || '';
        const val = l.match(/^(\s*"\$value": )(.+)$/);
        return val ? esc(val[1]) + b(k, val[2]) : esc(l);
      }).join('\n');
    } else if (fmt === 'tw') {
      html = `@theme {\n  --color-accent: #233df4;\n}\n\n&lt;button class="rounded-[${b('radius', lab.radius + 'px')}] px-[${b('padx', lab.padx + 'px')}]\n`
        + `  font-[${b('weight', lab.weight)}] [font-stretch:${b('wdth', lab.wdth + '%')}]\n`
        + `  ${b('fill', f.tw)} ${b('text', text.tw)}`
        + TW_STATES[lab.state].map(c => `\n  ${b('state', c.replace('HOVER', hov.tw))}`).join('')
        + '"&gt;\n  Réserver le séjour\n&lt;/button&gt;';
    } else {
      html = '<span class="c">/* généré depuis les propriétés */</span>\n.btn-primary {\n'
        + `  --radius: ${b('radius', lab.radius + 'px')};\n  --pad-x: ${b('padx', lab.padx + 'px')};\n`
        + `  font-weight: ${b('weight', lab.weight)};\n  font-stretch: ${b('wdth', lab.wdth + '%')};\n`
        + '  border-radius: var(--radius);\n  padding: 0 var(--pad-x);\n'
        + `  background: ${b('fill', f.css)};\n  color: ${b('text', text.css)};\n`
        + (lab.fill === 'outline' ? `  border: ${b('fill', '1px solid currentColor')};\n` : '')
        // valeurs entre {…} (sur une ligne) : l'accolade du sélecteur n'en fait pas partie
        + '}' + STATES[lab.state].replace(/\{([^{}\n]+)\}(?=;)/g, (m, v) => b('state', v === 'HOVER' ? hov.css : v));
    }
    labOut.firstElementChild.innerHTML = html;
    fadeCode();
  }
  // code plus haut que son cadre : fondu en bas tant qu'il reste des lignes à faire défiler
  // (relu au scroll du code et quand sa taille change : volet ouvert au doigt, largeur)
  function fadeCode() {
    const max = labOut.scrollHeight - labOut.clientHeight;
    labOut.classList.toggle('is-more', labOut.clientHeight > 0 && max > 1 && labOut.scrollTop < max - 1);
  }
  labOut.addEventListener('scroll', fadeCode, { passive: true });
  new ResizeObserver(fadeCode).observe(labOut);

  /* thème : un fond qui rend la même couleur qu'un fond placé avant lui (Marine
     et Encre en thème clair) est masqué, pour ne jamais montrer deux pastilles
     identiques ; s'il était choisi, son équivalent visible prend le relais (même rendu) */
  const swBtns = $$('.swatches button');
  function dedupeSwatches() {
    const seen = new Map();
    let swap = null;
    swBtns.forEach(b => {
      const key = resolve(FILLS[b.dataset.fill].v).join();
      const first = seen.get(key);
      b.hidden = !!first;
      if (!first) seen.set(key, b);
      else if (lab.fill === b.dataset.fill) swap = first;
    });
    if (swap) {
      const had = document.activeElement === swBtns.find(x => x.dataset.fill === lab.fill);
      firstFill.select(swap);
      if (had) swap.focus({ preventScroll: true });   // touche T sur la pastille masquée : le focus suit
    } else firstFill.place();
  }

  // une passe : bouton, code, contraste. 'theme' : les couleurs du thème ont changé
  function update(changed) {
    if (changed.includes('theme')) dedupeSwatches();
    if (changed.includes('fill') || changed.includes('theme')) {
      const t = pickText();
      if (t !== text) { text = t; changed.push('text'); }
    }
    demo.style.setProperty('--bg', FILLS[lab.fill].v);
    demo.style.setProperty('--fg', text.v);
    demo.dataset.fill = lab.fill;
    render(changed);
    // les curseurs ne changent pas les couleurs
    if (!changed.every(k => k in units)) readContrast(!changed.includes('theme'));
  }

  const setFill = inp => inp.style.setProperty('--fill', ((inp.value - inp.min) / (inp.max - inp.min) * 100).toFixed(1) + '%');
  // valeur annoncée avec son unité (« 10 px ») ; la sortie visible est aria-hidden
  const setText = (inp, k) => inp.setAttribute('aria-valuetext', units[k] ? `${inp.value} ${units[k]}` : inp.value);
  // curseur → sortie, piste, bouton et état ; vrai si la valeur a changé
  function setToken(inp) {
    const k = inp.dataset.token, v = +inp.value;
    inp.nextElementSibling.textContent = v;
    setFill(inp); setText(inp, k);
    demo.style.setProperty(cssVar[k], v + (units[k] === 'px' ? 'px' : ''));
    if (lab[k] === v) return false;
    lab[k] = v;
    return true;
  }
  let resetRaf = 0;
  ranges.forEach(inp => {
    setToken(inp);
    inp.addEventListener('input', () => {
      cancelAnimationFrame(resetRaf);
      if (setToken(inp)) update([inp.dataset.token]);
    });
    /* au toucher, Chromium pose la valeur du doigt dès le contact, avant de savoir
       que le geste est un défilement vertical ; s'il l'annule (pointercancel),
       on remet la valeur d'avant (sortie, piste, bouton et code suivent) */
    let v0 = null;
    inp.addEventListener('pointerdown', e => { v0 = e.pointerType === 'touch' ? inp.value : null; });
    inp.addEventListener('pointerup', () => { v0 = null; });
    inp.addEventListener('pointercancel', () => {
      if (v0 !== null && inp.value !== v0) {
        inp.value = v0;
        inp.dispatchEvent(new Event('input', { bubbles: true }));
      }
      v0 = null;
    });
  });

  // groupe à choix unique (radios ou onglets) : un seul arrêt de tabulation, les
  // flèches choisissent le voisin (en boucle) et le focus suit ; --i place l'indicateur
  // les options masquées (hidden) ne comptent ni pour les flèches, ni pour la place de l'indicateur
  function choice(group, pick) {
    const btns = $$('button', group);
    const shown = () => btns.filter(x => !x.hidden);
    const tabs = btns[0].getAttribute('role') === 'tab';
    const attr = tabs ? 'aria-selected' : 'aria-checked';
    const keys = tabs ? { ArrowLeft: -1, ArrowRight: 1 } : { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 };
    const place = () => group.style.setProperty('--i', shown().findIndex(x => x.getAttribute(attr) === 'true'));
    const select = b => {
      btns.forEach(x => { x.setAttribute(attr, x === b); x.tabIndex = x === b ? 0 : -1; });
      place();
      pick(b);
    };
    btns.forEach(b => b.addEventListener('click', () => select(b)));
    group.addEventListener('keydown', e => {
      const d = keys[e.key];
      if (!d) return;
      e.preventDefault();
      const vis = shown();
      const b = vis[(vis.indexOf(document.activeElement) + d + vis.length) % vis.length];
      b.click(); b.focus();
    });
    const first = () => select(shown()[0]);   // retour au premier choix (Réinitialiser)
    first.select = select;
    first.place = place;
    return first;
  }
  const swName = $('.sw-name');
  const firstFill = choice($('.swatches'), b => {
    if (lab.fill === b.dataset.fill) return;
    lab.fill = b.dataset.fill;
    swName.textContent = b.getAttribute('aria-label');
    update(['fill']);
  });
  const firstState = choice($('.lab-props .seg'), b => {
    if (lab.state === b.dataset.state) return;
    lab.state = b.dataset.state;
    ['hover', 'focus', 'disabled'].forEach(s => demo.classList.toggle('is-' + s, s === lab.state));
    // état Inactif : le bouton de démo le dit aussi aux technologies d'assistance
    if (lab.state === 'disabled') demo.setAttribute('aria-disabled', 'true'); else demo.removeAttribute('aria-disabled');
    update(['state']);
  });
  choice($('.seg--tabs'), b => {
    fmt = b.dataset.fmt;
    labOut.setAttribute('aria-labelledby', b.id);
    render([]);
  });

  // Réinitialiser : les curseurs glissent vers leur valeur d'origine en 400 ms
  // (une boucle qui s'arrête) ; fond Encre, état Défaut
  $('.lab-reset').addEventListener('click', () => {
    firstFill(); firstState();
    const from = ranges.map(inp => +inp.value), to = ranges.map(inp => +inp.defaultValue);
    const t0 = performance.now();
    cancelAnimationFrame(resetRaf);
    const frame = now => {
      const t = reduce ? 1 : Math.min(1, (now - t0) / 400), e = 1 - (1 - t) ** 3;
      const changed = ranges.filter((inp, j) => {
        inp.value = Math.round(from[j] + (to[j] - from[j]) * e);
        return setToken(inp);
      }).map(inp => inp.dataset.token);
      if (changed.length) update(changed);
      if (t < 1) resetRaf = requestAnimationFrame(frame);
    };
    resetRaf = requestAnimationFrame(frame);
  });

  // Copier : le texte de l'onglet actif ; « Copier » devient « Copié » pendant 1,6 s
  const copyBtn = $('.lab-copy');
  const copyLbl = $('.lab-copy-lbl');
  const copyMsg = copyBtn.nextElementSibling;
  let copyT = 0;
  copyBtn.addEventListener('click', async () => {
    if (!(await copyText(labOut.textContent, copyBtn))) return;
    copyBtn.classList.add('is-done');
    copyLbl.textContent = 'Copié';
    copyMsg.textContent = 'Code copié';
    clearTimeout(copyT);
    copyT = setTimeout(() => {
      copyBtn.classList.remove('is-done');
      copyLbl.textContent = 'Copier';
      copyMsg.textContent = '';
    }, 1600);
  });

  // code ouvert au-dessus de 760 px ; replié en dessous, derrière « Voir le code généré »
  // (ouvert dans le HTML : sans script, il reste lisible partout)
  const labDetails = $('.lab-details');
  const wideLab = matchMedia('(min-width: 761px)');
  const syncDetails = () => { labDetails.open = wideLab.matches; };
  syncDetails();
  wideLab.addEventListener('change', syncDetails);

  /* premier calcul (couleurs lues, pastilles en double masquées, texte du bouton,
     contraste) hors de la tâche de démarrage : quand Méthode arrive à moins d'un
     écran, ou au premier moment libre (2 s au plus) */
  let labOn = false;
  function labInit() {
    if (labOn) return;
    labOn = true;
    labIO.disconnect();
    update(['theme']);
  }
  const labIO = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) labInit(); }, { rootMargin: '100% 0px' });
  labIO.observe($('#methode'));
  if (window.requestIdleCallback) requestIdleCallback(labInit, { timeout: 2000 });
  else setTimeout(labInit, 2000);

  // contextes d'usage : chaque exemple ouvre sa fiche ; à la fermeture, le focus revient au bouton
  $$('.contexts [data-case]').forEach(b => b.addEventListener('click', () => {
    b.focus({ preventScroll: true });   // Safari ne donne pas le focus au clic
    openCase(PROJECTS.findIndex(p => p.id === b.dataset.case));
  }));

  /* ---------- Horloges ---------- */
  const clocks = $$('[data-clock]');
  const tick = () => clocks.forEach(c => {
    c.textContent = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: c.dataset.clock }).format(new Date());
  });
  tick(); setInterval(tick, 15000);

  /* ---------- Tout ce qui dépend du scroll, en une passe ----------
     Deux temps : measureLayout() lit les positions (au démarrage, au
     redimensionnement, quand la page change de hauteur) ; onScroll() ne fait
     que comparer scrollY à ces valeurs et n'écrit que ce qui change. */
  // le hero n'attend pas le scroll : il entre avec named()
  let pending = $$('.reveal, .sec-title, .work-row, .eyebrow').filter(el => !el.closest('.hero')).map(el => ({ el, top: 0 }));
  const progress = $('.progress');
  const heroEl = $('.hero');
  const nameLines = $$('.name-line');
  const timeline = $('.timeline');
  const tItems = $$('.timeline li');
  const sections = $$('main section[id]');
  const L = { heroH: 1, docH: 0, tlTop: 0, tlH: 1, liTops: [], secs: [] };
  const past = tItems.map(() => false);
  const last = { p: '', tp: '', n0: '', n1: '' };
  let scrollRaf = 0, activeId = null, scrolled = false;
  const dock = $('.dock');
  let dockY = scrollY, dockAcc = 0, dockHidden = false, dockT = 0;

  function measureLayout() {
    const y = scrollY;
    const docTop = el => el.getBoundingClientRect().top + y;
    L.heroH = heroEl.offsetHeight || 1;
    L.docH = root.scrollHeight;
    pending.forEach(o => { o.top = docTop(o.el); });
    L.tlTop = docTop(timeline);
    L.tlH = timeline.offsetHeight || 1;
    L.liTops = tItems.map(docTop);
    L.secs = sections.map(s => { const r = s.getBoundingClientRect(); return { id: s.id, top: r.top + y, bottom: r.bottom + y }; });
  }

  function onScroll() {
    if (!L.docH) return;   // positions pas encore lues (démarrage, voir boot) : rien à comparer
    const y = scrollY, vh = innerHeight;
    if (inspecting) inspectScroll(y);   // en premier : ses lectures passent avant les écritures

    // révélations (vérifiées au scroll : un saut d'ancre ne les rate pas)
    if (pending.length) {
      const limit = y + vh * .9;
      pending = pending.filter(o => {
        if (o.top < limit) { o.el.classList.add('is-in'); return false; }
        return true;
      });
    }

    if ((y > 40) !== scrolled) { scrolled = y > 40; root.classList.toggle('is-scrolled', scrolled); }
    const max = L.docH - vh;
    const p = max > 0 ? clamp(y / max, 0, 1).toFixed(4) : '0';
    if (p !== last.p) { last.p = p; progress.style.setProperty('--p', p); }

    // le nom s'écarte en sortant de l'écran
    if (!reduce) {
      const k = clamp(y / L.heroH, 0, 1);
      const n0 = `translate3d(${(-k * 9).toFixed(2)}%, 0, 0)`, n1 = `translate3d(${(k * 6).toFixed(2)}%, 0, 0)`;
      if (n0 !== last.n0) { last.n0 = n0; nameLines[0].style.transform = n0; }
      if (n1 !== last.n1) { last.n1 = n1; nameLines[1].style.transform = n1; }
    }

    // frise du parcours
    const mid = y + vh * .55;
    const tp = clamp((mid - L.tlTop) / L.tlH, 0, 1).toFixed(4);
    if (tp !== last.tp) { last.tp = tp; timeline.style.setProperty('--tp', tp); }
    L.liTops.forEach((top, i) => {
      const on = top + 30 < mid;
      if (on !== past[i]) { past[i] = on; tItems[i].classList.toggle('is-past', on); }
    });

    // section active
    const probeY = y + vh * .45;
    const sec = L.secs.find(s => s.top < probeY && s.bottom > probeY);
    const id = sec ? sec.id : null;
    if (id !== activeId) { activeId = id; setActive(id); }

    // barre du bas : cachée tant que les boutons du hero ou les sites en ligne sont à
    // l'écran (elle les couvrirait), puis là jusqu'à la fin du hero (à la remontée ou à
    // l'arrêt), près du bas de page et pendant un saut d'ancre ; ailleurs, cachée après 60 px de descente, rendue
    // après 20 px de remontée (pas en mouvement réduit : elle reste là)
    const dy = y - dockY;
    dockY = y;
    if (dy * dockAcc < 0) dockAcc = 0;   // changement de sens : on repart de zéro
    dockAcc += dy;
    let hide = dockHidden;
    clearTimeout(dockT);
    if (heroCtaIn) { hide = true; dockAcc = 0; }
    else if (reduce || y + vh > L.docH - 240 || performance.now() < dockHold) { hide = false; dockAcc = 0; }
    else if (y <= L.heroH) {
      // fin du hero : montrée à la remontée, ou 150 ms après l'arrêt du défilement ; en
      // descente, elle garde son état (pas d'apparition puis de disparition en passant)
      dockAcc = 0;
      if (dy < 0) hide = false;
      else if (hide) dockT = setTimeout(() => { if (scrollY <= L.heroH) showDock(); }, 150);
    }
    else if (dockAcc > 60) hide = true;
    else if (dockAcc < -20) hide = false;
    if (hide !== dockHidden) { dockHidden = hide; dock.classList.toggle('dock-hidden', hide); }
  }
  function showDock() {
    if (heroCtaIn) return;   // les boutons du hero sont à l'écran : elle reste cachée
    dockAcc = 0; dockHidden = false;
    dock.classList.remove('dock-hidden');
  }
  // boutons du hero et sites en ligne visibles (sous la barre du haut) : suivis par un
  // IntersectionObserver ; état de départ lu tout de suite, sans attendre son premier rappel
  const heroCta = $$('.hero .cta-row, .hero .live');
  const heroSeen = new Set();
  // 24 px sous la barre du haut : une frange qui dépasse encore (après un saut vers les Travaux) ne compte pas
  const topH = () => $('.topbar').offsetHeight;
  const heroTop = () => topH() + 24;
  heroCta.forEach(el => { const r = el.getBoundingClientRect(); if (r.bottom > heroTop() && r.top < innerHeight) heroSeen.add(el); });
  let heroCtaIn = heroSeen.size > 0;
  if (heroCtaIn) { dockHidden = true; dock.classList.add('dock-hidden'); }
  const heroIO = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) heroSeen.add(e.target); else heroSeen.delete(e.target); });
    const on = heroSeen.size > 0;
    if (on !== heroCtaIn) { heroCtaIn = on; queueScroll(); }
  }, { rootMargin: `-${heroTop()}px 0px 0px 0px` });
  heroCta.forEach(el => heroIO.observe(el));
  const queueScroll = () => { if (!scrollRaf) scrollRaf = requestAnimationFrame(() => { scrollRaf = 0; onScroll(); }); };
  // remplacé par l'événement de Lenis dès que celui-ci existe
  window.addEventListener('scroll', queueScroll, { passive: true });

  /* ---------- Navigation : pastille qui glisse ---------- */
  const navs = $$('.nav, .dock');
  const moveInd = (nav, a) => {
    const ind = $('.nav-ind', nav);
    ind.style.opacity = 1;
    // haut et bas aussi : la barre du bas passe sur deux lignes quand l'espacement du texte est forcé (WCAG 1.4.12)
    const t = Math.max(0, a.offsetTop - ind.offsetTop), b = Math.max(0, ind.offsetTop + ind.offsetHeight - a.offsetTop - a.offsetHeight);
    // bords gauche et droit posés sur le lien (la boîte de la pastille ne couvre que lui : le
    // contraste des autres liens se calcule sur le fond de la barre), haut et bas découpés
    ind.style.left = a.offsetLeft + 'px';
    ind.style.right = (nav.clientWidth - a.offsetLeft - a.offsetWidth) + 'px';
    ind.style.clipPath = `inset(${t}px 0 ${b}px 0 round var(--r-pill))`;
  };
  function placeInd(nav) {
    const a = $('a.is-active', nav);
    if (a) moveInd(nav, a);
    else $('.nav-ind', nav).style.opacity = 0;
  }
  function setActive(id) {
    navs.forEach(nav => {
      // la section en cours est aussi annoncée (aria-current), pas seulement colorée
      $$('a', nav).forEach(a => {
        const on = a.getAttribute('href') === '#' + id;
        a.classList.toggle('is-active', on);
        if (on) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
      });
      placeInd(nav);
    });
  }
  // survol : la pastille suit la souris dans la nav du haut
  const topNav = $('.nav');
  $$('a', topNav).forEach(a => a.addEventListener('pointerenter', () => moveInd(topNav, a)));
  topNav.addEventListener('pointerleave', () => placeInd(topNav));

  /* ---------- Boutons : largeur de l'état survolé ----------
     Au survol, le libellé s'élargit (style.css). Chaque contrôle reçoit en
     min-width sa largeur survolée, mesurée pour tous d'un coup : rien ne
     bouge autour. Relancé avec refit (polices, largeur) et à chaque fiche. */
  const WIDE = '.btn, .links a, .live a, .case-site, .case-share';
  function lockWidths(scope = document) {
    const els = $$(WIDE, scope);
    els.forEach(el => { el.style.minWidth = ''; el.classList.add('is-measure', 'is-still'); });
    const ws = els.map(el => el.getBoundingClientRect().width);   // 0 : caché (fiche fermée)
    els.forEach((el, k) => { if (ws[k]) el.style.minWidth = ws[k] + 'px'; el.classList.remove('is-measure'); });
    // retour au repos appliqué sans transition, puis transitions rendues
    void document.body.offsetWidth;
    els.forEach(el => el.classList.remove('is-still'));
  }

  /* ---------- Thème ---------- */
  const themeBtn = $('.theme-btn');
  const themeMeta = $('meta[name="theme-color"]');
  const syncTheme = () => {
    const light = root.dataset.theme === 'light';
    themeBtn.setAttribute('aria-label', light ? 'Passer en thème sombre' : 'Passer en thème clair');
    themeMeta.content = light ? '#f4f6ff' : '#09090b';
  };
  syncTheme();
  // bouton du haut et touche T (Clavier)
  let themeT = 0;
  function switchTheme() {
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    try { localStorage.setItem('ql-theme', root.dataset.theme); } catch (e) {}
    syncTheme();
    // couleurs déjà finales : panneau Inspecter, texte et contraste du playground relus tout de suite
    tokens = null; if (sel) renderPanel();
    // relu une seconde fois après les fondus de couleur (--dur-2, .3 s) : un
    // élément encore en transition aurait donné sa couleur intermédiaire
    clearTimeout(themeT);
    themeT = setTimeout(() => { if (sel) { tokens = null; renderPanel(); } }, 450);
    if (labOn) update(['theme']);   // sinon, labInit() lira le thème en place
  }
  function toggleTheme() {
    // fondu enchaîné de toute la page (View Transitions, .3 s dans style.css). Pas pendant
    // le passage aperçu vers fiche (.vt) : une seconde transition couperait la première.
    // Sans View Transitions ou en mouvement réduit : bascule directe
    if (document.startViewTransition && !reduce && !root.classList.contains('vt')) {
      document.startViewTransition(switchTheme).ready.catch(() => {});
    } else switchTheme();
  }
  themeBtn.addEventListener('click', toggleTheme);

  /* ---------- Contact ----------
     ÉCRIVEZ-MOI : à la souris, le clic copie l'adresse ; au doigt, le tap
     ouvre la messagerie. Dans les deux cas, une onde de largeur part de la
     lettre touchée. « Copier », à côté de l'adresse : sans toast, le libellé
     devient « Copié » pendant 1,8 s. */
  const toastEl = $('.toast');
  /* Durée proportionnelle au texte (2,2 s au moins, 55 ms par caractère), mise
     en pause tant que la souris ou le focus est sur le message (WCAG 2.2.1) */
  let toastT, toastLeft = 0, toastEnd = 0;
  const toastRun = ms => {
    clearTimeout(toastT);
    toastEnd = Date.now() + ms;
    toastT = setTimeout(() => toastEl.classList.remove('is-on'), ms);
  };
  function toast(msg, ms = Math.max(2200, 1500 + msg.length * 55)) {
    toastEl.textContent = msg; toastEl.classList.add('is-on');
    toastLeft = 0;
    toastRun(ms);
  }
  const toastHold = () => {
    if (!toastEl.classList.contains('is-on') || toastLeft) return;
    clearTimeout(toastT);
    toastLeft = Math.max(1200, toastEnd - Date.now());
  };
  const toastGo = () => { if (toastLeft) { const ms = toastLeft; toastLeft = 0; toastRun(ms); } };
  toastEl.addEventListener('mouseenter', toastHold);
  toastEl.addEventListener('focusin', toastHold);
  toastEl.addEventListener('mouseleave', toastGo);
  toastEl.addEventListener('focusout', toastGo);
  // même date que la fiche candidat du hero
  $('.contact-avail span').textContent = $('.brief [data-avail]').textContent;

  const mailBtn = $('.mail');
  // nom accessible et nom du bloc en mode Inspecter : ce que fait vraiment le clic ou le toucher
  const mailLabel = () => {
    mailBtn.setAttribute('aria-label', noHover.matches
      ? `Écrivez-moi : écrire à ${MAIL}`
      : `Écrivez-moi : copier l’adresse ${MAIL}`);
    mailBtn.dataset.spec = noHover.matches ? 'CTA · ouvre la messagerie au toucher' : 'CTA · copie l’adresse au clic';
  };
  mailLabel();
  noHover.addEventListener('change', mailLabel);

  // lettre la plus proche du clic ; au clavier (detail 0), le milieu du mot
  function letterAt(e) {
    const s = mailStretch;
    if (!e.detail || !s.cx.length) return (s.chars.length - 1) / 2;
    const x = e.clientX - s.line.getBoundingClientRect().left;
    return s.cx.reduce((best, cx, i) => Math.abs(cx - x) < Math.abs(s.cx[best] - x) ? i : best, 0);
  }
  // deux crêtes partent de la lettre et filent vers les bords : 2,5 lettres
  // par 100 ms, gain 26, sigma 1 lettre, 700 ms, puis retour au repos
  let rippleId = 0;
  function ripple(from) {
    return new Promise(done => {
      if (reduce) return done(true);
      const s = mailStretch, id = ++rippleId, t0 = performance.now();
      const g = d => Math.exp(-(d * d) / 2);
      s.hold = true;
      const frame = now => {
        if (id !== rippleId) return done(false);   // relancée par un autre clic
        const t = now - t0;
        if (t >= 700) { s.hold = false; s.rest(); return done(true); }
        const d = t * .025;
        s.setRaw(s.chars.map((_, i) => 100 + 26 * (g(i - from - d) + g(i - from + d))));
        requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
    });
  }
  // navigateur piloté par un test automatisé : on n'ouvre pas le client mail du poste
  const openMail = url => { if (navigator.webdriver) toast('mailto bloqué (test)'); else location.href = url; };
  if (navigator.webdriver) document.addEventListener('click', e => {
    if (e.target.closest && e.target.closest('a[href^="mailto:"]')) e.preventDefault();
  }, true);
  mailBtn.addEventListener('click', async e => {
    const wave = ripple(letterAt(e));
    if (noHover.matches) {
      // vague relancée par un second toucher : c'est lui qui ouvrira le mail (une seule fois)
      if (!(await wave)) return;
      openMail(`mailto:${MAIL}?subject=${encodeURIComponent('Prise de contact')}`);
    } else if (await copyText(MAIL, mailBtn)) toast('Adresse copiée');
    else openMail('mailto:' + MAIL);
  });

  // « Copier » + « l’adresse » en sr-only : le nom accessible contient toujours le texte visible
  const mailCopy = $('.mail-copy');
  const [mailLbl, mailSr] = mailCopy.children;
  const MAIL_SR = mailSr.textContent;
  const mailMsg = mailCopy.nextElementSibling;
  let mailT = 0;
  mailCopy.addEventListener('click', async () => {
    if (!(await copyText(MAIL, mailCopy))) return;
    mailCopy.classList.add('is-done');
    mailLbl.textContent = 'Copié';
    mailSr.textContent = '';
    mailMsg.textContent = 'Adresse copiée';
    clearTimeout(mailT);
    mailT = setTimeout(() => {
      mailCopy.classList.remove('is-done');
      mailLbl.textContent = 'Copier';
      mailSr.textContent = MAIL_SR;
      mailMsg.textContent = '';
    }, 1800);
  });

  /* ---------- Clavier ----------
     Échap et les flèches marchent toujours. Les raccourcis à une touche (I, T,
     C, 1 à 4, ?) se coupent dans la fenêtre des raccourcis (WCAG 2.1.4, choix
     gardé dans localStorage) ; ils ne jouent ni dans un champ, ni avec Ctrl,
     Alt ou Cmd (Maj oui : ? et les chiffres en AZERTY), ni sur une fiche ouverte.
     La fenêtre (touche ? ou bouton du pied de page) et son interrupteur n'existent
     qu'avec un survol (.only-fine) : sans survol, pas de raccourci à une touche,
     puisqu'on ne pourrait pas les couper. */
  const keysEl = $('.keys');
  const keysSwitch = $('.keys-switch');
  const footKeys = $('.foot-keys');
  const SECTION_KEYS = { 1: '#travaux', 2: '#methode', 3: '#parcours', 4: '#contact' };
  let keysOn = true, keysBack = null;
  try { keysOn = localStorage.getItem('ql-keys') !== 'off'; } catch (e) {}
  const syncKeys = () => {
    keysSwitch.setAttribute('aria-checked', keysOn);
    keysEl.classList.toggle('is-off', !keysOn);
    root.classList.toggle('keys-off', !keysOn);   // le I du bouton Inspecter s'éteint aussi
    inspectBtn.title = 'Afficher la grille et les specs' + (keysOn ? ' (touche I)' : '');
  };
  syncKeys();
  keysSwitch.addEventListener('click', () => {
    keysOn = !keysOn;
    syncKeys();
    try { localStorage.setItem('ql-keys', keysOn ? 'on' : 'off'); } catch (e) {}
  });
  const keysOpen = () => keysEl.classList.contains('is-open');
  /* Ouverte depuis le bouton du pied de page (.is-foot) : juste au-dessus du
     pied, calée sur le bord droit du bouton, et suivie au scroll. Par la touche ? :
     sous la barre du haut, à droite (style.css). La fenêtre suit le bouton dans
     le DOM : Tab passe de l'un à l'autre, puis au lien « Haut de page » (RGAA 12.8). */
  const foot = $('.foot');
  function placeKeys() {
    const b = footKeys.getBoundingClientRect();
    const top = Math.min(foot.getBoundingClientRect().top, b.top - 8);
    const hi = innerHeight - keysEl.offsetHeight - topH() - 8;   // jamais sous la barre du haut
    keysEl.style.setProperty('--kb', Math.max(12, Math.min(innerHeight - top + 12, hi)) + 'px');
    // bord droit du bloc de la fenêtre (la gouttière de la barre de défilement en est exclue)
    const edge = keysEl.offsetLeft + keysEl.offsetWidth + parseFloat(getComputedStyle(keysEl).right);
    keysEl.style.setProperty('--kr', Math.max(16, edge - b.right) + 'px');
  }
  // back : le focus revient où il était (Échap, ?, bouton) ; pas après un clic ailleurs
  function showKeys(on, back = true, fromFoot = false) {
    if (on === keysOpen()) return;
    if (on) {
      keysEl.classList.toggle('is-foot', fromFoot);
      if (fromFoot) placeKeys();
    }
    keysEl.classList.toggle('is-open', on);
    footKeys.setAttribute('aria-expanded', on);
    if (on) {
      keysBack = document.activeElement;
      keysEl.focus({ preventScroll: true });
    } else if (back && keysBack && keysBack.isConnected) keysBack.focus({ preventScroll: true });
  }
  footKeys.addEventListener('click', () => showKeys(!keysOpen(), true, true));
  window.addEventListener('scroll', () => { if (keysOpen() && keysEl.classList.contains('is-foot')) placeKeys(); }, { passive: true });
  window.addEventListener('resize', () => { if (keysOpen() && keysEl.classList.contains('is-foot')) placeKeys(); });
  document.addEventListener('pointerdown', e => {
    if (keysOpen() && !keysEl.contains(e.target) && !footKeys.contains(e.target)) showKeys(false, false);
  });
  // le focus arrive ailleurs (Tab, Maj+Tab, retour depuis la barre du navigateur,
  // touches 1 à 4) : la fenêtre se ferme, elle ne masque jamais l'élément focalisé
  const inKeys = el => el && (keysEl.contains(el) || footKeys.contains(el));
  document.addEventListener('focusin', e => {
    if (keysOpen() && !inKeys(e.target)) showKeys(false, false);
  });
  // le focus quitte la fenêtre sans se poser ailleurs (vers la page) : fermée aussi,
  // sauf quand c'est la fenêtre du navigateur qui perd le focus
  keysEl.addEventListener('focusout', e => {
    if (inKeys(e.relatedTarget)) return;
    setTimeout(() => {
      if (keysOpen() && document.hasFocus() && !inKeys(document.activeElement)) showKeys(false, false);
    });
  });
  // fenêtre ouverte : la touche jouée s'enfonce 120 ms
  function press(id) {
    if (!keysOpen()) return;
    $$('kbd', keysEl).filter(k => k.dataset.k === id).forEach(k => {
      k.classList.add('is-press');
      setTimeout(() => k.classList.remove('is-press'), 120);
    });
  }
  window.addEventListener('keydown', e => {
    if (e.key !== 'Escape' && typing(e.target)) return;
    const open = current >= 0;   // une fiche en train de se fermer compte comme fermée
    if (e.key === 'Escape') {
      press('escape');
      if (keysOpen()) showKeys(false);
      else if (open) requestClose();
      else if (inspecting) { if (sel) deselect(); else setInspect(false); }
      // aperçu de la liste : fermé, et tenu fermé tant qu'on reste sur la ligne (WCAG 1.4.13)
      else if (peek.classList.contains('is-on')) { peekMuted = peekRow; hidePeek(); }
      return;
    }
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') press(e.key.toLowerCase());
    if (open) {
      // rangée de téléphones qui défile : les flèches la font défiler, sans changer de projet
      if (e.target.closest && e.target.closest('[data-scroll-x]')) return;
      if (e.key === 'ArrowRight') step(1);
      else if (e.key === 'ArrowLeft') step(-1);
      return;
    }
    if (e.key === 'Enter' && inspecting && sel) press(e.shiftKey ? 'shift-enter' : 'enter');   // action : mode Inspecter, plus haut
    if (!keysOn || noHover.matches || e.repeat || e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === '?') showKeys(!keysOpen());
    else if (k === 'i') setInspect(!inspecting);
    else if (k === 't') toggleTheme();
    else if (SECTION_KEYS[k]) goTo(SECTION_KEYS[k]);
    else if (k !== 'c') return;   // C : copie du CSS, mode Inspecter (plus haut)
    press(k);
  });

  /* ---------- Démarrage ----------
     boot() : tout de suite. named() : quand la police du nom est là (ou au
     plus tard après 1,2 s, 0,9 s au doigt) ; le nom entre en premier, puis
     le reste (délais dans style.css). */
  const NAME_FONT = '850 100px Anybody';
  // ajustement du texte et mesures ; relancé à chaque police chargée, sans garde
  function refit() {
    measureCap(); fitAll(); fitTitles(); lockWidths(); measureLayout(); navs.forEach(placeInd);
    if (current >= 0) fitCaseTitle();
    if (inspecting) inspectMeasure();
  }
  let deepLink = false, isNamed = false;
  // fin de l'entrée du nom : la première relecture des positions (ResizeObserver, plus
  // bas) attend jusque-là ; recalée par named()
  let quietUntil = performance.now() + 1500;
  /* Dans la première tâche, seulement le nom (et ÉCRIVEZ-MOI s'il est déjà à l'écran :
     page rechargée plus bas). Chaque mesure force une mise en page : les autres
     passent après la première image, en deux tâches courtes (téléphone moyen) */
  function boot() {
    measureCap();
    const m = $('.mail').getBoundingClientRect();
    const mailIn = m.bottom > 0 && m.top < innerHeight;
    fitAll(mailIn);
    requestAnimationFrame(() => {
      root.classList.add('is-ready');   // repère : page démarrée
      setTimeout(() => {
        if (!mailIn) fitMail();
        lockWidths(); navs.forEach(placeInd);
        setTimeout(() => { fitTitles(); measureLayout(); measurePeek(); onScroll(); }, 0);
      }, 0);
    });
    // ancre inconnue (lien partagé vers un projet retiré du portfolio) : l’adresse revient à la page, sans erreur
    if (location.hash.length > 1 && fromHash() < 0 && !document.getElementById(location.hash.slice(1))) history.replaceState(null, '', location.pathname + location.search);
    const i = fromHash();
    if (i >= 0) { deepLink = true; openCase(i, { push: false }); }
    else if (new URLSearchParams(location.search).has('inspect')) setInspect(true);
  }
  function named() {
    if (isNamed) return; isNamed = true;
    const fontIn = !document.fonts || document.fonts.check(NAME_FONT);
    // police en retard : le nom entre avec la police de secours, ajustée à son tour
    if (!fontIn) refit();
    root.classList.add('is-named');
    if (reduce || deepLink) { quietUntil = 0; return; }
    // entrée en largeur, seulement si la vraie police est affichée. Téléphone modeste
    // (au doigt, 4 cœurs ou moins) : plus courte, toutes les lettres ensemble
    if (fontIn) {
      const slow = !fine && matchMedia('(pointer: coarse)').matches && (navigator.hardwareConcurrency || 8) <= 4;
      heroStretch.forEach((s, li) => s.intro(slow
        ? { from: 58, dur: 700, stagger: 0, delay: li ? 200 : 80 }
        : { from: 58, dur: 1100, stagger: 35, delay: li ? 380 : 80 }));
      quietUntil = performance.now() + (slow ? 1000 : 1700);
    } else quietUntil = 0;
    // tactile : un balayage pour montrer que le nom réagit au doigt
    if (!fine) setTimeout(sweep, 1500);
    setTimeout(cameo, 1500);
  }

  // aperçu du mode Inspecter : une fois par session, page en haut, sans fiche ouverte
  function cameo() {
    if (scrollY >= 40 || !caseEl.hidden || inspecting) return;
    try {
      if (sessionStorage.getItem('ql-intro') !== null) return;
      sessionStorage.setItem('ql-intro', '1');
    } catch (e) { return; }
    const r = name.getBoundingClientRect(), h = heroEl.getBoundingClientRect();
    const c = document.createElement('div');
    c.className = 'cameo';
    c.setAttribute('aria-hidden', 'true');
    Object.assign(c.style, { left: r.left - h.left + 'px', top: r.top - h.top + 'px', width: r.width + 'px', height: r.height + 'px' });
    c.innerHTML = `<span class="cameo-line t"></span><span class="cameo-line r"></span><span class="cameo-line b"></span><span class="cameo-line l"></span><span class="cameo-tag mono">H1 · Anybody 850 · ${Math.round(r.width)} × ${Math.round(r.height)}</span>`;
    heroEl.appendChild(c);
    void c.offsetWidth;   // état de départ appliqué avant l'entrée
    c.classList.add('is-on');
    // tracé 450 ms, lecture 700 ms, disparition 300 ms
    setTimeout(() => c.classList.add('is-out'), 1150);
    setTimeout(() => {
      c.remove();
      if (!keysOn) return;   // raccourcis coupés : pas de touche à montrer
      const kbd = $('kbd', inspectBtn);
      kbd.classList.add('is-nudge');
      setTimeout(() => kbd.classList.remove('is-nudge'), 600);
    }, 1450);
  }

  boot();
  setTimeout(named, matchMedia('(pointer: coarse)').matches ? 900 : 1200);
  if (document.fonts) {
    document.fonts.load(NAME_FONT).then(named, named);
    // police arrivée tard (réseau lent) : nom recalé, centres des lettres et positions relus.
    // Une seule fois par image (les deux signaux arrivent ensemble) ; polices déjà là au
    // démarrage : rien à refaire. loadingdone : le premier lot seulement
    let refitRaf = 0;
    const queueRefit = () => { if (!refitRaf) refitRaf = requestAnimationFrame(() => { refitRaf = 0; refit(); queueScroll(); }); };
    if (document.fonts.status !== 'loaded') document.fonts.ready.then(queueRefit);
    document.fonts.addEventListener('loadingdone', queueRefit, { once: true });
  }
  // la page change de hauteur (images, polices, contenu) : positions à relire
  // (pendant l'entrée du nom, une seule relecture, à sa fin : pas de mise en page complète entre deux images)
  let layoutRaf = 0, layoutT = 0;
  new ResizeObserver(() => {
    if (layoutRaf || layoutT) return;
    const wait = quietUntil - performance.now();
    if (wait > 0) { layoutT = setTimeout(() => { layoutT = 0; relayout(); }, wait); return; }
    relayout();
  }).observe(document.body);
  function relayout() {
    if (layoutRaf) return;
    layoutRaf = requestAnimationFrame(() => { layoutRaf = 0; measureLayout(); if (inspecting) placeLabels(); onScroll(); });
  }
  // seules les variations de largeur relancent les mesures ; une variation de
  // hauteur (barre d'adresse mobile) ne demande qu'un nouveau passage du scroll
  let resizeRaf = 0, lastW = innerWidth;
  window.addEventListener('resize', () => {
    if (resizeRaf) return;
    resizeRaf = requestAnimationFrame(() => {
      resizeRaf = 0;
      if (innerWidth !== lastW) { lastW = innerWidth; refit(); }
      else if (inspecting) inspectMeasure();   // hauteur seule : règle verticale
      measurePeek();   // la hauteur de la fenêtre plafonne aussi l'aperçu
      queueScroll();
    });
  });
  // entrée ou sortie du format « téléphone à l'horizontale » sans changer de largeur
  landscape.addEventListener('change', refit);
  // espacement du texte changé page ouverte (WCAG 1.4.12 : feuille de style de
  // l'utilisateur, extension, favori) : le nom et ÉCRIVEZ-MOI sont recalés. Une sonde
  // cachée, hors de l'étirement au curseur et de l'ouverture au scroll, ne change de
  // taille que si ces réglages changent (styles « !important » de l'utilisateur)
  const spacing = document.createElement('span');
  spacing.setAttribute('aria-hidden', 'true');
  spacing.textContent = 'QUENTIN';
  // fixe : jamais de défilement horizontal, même plus large que l'écran
  Object.assign(spacing.style, { position: 'fixed', left: '0', top: '0', visibility: 'hidden', pointerEvents: 'none', whiteSpace: 'nowrap', font: '850 24px Anybody' });
  document.body.appendChild(spacing);
  let spacingFirst = true, spaceRaf = 0;
  new ResizeObserver(() => {
    if (spacingFirst) { spacingFirst = false; return; }   // premier rappel : taille de départ
    if (spaceRaf) return;
    spaceRaf = requestAnimationFrame(() => { spaceRaf = 0; refit(); queueScroll(); });
  }).observe(spacing);
  // le script a fini de s'initialiser : la page garde ses états d'entrée. Une erreur plus haut
  // laisse ce repère absent : tout s'affiche dans son état final (voir <head>)
  window.__qlBooted = true;
})();
