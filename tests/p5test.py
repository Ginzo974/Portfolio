"""P5 : critères d'acceptation (fiche candidat, colonne de droite, typographie, métadonnées, icônes)."""
import json, os, re, time
from playwright.sync_api import sync_playwright
from PIL import Image
import sys
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée
SP = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
AS = 'C:/Users/quent/Projects/portfolio-quentin/assets/'
URL = 'http://localhost:5178/?t=p5' + str(int(time.time()))
res = []
def check(name, ok, info=''):
    res.append((name, bool(ok), info)); print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(info))

TEXT_SCAN = r"""(() => {
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const bad = { apos: [], space: [], dash: [], emoji: [] };
  let n;
  while ((n = w.nextNode())) {
    const p = n.parentElement;
    if (!p || p.closest('script, style, noscript')) continue;
    const t = n.nodeValue;
    if (/\w'\w/.test(t)) bad.apos.push(t.trim().slice(0, 60));
    if (/ [:;?!](\s|$)/.test(t)) bad.space.push(t.trim().slice(0, 60));
    if (t.includes('\u2014')) bad.dash.push(t.trim().slice(0, 60));
    if (/\p{Emoji_Presentation}|\uFE0F/u.test(t)) bad.emoji.push(t.trim().slice(0, 60));
  }
  return bad;
})()"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    for theme in ['dark', 'light']:
        # ---- bureau 1440 x 900
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.add_init_script("localStorage.setItem('ql-theme','%s'); sessionStorage.setItem('ql-intro','1')" % theme)
        pg.goto(URL, wait_until='networkidle'); pg.wait_for_timeout(3000)
        if theme == 'dark':
            r = pg.evaluate("""(() => { const R = s => document.querySelector(s).getBoundingClientRect();
              const b = [...document.querySelectorAll('.cta-row .btn')].map(e => e.getBoundingClientRect().width);
              return { brief: R('.brief').bottom, hero: R('.hero').height, cta: R('.cta-row').left, col9: R('.grid-overlay i:nth-child(9)').left, btns: b,
                       cells: [...document.querySelectorAll('.brief-cell')].map(e => [Math.round(e.getBoundingClientRect().left), Math.round(e.getBoundingClientRect().width), getComputedStyle(e).opacity]) }; })()""")
            check('1440: brief bottom < 900 and hero == 900', r['brief'] < 900 and abs(r['hero'] - 900) < .5, r)
            check('1440: cta-row left == col 9 left (1px), equal buttons', abs(r['cta'] - r['col9']) <= 1 and abs(r['btns'][0] - r['btns'][1]) <= 1, (r['cta'], r['col9'], r['btns']))
            live = pg.evaluate("[...document.querySelectorAll('.hero .live a[target=_blank]')].map(a => a.href)")
            ghost = pg.evaluate("(() => { const a = document.querySelector('.cta-row .btn--ghost'); return [a.hasAttribute('download'), a.target, a.rel, a.textContent.trim(), !!a.querySelector('svg')]; })()")
            check('3 live links + ghost CTA', len(live) == 3 and [re.sub(r'https://|/$', '', h) for h in live] == ['springbreak.fr', 'wei-go.fr', 'lez-go.fr'] and ghost[0] is False and ghost[1] == '_blank', (live, ghost))
            bad = pg.evaluate(TEXT_SCAN)
            check('typography scan (after JS)', not any(bad.values()), bad)
            txt = pg.evaluate('document.body.innerText')
            check('copy: Huit projets, no Travaux choisis/Moi c’est Quentin/codé à la main',
                  'Huit projets' in txt and 'Travaux choisis' not in txt and 'Moi, c’est Quentin' not in txt and "Moi, c'est Quentin" not in txt and 'codé à la main' not in txt)
            check('no 9 400 km, has 9 250 km', '9 400' not in pg.content() and '9\u00a0250' in txt)
            ld = pg.evaluate("JSON.parse(document.querySelector('script[type=\"application/ld+json\"]').textContent)")
            head = pg.evaluate('document.head.innerHTML')
            check('JSON-LD Person + og/twitter meta', ld['@type'] == 'Person' and 'og:image:width" content="1200"' in head and 'twitter:card" content="summary_large_image"' in head and 'worksFor' not in ld and 'url' not in ld, ld.get('@type'))
            # console : ouvrir une fiche, survol des liens
            pg.hover('.live a >> nth=1'); pg.wait_for_timeout(600)
            bs = pg.evaluate("getComputedStyle(document.querySelectorAll('.live a')[1]).backgroundSize")
            check('live link hover underline 100%', bs.startswith('100%'), bs)
            pg.screenshot(path=SP + 'p5_hero_d_live.png', clip={'x': 700, 'y': 560, 'width': 740, 'height': 340})
            pg.mouse.move(10, 10)
        pg.wait_for_timeout(500)
        pg.screenshot(path=SP + f'p5_hero_d_{theme}.png')
        # 1024
        pg.set_viewport_size({'width': 1024, 'height': 900}); pg.wait_for_timeout(700)
        pg.screenshot(path=SP + f'p5_hero_t_{theme}.png')
        pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(300)
        # pied de page / contact
        pg.evaluate("window.__lenis ? window.__lenis.scrollTo(document.body.scrollHeight, {immediate:true}) : scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=SP + f'p5_foot_d_{theme}.png')
        check(f'desktop {theme}: no console/page errors', not errs, errs)
        ctx.close()

        # ---- mobile 390 x 844
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.add_init_script("localStorage.setItem('ql-theme','%s')" % theme)
        pg.goto(URL, wait_until='networkidle'); pg.wait_for_timeout(3000)
        r = pg.evaluate("""(() => { const dd = [...document.querySelectorAll('.brief dd')].find(e => e.textContent.trim() === 'UI/UX & Brand Designer');
            const rc = dd.getBoundingClientRect(); return { bottom: rc.bottom, top: rc.top, op: getComputedStyle(dd.closest('.brief-cell')).opacity,
              cells: [...document.querySelectorAll('.brief-cell')].map(e => [Math.round(e.getBoundingClientRect().left), Math.round(e.getBoundingClientRect().top), Math.round(e.getBoundingClientRect().width)]),
              sw: document.documentElement.scrollWidth }; })()""")
        check(f'390 {theme}: role visible in first screen, opacity 1', r['bottom'] < 844 and r['top'] >= 0 and r['op'] == '1', r)
        check(f'390 {theme}: no horizontal scroll', r['sw'] <= 390, r['sw'])
        pg.screenshot(path=SP + f'p5_hero_m_{theme}.png')
        pg.evaluate("scrollTo(0, 520)"); pg.wait_for_timeout(1200)
        pg.screenshot(path=SP + f'p5_hero_m2_{theme}.png')
        bad = pg.evaluate(TEXT_SCAN)
        check(f'390 {theme}: typography scan', not any(bad.values()), bad)
        check(f'mobile {theme}: no console/page errors', not errs, errs)
        ctx.close()
    b.close()

for f, size in [('og.jpg', (1200, 630)), ('favicon-32.png', (32, 32)), ('apple-touch-icon.png', (180, 180))]:
    im = Image.open(AS + f)
    check(f'{f} size', im.size == size and (f != 'og.jpg' or os.path.getsize(AS + f) < 200_000), (im.size, os.path.getsize(AS + f)))
html = open('C:/Users/quent/Projects/portfolio-quentin/index.html', encoding='utf-8').read()
check("no 'Arial' in index.html", 'Arial' not in html)
print(f"\n{sum(r[1] for r in res)}/{len(res)} pass")
