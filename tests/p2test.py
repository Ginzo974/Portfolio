"""P2 acceptance checks. python p2test.py [only-substring]"""
import sys, time, json, re
from playwright.sync_api import sync_playwright
from PIL import Image
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée
OUT = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
BASE = 'http://localhost:5178/'
ONLY = sys.argv[1] if len(sys.argv) > 1 else ''
res = []
def check(name, ok, ev=''):
    res.append((name, ok, ev))
    print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(ev), flush=True)
def u(tag): return f'{BASE}?t=p2{tag}{time.time()}'
DESK = dict(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
MOB = dict(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
def want(k): return not ONLY or k in ONLY.split(',')

def newpage(b, **kw):
    ctx = b.new_context(**kw)
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    return ctx, pg

SAMPLER = """
window.__s = {}; window.__cameo = [];
new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
  if (n.classList && n.classList.contains('cameo')) window.__cameo.push({ t: Math.round(performance.now() - (window.__named || 0)), txt: n.textContent });
}))).observe(document, { childList: true, subtree: true });
new MutationObserver(() => { if (!window.__named && document.documentElement && document.documentElement.classList.contains('is-named')) window.__named = performance.now(); })
  .observe(document, { attributes: true, attributeFilter: ['class'], subtree: true });
document.addEventListener('DOMContentLoaded', () => {
  const t0 = performance.now(); window.__dcl = t0;
  [250, 400, 600, 1000, 1300, 1600, 2400].forEach(ms => setTimeout(() => {
    const q = s => document.querySelector(s), op = s => q(s) ? +getComputedStyle(q(s)).opacity : null;
    const l1 = [...document.querySelectorAll('.name-line--1 .ch')], all = [...document.querySelectorAll('.name .ch')];
    window.__s[ms] = {
      real: Math.round(performance.now() - t0),
      named: window.__named ? Math.round(window.__named - t0) : null,
      lede: op('.lede'), cta: op('.cta-row'), meta: op('.hero-meta .status'),
      tf: l1.map(c => { const m = getComputedStyle(c).transform; if (m === 'none') return 0; return +m.split(',')[5].replace(')', ''); }),
      fs: parseFloat(getComputedStyle(l1[0] || q('.name')).fontSize),
      w: all.map(c => c.style.getPropertyValue('--w')),
      photo: q('.name-photo') ? getComputedStyle(q('.name-photo')).clipPath : null,
    };
  }, ms));
});
"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    if want('cls'):
        for label, kw in (('1440', DESK), ('390', MOB)):
            ctx, pg = newpage(b, **kw)
            pg.add_init_script("""window.__cls = 0; window.__shifts = [];
              new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) { window.__cls += e.value; window.__shifts.push([Math.round(e.startTime), +e.value.toFixed(4), e.sources.map(s => s.node && (s.node.className || s.node.nodeName)).slice(0,4)]); } }))
                .observe({ type: 'layout-shift', buffered: true });""")
            pg.goto(u('cls'), wait_until='load'); pg.wait_for_timeout(4000)
            cls = pg.evaluate('window.__cls'); sh = pg.evaluate('window.__shifts')
            check(f'CLS fresh load {label} < 0.02', cls < .02, f'{cls:.4f} {sh[:5]}')
            check(f'no errors fresh load {label}', not pg.errs, pg.errs[:3])
            ctx.close()

    if want('intro'):
        ctx, pg = newpage(b, **DESK)
        pg.goto(u('warm'), wait_until='load'); pg.wait_for_timeout(1500)   # police en cache
        pg.add_init_script(SAMPLER)
        pg.goto(u('intro'), wait_until='domcontentloaded')
        t0 = time.time()
        for ms in (250, 600, 1000, 1600, 2400):
            d = ms / 1000 - (time.time() - t0)
            if d > 0: time.sleep(d)
            pg.screenshot(path=f'{OUT}p2i_{ms}.png')
        pg.wait_for_timeout(600)
        S = pg.evaluate('window.__s')
        json.dump(S, open(OUT + 'p2_intro.json', 'w'), indent=1)
        s250, s400, s1000, s2400 = S['250'], S['400'], S['1000'], S['2400']
        check('intro: named time (ms after DCL)', s250['named'] is not None, s250['named'])
        # E4 : l'accroche s'affiche dès la première image (LCP), sans attendre l'entrée du nom
        check('intro: lede painted (opacity 1) at 250', s250['lede'] == 1, s250['lede'])
        near = sum(1 for t in s1000['tf'] if abs(t) < 0.03 * s1000['fs'])
        check('intro: >=6 QUENTIN letters ~none at 1000', near >= 6, f"{near} tf={[round(t,1) for t in s1000['tf']]} fs={s1000['fs']}")
        check('intro: lede+cta opacity 1 at 2400', s2400['lede'] == 1 and s2400['cta'] == 1, (s2400['lede'], s2400['cta']))
        w0 = s400['w'][0].strip()
        check('intro: first --w integer <100 at 400', w0.isdigit() and int(w0) < 100, s400['w'])
        check('intro: all --w 100 at 2400', all(v.strip() == '100' for v in s2400['w']), s2400['w'])
        check('intro: no errors', not pg.errs, pg.errs[:3])
        ctx.close()

    if want('nojs'):
        for label, kw in (('1440', DESK), ('390', MOB)):
            ctx, pg = newpage(b, java_script_enabled=False, **kw)
            pg.goto(u('nojs'), wait_until='load'); pg.wait_for_timeout(1500)
            r = pg.evaluate("""(() => {
              const op = el => +getComputedStyle(el).opacity, vis = el => getComputedStyle(el).visibility;
              const els = [...document.querySelectorAll('.lede, .cta-row, .sec-title, .timeline li, .reveal, .hero-meta > *')];
              const bad = els.filter(el => op(el) !== 1 || vis(el) !== 'visible').map(el => el.className);
              const tf = [...document.querySelectorAll('.sec-title, .timeline li, .lede')].filter(el => getComputedStyle(el).transform !== 'none').length;
              const st = document.querySelector('.work-list--static');
              return { n: els.length, bad, tf, rows: st ? st.querySelectorAll('li').length : 0, links: st ? st.querySelectorAll('a').length : 0,
                       htmlJs: document.documentElement.classList.contains('js'), nameVis: vis(document.querySelector('.name-word')),
                       fs: getComputedStyle(document.querySelector('.name')).fontSize, wrap: document.querySelector('.hero .wrap').clientWidth };
            })()""")
            check(f'nojs {label}: all visible', not r['bad'] and not r['tf'] and not r['htmlJs'] and r['nameVis'] == 'visible', r)
            check(f'nojs {label}: noscript 8 rows 5 links', r['rows'] == 8 and r['links'] == 5, (r['rows'], r['links']))
            pg.screenshot(path=f'{OUT}p2nojs_{label}_0.png')
            for i, sel in enumerate(['#travaux', '#methode', '#parcours']):
                pg.evaluate(f"document.querySelector('{sel}').scrollIntoView()"); pg.wait_for_timeout(200)
                pg.screenshot(path=f'{OUT}p2nojs_{label}_{i+1}.png')
            ctx.close()

    if want('abort'):
        ctx, pg = newpage(b, **DESK)
        pg.route('**/main.js*', lambda r: r.abort())
        pg.goto(u('abort'), wait_until='load'); pg.wait_for_timeout(4500)
        r = pg.evaluate("""(() => ({ js: document.documentElement.classList.contains('js'),
          bad: [...document.querySelectorAll('.reveal, .hero-meta > *')].filter(el => +getComputedStyle(el).opacity !== 1).length,
          n: document.querySelectorAll('.reveal').length,
          name: getComputedStyle(document.querySelector('.name-word')).visibility }))()""")
        check('abort main.js: no .js and reveals opacity 1 after 4.5s', not r['js'] and r['bad'] == 0 and r['name'] == 'visible', r)
        pg.screenshot(path=f'{OUT}p2abort.png')
        ctx.close()

    if want('cameo'):
        ctx, pg = newpage(b, **DESK)
        pg.add_init_script(SAMPLER)
        pg.goto(u('cameo'), wait_until='load')
        pg.wait_for_function('window.__cameo && window.__cameo.length', timeout=5000)
        pg.wait_for_timeout(450)
        pg.screenshot(path=f'{OUT}p2cameo_d.png')
        pg.wait_for_timeout(1600)
        c = pg.evaluate('window.__cameo')
        ok = len(c) == 1 and re.match(r'^H1 · Anybody 850 · \d+[\s\u00a0]×[\s\u00a0]\d+$', c[0]['txt']) and 1300 < c[0]['t'] < 1900
        check('cameo: appears once at named+~1.5s with label', bool(ok), c)
        check('cameo: removed afterwards', pg.evaluate("!document.querySelector('.cameo')"), '')
        pg.reload(wait_until='load'); pg.wait_for_timeout(3500)
        check('cameo: not on reload', pg.evaluate('window.__cameo.length') == 0, pg.evaluate('window.__cameo'))
        check('cameo: no errors', not pg.errs, pg.errs[:3])
        ctx.close()
        ctx, pg = newpage(b, **MOB)
        pg.add_init_script(SAMPLER)
        pg.goto(u('cameom'), wait_until='load')
        pg.wait_for_function('window.__cameo && window.__cameo.length', timeout=5000)
        pg.wait_for_timeout(450)
        pg.screenshot(path=f'{OUT}p2cameo_m.png')
        pg.wait_for_timeout(2500)
        check('mobile: no errors', not pg.errs, pg.errs[:3])
        ctx.close()
        ctx, pg = newpage(b, **DESK)
        pg.add_init_script("try{localStorage.setItem('ql-theme','light')}catch(e){}")
        pg.add_init_script(SAMPLER)
        pg.goto(u('cameol'), wait_until='load')
        pg.wait_for_function('window.__cameo && window.__cameo.length', timeout=5000)
        pg.wait_for_timeout(450)
        pg.screenshot(path=f'{OUT}p2cameo_dl.png')
        ctx.close()

    if want('deep'):
        ctx, pg = newpage(b, **DESK)
        pg.add_init_script(SAMPLER)
        pg.goto(u('deep') + '#springbreak', wait_until='load'); pg.wait_for_timeout(3000)
        S = pg.evaluate('window.__s')
        ws = [v for k in S for v in S[k]['w']]
        vis = pg.evaluate("!document.querySelector('.case').hidden && document.querySelector('.case').classList.contains('is-open')")
        check('deep link: case open, no cameo, all --w 100', vis and pg.evaluate('window.__cameo.length') == 0 and all(v in ('', '100') for v in ws), (vis, pg.evaluate('window.__cameo'), sorted(set(ws))))
        check('deep link: no errors', not pg.errs, pg.errs[:3])
        ctx.close()

    if want('reduce'):
        ctx, pg = newpage(b, reduced_motion='reduce', **DESK)
        pg.add_init_script(SAMPLER)
        pg.goto(u('reduce'), wait_until='load'); pg.wait_for_timeout(3500)
        S = pg.evaluate('window.__s'); s = S['1300']
        ws = [v for k in S for v in S[k]['w']]
        check('reduce: visible at 1.3s', s['lede'] == 1 and s['cta'] == 1 and s['meta'] == 1 and all(t == 0 for t in s['tf']) and s['photo'] == 'none', s)
        check('reduce: no cameo, no tween', pg.evaluate('window.__cameo.length') == 0 and all(v in ('', '100') for v in ws), sorted(set(ws)))
        ctx.close()

    if want('frame'):
        for label, kw in (('1440', DESK), ('390', MOB)):
            ctx, pg = newpage(b, **kw)
            pg.goto(u('fr0'), wait_until='load'); pg.wait_for_timeout(2500)
            rects = pg.evaluate("[...document.querySelectorAll('.name-line')].map(l => { const r = l.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })")
            ctx.close()
            worst = []
            for delay in (50, 150, 300, 600):
                ctx, pg = newpage(b, **kw)
                pg.goto(u('fr'), wait_until='commit'); pg.wait_for_timeout(delay)
                path = f'{OUT}p2frame_{label}_{delay}.png'
                pg.screenshot(path=path)
                im = Image.open(path).convert('L')
                light = 0
                for (l, t, r_, bt) in rects:
                    box = im.crop((max(0, int(l)), max(0, int(t)), int(r_), int(bt)))
                    light += sum(1 for v in box.getdata() if v > 110)
                worst.append((delay, light, im.getpixel((5, 5))))
                ctx.close()
            check(f'first frames {label}: no light pixels in name masks', all(l == 0 for _, l, _ in worst), worst)
    print(f"{sum(1 for r in res if r[1])}/{len(res)} passed")
