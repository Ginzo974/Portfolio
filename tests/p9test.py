"""P9 acceptance: Parcours and contact."""
import sys, time, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
BASE = 'http://localhost:5178/'
SP = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
Q = '?t=p9' + str(int(time.time()))
MAIL = 'quentinlouis97400@gmail.com'
res = []
out = open(SP + 'p9test_out.txt', 'w', encoding='utf-8')
def check(name, ok, ev=''):
    res.append(bool(ok))
    line = ('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(ev)
    print(line); out.write(line + '\n'); out.flush()

def page(b, w=1440, h=900, mobile=False, theme=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE.rstrip('/'))
    if theme: ctx.add_init_script(f"try{{localStorage.setItem('ql-theme','{theme}')}}catch(e){{}}")
    else: ctx.add_init_script("try{localStorage.removeItem('ql-theme')}catch(e){}")
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    pg.goto(BASE + Q, wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached')
    pg.wait_for_timeout(1800)
    return ctx, pg

def reveal_all(pg):
    pg.evaluate("document.querySelectorAll('.reveal').forEach(e => e.classList.add('is-in'))")
    pg.wait_for_timeout(1400)

CV = [['2021'], ['2022'], ['déc. 2022', 'sept. 2023'], ['sept. 2023', 'juil. 2024'], ['janv. 2024', 'août 2024'],
      ['sept. 2024'], ['nov. 2024', 'sept. 2025'], ['sept. 2025', 'sept. 2026']]
DT = ['2021', '2022', '2022-12', '2023-09', '2024-01', '2024-09', '2024-11', '2025-09']

GEOM = """(() => {
  const g = document.querySelector('.path-grid'), cs = getComputedStyle(g), r = g.getBoundingClientRect();
  const cols = cs.gridTemplateColumns.split(' ').map(parseFloat), gap = parseFloat(cs.columnGap);
  const left = i => r.left + parseFloat(cs.paddingLeft) + cols.slice(0, i).reduce((a, b) => a + b, 0) + i * gap;  // i: 0-based column
  const right = i => left(i) + cols[i];
  const times = [...document.querySelectorAll('.timeline time')].map(t => {
    const rg = document.createRange(); rg.selectNodeContents(t);
    const spans = [...t.querySelectorAll('span:not(.sr-only)')].map(s => { const q = document.createRange(); q.selectNodeContents(s); return q.getBoundingClientRect().right; });
    return [t.getBoundingClientRect().right, Math.max(...spans), t.scrollWidth - t.clientWidth, t.getBoundingClientRect().left];
  });
  const rail = document.querySelector('.rail').getBoundingClientRect();
  const dots = [...document.querySelectorAll('.timeline li')].map(li => { const s = getComputedStyle(li, '::before'); const lr = li.getBoundingClientRect(); return lr.left + parseFloat(s.left) + parseFloat(s.width) / 2; });
  const cv = document.querySelector('.cv-card').getBoundingClientRect(), tl = document.querySelector('.timeline').getBoundingClientRect();
  const kit = document.querySelector('.kit-table').getBoundingClientRect();
  const h3 = document.querySelector('.timeline h3').getBoundingClientRect();
  return { c5r: right(4), c6l: left(5), c5l: left(4), c1l: left(0), times, rail: rail.left + rail.width / 2, railL: rail.left, dots, cvR: cv.right, tlL: tl.left, kitL: kit.left, h3L: h3.left, h3R: h3.right, gap };
})()"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    # ---------- desktop ----------
    ctx, pg = page(b)
    t = pg.evaluate("[...document.querySelectorAll('.timeline time')].map(t => [[...t.querySelectorAll('span:not(.sr-only)')].map(s => s.textContent.replace(/\\u00a0/g, ' ')), t.getAttribute('datetime')])")
    check('A1 time texts = CV strings, datetime set', [x[0] for x in t] == CV and [x[1] for x in t] == DT, t)
    reveal_all(pg)
    g = pg.evaluate(GEOM)
    tr = [round(x[1] - g['c5r'], 2) for x in g['times']]
    check('A2a 1440 time text right edges = col 5 right (±2)', all(abs(d) <= 2 for d in tr) and all(x[2] <= 0 for x in g['times']), f'diffs={tr} c5r={g["c5r"]:.1f}')
    check('A2b rail x = col 6 left (±2), dots centred on rail', abs(g['railL'] - g['c6l']) <= 2 and all(abs(d - g['rail']) <= 1 for d in g['dots']), f"railL={g['railL']:.1f} c6l={g['c6l']:.1f} dots={[round(d - g['rail'], 2) for d in g['dots']]}")
    check('A2c CV card does not overlap the timeline', g['cvR'] <= g['tlL'], f"cvR={g['cvR']:.1f} tlL={g['tlL']:.1f}")
    cv = pg.evaluate("""(() => { const c = document.querySelector('.cv-card'); const th = c.querySelector('a.cv-thumb');
      const dl = [...c.querySelectorAll('a')].find(a => a.textContent.trim() === 'Télécharger');
      const v = [...c.querySelectorAll('a')].find(a => a.textContent.trim() === 'Voir');
      return [c.tagName, th.target, th.hasAttribute('download'), th.querySelector('img').alt, !!dl && dl.hasAttribute('download'), v && v.target,
        c.querySelector('.cv-meta span').textContent, c.querySelector('.cv-label').textContent]; })()""")
    check('A3 CV card: thumb _blank no download, Télécharger download, 715 Ko', cv[0] == 'DIV' and cv[1] == '_blank' and not cv[2] and cv[4] and cv[5] == '_blank' and cv[6] == 'PDF · 1 page · 715 Ko', cv)
    k = pg.evaluate("[document.querySelectorAll('.chips, .kit-skills, .langs, .kit-col').length, document.querySelectorAll('.kit-table > div').length, [...document.querySelectorAll('.kit-table dt')].map(d => d.textContent)]")
    check('A4 no chips/kit-skills, 5 rows, left = col 5 left (±2)', k[0] == 0 and k[1] == 5 and abs(g['kitL'] - g['c5l']) <= 2, f"{k} kitL={g['kitL']:.1f} c5l={g['c5l']:.1f}")
    av = pg.evaluate("[document.querySelector('.contact-avail span').textContent, document.querySelector('.brief [data-avail]').textContent, document.querySelector('.contact-avail').textContent]")
    check('A5 contact-avail = brief data-avail', av[0] == av[1] and av[2].startswith('Disponibilité\u202f: '), av)
    # A6 desktop click ripple + clipboard
    pg.evaluate("navigator.clipboard.writeText('x')")
    pg.locator('.mail').scroll_into_view_if_needed(); pg.wait_for_timeout(900)
    box = pg.locator('.mail-txt').bounding_box()
    pg.mouse.move(box['x'] + box['width'] * .15, box['y'] + box['height'] - 5)   # sur une lettre de gauche
    pg.wait_for_timeout(900)
    pg.mouse.down(); pg.mouse.up()
    t0 = time.time()
    samples = []
    for ms in (80, 200, 350):
        pg.wait_for_timeout(max(0, ms - (time.time() - t0) * 1000))
        samples.append(pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].map(c => c.style.getPropertyValue('--w') || '100').join(',')"))
    pg.wait_for_timeout(max(0, 1500 - (time.time() - t0) * 1000))
    end = pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].map(c => c.style.getPropertyValue('--w') || '100')")
    clip = pg.evaluate("navigator.clipboard.readText()")
    check('A6 desktop click: clipboard = address, ripple at +200ms, all 100 at +1500ms', clip == MAIL and any(v != '100' for v in samples[1].split(',')) and all(v == '100' for v in end), f'clip={clip} samples={samples} end={end}')
    pg.screenshot(path=SP + 'p9_d_toast.png', clip={'x': 0, 'y': 400, 'width': 1440, 'height': 500})
    # ripple on keyboard click (detail 0), from the middle
    pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelector('.mail').click()"); pg.wait_for_timeout(160)
    mid = pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].map(c => c.style.getPropertyValue('--w') || '100').join(',')")
    check('A6b keyboard/JS click ripples from the middle', mid.split(',') != ['100'] * 11, mid)
    # A8 Copier
    pg.wait_for_timeout(2000)
    pg.evaluate("navigator.clipboard.writeText('x')")
    pg.locator('.mail-copy').click(); pg.wait_for_timeout(150)
    c8 = pg.evaluate("[document.querySelector('.mail-copy').textContent, document.querySelector('.mail-copy').nextElementSibling.textContent, document.querySelector('.mail-copy').nextElementSibling.getAttribute('aria-live'), document.querySelector('.toast').classList.contains('is-on')]")
    clip = pg.evaluate("navigator.clipboard.readText()")
    pg.screenshot(path=SP + 'p9_d_copied.png', clip={'x': 0, 'y': 560, 'width': 1440, 'height': 340})
    pg.wait_for_timeout(1900)
    back = pg.evaluate("document.querySelector('.mail-copy').textContent")
    mbox = pg.locator('.mail-copy').bounding_box()
    check('A8 Copier -> Copié (1.8s), clipboard = address, live region, no toast', c8[0] == 'Copié' and clip == MAIL and c8[1] == 'Adresse copiée' and c8[2] == 'polite' and back.startswith('Copier') and back != 'Copié' and mbox['height'] >= 32, f'{c8} clip={clip} back={back} h={mbox["height"]}')
    lab = pg.evaluate("[document.querySelector('.mail').getAttribute('aria-label'), getComputedStyle(document.querySelector('.mail-hint .only-fine')).display, getComputedStyle(document.querySelector('.mail-hint .only-touch')).display]")
    check('desktop aria-label and hint', lab[0] == 'Écrivez-moi\u202f: copier l’adresse ' + MAIL and lab[1] != 'none' and lab[2] == 'none', lab)
    cvl = pg.evaluate("[...document.querySelectorAll('.links a')].map(a => [a.textContent.trim(), a.target, a.hasAttribute('download')])")
    check('links: CV ↗ opens the PDF in a new tab', ['CV ↗', '_blank', False] in cvl, cvl)
    f = pg.evaluate("[getComputedStyle(document.querySelector('.cv-thumb img')).filter]")
    check('dark: cv thumb brightness .88', f[0] == 'brightness(0.88)', f)
    check('desktop: zero errors', not pg.errs, pg.errs[:3])
    # screenshots parcours dark
    pg.evaluate("document.querySelector('#parcours .path-grid').scrollIntoView()"); pg.wait_for_timeout(1200)
    pg.screenshot(path=SP + 'p9_d_path_dark.png')
    pg.evaluate("document.querySelector('.kit').scrollIntoView({block:'center'})"); pg.wait_for_timeout(1200)
    pg.screenshot(path=SP + 'p9_d_kit_dark.png')
    pg.evaluate("document.querySelector('#contact').scrollIntoView()"); pg.wait_for_timeout(1500)
    pg.screenshot(path=SP + 'p9_d_contact_dark.png')
    ctx.close()

    # light
    ctx, pg = page(b, theme='light'); reveal_all(pg)
    f = pg.evaluate("getComputedStyle(document.querySelector('.cv-thumb img')).filter")
    check('light: no filter on cv thumb', f == 'none', f)
    pg.evaluate("document.querySelector('#parcours .path-grid').scrollIntoView()"); pg.wait_for_timeout(1200)
    pg.screenshot(path=SP + 'p9_d_path_light.png')
    pg.evaluate("document.querySelector('.kit').scrollIntoView({block:'center'})"); pg.wait_for_timeout(1200)
    pg.screenshot(path=SP + 'p9_d_kit_light.png')
    pg.evaluate("document.querySelector('#contact').scrollIntoView()"); pg.wait_for_timeout(1500)
    pg.screenshot(path=SP + 'p9_d_contact_light.png')
    check('light desktop: zero errors', not pg.errs, pg.errs[:3])
    ctx.close()

    # other widths: 1101 / 1920 / 2560 grid alignment; 1024 previous layout fits
    for w in (1101, 1280, 1920, 2560):
        ctx, pg = page(b, w=w); reveal_all(pg)
        g = pg.evaluate(GEOM)
        tr = [round(x[1] - g['c5r'], 1) for x in g['times']]
        check(f'{w}: time right = col5 right, rail = col6 left, no overflow', all(abs(d) <= 2 for d in tr) and abs(g['railL'] - g['c6l']) <= 2 and all(x[2] <= 0 for x in g['times']) and g['cvR'] <= g['tlL'] and min(x[3] for x in g['times']) >= g['cvR'] + 4, f"{tr} minTimeL-cvR={min(x[3] for x in g['times']) - g['cvR']:.1f} rail={g['railL'] - g['c6l']:.1f} ovf={[x[2] for x in g['times']]}")
        if w == 1101:
            pg.evaluate("document.querySelector('#parcours .path-grid').scrollIntoView()"); pg.wait_for_timeout(1200)
            pg.screenshot(path=SP + 'p9_1101_path.png')
        ctx.close()
    ctx, pg = page(b, w=1024, h=900); reveal_all(pg)
    g = pg.evaluate(GEOM)
    check('1024: previous layout, no time overflow, card beside timeline, kit full width', all(x[2] <= 0 for x in g['times']) and g['cvR'] <= g['tlL'] and abs(g['kitL'] - g['c1l']) <= 2, f"ovf={[x[2] for x in g['times']]} kitL-c1l={g['kitL'] - g['c1l']:.1f}")
    pg.evaluate("document.querySelector('#parcours .path-grid').scrollIntoView()"); pg.wait_for_timeout(1200)
    pg.screenshot(path=SP + 'p9_1024_path.png')
    pg.evaluate("document.querySelector('.kit').scrollIntoView({block:'center'})"); pg.wait_for_timeout(1200)
    pg.screenshot(path=SP + 'p9_1024_kit.png')
    ctx.close()

    # ---------- mobile ----------
    for theme in (None, 'light'):
        ctx, pg = page(b, 390, 844, mobile=True, theme=theme)
        tag = 'light' if theme else 'dark'
        reveal_all(pg)
        if not theme:
            h = pg.evaluate("[getComputedStyle(document.querySelector('.mail-hint .only-touch')).display, getComputedStyle(document.querySelector('.mail-hint .only-fine')).display, document.querySelector('.mail').getAttribute('aria-label')]")
            check('A7a touch: only-touch hint visible, only-fine hidden, touch aria-label', h[0] != 'none' and h[1] == 'none' and h[2] == 'Écrivez-moi\u202f: écrire à ' + MAIL, h)
            L = pg.evaluate("""(() => { const l = document.querySelector('.links'); const cs = getComputedStyle(l);
              const as = [...l.querySelectorAll('a')].map(a => { const r = a.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; });
              return [cs.display, cs.gridTemplateColumns, as, l.getBoundingClientRect().width]; })()""")
            rows = sorted(set(a[1] for a in L[2]))
            check('A9 390: .links 2-column grid, 4 links in 2 rows', L[0] == 'grid' and len(L[1].split(' ')) == 2 and len(rows) == 2 and all(sum(1 for a in L[2] if a[1] == r) == 2 for r in rows), L)
            ms = pg.evaluate("[getComputedStyle(document.querySelector('.mail-sub')).flexDirection, getComputedStyle(document.querySelector('.kit-table div')).gridTemplateColumns]")
            check('390: mail-sub stacks, kit dt above dd', ms[0] == 'column' and len(ms[1].split(' ')) == 1, ms)
            hit = pg.evaluate("(() => { const b = document.querySelector('.mail-copy'); const r = b.getBoundingClientRect(); const a = getComputedStyle(b, '::after'); return [r.height, r.height - parseFloat(a.top) - parseFloat(a.bottom) - 2]; })()")
            check('390 coarse: Copier 32px, hit area >= 44px', hit[0] >= 32 and hit[1] >= 44, hit)
            # A7b: tap .mail -> mailto navigation (CDP frameRequestedNavigation)
            cdp = pg.context.new_cdp_session(pg); cdp.send('Page.enable')
            navs = []
            cdp.on('Page.frameRequestedNavigation', lambda e: navs.append(e.get('url')))
            pg.locator('.mail').scroll_into_view_if_needed(); pg.wait_for_timeout(700)
            pg.locator('.mail').tap()
            pg.wait_for_timeout(250)
            mid = pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].map(c => c.style.getPropertyValue('--w') || '100').join(',')")
            pg.wait_for_timeout(1200)
            # garde voulue dans main.js : sous navigator.webdriver, pas de navigation mailto, toast de test à la place
            wd = pg.evaluate('navigator.webdriver')
            tst = pg.evaluate("[document.querySelector('.toast').classList.contains('is-on'), document.querySelector('.toast').textContent]")
            nav_ok = any(u and u.startswith('mailto:' + MAIL + '?subject=Prise%20de%20contact') for u in navs)
            guard_ok = wd and not navs and 'mailto bloqu' in tst[1]
            check('A7b touch tap: ripple, then mailto with subject (blocked under webdriver)', any(v != '100' for v in mid.split(',')) and (nav_ok or guard_ok), f'mid={mid} navs={navs} webdriver={wd} toast={tst}')
            check('touch tap: no copy toast', not tst[0] or 'mailto bloqu' in tst[1], tst)
        pg.evaluate("document.querySelector('#parcours .path-grid').scrollIntoView()"); pg.wait_for_timeout(1200)
        pg.screenshot(path=SP + f'p9_m_path_{tag}.png')
        pg.evaluate("document.querySelector('.kit').scrollIntoView()"); pg.wait_for_timeout(1200)
        pg.screenshot(path=SP + f'p9_m_kit_{tag}.png')
        pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(1500)
        pg.screenshot(path=SP + f'p9_m_contact_{tag}.png')
        check(f'mobile {tag}: zero errors', not pg.errs, pg.errs[:3])
        ctx.close()

    # reduced motion: click copies, no ripple
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE.rstrip('/'))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + Q, wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached'); pg.wait_for_timeout(800)
    pg.evaluate("document.querySelector('.mail').click()"); pg.wait_for_timeout(150)
    w = pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].every(c => (c.style.getPropertyValue('--w') || '100') === '100')")
    clip = pg.evaluate("navigator.clipboard.readText()")
    check('reduce: no ripple, still copies', w and clip == MAIL and not errs, [w, clip, errs])
    ctx.close()
    b.close()
n = res.count(False)
print(f'{len(res) - n}/{len(res)} pass'); out.write(f'{len(res) - n}/{len(res)} pass\n')
