"""P4 acceptance tests (phones, tablets, extreme viewports). python p4test.py"""
import time, json
from playwright.sync_api import sync_playwright
import sys
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée

BASE = 'http://localhost:5178/'
res = []
def rec(name, ok, ev):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(ev), flush=True)

def mk(b, w, h, mobile=False, reduce=False):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile,
                        reduced_motion='reduce' if reduce else 'no-preference')
    try: ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE.rstrip('/'))
    except Exception: pass
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    pg.goto(BASE + '?t=p4' + str(time.time_ns()), wait_until='load')
    pg.wait_for_selector('html.is-ready', state='attached')
    pg.wait_for_timeout(2600)
    return ctx, pg

R = "(s) => { const r = document.querySelector(s).getBoundingClientRect(); return {x:r.left, y:r.top, w:r.width, h:r.height, r:r.right, b:r.bottom}; }"

def scroll_to(pg, y, step=40):
    cur = pg.evaluate('scrollY')
    n = max(1, int(abs(y - cur) / step))
    for i in range(1, n + 1):
        pg.evaluate(f'window.scrollTo(0, {cur + (y - cur) * i / n})')
        pg.wait_for_timeout(20)
    pg.wait_for_timeout(250)

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    # 1) (fix A1, replaces 'eyebrow above the dock') hero CTAs fully visible, dock hidden
    #    while the CTA row / live links are in view, dock visible after scrolling past them
    CTA = """() => { const d = document.querySelector('.dock'); const dr = d.getBoundingClientRect();
      const shown = !d.classList.contains('dock-hidden') || d.matches(':focus-within');
      const bs = [...document.querySelectorAll('.cta-row .btn')].map(e => e.getBoundingClientRect());
      return { bottoms: bs.map(r => Math.round(r.bottom)), vh: innerHeight, dockShown: shown,
        overlap: shown && bs.some(r => r.bottom > dr.top && r.top < dr.bottom) }; }"""
    for w, h in ((320, 640), (360, 740), (375, 812), (390, 664), (390, 844)):
        c0, g0 = mk(b, w, h, True)
        r = g0.evaluate(CTA)
        full = max(r['bottoms']) <= r['vh']
        rec(f'{w}x{h} CTAs fully visible, dock hidden, no overlap', full and not r['dockShown'] and not r['overlap'], r)
        lb = g0.evaluate("document.querySelector('.hero .live').getBoundingClientRect().bottom + scrollY")
        scroll_to(g0, lb - 40, 20); g0.wait_for_timeout(500)
        after = g0.evaluate("!document.querySelector('.dock').classList.contains('dock-hidden')")
        rec(f'{w}x{h} dock shown once past the CTAs and live links', after, dict(y=g0.evaluate('scrollY'), shown=after))
        c0.close()
    ctx, pg = mk(b, 390, 844, True)
    dk = pg.evaluate(R, '.dock')
    row = pg.evaluate(R, '.work-row')
    print('   first row top', round(row['y']), 'hero h', pg.evaluate("document.querySelector('.hero').offsetHeight"))
    hs = pg.evaluate("[...document.querySelectorAll('.dock a')].map(a => a.getBoundingClientRect().height)")
    rec('390 dock links >= 44', min(hs) >= 44, hs)
    rec('390 dock inside', dk['x'] >= 0 and dk['r'] <= 390, dk)
    # hit areas (coarse pointer)
    hit = pg.evaluate("""() => { const q = s => document.querySelector(s); const out = {};
      for (const [k, s, m] of [['theme', '.theme-btn', 5], ['cv', '.tools .btn--sm', 0]]) { const r = q(s).getBoundingClientRect();
        const cx = r.left + r.width / 2, bw = parseFloat(getComputedStyle(q(s)).borderTopWidth);
        out[k] = { visual: m ? r.height : r.height - 2 * bw, up: !!document.elementFromPoint(cx, r.top - m + .5)?.closest(s), down: !!document.elementFromPoint(cx, r.bottom + m - .5)?.closest(s), hit: r.height + 2 * m }; }
      return out; }""")
    rec('390 theme/CV visual 34 + hit area 44', all(v['up'] and v['down'] and abs(v['visual'] - 34) < 1 and v['hit'] >= 44 for v in hit.values()), hit)
    fa = pg.evaluate("[...document.querySelectorAll('.foot a')].map(a => a.getBoundingClientRect().height)")
    la = pg.evaluate("[...document.querySelectorAll('.links a')].map(a => a.getBoundingClientRect().height)")
    rec('390 .links a >= 44, .foot a padded', min(la) >= 44 and min(fa) >= 40, {'links': la, 'foot': fa})
    # 3) dock hide / show
    hero = pg.evaluate("document.querySelector('.hero').offsetHeight")
    scroll_to(pg, hero + 100)   # past the hero (was a fixed 800, inside the 868 px hero: stale)
    c1 = pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
    scroll_to(pg, pg.evaluate('scrollY') + 400)
    c1b = pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
    scroll_to(pg, pg.evaluate('scrollY') - 60, 10)
    c2 = pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
    scroll_to(pg, pg.evaluate('scrollY') + 300)
    c3 = pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
    scroll_to(pg, pg.evaluate('document.documentElement.scrollHeight - innerHeight'), 80)
    c4 = pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
    rec('dock hides down past hero / shows up 60 / shows at bottom', c1 and c1b and not c2 and c3 and not c4, dict(hero=hero, down800=c1, down1200=c1b, up60=c2, down_again=c3, bottom=c4))
    # dock hidden + focus-within => visible
    scroll_to(pg, 1400); scroll_to(pg, 1800)
    pg.evaluate("document.querySelector('.dock a').focus()")
    pg.wait_for_timeout(600)
    op = pg.evaluate("getComputedStyle(document.querySelector('.dock')).opacity")
    rec('hidden dock with focus-within is visible', pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')") and float(op) > .99, op)
    pg.evaluate("document.activeElement.blur()")
    # dock link click: no hide during the anchor jump (from past the hero: at the top the dock is away, fix A1)
    scroll_to(pg, 1400); scroll_to(pg, 1300, 10)
    pg.wait_for_timeout(600)
    pg.tap('.dock a[href="#parcours"]')
    samples = []
    for i in range(12):
        pg.wait_for_timeout(150)
        samples.append(pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')"))
    rec('dock stays during an anchor jump', not any(samples), samples)
    # 4) toast above the dock
    scroll_to(pg, pg.evaluate("document.querySelector('.contact').getBoundingClientRect().top + scrollY - 100"))
    pg.evaluate("document.querySelector('.dock').classList.remove('dock-hidden')")
    pg.evaluate("document.querySelector('.mail').click()")
    # au doigt, le toast part après l'onde (700 ms) puis glisse (.5 s) : mesure une fois sa transition finie
    pg.wait_for_function("document.querySelector('.toast').classList.contains('is-on')", timeout=3000)
    pg.wait_for_function("document.querySelector('.toast').getAnimations().every(a => a.playState !== 'running')", timeout=3000)
    t = pg.evaluate(R, '.toast'); d = pg.evaluate(R, '.dock')
    on = pg.evaluate("document.querySelector('.toast').classList.contains('is-on')")
    rec('toast bottom < dock top', on and t['b'] < d['y'], f"toast on={on} bottom {t['b']:.0f}, dock top {d['y']:.0f}")
    pg.screenshot(path='p4t_toast.png')
    # 8) case open: topbar up
    scroll_to(pg, 0)
    pg.evaluate("document.querySelector('.work-row').click()")
    pg.wait_for_timeout(900)
    tf = pg.evaluate("getComputedStyle(document.querySelector('.topbar')).transform")
    ty = float(tf.split(',')[5].strip(' )')) if tf.startswith('matrix') else 0
    rec('390 case open: topbar translated up', ty < 0, tf)
    ar = pg.evaluate("""() => { const b = document.querySelector('.case-nav [data-step]'); const r = b.getBoundingClientRect();
      return { h: r.height, up: document.elementFromPoint(r.left + r.width/2, r.top - 5.5) === b, down: document.elementFromPoint(r.left + r.width/2, r.bottom + 5.5) === b, left: !!(document.elementFromPoint(r.left - 5.5, r.top + r.height/2) || document.body).closest('button, a') }; }""")
    # à gauche, la sonde tombe sur le bouton voisin (« Lien ») : il suffit qu'elle touche une commande
    rec('case arrows hit area', ar['up'] and ar['down'] and ar['left'], ar)
    pg.screenshot(path='p4t_case.png')
    pg.evaluate("document.querySelector('.case-close').click()")
    pg.wait_for_timeout(1000)
    tf2 = pg.evaluate("getComputedStyle(document.querySelector('.topbar')).transform")
    rec('390 case closed: topbar back', tf2 in ('none', 'matrix(1, 0, 0, 1, 0, 0)'), tf2)
    rec('390 no errors', not pg.errs, pg.errs)
    ctx.close()

    for w, h in ((360, 740), (320, 640)):
        ctx, pg = mk(b, w, h, True)
        hs = pg.evaluate("[...document.querySelectorAll('.dock a')].map(a => a.getBoundingClientRect().height)")
        dk = pg.evaluate(R, '.dock')
        rec(f'{w} dock links >= 44 and inside', min(hs) >= 44 and dk['x'] >= 0 and dk['r'] <= w, dict(h=hs, left=dk['x'], right=dk['r']))
        pg.screenshot(path=f'p4t_dock{w}.png')
        ctx.close()

    # 9) reduced motion
    ctx, pg = mk(b, 390, 844, True, True)
    scroll_to(pg, 1000); scroll_to(pg, 1600)
    rec('reduce: dock never hidden past the hero CTAs', not pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')"), '')
    ctx.close()

    # 5) tablet and desktop hero
    ctx, pg = mk(b, 1024, 1366, True)
    hh = pg.evaluate("document.querySelector('.hero').getBoundingClientRect().height")
    eb = pg.evaluate(R, '.work .eyebrow')
    navh = pg.evaluate("[...document.querySelectorAll('.nav a')].map(a => a.getBoundingClientRect().height)")
    rec('1024x1366 hero <= 900, eyebrow < 1366, nav links >= 40', hh <= 900 and eb['y'] < 1366 and min(navh) >= 40, dict(hero=hh, eyebrow=eb['y'], nav=navh))
    pg.screenshot(path='p4t_tab.png')
    ctx.close()
    ctx, pg = mk(b, 1440, 900)
    hh = pg.evaluate("document.querySelector('.hero').getBoundingClientRect().height")
    rec('1440x900 hero == 900', abs(hh - 900) < .5, hh)
    rec('1440 no errors', not pg.errs, pg.errs)
    ctx.close()

    # 6) landscape phone
    ctx, pg = mk(b, 844, 390, True)
    nm = pg.evaluate(R, '.name'); ld = pg.evaluate(R, '.lede')
    rec('844x390 name h <= 230.2, lede top < 780', nm['h'] <= .58 * 390 + 4 and ld['y'] < 780, dict(name=nm['h'], lede=ld['y']))
    pg.screenshot(path='p4t_land.png', full_page=False)
    rec('844 no errors', not pg.errs, pg.errs)
    ctx.close()

    # 7) wide + overflow
    ctx, pg = mk(b, 2560, 1440)
    ww = pg.evaluate(R, '.hero .wrap')['w']
    ms = pg.evaluate("getComputedStyle(document.querySelector('.hero-meta')).fontSize")
    rec('2560 wrap in (1680, 2080]', 1680 < ww <= 2080, dict(wrap=ww, mono=ms))
    pg.screenshot(path='p4t_wide.png')
    ctx.close()
    ov = {}
    for w in (320, 360, 390, 768, 820, 1024, 1440, 2560):
        mob = w <= 820
        ctx, pg = mk(b, w, 900 if w > 400 else 780, mob)
        pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(1500)
        ov[w] = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth, innerWidth]")
        if pg.errs: ov[str(w) + 'err'] = pg.errs
        ctx.close()
    rec('no horizontal overflow', all(v[0] <= v[1] <= v[2] and v[2] - v[1] <= 15 for k, v in ov.items() if isinstance(k, int)) and not any(isinstance(k, str) for k in ov), ov)
    b.close()
print(f'{sum(res)}/{len(res)} pass')
