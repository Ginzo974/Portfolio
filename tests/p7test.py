"""P7 acceptance tests (case sheet). python p7test.py [shots]"""
import sys, time, urllib.parse
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée

BASE = 'http://localhost:5178/'
SC = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
SHOTS = 'shots' in sys.argv
Q = '?t=p7' + str(int(time.time()))
res = []

def check(name, ok, ev=''):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (' :: ' + str(ev) if ev else ''), flush=True)

def page(b, w, h, mobile=False, theme=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE.rstrip('/'))
    if theme:
        ctx.add_init_script(f"try{{localStorage.setItem('ql-theme','{theme}')}}catch(e){{}}")
    else:
        ctx.add_init_script("try{localStorage.removeItem('ql-theme')}catch(e){}")
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    return ctx, pg

def load(pg, hash=''):
    pg.goto(BASE + Q + hash, wait_until='load')
    pg.wait_for_selector('html.is-ready', state='attached', timeout=10000)

FIT = """(() => [...document.querySelectorAll('.case-title .ln > span')].map(s => [s.scrollWidth, s.clientWidth]))()"""
TITLE = "document.querySelector('#case-title').textContent"
BAR = """(() => { const b = document.querySelector('.case-bar'); const r = b.getBoundingClientRect();
  const kids = [...b.querySelectorAll('.case-idx, .case-nav > *')].filter(e => e.offsetParent);
  const over = kids.some(e => { const k = e.getBoundingClientRect(); return k.right > r.right - 15.5 || k.left < r.left + 15.5; });
  const nav = b.querySelector('.case-nav').getBoundingClientRect(), idx = b.querySelector('.case-idx').getBoundingClientRect();
  return { over, clash: idx.right > nav.left && idx.bottom > nav.top, h: Math.round(r.height), lines: kids.map(e => Math.round(e.getBoundingClientRect().height)) }; })()"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    # 1) titles fit at 360 and 390 (and 320 for info)
    for (w, h) in [(360, 740), (390, 844), (320, 640)]:
        ctx, pg = page(b, w, h, mobile=True)
        load(pg, '#springbreak'); pg.wait_for_timeout(1200)
        bad, seen, bars = [], [], []
        for k in range(8):
            if k:
                pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(700)
            seen.append(pg.evaluate(TITLE))
            f = pg.evaluate(FIT)
            if any(sw > cw + 1 for sw, cw in f): bad.append((seen[-1], f))
            bar = pg.evaluate(BAR)
            if bar['over'] or bar['clash']: bars.append((seen[-1], bar))
            if SHOTS and w == 390 and k in (0, 4, 5):
                pg.screenshot(path=SC + f'p7_m{w}_case{k}.png')
        check(f'{w}x{h}: all 8 titles fit (scrollWidth <= clientWidth + 1)', not bad and len(set(seen)) == 8, f'bad={bad} seen={seen}')
        check(f'{w}x{h}: bar content inside the bar, no overlap', not bars, bars[:2])
        if w == 390:
            pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(900)
            r = pg.evaluate("""[document.querySelector('.case-idx').textContent, getComputedStyle(document.querySelector('.case-idx')).display,
              document.querySelector('.case-idx').getBoundingClientRect().width, getComputedStyle(document.querySelector('.case-close kbd')).display,
              getComputedStyle(document.querySelector('.case-kind')).display]""")
            check('390x844: .case-idx visible, starts 01 / 08, kbd hidden on touch', r[0].startswith('01 / 08') and r[1] != 'none' and r[2] > 0 and r[3] == 'none' and r[4] == 'none', r)
            # coarse hit areas of bar controls >= 44
            hs = pg.evaluate("""[...document.querySelectorAll('.case-nav > *')].map(e => { const a = getComputedStyle(e, '::after'); return [e.className || e.dataset.step, e.offsetHeight - parseFloat(a.top) - parseFloat(a.bottom)]; })""")
            check('390 coarse: every bar control hit area >= 44 px tall', all(x[1] >= 44 for x in hs), hs)
            hd = pg.evaluate("[getComputedStyle(document.querySelector('.case-bar'), '::before').width, getComputedStyle(document.querySelector('.case-bar'), '::before').height]")
            check('touch: grab handle 36x4', hd == ['36px', '4px'], hd)
        check(f'{w}: no errors', not pg.errs, pg.errs[:3])
        ctx.close()

    # desktop
    ctx, pg = page(b, 1440, 900)
    load(pg, '#springbreak'); pg.wait_for_timeout(1500)
    sizes = {}
    for k in range(8):
        if k:
            pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(700)
        t = pg.evaluate(TITLE)
        sizes[t] = pg.evaluate("""(() => { const h = document.querySelector('#case-title'); const s = h.querySelector('.ln > span');
          return [parseFloat(getComputedStyle(h).fontSize), getComputedStyle(h).fontVariationSettings, Math.round(s.getBoundingClientRect().height / parseFloat(getComputedStyle(h).lineHeight))]; })()""")
        f = pg.evaluate(FIT)
        if any(sw > cw + 1 for sw, cw in f): sizes[t].append('OVERFLOW')
        if SHOTS: pg.screenshot(path=SC + f'p7_d_case{k}.png')
    print(sizes)
    ok = sizes['LCO'][0] <= 180 and sizes['QUASAR'][0] <= 180 and sizes['Springbreak'][2] == 1 and not any('OVERFLOW' in v for v in sizes.values())
    check('1440: LCO/QUASAR <= 180px, SPRINGBREAK one line, nothing overflows', ok, {k: v for k, v in sizes.items() if k in ('LCO', 'QUASAR', 'Springbreak')})
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(900)   # back to springbreak
    r = pg.evaluate("""(() => { const a = document.querySelector('.case-bar a.case-site'); return a && [a.getAttribute('href'), a.target, a.rel, a.textContent]; })()""")
    check('#springbreak bar: a.case-site springbreak.fr _blank', r and r[0] == 'https://springbreak.fr' and r[1] == '_blank', r)
    fr = pg.evaluate("(() => { const d = document.querySelector('.case-intro dl div'); return [d.querySelector('dt').textContent, d.querySelector('dd a')?.href, d.querySelector('dd a')?.target, d.querySelector('dd').textContent]; })()")
    check('facts start with En ligne link', fr[0] == 'En ligne' and fr[1].startswith('https://springbreak.fr') and fr[2] == '_blank', fr)

    # share copy
    pg.click('.case-share')
    pg.wait_for_timeout(150)
    lbl = pg.evaluate("document.querySelector('.case-share-lbl').textContent")
    clip = pg.evaluate("navigator.clipboard.readText()")
    live = pg.evaluate("document.querySelector('.case-bar [aria-live]').textContent")
    org = pg.evaluate("location.origin")
    check('share: clipboard = origin/#springbreak, label Copié within 200 ms', clip == org + '/#springbreak' and lbl == 'Copié' and live == 'Lien copié', [clip, lbl, live])
    if SHOTS: pg.wait_for_timeout(250); pg.screenshot(path=SC + 'p7_d_copied.png', clip={'x': 900, 'y': 16, 'width': 540, 'height': 64})
    pg.wait_for_timeout(1900)
    check('share: back to Lien after 2 s', pg.evaluate("document.querySelector('.case-share-lbl').textContent") == 'Lien')

    # progress
    pg.evaluate("document.querySelector('.case-sheet').scrollTop = 1e6"); pg.wait_for_timeout(200)
    bot = pg.evaluate("getComputedStyle(document.querySelector('.case-bar'), '::after').transform")
    pg.evaluate("document.querySelector('.case-sheet').scrollTop = 0"); pg.wait_for_timeout(200)
    top = pg.evaluate("getComputedStyle(document.querySelector('.case-bar'), '::after').transform")
    sx = lambda m: float(m.split('(')[1].split(',')[0]) if m != 'none' else 1.0
    check('progress: bottom scaleX >= .98, top <= .02', sx(bot) >= .98 and sx(top) <= .02, [bot, top])

    # zecheck: no case-site, mailto
    pg.goto(BASE + Q + 'b#zecheck'); pg.wait_for_selector('html.is-ready', state='attached'); pg.wait_for_timeout(1200)
    r = pg.evaluate("""[!!document.querySelector('.case-site'), document.querySelector('.case-ask a[href^="mailto:"]')?.getAttribute('href')]""")
    subj = urllib.parse.unquote(r[1].split('subject=')[1]) if r[1] else None
    check('#zecheck: no .case-site, mailto subject Écrans du projet ZE CHECK', not r[0] and subj == 'Écrans du projet ZE CHECK', [r, subj])
    if SHOTS: pg.evaluate("document.querySelector('.case-ask').scrollIntoView({block:'center'})"); pg.wait_for_timeout(1500); pg.screenshot(path=SC + 'p7_d_ask.png')
    pg.evaluate("document.querySelector('.case-sheet').scrollTop = 0"); pg.wait_for_timeout(300)

    # directional swap
    t0 = pg.evaluate(TITLE)
    pg.keyboard.press('ArrowRight')
    pg.wait_for_timeout(90)
    o90 = pg.evaluate("+getComputedStyle(document.querySelector('.case-body')).opacity")
    tx = pg.evaluate("getComputedStyle(document.querySelector('.case-body')).transform")
    if SHOTS: pg.screenshot(path=SC + 'p7_d_midswap.png')
    pg.wait_for_timeout(250)
    if SHOTS: pg.screenshot(path=SC + 'p7_d_midswap2.png')
    kid = pg.evaluate("getComputedStyle(document.querySelector('.case-intro')).transform")
    pg.wait_for_timeout(860)
    r = pg.evaluate(f"[{TITLE}, +getComputedStyle(document.querySelector('.case-body')).opacity, location.hash]")
    check('ArrowRight: +90 opacity < 1 and offset; +1200 new title, opacity 1, hash', o90 < 1 and tx != 'none' and r[0] != t0 and r[1] == 1 and r[2] == '#poulettes' and not pg.errs, [o90, tx, kid, r, pg.errs[:2]])

    # rapid x3 from project 1
    pg.goto(BASE + Q + 'c#springbreak'); pg.wait_for_selector('html.is-ready', state='attached'); pg.wait_for_timeout(1200)
    for _ in range(3):
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(40)
    pg.wait_for_timeout(2200)
    r = pg.evaluate(f"""[{TITLE}, location.hash, +getComputedStyle(document.querySelector('.case-body')).opacity,
      [...document.querySelectorAll('.case-body > *')].map(e => +getComputedStyle(e).opacity).every(o => o === 1), document.querySelector('.case-body').getAnimations().length]""")
    check('rapid ArrowRight x3: project 4, nothing stuck', r[0] == 'ZE CHECK' and r[1] == '#zecheck' and r[2] == 1 and r[3] and r[4] == 0, r)
    # prev arrow button then 'Projet suivant' button
    pg.click('.case-nav [data-step="-1"]'); pg.wait_for_timeout(1500)
    a = pg.evaluate(TITLE)
    pg.evaluate("document.querySelector('.case-next').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(1200)
    pg.click('.case-next'); pg.wait_for_timeout(1500)
    bb = pg.evaluate(f"[{TITLE}, document.activeElement.id]")
    check('prev button then Projet suivant', a == 'LEZGO' and bb == ['ZE CHECK', 'case-title'], [a, bb])

    # drag
    def bar_pt():
        r = pg.evaluate("(() => { const r = document.querySelector('.case-idx').getBoundingClientRect(); return [r.right + 40, r.top + r.height / 2]; })()")
        return r
    x, y = bar_pt()
    pg.mouse.move(x, y); pg.mouse.down()
    for i in range(1, 13):
        pg.mouse.move(x, y + 5 * i); pg.wait_for_timeout(25)
    if SHOTS: pg.screenshot(path=SC + 'p7_d_drag60.png')
    pg.wait_for_timeout(150)
    pg.mouse.up(); pg.wait_for_timeout(700)
    r = pg.evaluate("[getComputedStyle(document.querySelector('.case-sheet')).transform, document.querySelector('.case').hidden, document.querySelector('.case-sheet').style.cssText, location.hash]")
    check('60 px drag: springs back to transform none, still open', r[0] == 'none' and not r[1] and r[3] == '#zecheck', r)
    # click on bar (< 6 px) is not a drag
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x, y + 3); pg.mouse.up(); pg.wait_for_timeout(300)
    check('bar click (< 6 px) keeps sheet open', not pg.evaluate("document.querySelector('.case').hidden") and pg.evaluate("document.querySelector('.case-sheet').style.transform") == '')
    pg.mouse.move(x, y); pg.mouse.down()
    for i in range(1, 17):
        pg.mouse.move(x, y + 20 * i); pg.wait_for_timeout(16)
    if SHOTS: pg.screenshot(path=SC + 'p7_d_drag320.png')
    pg.mouse.up()
    tt = time.time()
    try:
        pg.wait_for_function("document.querySelector('.case').hidden", timeout=1000); dt = time.time() - tt
    except Exception:
        dt = None
    r = pg.evaluate("[location.hash, document.querySelector('.case-sheet').style.cssText, document.body.classList.contains('no-scroll')]")
    check('320 px drag: hidden within 1 s, hash empty', dt is not None and r[0] == '' and not r[2], [dt, r])
    # reopen after drag close: slides normally
    pg.evaluate("document.querySelectorAll('.work-row')[0].click()"); pg.wait_for_timeout(1300)
    r = pg.evaluate("[getComputedStyle(document.querySelector('.case-sheet')).transform, +getComputedStyle(document.querySelector('.case-intro')).opacity, location.hash]")
    check('reopen after drag close: sheet in place, content in', r[0] == 'none' and r[1] > .99 and r[2] == '#springbreak', r)
    # velocity flick: small fast drag closes
    x, y = bar_pt()
    pg.mouse.move(x, y); pg.mouse.down()
    for i in range(1, 6):
        pg.mouse.move(x, y + 16 * i)
    pg.mouse.up()
    try:
        pg.wait_for_function("document.querySelector('.case').hidden", timeout=1000); fl = True
    except Exception:
        fl = False
    check('fast 80 px flick closes', fl)
    # Tab order in bar
    pg.evaluate("document.querySelectorAll('.work-row')[1].click()"); pg.wait_for_timeout(1300)
    order = []
    for _ in range(6):
        pg.keyboard.press('Tab')
        order.append(pg.evaluate("(document.activeElement.className || document.activeElement.dataset.step || document.activeElement.tagName) + ''"))
    check('Tab from title: site, share, prev, next, close', order[:5] == ['case-site', 'case-share', '-1', '1', 'case-close'], order)
    check('desktop: no errors', not pg.errs, pg.errs[:3])
    ctx.close()

    # reduced motion: instant swap
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    load(pg, '#springbreak'); pg.wait_for_timeout(500)
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(50)
    r = pg.evaluate(f"[{TITLE}, +getComputedStyle(document.querySelector('.case-intro')).opacity, +getComputedStyle(document.querySelector('.case-body')).opacity]")
    r[0] = r[0].replace(' ', ' ').replace('⁠', '')   # fix B19: displayed titles glue 'WEI & GO' with no-break spaces
    check('reduced motion: instant swap', r == ['WEI & GO', 1, 1] and not pg.errs, r)
    ctx.close()

    if SHOTS:
        for theme in ('dark', 'light'):
            ctx, pg = page(b, 390, 844, mobile=True, theme=theme)
            load(pg, '#livre-blanc'); pg.wait_for_timeout(2000)
            pg.screenshot(path=SC + f'p7_m_{theme}_lb.png')
            pg.evaluate("document.querySelector('.case-sheet').scrollTop = 900"); pg.wait_for_timeout(1200)
            pg.screenshot(path=SC + f'p7_m_{theme}_lb2.png')
            ctx.close()
            ctx, pg = page(b, 1440, 900, theme=theme)
            load(pg, '#poulettes'); pg.wait_for_timeout(2000)
            pg.screenshot(path=SC + f'p7_d_{theme}_poul.png')
            pg.evaluate("document.querySelector('.case-sheet').scrollTop = 1200"); pg.wait_for_timeout(1500)
            pg.screenshot(path=SC + f'p7_d_{theme}_poul2.png')
            ctx.close()
        ctx, pg = page(b, 360, 740, mobile=True)
        load(pg, '#lco'); pg.wait_for_timeout(1800)
        pg.screenshot(path=SC + 'p7_m360_lco.png')
        ctx.close()
    b.close()

n = res.count(False)
print(f'{len(res) - n}/{len(res)} passed')
