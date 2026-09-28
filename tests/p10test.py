"""P10 acceptance: motion language."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
BASE = 'http://localhost:5178/'
SP = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
Q = '?t=p10' + str(int(time.time()))
res = []
out = open(SP + 'p10test_out.txt', 'w', encoding='utf-8')
def check(name, ok, ev=''):
    res.append(bool(ok))
    line = ('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(ev)
    print(line); out.write(line + '\n'); out.flush()

def page(b, w=1440, h=900, mobile=False, theme=None, reduce=False, path=''):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile,
                        reduced_motion='reduce' if reduce else 'no-preference')
    if theme: ctx.add_init_script(f"try{{localStorage.setItem('ql-theme','{theme}')}}catch(e){{}}")
    else: ctx.add_init_script("try{localStorage.removeItem('ql-theme')}catch(e){}")
    # compte les transitions de vue demandées
    ctx.add_init_script("""if (document.startViewTransition) { const o = document.startViewTransition.bind(document);
      window.__vtCount = 0; document.startViewTransition = cb => { window.__vtCount++; return o(cb); }; }""")
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    pg.goto(BASE + Q + path, wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached')
    pg.wait_for_timeout(2200)
    return ctx, pg

def to(pg, y):
    pg.evaluate(f"window.__lenis ? __lenis.scrollTo({y}, {{immediate: true, force: true}}) : scrollTo(0, {y})")
    pg.wait_for_timeout(300)

def doc_top(pg, sel):
    return pg.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top + scrollY")

MAILP = """(() => {
  const m = document.querySelector('.mail-txt'), chs = m.querySelectorAll('.ch');
  const w = document.querySelector('.contact .wrap'), cs = getComputedStyle(w);
  return { wb: +getComputedStyle(m).getPropertyValue('--wb'), fs: m.style.getPropertyValue('--fs'),
    last: chs[chs.length-1].getBoundingClientRect().right, first: chs[0].getBoundingClientRect().left,
    content: w.getBoundingClientRect().right - parseFloat(cs.paddingRight), cl: w.getBoundingClientRect().left + parseFloat(cs.paddingLeft) };
})()"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    for theme in ['dark', 'light']:
        tag = 'd' if theme == 'dark' else 'l'
        ctx, pg = page(b, theme=theme)
        # A1 magnetic gone, CTA transform never changes
        n = pg.evaluate("document.querySelectorAll('[data-magnetic]').length")
        cta = pg.locator('.cta-row .btn').first
        bb = cta.bounding_box()
        trs = []
        for fx, fy in [(.2, .3), (.8, .7), (.5, .5), (.95, .1)]:
            pg.mouse.move(bb['x'] + bb['width'] * fx, bb['y'] + bb['height'] * fy); pg.wait_for_timeout(120)
            trs.append(pg.evaluate("(() => { const e = document.querySelector('.cta-row .btn'); return getComputedStyle(e).transform + '|' + e.style.transform; })()"))
        check(f'{tag} A1 no data-magnetic, CTA transform unchanged on hover', n == 0 and all(t == 'none|' for t in trs), (n, set(trs)))
        pg.mouse.move(5, 400); pg.wait_for_timeout(700)
        # A2 width hover lock
        GEO = """(() => { const [a, c] = document.querySelectorAll('.cta-row .btn'); const ra = a.getBoundingClientRect(), rc = c.getBoundingClientRect();
          return { w: a.offsetWidth, rw: ra.width, nx: rc.left, bw: getComputedStyle(a.querySelector('.lbl')).getPropertyValue('--bw'), lblw: a.querySelector('.lbl').getBoundingClientRect().width, min: a.style.minWidth }; })()"""
        g0 = pg.evaluate(GEO)
        pg.mouse.move(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2); pg.wait_for_timeout(500)
        g1 = pg.evaluate(GEO)
        pg.screenshot(path=SP + f'p10_{tag}_btnhover.png', clip={'x': bb['x'] - 40, 'y': bb['y'] - 60, 'width': 700, 'height': 220})
        check(f'{tag} A2 Voir les projets hover: --bw 112, width and neighbour x unchanged', g1['bw'].strip() == '112' and abs(g1['rw'] - g0['rw']) <= .5 and abs(g1['nx'] - g0['nx']) <= .5 and g1['lblw'] > g0['lblw'] + 3, (g0, g1))
        pg.mouse.move(5, 400); pg.wait_for_timeout(600)
        # other controls: live links and topbar CV and ghost CTA, no neighbour shift
        SH = """(sel) => [...document.querySelectorAll(sel)].map(e => [Math.round(e.getBoundingClientRect().left * 100) / 100, Math.round(e.getBoundingClientRect().width * 100) / 100])"""
        for sel in ['.live a', '.tools > *', '.cta-row .btn']:
            els = pg.locator(sel)
            base = pg.evaluate(f"({SH})('{sel}')")
            worst = 0
            for k in range(els.count()):
                bx = els.nth(k).bounding_box()
                if not bx or bx['width'] == 0: continue
                pg.mouse.move(bx['x'] + bx['width'] / 2, bx['y'] + bx['height'] / 2); pg.wait_for_timeout(450)
                now = pg.evaluate(f"({SH})('{sel}')")
                worst = max(worst, max(abs(a[0] - c[0]) + abs(a[1] - c[1]) for a, c in zip(base, now)))
            pg.mouse.move(5, 400); pg.wait_for_timeout(450)
            check(f'{tag} A2b hover on {sel}: no shift', worst <= .5, worst)
        mw = pg.evaluate("(() => { const a = document.querySelector('.live a'); return [getComputedStyle(a).getPropertyValue('--mw'), a.style.minWidth]; })()")
        bx = pg.locator('.live a').first.bounding_box(); pg.mouse.move(bx['x'] + 5, bx['y'] + 5); pg.wait_for_timeout(500)
        mw2 = pg.evaluate("getComputedStyle(document.querySelector('.live a')).getPropertyValue('--mw')")
        pg.screenshot(path=SP + f'p10_{tag}_livehover.png', clip={'x': bx['x'] - 120, 'y': bx['y'] - 30, 'width': 560, 'height': 80})
        check(f'{tag} A2c .live a --mw 87.5 -> 100 on hover, min-width set', mw[0].strip() == '87.5' and mw2.strip() == '100' and mw[1].endswith('px'), (mw, mw2))
        pg.mouse.move(5, 400)

        # A8 reveal start state
        tr = pg.evaluate("(() => { const e = [...document.querySelectorAll('.reveal')].find(e => !e.classList.contains('is-in')); return e ? getComputedStyle(e).transform : 'none-pending'; })()")
        check(f'{tag} A8 .js .reveal start transform translateY(16px)', tr == 'matrix(1, 0, 0, 1, 0, 16)', tr)

        # A3 sec-title width by scroll
        top = doc_top(pg, '#methode .sec-title')
        to(pg, top - 900 * .9)
        s1 = pg.evaluate("(() => { const t = document.querySelector('#methode .sec-title'); return [getComputedStyle(t).getPropertyValue('--swd'), t.getBoundingClientRect().top]; })()")
        pg.screenshot(path=SP + f'p10_{tag}_sec90.png')
        to(pg, top - 900 * .4)
        pg.wait_for_timeout(1300)
        s2 = pg.evaluate("(() => { const t = document.querySelector('#methode .sec-title'); return [getComputedStyle(t).getPropertyValue('--swd'), t.getBoundingClientRect().top, getComputedStyle(t).fontVariationSettings]; })()")
        pg.screenshot(path=SP + f'p10_{tag}_sec40.png')
        check(f'{tag} A3 #methode --swd < 86 at 90%, == 86 at 40%', int(s1[0]) < 86 and int(s2[0]) == 86, (s1, s2))
        # titles never wrap more than at rest: heights at 62 vs 86
        hh = pg.evaluate("""(() => [...document.querySelectorAll('.sec-title')].map(t => { const h86 = t.offsetHeight; t.style.setProperty('--swd', 62); t.style.animation = 'none'; const h62 = t.offsetHeight; t.style.animation = ''; t.style.removeProperty('--swd'); return [h62, h86]; }))()""")
        check(f'{tag} A3b section titles never taller at 62 than at 86', all(a <= c for a, c in hh), hh)

        # A4 contact
        mx = pg.evaluate("document.documentElement.scrollHeight - innerHeight")
        ct = doc_top(pg, '.contact')
        to(pg, ct - 900 * .6)
        m0 = pg.evaluate(MAILP)
        pg.screenshot(path=SP + f'p10_{tag}_mail_entry.png')
        to(pg, mx); pg.wait_for_timeout(300)
        m1 = pg.evaluate(MAILP)
        pg.screenshot(path=SP + f'p10_{tag}_mail_settled.png')
        check(f'{tag} A4 contact: entry --wb < 100, settled --wb 100 and last .ch within 2 px of content edge', m0['wb'] < 100 and m1['wb'] == 100 and abs(m1['last'] - m1['content']) <= 2, (m0['wb'], m1))
        # A5 refit mid-animation
        to(pg, ct - 900 * .75); mid = pg.evaluate(MAILP)
        pg.set_viewport_size({'width': 1420, 'height': 900}); pg.wait_for_timeout(300)
        pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(300)
        pg.evaluate("document.fonts.dispatchEvent(new Event('loadingdone'))"); pg.wait_for_timeout(200)
        to(pg, pg.evaluate("document.documentElement.scrollHeight - innerHeight")); pg.wait_for_timeout(300)
        m2 = pg.evaluate(MAILP)
        check(f'{tag} A5 1440 refit mid-animation (wb {mid["wb"]}): same --fs, still flush, no overflow', mid['wb'] < 100 and m2['fs'] == m1['fs'] and -2 <= m2['last'] - m2['content'] <= .5, (mid['wb'], m1['fs'], m2))
        check(f'{tag} errors desktop', not pg.errs, pg.errs)
        ctx.close()

    # A6 shared element
    ctx, pg = page(b)
    to(pg, doc_top(pg, '#travaux') - 60)
    pg.evaluate("document.querySelectorAll('.work-row').forEach(r => r.classList.add('is-in'))"); pg.wait_for_timeout(1200)
    row = pg.locator('.work-row').first; bx = row.bounding_box()
    pg.mouse.move(bx['x'] + bx['width'] * .3, bx['y'] + bx['height'] / 2); pg.wait_for_timeout(900)
    on = pg.evaluate("document.querySelector('.peek').classList.contains('is-on')")
    pg.mouse.down(); pg.mouse.up()
    pg.wait_for_timeout(150)
    mid = pg.evaluate("""(() => ({ active: !!document.activeViewTransition, pseudo: document.getAnimations().filter(a => a.effect && a.effect.pseudoElement && a.effect.pseudoElement.includes('view-transition')).map(a => a.effect.pseudoElement).slice(0, 8), count: window.__vtCount }))()""")
    pg.screenshot(path=SP + 'p10_d_morph150.png')
    pg.wait_for_timeout(200)
    pg.screenshot(path=SP + 'p10_d_morph350.png')
    pg.wait_for_timeout(850)
    end = pg.evaluate("""(() => { const t = document.querySelector('#case-title'), r = t.getBoundingClientRect();
      return { open: document.querySelector('.case').classList.contains('is-open'), hidden: document.querySelector('.case').hidden, hash: location.hash,
        titleVis: r.top >= 0 && r.bottom <= innerHeight && new DOMMatrix(getComputedStyle(t.querySelector('.ln > span')).transform).m42 < .25 * t.querySelector('.ln > span').offsetHeight, isIn: document.querySelector('.case-body').classList.contains('is-in'),
        peekName: document.querySelector('.peek-in').style.viewTransitionName, frameName: getComputedStyle(document.querySelector('.case-media .frame')).viewTransitionName,
        sheetName: getComputedStyle(document.querySelector('.case-sheet')).viewTransitionName, vt: document.documentElement.classList.contains('vt'),
        media: getComputedStyle(document.querySelector('.case-media')).opacity, focus: document.activeElement && document.activeElement.id, active: !!document.activeViewTransition }; })()""")
    pg.screenshot(path=SP + 'p10_d_morph1200.png')
    check('A6 morph in progress at +150 ms', on and (mid['active'] or mid['pseudo']) and mid['count'] == 1, (on, mid))
    check('A6 at +1200 ms: open, #springbreak, title visible, no names left', end['open'] and end['hash'] == '#springbreak' and end['titleVis'] is True and end['isIn'] and end['peekName'] == '' and end['frameName'] == 'none' and end['sheetName'] == 'none' and not end['vt'] and not end['active'] and end['focus'] == 'case-title', end)
    check('A6 no console errors', not pg.errs, pg.errs)
    # close and reopen via morph a second project; then keyboard on row
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1200)
    closed = pg.evaluate("[document.querySelector('.case').hidden, location.hash, document.activeElement.className]")
    # A7 keyboard Enter
    pg.mouse.move(5, 300); pg.wait_for_timeout(300)
    pg.evaluate("window.__vtCount = 0")
    pg.keyboard.press('Tab'); pg.keyboard.press('Shift+Tab')   # clavier : focus-visible sur la ligne
    pg.evaluate("document.querySelectorAll('.work-row')[2].focus()")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(1300)
    k = pg.evaluate("({ c: window.__vtCount, open: document.querySelector('.case').classList.contains('is-open'), hash: location.hash, isIn: document.querySelector('.case-body').classList.contains('is-in') })")
    check('A7 keyboard Enter: opens without view transition', k['c'] == 0 and k['open'] and k['hash'] == '#lezgo' and k['isIn'], (closed, k))
    # arrows inside after morph still work
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(900)
    check('A7b arrow after keyboard open works', pg.evaluate("location.hash") != '#lezgo', pg.evaluate("location.hash"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1100)
    # morph again then ArrowRight during transition, then Escape during transition
    row = pg.locator('.work-row').nth(1); bx = row.bounding_box()
    if bx['y'] < 80 or bx['y'] > 800:
        to(pg, doc_top(pg, '.work-list') - 100); bx = row.bounding_box()
    pg.mouse.move(bx['x'] + bx['width'] * .3, bx['y'] + bx['height'] / 2); pg.wait_for_timeout(900)
    pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(80)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1400)
    esc = pg.evaluate("({ hidden: document.querySelector('.case').hidden, vt: document.documentElement.classList.contains('vt'), noScroll: document.body.classList.contains('no-scroll'), inert: document.querySelector('main').inert, isIn: document.querySelector('.case-body').classList.contains('is-in') })")
    check('A6b Escape during the morph closes cleanly', esc['hidden'] and not esc['vt'] and not esc['noScroll'] and not esc['inert'] and not esc['isIn'], esc)
    # button min-width inside case sheet
    pg.evaluate("document.querySelectorAll('.work-row')[0].focus()"); pg.keyboard.press('Enter'); pg.wait_for_timeout(1300)
    cb = pg.evaluate("(() => { const b = document.querySelector('.case-actions .btn'), s = document.querySelector('.case-site'), l = document.querySelector('.case-share'); return [b.style.minWidth, s.style.minWidth, l.style.minWidth, b.querySelector('.lbl') !== null, b.querySelector('svg.out') !== null]; })()")
    check('A2d case sheet controls locked (btn, site, share) and btn label wrapped', all(x.endswith('px') for x in cb[:3]) and cb[3] and cb[4], cb)
    bxs = pg.locator('.case-site').bounding_box(); base = pg.evaluate("[...document.querySelectorAll('.case-nav > *')].map(e => e.getBoundingClientRect().left)")
    pg.mouse.move(bxs['x'] + 10, bxs['y'] + 10); pg.wait_for_timeout(500)
    now = pg.evaluate("[...document.querySelectorAll('.case-nav > *')].map(e => e.getBoundingClientRect().left)")
    pg.screenshot(path=SP + 'p10_d_casebar_hover.png', clip={'x': 700, 'y': 10, 'width': 740, 'height': 70})
    check('A2e case bar hover: no neighbour shift', max(abs(a - c) for a, c in zip(base, now)) <= .5, (base, now))
    check('errors desktop A6/A7', not pg.errs, pg.errs)
    ctx.close()

    # A6 light theme screenshot of the morph
    ctx, pg = page(b, theme='light')
    to(pg, doc_top(pg, '#travaux') - 60)
    pg.evaluate("document.querySelectorAll('.work-row').forEach(r => r.classList.add('is-in'))"); pg.wait_for_timeout(1200)
    row = pg.locator('.work-row').nth(2); bx = row.bounding_box()
    pg.mouse.move(bx['x'] + bx['width'] * .3, bx['y'] + bx['height'] / 2); pg.wait_for_timeout(900)
    pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(250)
    pg.screenshot(path=SP + 'p10_l_morph250.png')
    pg.wait_for_timeout(1300)
    pg.screenshot(path=SP + 'p10_l_morph_end.png')
    check('light morph: no errors, open', not pg.errs and pg.evaluate("document.querySelector('.case').classList.contains('is-open')"), pg.errs)
    ctx.close()

    # A7 reduced motion
    ctx, pg = page(b, reduce=True)
    to(pg, doc_top(pg, '#travaux') - 60); pg.wait_for_timeout(400)
    row = pg.locator('.work-row').first; bx = row.bounding_box()
    pg.mouse.move(bx['x'] + bx['width'] * .3, bx['y'] + bx['height'] / 2); pg.wait_for_timeout(700)
    pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(600)
    r = pg.evaluate("({ c: window.__vtCount, open: document.querySelector('.case').classList.contains('is-open'), hash: location.hash })")
    check('A7 reduced motion: opens without view transition', r['c'] == 0 and r['open'] and r['hash'] == '#springbreak', r)
    sw = pg.evaluate("[getComputedStyle(document.querySelector('.sec-title')).getPropertyValue('--swd'), getComputedStyle(document.querySelector('.mail-txt')).getPropertyValue('--wb'), getComputedStyle(document.querySelector('.sec-title')).animationName]")
    check('reduced motion: no scroll-driven width', sw[0].strip() == '86' and sw[1].strip() == '100' and sw[2] == 'none', sw)
    check('errors reduced', not pg.errs, pg.errs)
    ctx.close()

    # A5 at 390 + mobile checks
    for theme in ['dark', 'light']:
        tag = 'md' if theme == 'dark' else 'ml'
        ctx, pg = page(b, 390, 844, mobile=True, theme=theme)
        ct = doc_top(pg, '.contact')
        to(pg, ct - 844 * .7); mid = pg.evaluate(MAILP)
        pg.screenshot(path=SP + f'p10_{tag}_mail_entry.png')
        pg.set_viewport_size({'width': 380, 'height': 844}); pg.wait_for_timeout(300)
        pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(300)
        to(pg, pg.evaluate("document.documentElement.scrollHeight - innerHeight")); pg.wait_for_timeout(300)
        m = pg.evaluate(MAILP)
        pg.screenshot(path=SP + f'p10_{tag}_mail_settled.png')
        check(f'{tag} A5 390 refit mid-animation: flush, no overflow', mid['wb'] < 100 and m['wb'] == 100 and -2 <= m['last'] - m['content'] <= .5, (mid['wb'], m))
        to(pg, 0); pg.wait_for_timeout(300)
        pg.screenshot(path=SP + f'p10_{tag}_hero.png')
        mn = pg.evaluate("[...document.querySelectorAll('.btn, .links a, .live a')].map(e => e.style.minWidth)")
        check(f'{tag} mobile min-widths set', all(x.endswith('px') for x in mn), mn)
        # tap a row: touch path, no view transition
        to(pg, doc_top(pg, '#travaux')); pg.wait_for_timeout(1200)
        pg.locator('.work-row').first.tap(); pg.wait_for_timeout(1300)
        r = pg.evaluate("({ c: window.__vtCount || 0, open: document.querySelector('.case').classList.contains('is-open'), hash: location.hash })")
        pg.screenshot(path=SP + f'p10_{tag}_case.png')
        check(f'{tag} touch opens without view transition', r['c'] == 0 and r['open'], r)
        check(f'{tag} errors mobile', not pg.errs, pg.errs)
        ctx.close()
    b.close()
print(f'{sum(res)}/{len(res)} pass'); out.write(f'{sum(res)}/{len(res)} pass\n')
