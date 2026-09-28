"""P3 acceptance : contraste, rayons, échelle mono, notes, thème, clavier, dialog, appui tactile."""
import time, json, sys
sys.stdout.reconfigure(errors='backslashreplace')   # espaces fines et accents : pas de plantage sur une console redirigée
from playwright.sync_api import sync_playwright

OUT = r'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
BASE = 'http://localhost:5178/'
res = []
def check(name, ok, info=''):
    res.append((ok, name, info)); print(('PASS' if ok else 'FAIL'), name, '|', info, flush=True)

def page(b, w=1440, h=900, mobile=False, theme=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append(m.text))
    pg.add_init_script("sessionStorage.setItem('ql-intro','1')")
    if theme: pg.add_init_script(f"localStorage.setItem('ql-theme','{theme}')")
    else: pg.add_init_script("if(!sessionStorage.getItem('keep')) localStorage.removeItem('ql-theme')")
    pg.goto(BASE + '?t=' + str(time.time()), wait_until='load')
    pg.wait_for_selector('html.is-named', state='attached', timeout=10000)
    pg.wait_for_timeout(2200)
    return ctx, pg

CONTRAST_JS = r"""(sels) => {
  const parse = c => { const m = c.match(/[\d.]+/g).map(Number); return { r: m[0], g: m[1], b: m[2], a: m.length > 3 ? m[3] : 1 }; };
  const toRgb = c => {  // couleurs possiblement en oklab/color-mix : passer par un canvas
    const cv = document.createElement('canvas'); cv.width = cv.height = 1; const x = cv.getContext('2d');
    x.clearRect(0,0,1,1); x.fillStyle = c; x.fillRect(0,0,1,1); const d = x.getImageData(0,0,1,1).data;
    return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 };
  };
  const lum = ({r,g,b}) => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126*f(r) + .7152*f(g) + .0722*f(b); };
  const blend = (fg, bg) => ({ r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a), b: fg.b*fg.a + bg.b*(1-fg.a), a: 1 });
  const bgOf = el => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = toRgb(getComputedStyle(e).backgroundColor);
      if (c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let bg = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = layers.length - 1; i >= 0; i--) bg = blend(layers[i], bg);
    return bg;
  };
  const out = {};
  for (const s of sels) {
    const els = [...document.querySelectorAll(s)].filter(e => e.getClientRects().length);
    let min = 99, where = '';
    for (const el of els) {
      const fg = toRgb(getComputedStyle(el).color), bg = bgOf(el);
      const f = blend(fg, bg);
      const L1 = lum(f), L2 = lum(bg);
      const cr = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
      if (cr < min) { min = cr; where = el.className + ' ' + getComputedStyle(el).color; }
    }
    out[s] = [els.length, +min.toFixed(2), where];
  }
  return out;
}"""
SELS = ['.work-head span', '.lab-label', '.kit-title', '.kit-table dt', '.contact-avail', '.cv-meta', '.mail-hint', '.foot-in span', '.case-intro dt', '.case-note', '.sec-note', '.eyebrow']

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    # ---------- 1. contraste, sombre et clair ----------
    for theme in ('dark', 'light'):
        ctx, pg = page(b, theme=theme)
        pg.evaluate("document.querySelector('.work-head').style.display"); # noop
        # fiche avec note (sans lien) pour .case-note et dt
        idx = pg.evaluate("PROJECTS.findIndex(p => !p.link)")
        pg.evaluate(f"document.querySelectorAll('.work-row')[{idx}].scrollIntoView()")
        pg.wait_for_timeout(300)
        pg.locator('.work-row').nth(idx).click()
        pg.wait_for_timeout(1800)
        r = pg.evaluate(CONTRAST_JS, SELS)
        bad = {k: v for k, v in r.items() if v[0] == 0 or v[1] < 4.5}
        check(f'contrast >= 4.5 ({theme})', not bad, json.dumps({k: v[1] for k, v in r.items()}) + (' BAD ' + json.dumps(bad, ensure_ascii=False) if bad else ''))
        lc = pg.evaluate(CONTRAST_JS, ['.lab-code .c', '.lab-code .lab-label', '.meta-clocks i', '.cv-label'])
        print('  info', theme, json.dumps({k: v[1] for k, v in lc.items()}))
        check(f'no errors ({theme})', not pg.errs, str(pg.errs[:3]))
        ctx.close()

    # ---------- 2. rayons ----------
    for w, h in ((1440, 900), (390, 844)):
        ctx, pg = page(b, w, h, mobile=(w < 500))
        r = pg.evaluate("""() => {
          const g = s => { const e = document.querySelector(s); return e ? getComputedStyle(e).borderTopLeftRadius : null; };
          document.querySelector('.work-list').dispatchEvent(new PointerEvent('pointerover', {bubbles: true}));
          return { cv: g('.cv-thumb'), lab: g('.lab'), peek: g('.peek-in'), photo: g('.name-photo'), peekClip: getComputedStyle(document.querySelector('.peek-in')).clipPath, photoClip: getComputedStyle(document.querySelector('.name-photo')).clipPath };
        }""")
        pg.locator('.work-row').first.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
        pg.locator('.work-row').first.click(); pg.wait_for_timeout(1500)
        r2 = pg.evaluate("({ media: getComputedStyle(document.querySelector('.case-media')).borderTopLeftRadius, sheet: getComputedStyle(document.querySelector('.case-sheet')).borderTopLeftRadius, sheetB: getComputedStyle(document.querySelector('.case-sheet')).borderBottomLeftRadius })")
        r.update(r2)
        ph = float(r['photo'].replace('px', ''))
        ok = r['cv'] == r['lab'] == r['peek'] == r['media'] == '12px' and r['sheet'] == '16px' and r['sheetB'] == '0px' and 6 <= ph <= 16
        check(f'radii at {w}', ok, json.dumps(r))
        ctx.close()

    # ---------- 3/4. échelle mono, notes ----------
    for w, h in ((1440, 900), (390, 844)):
        ctx, pg = page(b, w, h, mobile=(w < 500))
        pg.locator('.work-row').first.scroll_into_view_if_needed(); pg.wait_for_timeout(200)
        pg.locator('.work-row').first.click(); pg.wait_for_timeout(1500)
        bad = pg.evaluate("""() => {
          const out = [];
          const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          for (let n; (n = w.nextNode());) {
            if (!n.textContent.trim()) continue;
            const el = n.parentElement;
            if (el.closest('.cover, .ruler, .probe, .grid-overlay, noscript, script')) continue;
            const fs = getComputedStyle(el).fontSize;
            if (fs === '11px' || fs === '11.5px') out.push(el.tagName + '.' + el.className + ' ' + fs);
          }
          // pseudo-éléments hors Inspecter
          return out;
        }""")
        check(f'no 11/11.5px text at {w}', not bad, str(bad[:6]))
        sn = pg.evaluate("[...document.querySelectorAll('.sec-note')].map(e => [getComputedStyle(e).fontFamily.split(',')[0], getComputedStyle(e).fontSize, e.classList.contains('mono')])")
        check(f'.sec-note Anybody >= 16px at {w}', all(f.strip('"') == 'Anybody' and float(s[:-2]) >= 16 and not m for f, s, m in sn), str(sn))
        ctx.close()

    # ---------- 5. thème ----------
    ctx, pg = page(b)
    pg.evaluate("document.querySelector('.lab').scrollIntoView({block: 'center'})")
    pg.wait_for_timeout(1500)
    get = "[getComputedStyle(document.body).backgroundColor, getComputedStyle(document.querySelector('.lab-props')).backgroundColor, document.querySelector('meta[name=theme-color]').content]"
    start = pg.evaluate(get)
    pg.evaluate("sessionStorage.setItem('keep','1')")
    pg.evaluate("document.querySelector('.theme-btn').click()")
    pg.wait_for_timeout(250)
    mid = pg.evaluate(get)
    pg.screenshot(path=OUT + 'p3_theme_mid.png')
    pg.wait_for_timeout(450)
    end = pg.evaluate(get)
    pg.screenshot(path=OUT + 'p3_theme_end.png')
    # E7 : bascule d'un coup (fondu View Transitions de .3 s), plus de couleurs intermédiaires ; finales dès +250 ms
    atomic = mid == end and start[0] != end[0]
    check('theme switches at once (final at +250ms, same at +700)', atomic and end[0] == 'rgb(244, 246, 255)' and end[1] == 'rgb(233, 239, 253)', f'{start} -> {mid} -> {end}')
    check('theme-color light', end[2] == '#f4f6ff', end[2])
    pg.reload(wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached')
    rl = pg.evaluate("[document.documentElement.dataset.theme, document.querySelector('meta[name=theme-color]').content]")
    check('theme-color light after reload', rl == ['light', '#f4f6ff'], str(rl))
    pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelector('.theme-btn').click()"); pg.wait_for_timeout(700)
    d = pg.evaluate("document.querySelector('meta[name=theme-color]').content")
    pg.reload(wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached')
    d2 = pg.evaluate("[document.documentElement.dataset.theme, document.querySelector('meta[name=theme-color]').content]")
    check('theme-color dark, also after reload', d == '#09090b' and d2 == ['dark', '#09090b'], f'{d} {d2}')
    pg.evaluate("localStorage.removeItem('ql-theme'); sessionStorage.removeItem('keep')")
    check('scrollbar-gutter stable', pg.evaluate("getComputedStyle(document.documentElement).scrollbarGutter") == 'stable')
    ctx.close()

    # ---------- 6. clavier ----------
    ctx, pg = page(b)
    pg.keyboard.press('Tab')
    a1 = pg.evaluate("document.activeElement.className")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(1800)
    a2 = pg.evaluate("[document.activeElement.id, location.hash, Math.round(document.querySelector('#travaux').getBoundingClientRect().top)]")
    pg.keyboard.press('Tab')
    a3 = pg.evaluate("document.activeElement === document.querySelector('.work-row')")
    check('skip link -> #travaux focused, next Tab = first .work-row', a1 == 'skip' and a2[0] == 'travaux' and a3, f'{a1} {a2} {a3}')
    pg.wait_for_timeout(700)
    pg.screenshot(path=OUT + 'p3_rowfocus.png')
    fv = pg.evaluate("(() => { const r = document.querySelector('.work-row'); return [getComputedStyle(r, '::before').transform, getComputedStyle(r.querySelector('.ttl')).color, getComputedStyle(r.querySelector('.ttl')).getPropertyValue('--tw')]; })()")
    check('.work-row:focus-visible = hover state', fv[0] == 'matrix(1, 0, 0, 1, 0, 0)' and fv[1] == 'rgb(255, 255, 255)' and fv[2].strip() == '118', str(fv))

    snap = pg.locator('h1').aria_snapshot()
    check('h1 accessible name exactly Quentin Louis', snap.strip() == '- heading "Quentin Louis" [level=1]', repr(snap))
    full = pg.locator('body').aria_snapshot()
    check('no letter-by-letter text in snapshot', '- text: Q' not in full and '"Q"' not in full and 'Bordeaux, 25 ans' not in full, full[:300].replace('\n', ' / '))

    # demo-btn focus
    pg.evaluate("document.querySelector('.lab').scrollIntoView({block:'center'})"); pg.wait_for_timeout(1300)
    pg.evaluate("document.querySelector('.seg button[aria-checked=\"true\"]').focus()")
    pg.keyboard.press('Shift+Tab')   # retour vers la chasse, puis on cherche le demo-btn en avançant
    for _ in range(12):
        pg.keyboard.press('Tab')
        if pg.evaluate("document.activeElement.classList.contains('demo-btn')"): break
    ol = pg.evaluate("(() => { const cs = getComputedStyle(document.activeElement); return [document.activeElement.className, cs.outlineColor, cs.outlineWidth, cs.outlineStyle]; })()")
    check('Tab to .demo-btn: 2px visible outline', ol[0] == 'demo-btn' and ol[2] == '2px' and 'rgba(0, 0, 0, 0)' not in ol[1] and ol[3] == 'solid', str(ol))
    pg.screenshot(path=OUT + 'p3_demofocus.png')

    # seg (P8: 4 states, scoped to the Propriétés seg; the code tabs are a second .seg)
    pg.evaluate("document.querySelector('.lab-props .seg button[aria-checked=\"true\"]').focus()")
    tabbable = pg.evaluate("[...document.querySelectorAll('.lab-props .seg button')].map(b => b.tabIndex)")
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(100)
    s1 = pg.evaluate("[[...document.querySelectorAll('.lab-props .seg button')].map(b => b.getAttribute('aria-checked')), document.activeElement.dataset.state, [...document.querySelectorAll('.lab-props .seg button')].map(b => b.tabIndex), document.querySelector('.demo-btn').className]")
    pg.keyboard.press('ArrowLeft'); pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(100)
    s2 = pg.evaluate("document.activeElement.dataset.state")
    check('.seg roving tabindex + arrows', tabbable == [0, -1, -1, -1] and s1[0] == ['false', 'true', 'false', 'false'] and s1[1] == 'hover' and s1[2] == [-1, 0, -1, -1] and 'is-hover' in s1[3] and s2 == 'disabled', f'{tabbable} {s1} wrap->{s2}')
    pg.evaluate("document.querySelector('.seg button').click()")
    # ranges
    vt = pg.evaluate("[...document.querySelectorAll('[data-token]')].map(i => i.getAttribute('aria-valuetext'))")
    oh = pg.evaluate("[...document.querySelectorAll('.field output')].every(o => o.getAttribute('aria-hidden') === 'true')")
    pg.evaluate("(() => { const i = document.querySelector('[data-token=radius]'); i.value = 20; i.dispatchEvent(new Event('input')); })()")
    vt2 = pg.evaluate("document.querySelector('[data-token=radius]').getAttribute('aria-valuetext')")
    check('range aria-valuetext + output aria-hidden', vt == ['10 px', '26 px', '650', '100 %'] and oh and vt2 == '20 px', f'{vt} {oh} {vt2}')
    mail = pg.evaluate("document.querySelector('.mail').getAttribute('aria-label')")
    check('.mail aria-label', mail == 'Écrivez-moi\u202f: copier l’adresse quentinlouis97400@gmail.com', mail)

    # nav link -> focus + hash
    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(600)
    pg.locator('.nav a[href="#methode"]').click(); pg.wait_for_timeout(1800)
    nv = pg.evaluate("[document.activeElement.id, location.hash]")
    pg.locator('.brand').click(); pg.wait_for_timeout(1800)
    nt = pg.evaluate("[document.activeElement.tagName, location.hash, Math.round(scrollY)]")
    check('nav link focuses section + hash; brand -> main, clean URL', nv == ['methode', '#methode'] and nt == ['MAIN', '', 0], f'{nv} {nt}')
    check('no errors (keyboard run)', not pg.errs, str(pg.errs[:3]))
    ctx.close()

    # ---------- 7. dialog ----------
    ctx, pg = page(b)
    pg.locator('.work-row').first.scroll_into_view_if_needed(); pg.wait_for_timeout(1300)
    pg.locator('.work-row').nth(0).click(); pg.wait_for_timeout(1200)
    op = pg.evaluate("[document.activeElement.id, document.querySelector('main').inert, document.querySelector('.topbar').inert, document.querySelector('.dock').inert, document.querySelector('.skip').inert, document.querySelector('.foot').inert]")
    pg.keyboard.press('Tab')
    t1 = pg.evaluate("document.activeElement.closest('.case-bar') !== null")
    check('case: focus on #case-title, background inert, Tab -> bar', op == ['case-title', True, True, True, True, True] and t1, f'{op} {t1}')
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(150)
    pg.locator('.work-row').nth(1).click(timeout=2000)
    pg.wait_for_timeout(1200)
    st = pg.evaluate("[document.querySelector('.case').hidden, document.querySelector('.case').classList.contains('is-open'), document.body.classList.contains('no-scroll'), document.querySelector('main').inert, document.querySelector('#case-title').textContent]")
    check('case race: reopened and stays open', st[:4] == [False, True, True, True], str(st))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1200)
    cl = pg.evaluate("[document.querySelector('.case').hidden, document.querySelector('main').inert, document.activeElement.className]")
    check('case closed: hidden, main not inert, focus back on row', cl[0] is True and cl[1] is False and 'work-row' in cl[2], str(cl))
    # course via bouton précédent/suivant puis next : focus garde
    pg.locator('.work-row').nth(2).click(); pg.wait_for_timeout(1200)
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(200)
    fx = pg.evaluate("document.activeElement.id")
    check('ArrowRight in case: focus back on new title', fx == 'case-title', fx)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1200)
    # rapidité : fermer/rouvrir en boucle
    for k in range(3):
        pg.locator('.work-row').nth(k).click(); pg.wait_for_timeout(120); pg.keyboard.press('Escape'); pg.wait_for_timeout(120)
    pg.wait_for_timeout(1300)
    st2 = pg.evaluate("[document.querySelector('.case').hidden, document.querySelector('main').inert, document.body.classList.contains('no-scroll')]")
    check('case: rapid open/close leaves page usable', st2 == [True, False, False], str(st2))
    check('no errors (dialog run)', not pg.errs, str(pg.errs[:3]))
    ctx.close()

    # ---------- 8. mobile tap ----------
    ctx, pg = page(b, 390, 844, mobile=True)
    hv = pg.evaluate("[matchMedia('(hover: none)').matches, matchMedia('(hover: hover)').matches]")
    btn = pg.locator('.cta-row .btn--accent')
    btn.tap()
    pg.wait_for_timeout(600)
    pg.evaluate("window.__lenis ? __lenis.scrollTo(0, {immediate: true}) : scrollTo(0, 0)")
    pg.wait_for_timeout(100)
    tr = pg.evaluate("(() => { const b = document.querySelector('.cta-row .btn--accent'); return [getComputedStyle(b, '::before').transform, getComputedStyle(b).color, getComputedStyle(b).backgroundColor, getComputedStyle(b).scale]; })()")
    btn.screenshot(path=OUT + 'p3_tap_btn.png')
    check('mobile tap: button at rest (no white fill)', tr[0] != 'none' and tr[0] != 'matrix(1, 0, 0, 1, 0, 0)' and tr[1] == 'rgb(255, 255, 255)', f'hover media {hv} {tr}')
    check('mobile no errors', not pg.errs, str(pg.errs[:3]))
    ctx.close()
    b.close()

fails = [r for r in res if not r[0]]
print(f'\n{len(res) - len(fails)}/{len(res)} pass')
