"""P8 acceptance tests (Méthode lab). python p8test.py [shots]"""
import sys, time, json, re
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée

BASE = 'http://localhost:5178/'
SC = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
SHOTS = 'shots' in sys.argv
Q = '?t=p8' + str(int(time.time()))
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

def to_lab(pg):
    pg.evaluate("document.querySelector('.lab').scrollIntoView({ block: 'center' })")
    pg.wait_for_timeout(1400)

def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = [ch(x) for x in c[:3]]
    return .2126 * r + .7152 * g + .0722 * b

def ratio(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + .05) / (y + .05)

def rgb(s):
    return [float(v) for v in re.findall(r'[\d.]+', s)][:4]

PRE = "document.querySelector('#lab-out').textContent"
def tab(pg, fmt):
    pg.click(f'.seg--tabs [data-fmt="{fmt}"]'); pg.wait_for_timeout(50)
    return pg.evaluate(PRE)
def set_range(pg, k, v):
    pg.evaluate(f"(() => {{ const i = document.querySelector('[data-token=\"{k}\"]'); i.value = {v}; i.dispatchEvent(new Event('input', {{ bubbles: true }})); }})()")

def independent(pg):
    """ratio from the demo button's computed colours (after transitions), stage bg when transparent"""
    pg.wait_for_timeout(500)
    d = pg.evaluate("""(() => { const cs = getComputedStyle(document.querySelector('.demo-btn'));
      return [cs.backgroundColor, cs.color, getComputedStyle(document.querySelector('.lab-stage')).backgroundColor,
              document.querySelector('.contrast').textContent]; })()""")
    bg = rgb(d[0])
    if len(bg) == 4 and bg[3] == 0: bg = rgb(d[2])
    return ratio(bg, rgb(d[1])), d[3], d

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    for theme in (None, 'light'):
        tn = theme or 'dark'
        ctx, pg = page(b, 1440, 900, theme=theme)
        load(pg); to_lab(pg)

        # A1 JSON parses
        t = tab(pg, 'json')
        try:
            o = json.loads(t); ok = o['button']['primary']['radius']['$value'] == '10px'
        except Exception as e:
            ok, o = False, str(e)
        check(f'[{tn}] A1 JSON tab parses, radius $value 10px', ok, t[:80].replace('\n', ' '))
        check(f'[{tn}] A1b JSON background alias {{color.ink}} by default', ok and o['button']['primary']['background']['$value'] == '{color.ink}')

        # A2 radius 20 in every tab
        set_range(pg, 'radius', 20)
        flash = pg.evaluate("[...document.querySelectorAll('#lab-out b.flash')].map(b => b.textContent)")
        css, js, tw = tab(pg, 'css'), tab(pg, 'json'), tab(pg, 'tw')
        check(f'[{tn}] A2 Rayon 20: CSS 20px, JSON 20px, Tailwind rounded-[20px]', '--radius: 20px' in css and '"$value": "20px"' in js and 'rounded-[20px]' in tw, f'flash(json)={flash}')
        set_range(pg, 'padx', 40)
        fl = pg.evaluate("[...document.querySelectorAll('#lab-out b.flash')].map(b => b.textContent)")
        check(f'[{tn}] A2b changed value flashes in the active tab (Tailwind)', fl == ['40px'], fl)

        # A3 copy Tailwind
        pg.click('.lab-copy'); pg.wait_for_timeout(250)
        clip = pg.evaluate('navigator.clipboard.readText()')
        lbl = pg.evaluate("[document.querySelector('.lab-copy-lbl').textContent, document.querySelector('.lab-copy').className, document.querySelector('.lab-copy + [aria-live]').textContent]")
        if SHOTS: pg.locator('.lab').screenshot(path=SC + f'p8_lab_copied_{tn}.png')
        check(f'[{tn}] A3 Copier on Tailwind: clipboard starts with @theme {{, label Copié', clip.startswith('@theme {') and lbl[0] == 'Copié' and 'is-done' in lbl[1], [clip[:40], lbl])
        pg.wait_for_timeout(1600)
        lbl2 = pg.evaluate("document.querySelector('.lab-copy-lbl').textContent")
        check(f'[{tn}] A3b label back to Copier after 1.6 s', lbl2 == 'Copier', lbl2)
        check(f'[{tn}] A3c copied text equals the panel plain text (no HTML)', clip.replace('\r\n', '\n') == pg.evaluate(PRE) and '<b>' not in clip and 'flash' not in clip)

        # A4 contrast readout
        tab(pg, 'css')
        r, txt, d = independent(pg)
        m = re.match(r'^Contraste (\d+),(\d):1 · AA', txt)
        shown = float(f'{m.group(1)}.{m.group(2)}') if m else -1
        check(f'[{tn}] A4 default readout /^Contraste d,d:1 · AA/ equals independent ratio ±0.1', bool(m) and abs(shown - r) <= .1, f'{txt} vs {r:.3f} {d[:2]}')
        pg.click('.swatches [data-fill="accent"]')
        r, txt, d = independent(pg)
        check(f'[{tn}] A4b Bleu: readout ~6,9:1 and matches', txt.startswith('Contraste 6,9:1 · AA') and abs(r - 6.9) < .1, f'{txt} {r:.3f} {d[:2]}')
        check(f'[{tn}] A4c Bleu: CSS background var(--accent), text #fff; Tailwind bg-accent text-white', 'background: var(--accent)' in pg.evaluate(PRE) and 'color: #fff' in pg.evaluate(PRE) and 'bg-accent text-white' in tab(pg, 'tw'))
        tab(pg, 'css')
        for f in ('navy', 'outline'):
            if pg.is_hidden(f'.swatches [data-fill="{f}"]'): continue   # C4 : Marine masquée en clair (= Encre)
            pg.click(f'.swatches [data-fill="{f}"]')
            r, txt, d = independent(pg)
            m = re.match(r'^Contraste (\d+),(\d):1', txt)
            check(f'[{tn}] A4d {f}: readout matches independent ratio', bool(m) and abs(float(f'{m.group(1)}.{m.group(2)}') - r) <= .1, f'{txt} {r:.2f} {d[:3]}')
        out = pg.evaluate(PRE)
        check(f'[{tn}] A4e Contour: transparent + border currentColor in CSS, JSON transparent, Tailwind border-current',
              'background: transparent' in out and 'border: 1px solid currentColor' in out and '"transparent"' in tab(pg, 'json') and 'bg-transparent border border-current' in tab(pg, 'tw'))
        tab(pg, 'css')
        # ring over the selected swatch, seg indicator over the checked state
        geo = pg.evaluate("""(() => { const c = e => { const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
          return [c(document.querySelector('.sw-ring')), c(document.querySelector('.swatches [aria-checked=true]'))]; })()""")
        check(f'[{tn}] ring centred on the selected swatch', abs(geo[0][0] - geo[1][0]) < 1 and abs(geo[0][1] - geo[1][1]) < 1, geo)
        # low contrast chip path: force a weak ink on Contour
        pg.evaluate("document.documentElement.style.setProperty('--ink', getComputedStyle(document.documentElement).getPropertyValue('--paper-3'))")
        pg.click('.swatches [data-fill="ink"]'); pg.click('.swatches [data-fill="outline"]'); pg.wait_for_timeout(100)
        chip = pg.evaluate("[document.querySelector('.contrast').textContent, !!document.querySelector('.contrast .contrast-fail')]")
        pg.evaluate("document.documentElement.style.removeProperty('--ink')")
        check(f'[{tn}] A4f below 4.5: chip Insuffisant (AA 4,5:1)', chip[1] and chip[0].endswith('Insuffisant (AA 4,5:1)'), chip)
        pg.click('.swatches [data-fill="ink"]')

        # A5 Focus state
        pg.click('.lab-props .seg [data-state="focus"]'); pg.wait_for_timeout(100)
        f = pg.evaluate("(() => { const cs = getComputedStyle(document.querySelector('.demo-btn')); return [cs.outlineWidth, cs.outlineStyle, cs.outlineOffset]; })()")
        check(f'[{tn}] A5 Focus: outline 2px solid, offset 3px, code :focus-visible', f == ['2px', 'solid', '3px'] and ':focus-visible' in pg.evaluate(PRE), f)
        ind = pg.evaluate("""(() => { const i = document.querySelector('.lab-props .seg-ind').getBoundingClientRect(), b = document.querySelector('.lab-props .seg [aria-checked=true]').getBoundingClientRect();
          return [Math.round(i.left), Math.round(b.left), Math.round(i.width), Math.round(b.width)]; })()""")
        pg.wait_for_timeout(600)
        ind = pg.evaluate("""(() => { const i = document.querySelector('.lab-props .seg-ind').getBoundingClientRect(), b = document.querySelector('.lab-props .seg [aria-checked=true]').getBoundingClientRect();
          return [i.left, b.left, i.width, b.width]; })()""")
        check(f'[{tn}] state indicator (4 options) sits on the checked one', abs(ind[0] - ind[1]) < 1.5 and abs(ind[2] - ind[3]) < 1.5, ind)
        pg.click('.lab-props .seg [data-state="hover"]')
        r, txt, d = independent(pg)
        check(f'[{tn}] Survol: readout follows hover colours (6,9)', txt.startswith('Contraste 6,9:1'), txt)
        if SHOTS and tn == 'dark':
            pg.click('.lab-props .seg [data-state="focus"]'); pg.click('.swatches [data-fill="accent"]'); tab(pg, 'json'); pg.wait_for_timeout(900)
            pg.locator('.lab').screenshot(path=SC + f'p8_lab_json_{tn}.png')
            tab(pg, 'tw'); pg.wait_for_timeout(900)
            pg.locator('.lab').screenshot(path=SC + f'p8_lab_tw_{tn}.png')
            tab(pg, 'css')

        # A6 reset
        for k, v in (('radius', 30), ('padx', 44), ('weight', 350), ('wdth', 130)): set_range(pg, k, v)
        pg.locator('.swatches [data-fill="navy"]:not([hidden]), .swatches [data-fill="outline"]').first.click()   # C4
        t0 = time.time(); pg.click('.lab-reset')
        mid = pg.evaluate("new Promise(r => setTimeout(() => r([...document.querySelectorAll('[data-token]')].map(i => +i.value)), 150))")
        pg.wait_for_timeout(450)
        v = pg.evaluate("[[...document.querySelectorAll('[data-token]')].map(i => +i.value), document.querySelector('.swatches [aria-checked=true]').dataset.fill, document.querySelector('.lab-props .seg [aria-checked=true]').dataset.state, getComputedStyle(document.querySelector('.demo-btn')).getPropertyValue('--radius')]")
        check(f'[{tn}] A6 Réinitialiser: sliders 10/26/650/100 within 600 ms, fill ink, state default', v[0] == [10, 26, 650, 100] and v[1] == 'ink' and v[2] == 'default' and v[3].strip() == '10px', f'mid={mid} end={v}')
        check(f'[{tn}] A6b reset is tweened (mid values in between)', mid != [30, 44, 350, 130] and mid != [10, 26, 650, 100], mid)
        outs = pg.evaluate("[...document.querySelectorAll('.field output')].map(o => o.textContent)")
        check(f'[{tn}] outputs and code follow the reset', outs == ['10', '26', '650', '100'] and '--radius: 10px' in pg.evaluate(PRE), outs)

        # A7 grid alignment
        if tn == 'dark':
            g = pg.evaluate("""(() => { const h = document.querySelector('.method .sec-head').getBoundingClientRect(); const gap = parseFloat(getComputedStyle(document.querySelector('.method .sec-head')).columnGap);
              const c = (h.width - 11 * gap) / 12; const p = [...document.querySelectorAll('.lab-panel')].map(e => e.getBoundingClientRect().left);
              return [h.left + 3 * (c + gap), p[1], h.left + 8 * (c + gap), p[2]]; })()""")
            check('A7 1440: panel 2 at column 4 (±2), panel 3 at column 9 (±2)', abs(g[0] - g[1]) <= 2 and abs(g[2] - g[3]) <= 2, [round(x, 1) for x in g])
            det = pg.evaluate("[document.querySelector('.lab-details').open, getComputedStyle(document.querySelector('.lab-details > summary')).display, getComputedStyle(document.querySelector('#lab-out')).maxHeight, document.querySelector('#lab-out').hasAttribute('data-lenis-prevent')]")
            check('desktop: code open, summary hidden, pre max-height 260px, data-lenis-prevent', det == [True, 'none', '260px', True], det)

        # A9 contexts
        cx = pg.evaluate("[document.querySelectorAll('.steps').length, document.querySelectorAll('.contexts li').length, [...document.querySelectorAll('.contexts button')].map(b => b.textContent.trim())]")
        check(f'[{tn}] A9 no .steps, 3 .contexts rows', cx[0] == 0 and cx[1] == 3, cx)
        pg.evaluate("document.querySelector('.contexts').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(1500)
        if SHOTS: pg.screenshot(path=SC + f'p8_ctx_d_{tn}.png')
        pg.click('.contexts [data-case="wei"]'); pg.wait_for_timeout(900)
        h = pg.evaluate('[location.hash, document.querySelector("#case-title").textContent]')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
        fb = pg.evaluate("document.activeElement.dataset.case || document.activeElement.className")
        check(f'[{tn}] A9b WEI & GO opens #wei, Esc returns focus to its button', h[0] == '#wei' and fb == 'wei', [h, fb])
        rows = pg.evaluate("""(() => { const h = document.querySelector('.method .sec-head').getBoundingClientRect(); const gap = parseFloat(getComputedStyle(document.querySelector('.method .sec-head')).columnGap);
          const c = (h.width - 11 * gap) / 12; const li = document.querySelector('.contexts li'); const s = li.children;
          return [Math.round(s[0].getBoundingClientRect().left - h.left), Math.round(s[1].getBoundingClientRect().left - (h.left + 2 * (c + gap))), Math.round(h.right - s[2].getBoundingClientRect().right), getComputedStyle(s[1]).fontSize, getComputedStyle(document.querySelector('.method-note')).fontSize]; })()""")
        if tn == 'dark': check('contexts row: label col 1, sentence col 3, button flush right; 19px; note 18.72px at 1440', rows[:3] == [0, 0, 0] and rows[3] == '19px', rows)

        # A10 keyboard
        pg.evaluate("document.querySelector('.lab-reset').focus()")
        hits, seen = 0, []
        for _ in range(16):
            pg.keyboard.press('Tab')
            a = pg.evaluate("[document.activeElement.getAttribute('role'), document.activeElement.className, document.activeElement.textContent.trim().slice(0, 12)]")
            seen.append(a[0] or a[1] or a[2])
            if a[0] == 'tab': hits += 1
        check(f'[{tn}] A10 Tab reaches the tablist once', hits == 1, seen)
        pg.focus('.seg--tabs [aria-selected=true]'); pg.keyboard.press('ArrowRight')
        k = pg.evaluate("[document.activeElement.dataset.fmt, document.activeElement.getAttribute('aria-selected'), document.querySelector('#lab-out').getAttribute('aria-labelledby'), [...document.querySelectorAll('.seg--tabs button')].map(b => b.tabIndex)]")
        check(f'[{tn}] A10b ArrowRight switches to JSON, focus follows, roving tabindex', k[:3] == ['json', 'true', 'tab-json'] and k[3] == [-1, 0, -1] and pg.evaluate(PRE).lstrip().startswith('{'), k)
        pg.keyboard.press('ArrowLeft'); pg.keyboard.press('ArrowLeft')
        check(f'[{tn}] A10c ArrowLeft wraps to Tailwind', pg.evaluate("document.activeElement.dataset.fmt") == 'tw')

        if SHOTS:
            tab(pg, 'css'); to_lab(pg)
            pg.locator('.method .wrap').screenshot(path=SC + f'p8_method_d_{tn}.png')
        check(f'[{tn}] desktop: zero console/page errors', not pg.errs, pg.errs)
        ctx.close()

    # theme toggle: text colour and readout re-read after the change
    ctx, pg = page(b, 1440, 900)
    load(pg); to_lab(pg)
    before = pg.evaluate("[document.querySelector('.contrast').textContent, document.querySelector('.demo-btn').style.getPropertyValue('--fg')]")
    pg.click('.theme-btn'); pg.wait_for_timeout(1000)
    r, txt, d = independent(pg)
    after = [txt, pg.evaluate("document.querySelector('.demo-btn').style.getPropertyValue('--fg')")]
    m = re.match(r'^Contraste (\d+),(\d):1', txt)
    check('theme toggle: readout recomputed and matches the new colours', bool(m) and abs(float(f'{m.group(1)}.{m.group(2)}') - r) <= .1, [before, after])
    check('theme toggle: no errors', not pg.errs, pg.errs)
    ctx.close()

    # mobile 390x844
    for theme in (None, 'light'):
        tn = theme or 'dark'
        ctx, pg = page(b, 390, 844, mobile=True, theme=theme)
        load(pg); pg.wait_for_timeout(300)
        det = pg.evaluate("[document.querySelector('.lab-details').open, getComputedStyle(document.querySelector('.lab-details > summary')).display, document.querySelector('.lab-details > summary').textContent]")
        check(f'[{tn}] mobile: code folded behind « Voir le code généré »', det == [False, 'flex', 'Voir le code généré'], det)
        order = pg.evaluate("[...document.querySelectorAll('.lab-panel')].map(e => [e.className.split(' ')[1], Math.round(e.getBoundingClientRect().top)]).sort((a, b) => a[1] - b[1]).map(a => a[0])")
        check(f'[{tn}] mobile order: Canvas, Propriétés, Code', order == ['lab-stage', 'lab-props', 'lab-code'], order)
        for how in ('center', 'playwright', 'start'):
            if how == 'playwright':
                pg.evaluate('scrollTo(0, 0)'); pg.wait_for_timeout(300)
                pg.locator('[data-token="radius"]').scroll_into_view_if_needed()
            else:
                pg.evaluate(f"document.querySelector('[data-token=\"radius\"]').scrollIntoView({{ block: '{how}' }})")
            pg.wait_for_timeout(1300)
            v = pg.evaluate("""(() => { const d = document.querySelector('.demo-btn').getBoundingClientRect(), s = document.querySelector('[data-token="radius"]').getBoundingClientRect();
              const hit = document.elementFromPoint(s.left + s.width / 2, s.top + s.height / 2);
              return [d.top, d.bottom, d.left, d.right, s.top, s.bottom, hit && hit.dataset.token, innerHeight, innerWidth]; })()""")
            ok = v[0] >= 0 and v[1] <= v[7] and v[2] >= 0 and v[3] <= v[8] and v[4] >= 0 and v[5] <= v[7] and v[6] == 'radius'
            check(f'[{tn}] A8 390x844 ({how}): Rayon slider visible and hittable, .demo-btn fully in viewport', ok, [round(x) if isinstance(x, float) else x for x in v])
            if SHOTS and how == 'center': pg.screenshot(path=SC + f'p8_m_sticky_{tn}.png')
        # drag the slider with a finger: button changes while visible
        s = pg.evaluate("(() => { const r = document.querySelector('[data-token=\"radius\"]').getBoundingClientRect(); return [r.left, r.top + r.height / 2, r.width]; })()")
        pg.touchscreen.tap(s[0] + s[2] * .9, s[1]); pg.wait_for_timeout(200)
        rv = pg.evaluate("+document.querySelector('[data-token=\"radius\"]').value")
        check(f'[{tn}] mobile tap on the Rayon track sets a high value', rv > 20, rv)
        co = pg.evaluate("""(() => { const q = s => getComputedStyle(document.querySelector(s));
          return [q('[data-token=radius]').height, q('.lab-props .seg button').minHeight, q('.lab-props .seg button').fontSize, document.querySelector('.swatches button').getBoundingClientRect().width,
                  document.querySelector('.lab-stage').getBoundingClientRect().height]; })()""")
        check(f'[{tn}] coarse: range 44px, seg 40px min / 12px, swatch 32px, stage >= 168px', co[0] == '44px' and co[1] == '40px' and co[2] == '12px' and co[3] == 32 and co[4] >= 168, co)
        pg.tap('.lab-details > summary'); pg.wait_for_timeout(300)
        op = pg.evaluate("[document.querySelector('.lab-details').open, document.querySelector('#lab-out').getBoundingClientRect().height]")
        check(f'[{tn}] mobile: tapping the summary opens the code', op[0] and op[1] > 100, op)
        if SHOTS:
            pg.evaluate("document.querySelector('.lab-code').scrollIntoView({ block: 'end' })"); pg.wait_for_timeout(1300)
            pg.screenshot(path=SC + f'p8_m_code_{tn}.png')
            pg.evaluate("document.querySelector('.contexts').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(1500)
            pg.screenshot(path=SC + f'p8_m_ctx_{tn}.png')
        pg.evaluate("document.querySelector('.contexts').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(1200)
        pg.tap('.contexts [data-case="poulettes"]'); pg.wait_for_timeout(900)
        hh = pg.evaluate('location.hash')
        check(f'[{tn}] mobile: Rôtisserie Poulettes opens #poulettes', hh == '#poulettes', hh)
        check(f'[{tn}] mobile: zero console/page errors', not pg.errs, pg.errs)
        ctx.close()

    # visible copy rules in the method section
    ctx, pg = page(b, 1440, 900)
    load(pg)
    t = pg.evaluate("document.querySelector('.method').innerText")
    check('method copy: no React, no em dash, U+202F before colons, Next.js/Lovable/WordPress present',
          'React' not in t and '\u2014' not in t and ' :' not in t.replace('\u202f:', '') and 'WordPress, Lovable ou Next.js' in t, [l for l in t.split('\n') if ' :' in l][:3])
    ctx.close()
    b.close()

print(f'\n{sum(res)}/{len(res)} passed')
