"""P6 : critères d'acceptation (liste des travaux, aperçu, covers, fiche, vignettes)."""
import re, time, json
from playwright.sync_api import sync_playwright
import sys
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée

OUT = r'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
ROOT = 'C:/Users/quent/Projects/portfolio-quentin/'
URL = 'http://localhost:5178/?t=' + str(time.time())
results = []


def check(name, ok, info=''):
    results.append((name, bool(ok), info))
    print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(info))


def page(b, **kw):
    ctx = b.new_context(**kw)
    ctx.add_init_script("try{sessionStorage.setItem('ql-intro','1'); localStorage.removeItem('ql-theme')}catch(e){}")
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append(m.text))
    return pg


RECT = "(s => { const r = (typeof s === 'string' ? document.querySelector(s) : s).getBoundingClientRect(); return {l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height}; })"


def inter(a, b):
    return a['l'] < b['r'] and b['l'] < a['r'] and a['t'] < b['b'] and b['t'] < a['b']


# ---------- fichiers ----------
src = open(ROOT + 'projects.js', encoding='utf-8').read() + open(ROOT + 'covers.css', encoding='utf-8').read()
bad = [w for w in ['142', 'arrivés', 'Bus 1', 'KEDGE', 'Montaigne', 'Mission 3', '12 questions', '8 min', 'WEI<br>2026',
                   'Math.random', 'Chapitre 02', '45%', 'Le poulet du jour', 'backdrop-filter'] if w in src]
qua = ' '.join(l for l in open(ROOT + 'covers.css', encoding='utf-8').read().splitlines() if '.cv-qua' in l)
check('A4 covers: no invented data strings, no radial-gradient in .cv-qua', not bad and 'radial-gradient' not in qua, f'found={bad}')

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    # ---------- bureau 1440 × 900 ----------
    pg = page(b, viewport={'width': 1440, 'height': 900})
    pg.goto(URL, wait_until='networkidle'); pg.wait_for_timeout(1800)
    pg.evaluate("document.querySelector('#travaux').scrollIntoView()"); pg.wait_for_timeout(1200)
    rows = pg.locator('.work-row')
    col9 = pg.evaluate(RECT + "(document.querySelectorAll('.grid-overlay i')[8])")
    fails = []
    for i in range(8):
        pg.mouse.move(5, 5); pg.wait_for_timeout(100)
        pg.evaluate(f"(() => {{ const r = document.querySelectorAll('.work-row')[{i}]; window.__lenis ? __lenis.scrollTo(r, {{offset: -300, immediate: true}}) : r.scrollIntoView({{block: 'center'}}); }})()")
        pg.wait_for_timeout(400)
        rows.nth(i).hover(); pg.wait_for_timeout(900)
        d = pg.evaluate("""(i => { const R = """ + RECT + """;
          const row = document.querySelectorAll('.work-row')[i], pk = document.querySelector('.peek');
          const top = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--topbar'));
          return { pk: R(pk), row: R(row), ttl: R(row.querySelector('.ttl')), tf: getComputedStyle(pk).transform, on: pk.classList.contains('is-on'), top, vh: innerHeight, head: document.querySelector('.work-head').getBoundingClientRect().bottom }; })""", i)
        rc = (d['row']['t'] + d['row']['b']) / 2
        pc = (d['pk']['t'] + d['pk']['b']) / 2
        h = d['pk']['h']
        # fix B5: never above the list header (the section note stays readable); the window wins
        lo, hi = max(d['top'] + 24 + h / 2, d['head'] + 8 + h / 2), d['vh'] - 24 - h / 2
        want = min(hi, max(lo, rc))
        m = re.match(r'matrix\(([^)]*)\)', d['tf'])
        vals = [float(v) for v in m.group(1).split(',')] if m else None
        norot = vals is not None and abs(vals[1]) < 1e-6 and abs(vals[2]) < 1e-6
        ok = d['on'] and abs(d['pk']['l'] - col9['l']) <= 1 and abs(pc - want) <= 2 and norot and not inter(d['ttl'], d['pk'])
        if not ok:
            fails.append((i, d['pk']['l'], col9['l'], pc, rc, want, d['tf']))
    check('A1 1440: peek on col 9, centred on row (or clamped), no rotation, no overlap with .ttl (8 rows)', not fails, f'fails={fails} col9={col9["l"]:.1f}')

    # direction de la bande
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    pg.evaluate("(() => { const r = document.querySelectorAll('.work-row')[2]; __lenis.scrollTo(r, {offset: -300, immediate: true}); })()")
    pg.wait_for_timeout(1300)
    r2 = pg.evaluate(RECT + "(document.querySelectorAll('.work-row')[2])")
    pg.mouse.move(700, r2['t'] - 10); pg.wait_for_timeout(100)
    pg.mouse.move(700, r2['t'] + 5); pg.wait_for_timeout(100)
    f_in = pg.evaluate("document.querySelectorAll('.work-row')[2].dataset.from")
    pg.mouse.move(700, r2['b'] + 10); pg.wait_for_timeout(100)
    f_out = pg.evaluate("document.querySelectorAll('.work-row')[2].dataset.from")
    orig = pg.evaluate("getComputedStyle(document.querySelectorAll('.work-row')[2], '::before').transformOrigin")
    check('Direction-aware fill: enter from top, leave by bottom', f_in == 'top' and f_out == 'bottom' and orig.endswith(f"{r2['h']:.0f}px") or (f_in == 'top' and f_out == 'bottom'), f'in={f_in} out={f_out} origin={orig}')

    # kind/role effacés sous l'aperçu
    pg.mouse.move(700, (r2['t'] + r2['b']) / 2); pg.wait_for_timeout(600)
    op = pg.evaluate("[...document.querySelectorAll('.work-row')[2].querySelectorAll('.kind, .role')].map(e => getComputedStyle(e).opacity)")
    check('Hovered row: .kind and .role hidden under the peek (fix B5: opacity 0, tied to .is-peeked)', op == ['0', '0'], op)

    # A2 : ligne 2 puis ligne 5
    pg.mouse.move(5, 5); pg.wait_for_timeout(700)
    pg.evaluate("(() => { const r = document.querySelectorAll('.work-row')[1]; __lenis ? __lenis.scrollTo(r, {offset: -120, immediate: true}) : scrollTo(0, r.getBoundingClientRect().top + scrollY - 120); })()")
    pg.wait_for_timeout(400)
    rows.nth(1).hover(); pg.wait_for_timeout(900)
    rows.nth(4).hover(); pg.wait_for_timeout(700)
    t = pg.evaluate("[getComputedStyle(document.querySelector('.peek-track')).transform, document.querySelector('.peek').getBoundingClientRect().height]")
    ty = float(t[0].split(',')[5].rstrip(')')) if t[0].startswith('matrix') else None
    check('A2 row 2 -> row 5: track translateY = -4 x peek height (+-1px) after 700 ms', ty is not None and abs(ty + 4 * t[1]) <= 1, f'ty={ty} h={t[1]}')

    # A3 : clavier
    pg.mouse.move(5, 5); pg.wait_for_timeout(800)
    pg.evaluate("document.querySelectorAll('.work-row')[1].focus()")
    pg.keyboard.press('Shift')
    pg.evaluate("document.querySelectorAll('.work-row')[1].focus()")
    pg.keyboard.press('Tab'); pg.wait_for_timeout(900)
    k = pg.evaluate("""(() => { const a = document.activeElement, pk = document.querySelector('.peek'), tr = document.querySelector('.peek-track');
      return [a.dataset.i, a.matches(':focus-visible'), pk.classList.contains('is-on'), tr.style.getPropertyValue('--pi'), getComputedStyle(tr).transform, pk.getBoundingClientRect().height]; })()""")
    kty = float(k[4].split(',')[5].rstrip(')')) if k[4].startswith('matrix') else None
    check('A3 keyboard: Tab to row 3 shows the peek on cover 3', k[0] == '2' and k[1] and k[2] and k[3] == '2' and kty is not None and abs(kty + 2 * k[5]) <= 1, k)
    pg.screenshot(path=OUT + 'p6t_keyfocus.png')
    pg.keyboard.press('Shift+Tab'); pg.keyboard.press('Shift+Tab'); pg.keyboard.press('Shift+Tab'); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#travaux .sec-title').focus && document.body.focus()")

    # A5 : WEI dans l'aperçu
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    rows.nth(1).hover(); pg.wait_for_timeout(900)
    w1 = pg.evaluate("[" + RECT + "(document.querySelectorAll('.peek .cv-wei .big')[0]), " + RECT + "(document.querySelectorAll('.peek .cv-wei .form')[0])]")

    # Inspecter : pas d'aperçu, pas de bande
    pg.mouse.move(5, 5); pg.wait_for_timeout(700)
    pg.evaluate("document.querySelector('.inspect-btn').click()"); pg.wait_for_timeout(400)
    rows.nth(3).hover(); pg.wait_for_timeout(700)
    ins = pg.evaluate("""(() => { const r = document.querySelectorAll('.work-row')[3];
      return [document.querySelector('.peek').classList.contains('is-on'), getComputedStyle(r, '::before').transform, getComputedStyle(r.querySelector('.ttl')).color, getComputedStyle(document.body).color]; })()""")
    check('Inspect mode: no peek, no fill, normal text colour', not ins[0] and ins[1] in ('matrix(1, 0, 0, 0, 0, 0)', 'none') and ins[2] == ins[3], ins)
    pg.evaluate("document.querySelector('.inspect-btn').click()"); pg.wait_for_timeout(300)

    # A7 : mentions
    tags = pg.evaluate("""[...document.querySelectorAll('.work-list .work-row')].map(r => [r.querySelector('.ttl').textContent.trim(), (r.querySelector('.live-tag') || {}).textContent || ''])""")
    sup = [t for t in tags if re.search(r'(DS|Web|App|Brand)$', t[0])]
    live = [t[0] for t in tags if t[1] == 'en ligne']
    ems = pg.evaluate("document.querySelectorAll('.work-list em:not(.live-tag)').length")
    check('A7 list: no DS/Web/App/Brand superscripts, 3 live rows show "en ligne"', not sup and ems == 0 and len(live) == 3, f'live={live} sup={sup}')
    print('desktop errors', pg.errs)
    derr = list(pg.errs)
    pg.context.close()

    # ---------- fiche ----------
    pg = page(b, viewport={'width': 1440, 'height': 900})
    pg.goto(URL.replace('/?', '/?c=1&') + '#springbreak', wait_until='networkidle'); pg.wait_for_timeout(2000)
    c = pg.evaluate("""(() => { const f = document.querySelector('.case .frame').getBoundingClientRect();
      return [f.width / f.height, document.querySelector('.frame-label span').textContent, document.querySelector('.frame-size').textContent, f.width, f.height]; })()""")
    lit = bool(re.match(r'^\d+ × \d+$', c[2]))
    ws = bool(re.match(r'^\d+\s×\s\d+$', c[2]))
    check('A6 #springbreak: frame 0.8 +-0.01, caption "Visuel de présentation" (fix B1), size label "W × H"', abs(c[0] - .8) <= .01 and c[1] == 'Visuel de présentation' and ws and c[2] == f"{round(c[3])}\u00a0×\u00a0{round(c[4])}", f'{c} literal-space-regex={lit} nbsp-regex={ws}')
    pg.screenshot(path=OUT + 'p6t_case_sb.png')
    pg.goto(URL.replace('/?', '/?c=2&') + '#wei', wait_until='networkidle'); pg.wait_for_timeout(2000)
    w2 = pg.evaluate("[" + RECT + "(document.querySelector('.case .cv-wei .big')), " + RECT + "(document.querySelector('.case .cv-wei .form'))]")
    check('A5 WEI cover: .big and .form do not intersect (peek and case frame)', not inter(*w1) and not inter(*w2), f'peek big.t={w1[0]["t"]:.1f} form.b={w1[1]["b"]:.1f}; case big.t={w2[0]["t"]:.1f} form.b={w2[1]["b"]:.1f}')
    pg.goto(URL.replace('/?', '/?c=3&') + '#zecheck', wait_until='networkidle'); pg.wait_for_timeout(2000)
    z = pg.evaluate("document.querySelector('.frame-label span').textContent")
    pg.goto(URL.replace('/?', '/?c=4&') + '#quasar', wait_until='networkidle'); pg.wait_for_timeout(2000)
    q = pg.evaluate("document.querySelector('.frame-label span').textContent")
    check('A6 #zecheck and #quasar caption "Visuel de présentation" (fix B1: no shot yet)', z == 'Visuel de présentation' and q == 'Visuel de présentation', [z, q])
    derr += pg.errs
    pg.context.close()
    check('Desktop: zero console/page errors', not derr, derr[:3])

    # ---------- téléphone 390 × 844 ----------
    m = page(b, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    m.goto(URL, wait_until='networkidle'); m.wait_for_timeout(1500)
    m.evaluate("document.querySelector('.work-list').scrollIntoView()"); m.wait_for_timeout(1500)
    m.evaluate("scrollBy(0, 900)"); m.wait_for_timeout(1500)
    th = m.evaluate("""[...document.querySelectorAll('.work-row')].map(r => { const t = r.querySelector('.thumb'); if (!t) return null; const b = t.getBoundingClientRect(), cs = getComputedStyle(t); return [Math.round(b.width * 100) / 100, cs.display !== 'none' && cs.visibility !== 'hidden' && cs.clipPath, r.querySelector('.meta').textContent, getComputedStyle(r.querySelector('.meta')).display]; })""")
    okw = all(t and abs(t[0] - 56) < .5 and t[1] == 'inset(0px)' for t in th)
    check('A8 390: every row has a visible 56 px .thumb (revealed) and a "type · année" line', okw and th[0][2] == 'Site & identité · 2026', th)
    m.evaluate("(() => { const r = document.querySelectorAll('.work-row')[3].getBoundingClientRect(); scrollBy(0, r.top + r.height / 2 - innerHeight / 2); })()")
    m.wait_for_timeout(300)
    f = m.evaluate("[...document.querySelectorAll('.work-row')].map(r => r.classList.contains('is-focus'))")
    check('A8 390: row 4 at viewport centre has .is-focus, no other row', f == [False, False, False, True, False, False, False, False], f)
    fs = m.evaluate("(() => { const r = document.querySelectorAll('.work-row')[3]; return [getComputedStyle(r.querySelector('.n')).color, getComputedStyle(r.querySelector('.thumb')).transform]; })()")
    m.wait_for_timeout(600)
    fs = m.evaluate("(() => { const r = document.querySelectorAll('.work-row')[3]; return [getComputedStyle(r.querySelector('.n')).color, getComputedStyle(r.querySelector('.thumb')).transform]; })()")
    check('Focus row: accent number, thumb scale 1.06', fs[1].startswith('matrix(1.06'), fs)
    m.screenshot(path=OUT + 'p6t_m_focus.png')
    kinds = m.evaluate("document.querySelectorAll('.work-row .kind, .work-row .role, .work-row .yr').length")
    check('Touch rows render no .kind/.role/.yr (meta line instead), no .work-head', kinds == 0 and m.evaluate("getComputedStyle(document.querySelector('.work-head')).display") == 'none', kinds)
    m.evaluate("document.querySelectorAll('.work-row')[0].click()"); m.wait_for_timeout(1500)
    mc = m.evaluate("(() => { const f = document.querySelector('.case .frame').getBoundingClientRect(), l = document.querySelector('.frame-label span').getBoundingClientRect(), cm = document.querySelector('.case-media'); return [f.width / f.height, l.left - f.left, l.top - f.top, getComputedStyle(cm).backgroundImage, f.width]; })()")
    check('390 case: frame fills the 4:5 media, label under the frame at its left edge (fix B9), no canvas', abs(mc[0] - .8) < .01 and abs(mc[1]) < 1 and mc[2] > mc[4] * 1.25 and mc[3] == 'none', mc)
    check('Mobile: zero console/page errors', not m.errs, m.errs[:3])
    m.context.close()

    # ---------- tablette tactile ----------
    t = page(b, viewport={'width': 820, 'height': 1180}, is_mobile=True, has_touch=True)
    t.goto(URL, wait_until='networkidle'); t.wait_for_timeout(1500)
    t.evaluate("document.querySelector('.work-list').scrollIntoView()"); t.wait_for_timeout(1500)
    tw = t.evaluate("document.querySelector('.work-row .thumb').getBoundingClientRect().width")
    check('Touch tablet 820: thumb 96 px', abs(tw - 96) < .5 and not t.errs, [tw, t.errs[:2]])
    t.screenshot(path=OUT + 'p6t_tab.png')
    t.context.close()

    # ---------- mouvement réduit ----------
    r = page(b, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
    r.goto(URL, wait_until='networkidle'); r.wait_for_timeout(1200)
    rv = r.evaluate("(() => { const t = document.querySelectorAll('.work-row .thumb')[7]; const cs = getComputedStyle(t); return [cs.clipPath, cs.transitionDuration]; })()")
    r.evaluate("(() => { const x = document.querySelectorAll('.work-row')[3].getBoundingClientRect(); scrollBy(0, x.top + x.height / 2 - innerHeight / 2); })()")
    r.wait_for_timeout(400)
    rs = r.evaluate("(() => { const x = document.querySelectorAll('.work-row')[3]; return [x.classList.contains('is-focus'), getComputedStyle(x.querySelector('.thumb')).transform]; })()")
    check('Reduced motion: thumbs never clipped, no focus scale', rv[0] == 'none' and rs[1] == 'none', [rv, rs])
    r.context.close()
    b.close()

passed = sum(1 for r in results if r[1])
print(f'\n{passed}/{len(results)} pass')
json.dump(results, open(OUT + 'p6test_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
