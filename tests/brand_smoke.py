"""Smoke test for the brand edition (/brand/) and its isolation from the root edition (Edge via Playwright).
Usage: python brand_smoke.py [base_url]   -> prints PASS/FAIL per check, exits 1 on any failure.
SMOKE_ONLY="name1||name2" runs only the checks whose name contains one of the parts."""
import sys, os, time
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5178/').rstrip('/') + '/'
BRAND = BASE + 'brand/'
Q = '?smoke=' + str(int(time.time()))
AXE = 'https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js'
ORDER = ['lco', 'pop-mart-bumi', 'meoow', 'les-dieux', 'one-piece', 'livre-blanc', 'lezgo', 'wei', 'quasar']
TITLES = ['LCO', 'POP MART X BUMI', 'MEOOW!', 'LES DIEUX', 'ONE PIECE S2', 'Du logo à la scène', 'LEZGO', 'WEI & GO', 'QUASAR']
results = []
sys.stdout.reconfigure(errors='backslashreplace')

ONLY = [x for x in os.environ.get('SMOKE_ONLY', '').split('||') if x]
def check(name, fn):
    if ONLY and not any(x in name for x in ONLY):
        return
    try:
        ok, ev = fn()
    except Exception as e:  # a crash in one check must not hide the others
        ok, ev = False, 'exception: ' + str(e).splitlines()[0][:200]
    results.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (' :: ' + str(ev) if ev else ''), flush=True)

def ctx_page(b, w=1440, h=900, mobile=False, theme=None, reduce=False):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile,
                        reduced_motion='reduce' if reduce else 'no-preference')
    ctx.add_init_script("try{localStorage.removeItem('ql-theme')}catch(e){}" if theme is None
                        else f"try{{localStorage.setItem('ql-theme','{theme}')}}catch(e){{}}")
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    pg.on('response', lambda r: r.status >= 400 and pg.errs.append(f'http {r.status}: {r.url}'))
    return ctx, pg

def load(pg, url=BRAND, hash=''):
    pg.goto(url + Q + hash, wait_until='load')
    pg.wait_for_selector('html.is-ready', state='attached', timeout=10000)

def case_open(pg):
    return pg.evaluate("!document.querySelector('.case').hidden")

def scroll_all(pg):
    # every reveal in its final state (and every lazy cover requested) before measuring or auditing
    pg.evaluate("""(async () => { for (let y = 0; y < document.body.scrollHeight; y += innerHeight * .6) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); })()""")
    pg.wait_for_timeout(1500)

def scroll_sheet(pg):
    pg.evaluate("""(async () => { const s = document.querySelector('.case-sheet'); for (let y = 0; y < s.scrollHeight; y += s.clientHeight * .6) { s.scrollTo(0, y); await new Promise(r => setTimeout(r, 150)); } })()""")
    pg.wait_for_timeout(1500)

def axe(pg):
    if not pg.evaluate('!!window.axe'):
        pg.add_script_tag(url=AXE)
    v = pg.evaluate("""(async () => (await axe.run(document, { resultTypes: ['violations'] })).violations
        .map(v => v.id + ' x' + v.nodes.length + ' ' + v.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | ')))()""")
    return v

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    # ---------------- desktop ----------------
    ctx, pg = ctx_page(b)
    load(pg); pg.wait_for_timeout(2500)
    check('brand desktop: no console/page errors or HTTP >= 400 on load', lambda: (not pg.errs, pg.errs[:3]))

    def head():
        r = pg.evaluate("""(() => { const q = s => document.querySelector(s);
          const ld = JSON.parse(q('script[type="application/ld+json"]').textContent);
          return [document.documentElement.dataset.edition, document.title, q('link[rel=canonical]').href, q('meta[property="og:url"]').content,
                  q('meta[property="og:image"]').content, ld.jobTitle, ld.url, q('.status').textContent.trim(), q('.sec-title').textContent.trim()]; })()""")
        want = ['brand', 'Quentin Louis, UI/UX & Brand Designer', 'https://portfolio-quentin-louis.vercel.app/brand/', 'https://portfolio-quentin-louis.vercel.app/brand/',
                'https://portfolio-quentin-louis.vercel.app/assets/og-brand.jpg', 'UI/UX & Brand Designer', 'https://portfolio-quentin-louis.vercel.app/brand/',
                'Recherche CDI · Bordeaux']
        return r[:8] == want and 'Neuf projets' in r[8], r
    check('brand: edition, title, canonical, og, JSON-LD and hero status', head)

    def local_urls():
        # every local URL of the page is root-absolute (the page lives in /brand/)
        bad = pg.evaluate("""[...document.querySelectorAll('[href],[src],[srcset],[imagesrcset]')].flatMap(e => ['href', 'src', 'srcset', 'imagesrcset']
          .map(a => e.getAttribute(a)).filter(Boolean).flatMap(v => v.split(',').map(x => x.trim().split(' ')[0])))
          .filter(u => u && !/^(https?:|mailto:|#|\\/)/.test(u))""")
        cv = pg.evaluate("[...document.querySelectorAll('a[href$=\".pdf\"]')].map(a => a.getAttribute('href'))")
        ok_cv = len(cv) == 6 and all(h == '/assets/CV-Quentin-Louis-Brand.pdf' for h in cv)
        st = [pg.request.get(BASE + u.lstrip('/')).status for u in ('/assets/CV-Quentin-Louis-Brand.pdf', '/assets/og-brand.jpg', '/assets/cv-brand-apercu-800.webp', '/assets/cv-brand-apercu-400.jpg')]
        return not bad and ok_cv and st == [200] * 4, f'relative urls={bad[:4]} cv links={len(cv)} ok={ok_cv} status={st}'
    check('brand: local URLs root-absolute, 6 CV links to the brand PDF, brand assets served', local_urls)

    def order():
        r = pg.evaluate("""[...document.querySelectorAll('.work-list--grid > li > .work-row')].map(b => [b.querySelector('.n').textContent,
            b.querySelector('.ttl').textContent.replace(/\\u00a0/g, ' ').replace(/\\u2060/g, ''), !!b.querySelector('.card-cover img'), b.querySelector('.meta').textContent])""")
        titles = [x[1] for x in r]
        nums = [x[0] for x in r]
        return titles == TITLES and nums == [f'{i:02d}' for i in range(1, 10)] and all(x[2] for x in r), f'{len(r)} cards: {titles}'
    check('brand desktop: 9 cards in the brand order, numbered, each with a cover', order)

    def grid_modes():
        r = pg.evaluate("""[document.querySelector('.work-list').classList.contains('work-list--thumbs'), getComputedStyle(document.querySelector('.work-head')).display,
            document.querySelector('.peek-in').children.length, [...document.querySelectorAll('.work-list--grid .ttl')].some(t => t.style.getPropertyValue('--tw-max'))]""")
        pg.locator('.work-row').nth(1).scroll_into_view_if_needed(); pg.wait_for_timeout(600)
        pg.locator('.work-row').nth(1).hover(); pg.wait_for_timeout(700)
        on = pg.evaluate("document.querySelector('.peek').classList.contains('is-on')")
        return r == [False, 'none', 0, False] and not on, f'thumbs/head display/peek track/--tw-max={r} peek on after hover={on}'
    check('brand desktop: grid mode has no peek, no thumbs, no fitted titles, no table header', grid_modes)

    def hover_fit():
        # the hover width (--tw 118) never adds a line and the card does not grow
        r = pg.evaluate("""[...document.querySelectorAll('.work-list--grid .work-row')].map(row => { const t = row.querySelector('.ttl');
          t.style.transition = 'none'; const h0 = row.getBoundingClientRect().height, a = t.getBoundingClientRect().height;
          t.style.setProperty('--tw', '118'); const c = t.getBoundingClientRect().height, h1 = row.getBoundingClientRect().height;
          const rg = document.createRange(); rg.selectNodeContents(t); const over = rg.getBoundingClientRect().width > t.clientWidth + 1;
          t.style.removeProperty('--tw'); t.style.transition = ''; return a === c && h0 === h1 && !over; })""")
        return all(r), r
    check('brand desktop: titles keep one line and the card its height at the hover width', hover_fit)

    def click_card():
        row = pg.locator('.work-row').nth(3)
        row.scroll_into_view_if_needed(); pg.wait_for_timeout(500)
        row.click()
        pg.wait_for_function("!document.querySelector('.case').hidden", timeout=4000)
        pg.wait_for_timeout(900)
        r = [pg.evaluate('location.hash'), pg.text_content('#case-title'), pg.text_content('.case-idx')]
        pg.keyboard.press('Escape'); pg.wait_for_function("document.querySelector('.case').hidden", timeout=5000)
        focus = pg.evaluate("document.activeElement.dataset.i")
        return r[0] == '#les-dieux' and 'LES DIEUX' in r[1] and r[2].startswith('04 / 09') and focus == '3', f'{r} focus back on card {focus}'
    check('brand desktop: clicking card 04 opens LES DIEUX (04 / 09), Esc returns focus to the card', click_card)

    def arrows():
        load(pg, hash='#meoow'); pg.wait_for_function("!document.querySelector('.case').hidden", timeout=5000); pg.wait_for_timeout(1000)
        seen = [pg.evaluate('location.hash')]
        for _ in range(3):
            prev = pg.text_content('#case-title')
            pg.keyboard.press('ArrowRight')
            pg.wait_for_function(f"document.querySelector('#case-title') && document.querySelector('#case-title').textContent !== {prev!r}", timeout=4000)
            pg.wait_for_timeout(700)
            seen.append(pg.evaluate('location.hash'))
        pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(1200); seen.append(pg.evaluate('location.hash'))
        nxt = pg.evaluate("document.querySelector('.case-next b').textContent")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(800)
        want = ['#meoow', '#les-dieux', '#one-piece', '#livre-blanc', '#one-piece']
        return seen == want and nxt == 'Du logo à la scène', f'{seen} next={nxt!r}'
    check('brand desktop: ArrowRight / ArrowLeft and "Projet suivant" follow the brand order', arrows)

    def last_wraps():
        load(pg, hash='#quasar'); pg.wait_for_function("!document.querySelector('.case').hidden", timeout=5000); pg.wait_for_timeout(900)
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(1500)
        h = pg.evaluate('location.hash'); pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
        return h == '#lco', h
    check('brand desktop: ArrowRight on the last project (QUASAR) wraps to LCO', last_wraps)

    def deep():
        load(pg, hash='#les-dieux')
        pg.wait_for_function("!document.querySelector('.case').hidden", timeout=5000); pg.wait_for_timeout(1200)
        scroll_sheet(pg)
        imgs = pg.evaluate("[...document.querySelectorAll('.case-body img')].map(i => [i.currentSrc.split('/').slice(-2).join('/'), i.complete && i.naturalWidth > 0, !!i.alt, !!i.getAttribute('width')])")
        facts = pg.evaluate("document.querySelector('.case-body').innerText")
        link = pg.evaluate("document.querySelector('.case-site').href")
        # six images of the project, then the cover of the next one (ONE PIECE S2, decorative)
        ok = len(imgs) == 7 and all(i[1] for i in imgs) and all(i[2] and i[3] for i in imgs[:-1]) and all('les-dieux/' in i[0] for i in imgs[:-1]) and imgs[-1][0].startswith('one-piece/cover')
        ok = ok and 'Photoshop, Illustrator, Figma' in facts and link == 'https://www.behance.net/gallery/216527627/REBRANDING-LES-DIEUX' and not pg.errs
        return ok, f'imgs={imgs} link ok={link.endswith("LES-DIEUX")} errs={pg.errs[:2]}'
    check('brand desktop: #les-dieux deep link opens, all 7 images load (alt and size), Behance link', deep)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(600)

    def axe_brand(theme):
        def run():
            c2, m = ctx_page(b, theme=theme, reduce=True)
            load(m); m.wait_for_timeout(1500); scroll_all(m)
            v = axe(m)
            load(m, hash='#les-dieux'); m.wait_for_function("!document.querySelector('.case').hidden", timeout=5000); m.wait_for_timeout(1000)
            scroll_sheet(m)
            v2 = axe(m)
            c2.close()
            return not v and not v2, f'page={v[:3]} case={v2[:3]}'
        return run
    check('brand a11y dark: axe-core 0 violations on the page and the Les Dieux case', axe_brand('dark'))
    check('brand a11y light: axe-core 0 violations on the page and the Les Dieux case', axe_brand('light'))

    def keyboard():
        load(pg); pg.wait_for_timeout(1500)
        pg.evaluate("document.querySelectorAll('.work-row')[0].focus()")
        pg.keyboard.press('Tab'); pg.wait_for_timeout(700)
        r = pg.evaluate("""(() => { const a = document.activeElement, cs = getComputedStyle(a);
          return [a.dataset.i, a.matches(':focus-visible'), cs.outlineStyle, cs.outlineWidth, getComputedStyle(a.querySelector('.ttl')).fontVariationSettings]; })()""")
        pg.keyboard.press('Enter'); pg.wait_for_function("!document.querySelector('.case').hidden", timeout=4000); pg.wait_for_timeout(600)
        h = pg.evaluate('location.hash'); pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
        return r[:4] == ['1', True, 'solid', '2px'] and '118' in r[4] and h == '#pop-mart-bumi', f'{r} enter -> {h}'
    check('brand desktop: Tab reaches the next card with a 2px ring and the wide title, Enter opens it', keyboard)

    def print_mode():
        pg.emulate_media(media='print')
        r = pg.evaluate("""(() => { const l = document.querySelector('.work-list--grid'), row = l.querySelector('.work-row');
          return [getComputedStyle(l).display, getComputedStyle(row).display, getComputedStyle(row.querySelector('.card-cover')).display,
                  Math.round(row.getBoundingClientRect().height), getComputedStyle(document.querySelector('.topbar')).display]; })()""")
        pdf = pg.pdf(format='A4')
        pg.emulate_media(media='screen')
        pages = pdf.count(b'/Type /Page') - pdf.count(b'/Type /Pages')
        return r[0] == 'block' and r[1] == 'grid' and r[2] == 'none' and r[3] < 60 and r[4] == 'none' and pages <= 4, f'list/row/cover/row h/topbar={r} pdf pages={pages}'
    check('brand print: the grid prints as a compact list without covers', print_mode)
    check('brand desktop: no errors after interactions', lambda: (not pg.errs, pg.errs[:3]))
    ctx.close()

    # ---------------- grid columns ----------------
    def columns():
        out = {}
        for w, h, mob in ((1440, 900, False), (1024, 768, False), (390, 844, True)):
            c2, m = ctx_page(b, w, h, mobile=mob)
            load(m); m.wait_for_timeout(800)
            out[w] = m.evaluate("""[getComputedStyle(document.querySelector('.work-list--grid')).gridTemplateColumns.split(' ').length,
              new Set([...document.querySelectorAll('.work-list--grid .card-cover')].map(e => Math.round(e.getBoundingClientRect().width))).size,
              (() => { const r = document.querySelector('.card-cover').getBoundingClientRect(); return Math.round(r.height / r.width * 100) / 100; })(),
              document.documentElement.scrollWidth <= innerWidth]""")
            c2.close()
        ok = out[1440][0] == 3 and out[1024][0] == 2 and out[390][0] == 1 and all(v[1] == 1 and v[2] == 1.25 and v[3] for v in out.values())
        return ok, f'[cols, distinct widths, cover ratio, no overflow] = {out}'
    check('brand grid: 3 / 2 / 1 columns at 1440 / 1024 / 390, equal 4:5 covers, no horizontal scroll', columns)

    # ---------------- mobile ----------------
    ctx, pg = ctx_page(b, 390, 844, mobile=True)
    load(pg); pg.wait_for_timeout(2500)
    check('brand mobile: no console/page errors or HTTP >= 400 on load', lambda: (not pg.errs, pg.errs[:3]))
    def mob_case():
        r = pg.evaluate("[document.querySelector('.work-list').classList.contains('work-list--thumbs'), document.querySelectorAll('.work-row.is-focus').length]")
        row = pg.locator('.work-row').nth(3)
        row.scroll_into_view_if_needed(); pg.wait_for_timeout(700)
        row.tap()
        pg.wait_for_function("!document.querySelector('.case').hidden", timeout=4000); pg.wait_for_timeout(900)
        h = pg.evaluate('location.hash')
        scroll_sheet(pg)
        imgs = pg.evaluate("[...document.querySelectorAll('.case-body img')].every(i => i.complete && i.naturalWidth > 0)")
        pg.go_back(); pg.wait_for_function("document.querySelector('.case').hidden", timeout=5000)
        return r == [False, 0] and h == '#les-dieux' and imgs and not pg.errs, f'thumbs/focus band={r} hash={h} imgs={imgs} errs={pg.errs[:2]}'
    check('brand mobile: cards (no thumbs, no focus band), tap opens LES DIEUX, images load, back closes', mob_case)
    ctx.close()

    def ctas():
        out, ok = {}, True
        for w, h in ((320, 640), (360, 740), (375, 812), (390, 844)):
            c2, m = ctx_page(b, w, h, mobile=True)
            load(m); m.wait_for_timeout(1800)
            r = m.evaluate("""(() => { const d = document.querySelector('.dock');
              const cta = Math.max(...[...document.querySelectorAll('.cta-row .btn')].map(e => e.getBoundingClientRect().bottom));
              return [Math.round(cta), innerHeight, d.classList.contains('dock-hidden'), document.documentElement.scrollWidth <= innerWidth,
                      Math.max(...[...document.querySelectorAll('.brief dd')].map(e => Math.round(e.getBoundingClientRect().height)))]; })()""")
            out[w] = r
            ok = ok and r[0] <= r[1] and r[2] and r[3] and r[4] <= 44
            c2.close()
        return ok, f'[cta bottom, vh, dock away, no overflow, tallest brief answer] = {out}'
    check('brand mobile: both hero CTAs inside the first screen at 320x640 to 390x844, dock away', ctas)

    # ---------------- root edition untouched ----------------
    ctx, pg = ctx_page(b)
    def root_list():
        load(pg, BASE); pg.wait_for_timeout(1500)
        r = pg.evaluate("""[document.documentElement.dataset.edition || '', document.querySelectorAll('.work-list > li > .work-row').length,
            [...document.querySelectorAll('.work-list .ttl')].map(t => t.textContent.replace(/\\u00a0/g, ' ').replace(/\\u2060/g, '').replace('en ligne', '')),
            !!document.querySelector('.work-list--grid'), document.querySelector('.sec-title').textContent]""")
        want = ['WEI & GO', 'QUASAR', 'LEZGO', 'ONE PIECE S2', 'Du logo à la scène', 'LCO', 'POP MART X BUMI', 'MEOOW!']
        return r[0] == '' and r[1] == 8 and r[2] == want and r[3] and 'Huit projets' in r[4] and not pg.errs, f'{r} errs={pg.errs[:2]}'
    check('root: 8 projects in the UX order, no Les Dieux, grid mode, "Huit projets"', root_list)
    def root_hash():
        # a fresh load (not a same-document hash change), like a shared link
        pg.goto(BASE + Q + '-fresh#les-dieux', wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached'); pg.wait_for_timeout(1500)
        r = [case_open(pg), pg.evaluate('location.hash')]
        load(pg, BASE, '#lco'); pg.wait_for_function("!document.querySelector('.case').hidden", timeout=5000); pg.wait_for_timeout(900)
        idx = pg.text_content('.case-idx')
        imgs = pg.evaluate("[...document.querySelectorAll('.case-body img')].slice(0, 2).map(i => i.getAttribute('src'))")
        return r == [False, ''] and idx.startswith('06 / 08') and all(s.startswith('assets/projects/lco/') for s in imgs), f'#les-dieux -> open/hash={r}; #lco idx={idx!r} srcs={imgs}'
    check('root: #les-dieux is an unknown hash (no case, hash cleared), #lco still 06 / 08 with relative image paths', root_hash)
    check('root: no errors', lambda: (not pg.errs, pg.errs[:3]))
    ctx.close()

    b.close()

print(f'\n{sum(results)}/{len(results)} passed')
sys.exit(0 if results and all(results) else 1)
