"""P11 acceptance: Inspecter v2 (Edge via Playwright). python p11test.py [shots]"""
import sys, time, json
from playwright.sync_api import sync_playwright

SP = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
BASE = 'http://localhost:5178/'
SHOTS = 'shots' in sys.argv
sys.stdout.reconfigure(errors='backslashreplace')
res = []

def check(name, fn):
    try:
        ok, ev = fn()
    except Exception as e:
        ok, ev = False, 'exception: ' + str(e).splitlines()[0][:300]
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(ev), flush=True)

def mk(b, mobile=False, theme=None):
    ctx = b.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1440, 'height': 900},
                        device_scale_factor=1 if not mobile else 2, is_mobile=mobile, has_touch=mobile)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE.rstrip('/'))
    if theme:
        ctx.add_init_script(f"try{{localStorage.setItem('ql-theme','{theme}')}}catch(e){{}}")
    else:
        ctx.add_init_script("try{localStorage.removeItem('ql-theme')}catch(e){}")
    # pas d'aperçu (cameo) : il gênerait les mesures
    ctx.add_init_script("try{sessionStorage.setItem('ql-intro','1')}catch(e){}")
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    return ctx, pg

def load(pg, q=''):
    pg.goto(BASE + '?t=' + str(time.time()) + q, wait_until='load')
    pg.wait_for_selector('html.is-ready', state='attached')
    pg.wait_for_timeout(2600)

def scroll_to(pg, sel, block='center'):
    pg.evaluate(f"document.querySelector('{sel}').scrollIntoView({{block:'{block}'}})")
    pg.wait_for_timeout(600)

def shot(pg, name):
    if SHOTS:
        pg.screenshot(path=SP + name + '.png')

def run_desktop(b, theme):
    tag = theme or 'dark'
    ctx, pg = mk(b, theme=theme)
    load(pg)
    edge0 = pg.evaluate("(() => { const c = document.querySelectorAll('.hero .name-line .ch'); return c[c.length-1].getBoundingClientRect().right; })()")
    # the first line's last .ch (querySelector('.hero .name-line') is line 1)
    edge0 = pg.evaluate("(() => { const l = document.querySelector('.hero .name-line'); const c = l.querySelectorAll('.ch'); return c[c.length-1].getBoundingClientRect().right; })()")
    pg.keyboard.press('i')
    pg.wait_for_timeout(600)
    def a1():
        r = pg.evaluate("""(() => {
          const cols = [...document.querySelectorAll('.grid-overlay i')].map(i => new DOMMatrix(getComputedStyle(i).transform).d);
          const rul = [...document.querySelectorAll('.ruler')].map(r => getComputedStyle(r).transform);
          const l = document.querySelector('.hero .name-line'); const c = l.querySelectorAll('.ch');
          return { cols, rul, edge: c[c.length-1].getBoundingClientRect().right, on: document.documentElement.classList.contains('is-inspect') };
        })()""")
        ok = r['on'] and len(r['cols']) == 12 and all(d == 1 for d in r['cols']) and all(t == 'none' for t in r['rul']) and abs(r['edge'] - edge0) <= .5
        return ok, f"cols d={set(r['cols'])} rulers={r['rul']} edge {edge0:.2f}->{r['edge']:.2f}"
    check(f'[{tag}] A1 entrance at +600ms, no reflow', a1)
    pg.wait_for_timeout(400)
    shot(pg, f'p11_d_{tag}_on')

    def a2():
        xs = pg.evaluate("[...document.querySelectorAll('.ruler-nums span')].map(s => s.textContent)")
        y0 = pg.evaluate("document.querySelector('.ruler-track span').textContent")
        pg.mouse.wheel(0, 1000)
        pg.wait_for_timeout(1500)
        y1 = pg.evaluate("document.querySelector('.ruler-track span').textContent")
        sy = pg.evaluate("scrollY")
        return '1400' in xs and y0 != y1, f"x has 1400={'1400' in xs} y first {y0}->{y1} scrollY={sy}"
    check(f'[{tag}] A2 ruler numbers', a2)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(800)

    def a4():
        r = pg.evaluate("""(() => {
          const L = [...document.querySelectorAll('.spec-label')].map(s => s.getBoundingClientRect());
          const hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
          let pairs = 0;
          for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) if (hit(L[i], L[j])) pairs++;
          const labels = [...document.querySelectorAll('.spec-label')];
          const h1 = labels.find(s => s.textContent.startsWith('H1'));
          // le texte de la ligne méta (statut, horloges) ; le cadre du H1 peut toucher son filet du bas
          const metas = [...document.querySelectorAll('.hero-meta > *')].flatMap(e => { const g = document.createRange(); g.selectNodeContents(e); return [...g.getClientRects()]; });
          return { n: L.length, pairs, h1meta: metas.some(m => hit(h1.getBoundingClientRect(), m)), texts: labels.map(s => s.textContent.slice(0, 12) + (s.classList.contains('is-inside') ? '*' : '')) };
        })()""")
        return r['n'] >= 8 and r['pairs'] == 0 and not r['h1meta'], r
    check(f'[{tag}] A4 spec labels never collide', a4)

    # A3: hover demo while it transitions, read 500 ms later
    scroll_to(pg, '.demo-btn')
    def a3():
        box = pg.locator('.demo-btn').first.bounding_box()
        pg.mouse.move(box['x'] - 60, box['y'] + box['height'] / 2)
        pg.wait_for_timeout(300)
        pg.mouse.move(box['x'] + 12, box['y'] + box['height'] / 2, steps=2)
        pg.wait_for_timeout(500)
        r = pg.evaluate("""(() => {
          const t = document.querySelector('.probe-tag').textContent;
          const bg = getComputedStyle(document.querySelector('.demo-btn')).backgroundColor;
          const m = bg.match(/\\d+/g).slice(0, 3).map(Number);
          const hex = '#' + m.map(v => v.toString(16).padStart(2, '0')).join('');
          return { t, hex, on: document.querySelector('.probe').classList.contains('is-on') };
        })()""")
        return r['on'] and ('fill ' + r['hex']) in r['t'], r
    check(f'[{tag}] A3 probe reads the settled fill', a3)
    shot(pg, f'p11_d_{tag}_probe')

    # A6: select demo button
    def a6():
        pg.locator('.demo-btn').first.click()
        pg.wait_for_timeout(700)
        r = pg.evaluate("""(() => {
          const p = document.querySelector('.inspect-panel');
          const bg = getComputedStyle(document.querySelector('.demo-btn')).backgroundColor;
          const cols = document.querySelector('.ip-colors').textContent;
          return { vis: !p.hidden && p.classList.contains('is-on'), name: document.querySelector('.ip-name').textContent, cols, code: document.querySelector('.ip-code').textContent, bg };
        })()""")
        tokok = ('--ink' in r['cols']) or ('--accent' in r['cols'])
        # the token under "Fond" must be the bg's token
        fond = [l for l in pg.evaluate("[...document.querySelectorAll('.ip-colors li')].map(li => li.textContent)") if l.startswith('Fond')]
        pg.locator('.ip-copy').click()
        pg.wait_for_timeout(300)
        clip = pg.evaluate("navigator.clipboard.readText()").replace(chr(13), "")
        same = ''.join(clip.split()) == ''.join(r['code'].split())   # code affiché ligne par ligne (spans) : même texte, blancs à part
        ok = r['vis'] and r['name'] == 'button.demo-btn' and tokok and fond and ('--' in fond[0]) and 'var(--' in r['code'] and same
        return ok, {'name': r['name'], 'fond': fond, 'code': r['code'][:160], 'clip==code': same, 'clip': clip[:80], 'errs': pg.errs[:2]}
    check(f'[{tag}] A6 demo tokens, code, copy', a6)
    shot(pg, f'p11_d_{tag}_panel')

    def a7():
        # focus is on the demo button after the click; Shift+Enter -> parent
        pg.locator('.demo-btn').first.focus()
        pg.keyboard.press('Shift+Enter')
        pg.wait_for_timeout(200)
        n1 = pg.evaluate("document.querySelector('.ip-name').textContent")
        par = pg.evaluate("(() => { const p = document.querySelector('.demo-btn').parentElement; return p.tagName.toLowerCase() + (p.classList[0] ? '.' + p.classList[0] : ''); })()")
        pg.keyboard.press('Enter')   # focus (demo) is inside the parent selection -> first child
        pg.wait_for_timeout(200)
        n2 = pg.evaluate("document.querySelector('.ip-name').textContent")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
        s1 = pg.evaluate("[document.querySelector('.sel-box').classList.contains('is-on'), document.querySelector('.inspect-panel').hidden, document.documentElement.classList.contains('is-inspect')]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        s2 = pg.evaluate("document.documentElement.classList.contains('is-inspect')")
        ok = n1 == par and s1 == [False, True, True] and s2 is False
        return ok, f'shift+enter {n1} (parent {par}) enter-> {n2} esc1 sel/panelHidden/on={s1} esc2 on={s2}'
    check(f'[{tag}] A7 keyboard parent/child/escape', a7)

    # A5: row click and CTA
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(500)
    pg.keyboard.press('i'); pg.wait_for_timeout(500)
    def a5():
        popups, downloads = [], []
        pg.on('popup', lambda p: popups.append(p))
        pg.on('download', lambda d: downloads.append(d))
        ghost = pg.locator('.hero .btn--ghost')
        ghost.click()
        pg.wait_for_timeout(600)
        g = pg.evaluate("document.querySelector('.ip-name').textContent")
        scroll_to(pg, '.work-row')
        row = pg.locator('.work-row').first
        bb = row.bounding_box()
        pg.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
        pg.wait_for_timeout(700)
        r = pg.evaluate("""(() => {
          const s = document.querySelector('.sel-box').getBoundingClientRect();
          const row = document.querySelector('.work-row').getBoundingClientRect();
          const inside = s.left >= row.left - 1 && s.right <= row.right + 1 && s.top >= row.top - 1 && s.bottom <= row.bottom + 1;
          return { caseHidden: document.querySelector('.case').hidden, sel: document.querySelector('.sel-box').classList.contains('is-on') && s.width > 0, inside,
                   name: document.querySelector('.ip-name').textContent, panel: !document.querySelector('.inspect-panel').hidden,
                   blocks: [...document.querySelectorAll('.ip-eyebrow')].map(h => h.textContent) };
        })()""")
        ok = r['caseHidden'] and r['sel'] and r['inside'] and r['panel'] and 'Mise en page' in r['blocks'] and not popups and not downloads
        return ok, dict(r, ghost=g, popups=len(popups), downloads=len(downloads))
    check(f'[{tag}] A5 row click selects, CTA does nothing', a5)
    shot(pg, f'p11_d_{tag}_row')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # A8: Tab through the page
    def a8():
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(400)
        pg.evaluate("document.querySelector('.hero .btn--accent, .hero .btn').focus()")
        bad, n = [], 0
        # attend l'état réel (cadre posé sur l'élément atteint, défilement doux fini) plutôt qu'un délai fixe
        settled = """(() => { const a = document.activeElement; if (!a.closest('main, .foot')) return true;
          const f = a.getBoundingClientRect(), p = document.querySelector('.probe-box').getBoundingClientRect();
          return document.querySelector('.probe').classList.contains('is-on') && Math.max(Math.abs(f.left - p.left), Math.abs(f.top - p.top), Math.abs(f.width - p.width), Math.abs(f.height - p.height)) <= 1; })()"""
        for k in range(14):
            pg.keyboard.press('Tab')
            try:
                pg.wait_for_function(settled, timeout=2500)
            except Exception:
                pass   # relevé quand même : l'écart part dans bad
            r = pg.evaluate("""(() => {
              const a = document.activeElement;
              const inMain = !!a.closest('main, .foot');
              const f = a.getBoundingClientRect(), p = document.querySelector('.probe-box').getBoundingClientRect();
              return { tag: a.tagName + '.' + (a.classList[0] || ''), inMain, on: document.querySelector('.probe').classList.contains('is-on'),
                       d: Math.max(Math.abs(f.left - p.left), Math.abs(f.top - p.top), Math.abs(f.width - p.width), Math.abs(f.height - p.height)) };
            })()""")
            if not r['inMain']:
                continue
            n += 1
            if not r['on'] or r['d'] > 1: bad.append(r)
        return n >= 8 and not bad, f'checked {n} bad={bad[:3]}'
    check(f'[{tag}] A8 probe follows Tab', a8)
    shot(pg, f'p11_d_{tag}_tab')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    # exits by opening a case
    def x1():
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
        pg.keyboard.press('i'); pg.wait_for_timeout(300)
        pg.evaluate("location.hash = '#' + PROJECTS[0].id"); pg.wait_for_timeout(900)
        r = pg.evaluate("[document.documentElement.classList.contains('is-inspect'), !document.querySelector('.case').hidden, document.querySelectorAll('.spec-label').length]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
        return r[0] is False and r[1] and r[2] == 0, r
    check(f'[{tag}] opening a case leaves the mode', x1)
    check(f'[{tag}] no errors', lambda: (not pg.errs, pg.errs[:3]))
    ctx.close()

def run_url(b):
    ctx, pg = mk(b)
    pg.goto(BASE + '?inspect&t=' + str(time.time()), wait_until='load')
    pg.wait_for_selector('html.is-ready', state='attached')
    pg.wait_for_timeout(1500)
    check('A9 ?inspect enables the mode', lambda: (pg.evaluate("document.documentElement.classList.contains('is-inspect')") and not pg.errs, pg.errs[:2]))
    shot(pg, 'p11_d_url')
    ctx.close()

def run_mobile(b, theme):
    tag = theme or 'dark'
    ctx, pg = mk(b, mobile=True, theme=theme)
    load(pg)
    def a10():
        r0 = pg.evaluate("[getComputedStyle(document.querySelector('.inspect-touch')).display, getComputedStyle(document.querySelector('.inspect-btn')).display]")
        pg.locator('.inspect-touch').tap()
        pg.wait_for_timeout(700)
        r1 = pg.evaluate("""(() => ({
          cols: [...document.querySelectorAll('.grid-overlay i')].filter(i => i.getClientRects().length && getComputedStyle(i).display !== 'none').length,
          chip: getComputedStyle(document.querySelector('.inspect-chip')).visibility === 'visible' && document.querySelector('.inspect-chip').getBoundingClientRect().height > 0,
          rulers: [...document.querySelectorAll('.ruler')].map(r => getComputedStyle(r).display),
          pressed: document.querySelector('.inspect-touch').getAttribute('aria-pressed')
        }))()""")
        shot(pg, f'p11_m_{tag}_on')
        lede = pg.locator('.lede')
        lede.tap()
        pg.wait_for_timeout(900)
        r2 = pg.evaluate("""(() => {
          const p = document.querySelector('.inspect-panel'), r = p.getBoundingClientRect();
          const d = document.querySelector('.dock').getBoundingClientRect();
          return { vis: !p.hidden && p.classList.contains('is-on'), bottom: Math.round(r.bottom), top: Math.round(r.top), h: innerHeight,
                   typo: !document.querySelector('.ip-typo').hidden, dockTop: Math.round(d.top), dockOp: getComputedStyle(document.querySelector('.dock')).opacity,
                   name: document.querySelector('.ip-name').textContent, probe: document.querySelector('.probe').classList.contains('is-on') };
        })()""")
        shot(pg, f'p11_m_{tag}_sheet')
        pg.locator('.inspect-chip button').tap()
        pg.wait_for_timeout(500)
        r3 = pg.evaluate("[document.documentElement.classList.contains('is-inspect'), document.querySelector('.inspect-panel').hidden]")
        ok = r0 == ['grid', 'none'] and r1['cols'] == 4 and r1['chip'] and all(d == 'none' for d in r1['rulers']) and r2['vis'] and abs(r2['bottom'] - r2['h']) <= 1 and r2['typo'] and not r2['probe'] and (r2['dockTop'] >= r2['h'] or r2['dockOp'] == '0') and r3 == [False, True]
        return ok, {'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3}
    check(f'[{tag}] A10 mobile touch inspect', a10)
    def drag():
        pg.locator('.inspect-touch').tap(); pg.wait_for_timeout(500)
        pg.locator('.brief').tap(); pg.wait_for_timeout(700)
        cdp = pg.context.new_cdp_session(pg)
        r = pg.evaluate("(() => { const h = document.querySelector('.ip-head').getBoundingClientRect(); return [h.left + h.width / 2, h.top + 8]; })()")
        x, y = r
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
        for k in range(1, 11):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y + k * 12}]})
            pg.wait_for_timeout(16)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        pg.wait_for_timeout(700)
        s = pg.evaluate("[document.querySelector('.sel-box').classList.contains('is-on'), document.querySelector('.inspect-panel').hidden, document.documentElement.classList.contains('is-inspect')]")
        pg.locator('.inspect-touch').tap(); pg.wait_for_timeout(300)
        return s == [False, True, True], s
    check(f'[{tag}] mobile sheet drag down deselects', drag)
    check(f'[{tag}] mobile no errors', lambda: (not pg.errs, pg.errs[:3]))
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    for th in (None, 'light'):
        run_desktop(b, th)
    run_url(b)
    for th in (None, 'light'):
        run_mobile(b, th)
    b.close()
print(f'{sum(res)}/{len(res)} passed')
