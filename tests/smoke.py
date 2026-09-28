"""Regression smoke test for the portfolio (Edge via Playwright).
Usage: python smoke.py [base_url]   -> prints PASS/FAIL per check, exits 1 on any failure."""
import sys, time
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5178/').rstrip('/') + '/'
Q = '?smoke=' + str(int(time.time()))
results = []
sys.stdout.reconfigure(errors='backslashreplace')   # arrows and accents in evidence must not crash a redirected console

import os
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

def ctx_page(b, mobile=False, theme=None):
    ctx = b.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1440, 'height': 900},
                        device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
    try:
        ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE.rstrip('/'))
    except Exception:
        pass
    pg = ctx.new_page()
    pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errs.append('console: ' + m.text))
    if theme is None:
        ctx.add_init_script("try{ if(!sessionStorage.getItem('smoke-keep')) localStorage.removeItem('ql-theme') }catch(e){}")
    return ctx, pg

def load(pg, path=''):
    pg.goto(BASE + Q + path if not path.startswith('#') else BASE + Q + path, wait_until='load')
    pg.wait_for_selector('html.is-ready', state='attached', timeout=10000)

def case_open(pg):
    return pg.evaluate("!document.querySelector('.case').hidden")

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    # ---------------- desktop ----------------
    ctx, pg = ctx_page(b)
    load(pg)
    pg.wait_for_timeout(2500)   # intro letters settle
    check('desktop: no console/page errors on load', lambda: (not pg.errs, pg.errs[:3]))

    def edge():
        r = pg.evaluate("""(() => {
          const line = document.querySelector('.name-line');
          const chars = line.querySelectorAll('.ch');
          const nm = document.querySelector('.name');   // H3: the ink of the N ends on the box, the advance box overhangs by --rsb
          const last = chars[chars.length - 1].getBoundingClientRect().right - (parseFloat(getComputedStyle(nm).getPropertyValue('--rsb')) || 0) * parseFloat(getComputedStyle(line).fontSize);
          const box = nm.getBoundingClientRect().right;
          return [last, box, window.scrollY];
        })()""")
        return abs(r[0] - r[1]) <= 8, f'QUENTIN ink right={r[0]:.1f} .name right={r[1]:.1f} scrollY={r[2]}'
    check('desktop: QUENTIN right edge within 8px of .name', edge)

    def inspect():
        pg.mouse.move(5, 300)
        pg.keyboard.press('i')
        pg.wait_for_function("document.documentElement.classList.contains('is-inspect')", timeout=3000)
        pg.keyboard.press('i')
        pg.wait_for_function("!document.documentElement.classList.contains('is-inspect')", timeout=3000)
        return True, 'on then off'
    check('desktop: key I toggles html.is-inspect', inspect)

    def case_flow():
        pg.locator('.work-row').first.scroll_into_view_if_needed()
        pg.wait_for_timeout(600)
        pg.locator('.work-row').first.click()
        pg.wait_for_function("!document.querySelector('.case').hidden", timeout=4000)
        h = pg.evaluate('location.hash')
        pg.wait_for_timeout(900)
        t1 = pg.text_content('#case-title')
        pg.keyboard.press('ArrowRight')
        pg.wait_for_function(f"document.querySelector('#case-title') && document.querySelector('#case-title').textContent !== {t1!r}", timeout=4000)
        t2 = pg.text_content('#case-title')
        pg.wait_for_timeout(500)
        pg.go_back()
        pg.wait_for_function("document.querySelector('.case').hidden", timeout=5000)
        return bool(h) and t1 != t2, f'hash={h} title {t1!r} -> {t2!r}, closed after back'
    check('desktop: first .work-row opens case, ArrowRight changes title, back closes', case_flow)

    def theme():
        before = pg.evaluate("document.documentElement.dataset.theme || 'dark'")
        pg.evaluate("sessionStorage.setItem('smoke-keep','1')")
        pg.locator('.theme-btn').click()
        pg.wait_for_timeout(400)
        after = pg.evaluate("document.documentElement.dataset.theme || 'dark'")
        pg.reload(wait_until='load')
        pg.wait_for_selector('html.is-ready', state='attached', timeout=10000)
        kept = pg.evaluate("document.documentElement.dataset.theme || 'dark'")
        pg.evaluate("localStorage.removeItem('ql-theme'); sessionStorage.removeItem('smoke-keep')")
        return before != after and kept == after, f'{before} -> {after}, after reload {kept}'
    check('desktop: theme button toggles data-theme and persists after reload', theme)

    def mail_toast():
        pg.locator('.mail').scroll_into_view_if_needed()
        pg.wait_for_timeout(500)
        pg.locator('.mail').click()
        pg.wait_for_function("document.querySelector('.toast').classList.contains('is-on')", timeout=3000)
        return True, pg.text_content('.toast')
    check('desktop: clicking .mail shows the toast', mail_toast)
    def p9_copy():
        pg.evaluate("navigator.clipboard.writeText('x')")
        pg.locator('.mail-copy').click(); pg.wait_for_timeout(150)
        lbl = pg.text_content('.mail-copy'); clip = pg.evaluate('navigator.clipboard.readText()')
        k = pg.evaluate("[document.querySelectorAll('.chips, .kit-skills').length, document.querySelectorAll('.kit-table > div').length, document.querySelector('.contact-avail span').textContent === document.querySelector('.brief [data-avail]').textContent]")
        return lbl == 'Copié' and clip == pg.get_attribute('.mail', 'data-mail') and k == [0, 5, True], f'label={lbl} clip={clip} kit/avail={k}'
    check('P9: Copier copies the address, kit table has 5 rows, availability matches the hero', p9_copy)
    check('desktop: no errors after interactions', lambda: (not pg.errs, pg.errs[:3]))
    ctx.close()

    # deep link
    ctx, pg = ctx_page(b)
    def deep():
        load(pg, '#lco')
        pg.wait_for_function("!document.querySelector('.case').hidden", timeout=5000)
        t = pg.text_content('#case-title').strip()
        pg.wait_for_timeout(900)
        pg.keyboard.press('Escape')
        pg.wait_for_function("document.querySelector('.case').hidden", timeout=5000)
        return t == 'LCO', f'title={t!r}, Escape closed, errors={pg.errs[:2]}'
    check('desktop: /#lco opens the LCO case, Escape closes', deep)
    ctx.close()

    # ---------------- mobile ----------------
    ctx, pg = ctx_page(b, mobile=True)
    load(pg)
    pg.wait_for_timeout(2500)
    check('mobile: no console/page errors on load', lambda: (not pg.errs, pg.errs[:3]))
    check('mobile: QUENTIN right edge within 8px of .name', edge)
    def dock():
        # fix A1: away while the hero CTAs / live links are on screen, back once past them
        top = pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
        lb = pg.evaluate("document.querySelector('.hero .live').getBoundingClientRect().bottom + scrollY")
        for yy in range(0, int(lb), 40): pg.evaluate(f'window.scrollTo(0, {yy})'); pg.wait_for_timeout(16)
        pg.evaluate(f'window.scrollTo(0, {int(lb) - 30})'); pg.wait_for_timeout(700)
        shown = not pg.evaluate("document.querySelector('.dock').classList.contains('dock-hidden')")
        r = pg.locator('.dock').bounding_box()
        pg.evaluate('window.scrollTo(0, 0)'); pg.wait_for_timeout(500)
        return top and shown and r and r['x'] >= 0 and r['x'] + r['width'] <= 390 and r['y'] + r['height'] <= 844, f'hidden at top={top} shown past CTAs={shown} box={r}'
    check('mobile: .dock away over the hero CTAs, then visible and inside the viewport', dock)
    def mob_case():
        pg.locator('.work-row').first.scroll_into_view_if_needed()
        pg.wait_for_timeout(700)
        pg.locator('.work-row').first.tap()
        pg.wait_for_function("!document.querySelector('.case').hidden", timeout=4000)
        h = pg.evaluate('location.hash')
        pg.wait_for_timeout(900)
        pg.go_back()
        pg.wait_for_function("document.querySelector('.case').hidden", timeout=5000)
        return bool(h), f'hash={h}'
    check('mobile: tapping first .work-row opens the case, back closes', mob_case)
    def mob_mail():
        # P9 : au doigt, le tap ouvre la messagerie (mailto + sujet) après l'onde, sans toast
        cdp = pg.context.new_cdp_session(pg); cdp.send('Page.enable')
        navs = []
        cdp.on('Page.frameRequestedNavigation', lambda e: navs.append(e.get('url')))
        pg.locator('.mail').scroll_into_view_if_needed()
        pg.wait_for_timeout(600)
        pg.locator('.mail').tap()
        pg.wait_for_timeout(1300)
        # main.js bloque mailto sous navigator.webdriver (pas de client mail ouvert par les tests) : le toast de test en tient lieu
        wd, tst = pg.evaluate("[navigator.webdriver, document.querySelector('.toast').textContent]")
        nav_ok = any(u and u.startswith('mailto:') and 'subject=' in u for u in navs)
        return nav_ok or (wd and 'mailto bloqu' in tst), f'navs={navs} webdriver={wd} toast={tst!r}'
    check('mobile: tapping .mail navigates to mailto (P9; guarded toast under webdriver)', mob_mail)
    check('mobile: no errors after interactions', lambda: (not pg.errs, pg.errs[:3]))
    ctx.close()

    # ---------------- P2: boot, fitted type, intro ----------------
    # intro on a fresh desktop load: CLS stays tiny, name letters end at width 100, the Inspect cameo shows once per session
    ctx, pg = ctx_page(b)
    ctx.add_init_script("""window.__cls = 0; window.__cameo = 0;
      try { new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) window.__cls += e.value; })).observe({ type: 'layout-shift', buffered: true }); } catch (e) {}
      new MutationObserver(() => { const t = document.querySelector('.cameo-tag'); if (t && !window.__cameo) window.__cameo = t.textContent; }).observe(document, { childList: true, subtree: true });""")
    load(pg)
    pg.wait_for_timeout(3600)
    def p2_intro():
        r = pg.evaluate("""({ cls: window.__cls, html: document.documentElement.className,
          w: [...document.querySelectorAll('.name .ch')].map(c => c.style.getPropertyValue('--w')),
          lede: getComputedStyle(document.querySelector('.hero .lede')).opacity, cameo: window.__cameo })""")
        import re as _re
        ok = (r['cls'] < 0.02 and 'js' in r['html'].split() and 'is-named' in r['html'].split() and r['lede'] == '1'
              and all(w.strip() in ('', '100') for w in r['w']) and bool(_re.fullmatch(r'H1 · Anybody 850 · \d+\s×\s\d+', r['cameo'] or '')))
        return ok, f"CLS={r['cls']:.4f} html={r['html']!r} lede={r['lede']} --w={sorted(set(r['w']))} cameo={r['cameo']!r}"
    check('P2 desktop: fresh load CLS < 0.02, is-named, letters back to --w 100, cameo label shown', p2_intro)
    def p2_cameo_once():
        pg.reload(wait_until='load')
        pg.wait_for_selector('html.is-named', state='attached', timeout=5000)
        pg.wait_for_timeout(2600)
        c = pg.evaluate('window.__cameo')
        return not c, f'cameo after reload={c!r}'
    check('P2 desktop: no cameo on reload in the same session', p2_cameo_once)
    ctx.close()

    # main.js never runs: after the 4 s gate html loses .js and every reveal is visible
    ctx, pg = ctx_page(b)
    ctx.route('**/main.js*', lambda r: r.abort())
    def p2_abort():
        pg.goto(BASE + Q, wait_until='load')
        pg.wait_for_timeout(4500)
        r = pg.evaluate("""({ html: document.documentElement.className,
          hidden: [...document.querySelectorAll('.reveal, .hero .wrap, .hero-meta > *')].filter(e => getComputedStyle(e).opacity !== '1' || getComputedStyle(e).visibility !== 'visible').length })""")
        return 'js' not in r['html'].split() and r['hidden'] == 0, f"html={r['html']!r} hidden reveals={r['hidden']}"
    check('P2: main.js blocked -> .js removed after 4 s, everything visible', p2_abort)
    ctx.close()

    # JavaScript disabled: the noscript project list is there (8 rows, 5 links)
    ctx = b.new_context(java_script_enabled=False, viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    def p2_nojs():
        pg.goto(BASE + Q, wait_until='load')
        rows = pg.locator('.work-list--static .work-row').count()
        links = pg.locator('.work-list--static a').count()
        lede = pg.locator('.hero .lede').evaluate('e => getComputedStyle(e).opacity')
        return rows == 8 and links == 8 and lede == '1', f'rows={rows} links={links} lede opacity={lede}'
    check('P2: no-JS page shows the static project list and the hero', p2_nojs)
    ctx.close()

    # ---------------- P3: accessibility, tokens, theme, dialog ----------------
    ctx, pg = ctx_page(b)
    load(pg)
    def p3_a11y():
        # grey text tokens stay AA in both themes, h1 is read as one name, gutter reserved, hover rules are hover-only
        r = pg.evaluate("""() => {
          const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
          const rgb = c => { cx.clearRect(0,0,1,1); cx.fillStyle = c; cx.fillRect(0,0,1,1); return [...cx.getImageData(0,0,1,1).data].slice(0,3); };
          const L = c => { const f = v => { v /= 255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); }; return .2126*f(c[0]) + .7152*f(c[1]) + .0722*f(c[2]); };
          const cr = (a, b) => { const x = L(rgb(a)), y = L(rgb(b)); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
          const out = {}; const root = document.documentElement; const keep = root.dataset.theme;
          for (const t of ['dark', 'light']) { root.dataset.theme = t; const s = getComputedStyle(root); let m = 99;
            for (const ink of ['--ink-2', '--ink-3']) for (const bg of ['--paper', '--paper-2', '--paper-3']) m = Math.min(m, cr(s.getPropertyValue(ink).trim(), s.getPropertyValue(bg).trim()));
            out[t] = +m.toFixed(2); }
          if (keep) root.dataset.theme = keep; else delete root.dataset.theme;
          const bad = []; const walk = (rules, inH) => { for (const r of rules) { if (r.media) walk(r.cssRules, inH || /hover:\\s*hover/.test(r.media.mediaText));
            else if (r.selectorText && r.selectorText.includes(':hover') && !inH) bad.push(r.selectorText); } };
          for (const s of document.styleSheets) { try { walk(s.cssRules, false); } catch (e) {} }
          return { c: out, gutter: getComputedStyle(root).scrollbarGutter, hoverOutside: bad, h1label: document.querySelector('h1').getAttribute('aria-label') };
        }""")
        snap = pg.locator('h1').aria_snapshot()
        ok = min(r['c'].values()) >= 4.5 and r['gutter'] == 'stable' and not r['hoverOutside'] and r['h1label'] is None and snap.strip() == '- heading "Quentin Louis" [level=1]'
        return ok, f"min contrast ink-2/3 on papers={r['c']} gutter={r['gutter']} hover outside media={r['hoverOutside'][:3]} h1={snap.strip()!r}"
    check('P3: AA grey tokens (dark+light), h1 name, scrollbar-gutter, hover rules in (hover: hover)', p3_a11y)
    def p3_keys():
        # skip link moves focus to #travaux, Tab reaches the first row; .seg is one tab stop driven by arrows
        pg.evaluate("window.scrollTo(0, 0); document.activeElement && document.activeElement.blur()")
        pg.focus('.skip[href="#travaux"]'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
        a = pg.evaluate('document.activeElement.id')
        pg.keyboard.press('Tab')
        row = pg.evaluate("document.activeElement.classList.contains('work-row') && document.activeElement.dataset.i")
        tabs = pg.evaluate("[...document.querySelectorAll('.lab-props .seg button')].map(b => b.tabIndex)")
        pg.focus('.lab-props .seg button[aria-checked=true]'); pg.keyboard.press('ArrowRight')
        seg = pg.evaluate("[document.activeElement.dataset.state, document.activeElement.getAttribute('aria-checked'), [...document.querySelectorAll('.lab-props .seg button')].filter(b => b.tabIndex === 0).length]")
        pg.keyboard.press('ArrowLeft')
        ok = a == 'travaux' and row == '0' and tabs == [0, -1, -1, -1] and seg == ['hover', 'true', 1]
        return ok, f'skip->{a} tab->row {row} seg tabindex={tabs} after ArrowRight={seg}'
    check('P3: skip link focus + Tab to first row; .seg roving tabindex and arrows', p3_keys)
    def p3_case_race():
        # closing then reopening fast leaves a usable dialog; the page behind is inert only while open;
        # an arrow key during the close does not reopen the sheet
        pg.evaluate("document.querySelector('#travaux').scrollIntoView()"); pg.wait_for_timeout(600)
        rows = pg.locator('.work-row')
        rows.nth(0).click(); pg.wait_for_timeout(1000)
        f = pg.evaluate("[document.activeElement.id, document.querySelector('main').inert]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
        rows.nth(1).click(force=True); pg.wait_for_timeout(1200)
        o = pg.evaluate("[!document.querySelector('.case').hidden, document.querySelector('.case').classList.contains('is-open'), document.body.classList.contains('no-scroll'), document.querySelector('main').inert]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(1200)
        c = pg.evaluate("[document.querySelector('.case').hidden, document.querySelector('main').inert, document.body.classList.contains('no-scroll')]")
        ok = f == ['case-title', True] and o == [True, True, True, True] and c == [True, False, False] and not pg.errs
        return ok, f'first open focus/inert={f} reopened={o} closed(hidden,inert,no-scroll)={c} errs={pg.errs[:2]}'
    check('P3: case close/reopen race, inert page, initial focus on title, no reopen on arrow while closing', p3_case_race)
    def p3_theme():
        # E7: the theme switches at once (View Transitions crossfade, no html.theme-anim token transition):
        # colours and meta theme-color are final at +150 ms, and the switch survives a reload
        pg.evaluate("window.__t0 = performance.now(); document.querySelector('.theme-btn').click()")
        pg.wait_for_function('performance.now() - window.__t0 >= 150')
        mid = pg.evaluate("[getComputedStyle(document.body).backgroundColor, document.querySelector('meta[name=theme-color]').content, document.documentElement.classList.contains('theme-anim')]")
        pg.wait_for_timeout(600)
        end = pg.evaluate("[getComputedStyle(document.body).backgroundColor, document.querySelector('meta[name=theme-color]').content]")
        pg.evaluate("sessionStorage.setItem('smoke-keep', '1')")
        pg.reload(wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached', timeout=10000)
        rl = pg.evaluate("document.querySelector('meta[name=theme-color]').content")
        pg.click('.theme-btn'); pg.wait_for_timeout(700)
        back = pg.evaluate("document.querySelector('meta[name=theme-color]').content")
        pg.evaluate("sessionStorage.removeItem('smoke-keep')")
        ok = mid == ['rgb(244, 246, 255)', '#f4f6ff', False] and end == ['rgb(244, 246, 255)', '#f4f6ff'] and rl == '#f4f6ff' and back == '#09090b'
        return ok, f'+150ms body/meta/theme-anim={mid} end={end} after reload meta={rl} back to dark meta={back}'
    check('P3/E7: theme switches at once (crossfade), meta theme-color follows toggle and reload', p3_theme)
    ctx.close()

    ctx, pg = ctx_page(b)
    load(pg)
    def p3_tokens_focus():
        # radius/mono tokens applied (no 11/11.5px text outside covers and Inspect overlays), readable notes,
        # demo button focus ring shows at once, sliders announce their unit
        r = pg.evaluate("""() => { const seen = new Set(), bad = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (w.nextNode()) { const e = w.currentNode.parentElement; if (!w.currentNode.textContent.trim() || seen.has(e) || e.closest('.cover, .ruler, .probe')) continue; seen.add(e);
              const f = getComputedStyle(e).fontSize; if (parseFloat(f) < 11) bad.push(e.className || e.tagName); }
            const rad = ['.lab', '.cv-thumb', '.peek-in'].map(s => getComputedStyle(document.querySelector(s)).borderTopLeftRadius);
            const note = getComputedStyle(document.querySelector('.sec-note'));
            return { bad, rad, note: [note.fontFamily.split(',')[0].replace(/"/g, ''), parseFloat(note.fontSize)], sheet: getComputedStyle(document.querySelector('.case-sheet')).borderTopLeftRadius }; }""")
        pg.evaluate("document.querySelector('.lab').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(600)
        pg.focus('.seg button[aria-checked=true]'); pg.keyboard.press('Tab')
        d = pg.evaluate("(() => { const s = getComputedStyle(document.activeElement); return [document.activeElement.className, s.outlineWidth, s.outlineColor]; })()")
        vt = pg.evaluate("[...document.querySelectorAll('[data-token]')].map(i => i.getAttribute('aria-valuetext'))")
        ok = (not r['bad'] and r['rad'] == ['12px'] * 3 and r['sheet'] == '16px' and r['note'][0] == 'Anybody' and r['note'][1] >= 16
              and 'demo-btn' in d[0] and d[1] == '2px' and not d[2].endswith(', 0)') and vt == ['10 px', '26 px', '650', '100 %'])
        return ok, f"text under 11px={r['bad'][:3]} radii={r['rad']} sheet={r['sheet']} note={r['note']} demo focus={d} valuetext={vt}"
    check('P3: tokens (radii, mono sizes, reading notes), demo-btn focus ring, slider valuetext', p3_tokens_focus)
    ctx.close()

    ctx, pg = ctx_page(b, mobile=True)
    load(pg)
    def p3_touch():
        # after a tap the CTA returns to its resting accent style (no sticky hover fill); dock and CV line fit small phones
        pg.wait_for_timeout(1500)
        pg.locator('.hero a.btn--accent', has_text='Voir les projets').tap(); pg.wait_for_timeout(600)
        st = pg.evaluate("(() => { const b = document.querySelector('.hero a.btn--accent'); return [getComputedStyle(b).backgroundColor, getComputedStyle(b).color, getComputedStyle(b, '::before').transform]; })()")
        rest = st[2] != 'none' and not st[2].endswith(', 0)')
        pg.set_viewport_size({'width': 320, 'height': 700}); pg.wait_for_timeout(400)
        dk = pg.evaluate("(() => { const d = document.querySelector('.dock').getBoundingClientRect(); const c = [...document.querySelector('.cv-meta').children].map(e => e.getBoundingClientRect()); return [Math.round(d.left), Math.round(d.right), innerWidth, c[1].top >= c[0].bottom ? 99 : Math.round(c[1].left - c[0].right), Math.round(c[1].right - document.querySelector('.cv-card').getBoundingClientRect().right)]; })()")
        ok = st[0] == 'rgb(35, 61, 244)' and st[1] == 'rgb(255, 255, 255)' and rest and dk[0] >= 0 and dk[1] <= dk[2] and dk[3] >= 12 and dk[4] <= 1 and not pg.errs   # P9 : les actions du CV passent à la ligne (99) ou gardent 12 px, sans déborder de la carte
        return ok, f'CTA +600ms bg/color/::before={st} dock@320 left/right/vw + cv-meta gap={dk} errs={pg.errs[:2]}'
    check('P3 mobile: tapped CTA back to resting style, dock and CV line fit at 320', p3_touch)
    ctx.close()

    # ---------------- P4: phones, tablets, extreme viewports ----------------
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(1500)
    HID = "document.querySelector('.dock').classList.contains('dock-hidden')"
    def p4_dock():
        # first screen answers the screener (P5: role in the brief above the dock); 44px targets; hides on the way down (past the hero), back on the way up and at the bottom
        e = pg.evaluate("[document.querySelector('.brief dd').getBoundingClientRect().bottom, document.querySelector('.dock').getBoundingClientRect().top, Math.min(...[...document.querySelectorAll('.dock a')].map(a => a.getBoundingClientRect().height))]")
        pg.mouse.move(195, 500)
        for i in range(12): pg.mouse.wheel(0, 100); pg.wait_for_timeout(60)
        pg.wait_for_timeout(1200); down = pg.evaluate(HID)
        pg.mouse.wheel(0, -60); pg.wait_for_timeout(1000); up = pg.evaluate(HID)
        pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(500); bottom = pg.evaluate(HID)
        ok = e[0] < e[1] and e[2] >= 44 and down and not up and not bottom
        return ok, f'brief role bottom/dock top/min link h={[round(v) for v in e]} hidden after down={down} after up={up} at bottom={bottom}'
    check('P4 mobile: first screen rhythm, 44px dock links, direction-aware dock hiding', p4_dock)
    def p4_case():
        # after an anchor jump, opening then closing a case keeps the scroll position; the top bar leaves while the sheet is open
        # from past the hero: at the top the dock is away over the CTAs (fix A1)
        pg.evaluate("window.scrollTo(0, 1400)"); pg.wait_for_timeout(200); pg.mouse.wheel(0, -80); pg.wait_for_timeout(900)
        pg.locator('.dock a').nth(1).tap(); pg.wait_for_timeout(1900)
        pg.evaluate("document.querySelector('#travaux').scrollIntoView()"); pg.wait_for_timeout(700)
        pg.locator('.work-row').first.tap(); pg.wait_for_timeout(1200)
        y0 = pg.evaluate('Math.round(scrollY)')
        tb = pg.evaluate("[getComputedStyle(document.querySelector('.topbar')).transform, document.querySelector('.topbar').getBoundingClientRect().bottom]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(1000)
        c = pg.evaluate(f"[Math.round(scrollY), {HID}, getComputedStyle(document.querySelector('.dock')).opacity]")
        ty = float(tb[0].strip(')').split(',')[5]) if tb[0].startswith('matrix') else 0
        ok = ty < 0 and tb[1] <= 0 and abs(c[0] - y0) < 2 and not c[1] and float(c[2]) > .9 and not pg.errs
        return ok, f'open topbar={tb} y at open={y0} after close y/hidden/opacity={c} errs={pg.errs[:2]}'
    check('P4 mobile: case open hides top bar, close keeps scroll position and shows the dock', p4_case)
    ctx.close()
    def p4_viewports():
        out = {}
        for w, h, mob in ((844, 390, True), (1024, 1366, True), (1919, 1000, False), (1920, 1000, False), (2560, 1440, False)):
            c2 = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mob, has_touch=mob)
            g = c2.new_page(); g.goto(BASE + Q, wait_until='load'); g.wait_for_selector('html.is-ready', state='attached'); g.wait_for_timeout(1800)
            out[w] = g.evaluate("[Math.round(document.querySelector('.name').getBoundingClientRect().height), Math.round(document.querySelector('.hero').getBoundingClientRect().height), Math.round(document.querySelector('.hero .wrap').getBoundingClientRect().width), document.documentElement.scrollWidth <= document.documentElement.clientWidth]")
            c2.close()
        ok = (out[844][0] <= .58 * 390 + 4 and out[1024][1] <= 900 and out[1920][2] >= out[1919][2] and 1680 < out[2560][2] <= 2080
              and all(v[3] for v in out.values()))
        return ok, f'[name h, hero h, wrap w, no overflow] = {out}'
    check('P4: landscape name cap, tall tablet hero, wide max never shrinks at 1920, no overflow', p4_viewports)
    c3 = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True, reduced_motion='reduce')
    g = c3.new_page(); g.goto(BASE + Q, wait_until='load'); g.wait_for_selector('html.is-ready', state='attached')
    def p4_reduce():
        seen = []
        # fix A1: away over the hero CTAs (static, no motion); never hides past them
        start = int(g.evaluate("document.querySelector('.hero').offsetHeight"))
        for yy in range(start, start + 3000, 150):
            g.evaluate(f'window.scrollTo(0, {yy})')
            # IntersectionObserver des CTA puis onScroll : quelques images, pas un délai fixe (machine chargée)
            g.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))")
            seen.append(g.evaluate(HID))
        g.wait_for_timeout(200); seen.append(g.evaluate(HID))
        return not any(seen), f'{len(seen)} samples from {start}, hidden={any(seen)}'
    check('P4 reduced motion: dock never hides past the hero CTAs', p4_reduce)
    c3.close()

    # ---------------- P5: recruiter hero, editorial pass, share metadata ----------------
    ctx, pg = ctx_page(b)
    load(pg); pg.wait_for_timeout(2600)
    def p5_hero():
        # brief under the name, all in the first screen at 1440 x 900; CTA row on grid column 9, equal buttons; 3 live sites; CV opens (no download)
        r = pg.evaluate("""(() => { const R = s => document.querySelector(s).getBoundingClientRect();
          const w = [...document.querySelectorAll('.cta-row .btn')].map(e => e.getBoundingClientRect().width), g = document.querySelector('.cta-row .btn--ghost');
          return [R('.brief').bottom, R('.hero').height, R('.cta-row').left - R('.grid-overlay .grid12 > span:nth-child(9)').left, w[0] - w[1],
                  [...document.querySelectorAll('.hero .live a[target=_blank]')].map(a => a.hostname).join(' '), g.hasAttribute('download'), g.target,
                  [...document.querySelectorAll('.brief-cell')].map(e => getComputedStyle(e).opacity).join('')]; })()""")
        ok = (r[0] < 900 and abs(r[1] - 900) < .5 and abs(r[2]) <= 1 and abs(r[3]) <= 1 and r[4] == 'wei-go.fr lez-go.fr du-logo-a-la-scene.vercel.app'
              and not r[5] and r[6] == '_blank' and r[7] == '11111' and not pg.errs)
        return ok, f'brief bottom/hero h/cta-col9/btn diff/live/download/target/opacities={r} errs={pg.errs[:2]}'
    check('P5 desktop: brief in the first screen, CTA row on column 9, live links, CV opens', p5_hero)
    def p5_text():
        # visible text (page + every case sheet): typographic apostrophes, narrow space before : ; ? !, no em dash, no emoji; share metadata parses
        scan = r"""(() => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
          while ((n = w.nextNode())) { if (n.parentElement.closest('script, style, noscript')) continue; const t = n.nodeValue;
            if (/\w'\w/.test(t) || / [:;?!](\s|$)/.test(t) || t.includes('\u2014') || /\p{Emoji_Presentation}|\uFE0F/u.test(t)) out.push(t.trim().slice(0, 50)); }
          return out; })()"""
        bad = pg.evaluate(scan)
        seen = []
        for i in range(8):
            pg.evaluate(f"document.querySelectorAll('.work-row')[{i}].click()"); pg.wait_for_timeout(250)
            seen.append(pg.evaluate("document.querySelector('#case-title')?.textContent || ''")); bad += pg.evaluate(scan)
            pg.keyboard.press('Escape'); pg.wait_for_timeout(950)
        bad += [] if len(set(seen)) == 8 else ['case sheets opened: ' + str(seen)]
        ld = pg.evaluate("JSON.parse(document.querySelector('script[type=\"application/ld+json\"]').textContent)['@type']")
        meta = pg.evaluate("[document.querySelector('meta[property=\"og:image:width\"]')?.content, document.querySelector('meta[name=\"twitter:card\"]')?.content, document.querySelector('link[rel=icon]')?.getAttribute('href')]")
        ok = not bad and ld == 'Person' and meta == ['1200', 'summary_large_image', 'assets/favicon-32.png'] and not pg.errs
        return ok, f'bad text={bad[:4]} ld={ld} meta={meta} errs={pg.errs[:2]}'
    check('P5: typography over page and case sheets, JSON-LD and share metadata', p5_text)
    ctx.close()
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(3000)
    def p5_mobile():
        # 390 x 844: the role is readable in the first screen; brief on 2 columns (first cell full width); no horizontal scroll
        r = pg.evaluate("""(() => { const c = [...document.querySelectorAll('.brief-cell')].map(e => e.getBoundingClientRect());
          const dd = document.querySelector('.brief dd').getBoundingClientRect();
          return [Math.round(dd.bottom), getComputedStyle(document.querySelector('.brief-cell')).opacity, Math.round(c[0].width), Math.round(c[1].width), Math.round(c[2].left - c[1].left), document.documentElement.scrollWidth]; })()""")
        ok = r[0] < 780 and r[1] == '1' and r[2] > 1.9 * r[3] and r[4] > 0 and r[5] <= 390 and not pg.errs
        return ok, f'role bottom/opacity/cell widths/col offset/scrollWidth={r} errs={pg.errs[:2]}'
    check('P5 mobile: role in the first screen, brief on 2 columns', p5_mobile)
    ctx.close()
    # ---- P5 verifier additions ----
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(3000)
    def p5v_mobile_cta():
        # 390 x 844: each brief answer on two lines at most (16 px, balanced); both hero CTAs fully in the first screen
        # and not covered: the dock is away while they are on screen (fix A1)
        r = pg.evaluate("""(() => { const d = document.querySelector('.dock'); const t = d.classList.contains('dock-hidden') ? 1e9 : d.getBoundingClientRect().top;
          const b = [...document.querySelectorAll('.cta-row .btn')].map(e => Math.round(e.getBoundingClientRect().bottom));
          const h = [...document.querySelectorAll('.brief dd')].map(e => Math.round(e.getBoundingClientRect().height));
          return [Math.min(Math.round(t), innerHeight), b, h]; })()""")
        ok = len(r[1]) == 2 and max(r[1]) <= r[0] and max(r[2]) <= 44 and not pg.errs
        return ok, f'dock top/cta bottoms/dd heights={r} errs={pg.errs[:2]}'
    check('P5v mobile: both hero CTAs fully visible and uncovered at 390x844, brief answers on one line', p5v_mobile_cta)
    ctx.close()
    ctx, pg = ctx_page(b)
    load(pg); pg.wait_for_timeout(2600)
    def p5v_live_head():
        # live links: hover (fine pointer) and keyboard focus draw the underline; head keeps no og:url/canonical, relative og:image, reminder comment; JSON-LD has no worksFor/url
        pg.locator('.live a').nth(0).hover(); pg.wait_for_timeout(600)
        hov = pg.evaluate("getComputedStyle(document.querySelectorAll('.live a')[0]).backgroundSize")
        pg.mouse.move(600, 300); pg.wait_for_timeout(100)
        pg.evaluate("document.querySelector('.cta-row .btn--ghost').focus()"); pg.keyboard.press('Tab'); pg.wait_for_timeout(600)
        foc = pg.evaluate("[document.activeElement.getAttribute('href'), getComputedStyle(document.activeElement).backgroundSize]")
        head = pg.evaluate("""(() => { const j = JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent);
          return [!!document.querySelector('meta[property="og:url"], link[rel=canonical]'), document.querySelector('meta[property="og:image"]').content,
                  'worksFor' in j || 'url' in j, document.head.innerHTML.includes('URL absolue de og:image')]; })()""")
        ok = hov.startswith('100%') and foc == ['https://wei-go.fr', '100% 1px'] and head == [False, 'assets/og.jpg', False, True] and not pg.errs
        return ok, f'hover={hov} focus={foc} head(ogurl/canon, og:image, worksFor/url, comment)={head}'
    check('P5v desktop: live link underline on hover and focus; head stays domain-free', p5v_live_head)
    ctx.close()
    def p5v_assets():
        # share card and icons: sizes, weight, opaque apple-touch-icon (iOS fills transparency with black)
        import os
        from PIL import Image
        A = 'C:/Users/quent/Projects/portfolio-quentin/assets/'
        og, f32, ati = Image.open(A + 'og.jpg'), Image.open(A + 'favicon-32.png'), Image.open(A + 'apple-touch-icon.png')
        corner = ati.convert('RGBA').getpixel((0, 0))
        ok = og.size == (1200, 630) and os.path.getsize(A + 'og.jpg') < 200 * 1024 and f32.size == (32, 32) and ati.size == (180, 180) and corner[3] == 255
        return ok, f'og={og.size} {os.path.getsize(A + "og.jpg")}B favicon={f32.size} apple={ati.size} corner={corner}'
    check('P5v: og.jpg 1200x630 < 200 KB, favicon 32, opaque apple-touch-icon 180', p5v_assets)
    # ---- P6 verifier additions ----
    ctx, pg = ctx_page(b)
    load(pg); pg.wait_for_timeout(2600)
    def p6_peek():
        # hover row 3: peek on grid column 9, centred on the row (or clamped), reel on cover 3, no rotation;
        # the lerp loop stops (only Lenis keeps a rAF); Inspect mode never shows the peek
        y = pg.evaluate("document.querySelectorAll('.work-row')[2].getBoundingClientRect().top + scrollY - 350")
        pg.evaluate("y => window.__lenis ? __lenis.scrollTo(y, {immediate: true, force: true}) : scrollTo(0, y)", y); pg.wait_for_timeout(400)
        r = pg.evaluate("(() => { const r = document.querySelectorAll('.work-row')[2].getBoundingClientRect(); return [r.left + 200, r.top + r.height / 2]; })()")
        pg.mouse.move(r[0], r[1] - 60); pg.mouse.move(r[0], r[1], steps=4); pg.wait_for_timeout(1600)   # P10v: the row's 1.1s reveal transform can end ~1.05s after the hover and re-aim once (a finite lerp, not a loop)
        d = pg.evaluate("""(() => { const pk = document.querySelector('.peek'), row = document.querySelectorAll('.work-row')[2];
          const p = pk.getBoundingClientRect(), w = row.getBoundingClientRect(), col = document.querySelector('.grid-overlay .grid12 > span:nth-child(9)').getBoundingClientRect().left;
          const top = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--topbar')) || 60;
          const exp = Math.min(Math.max(w.top + w.height / 2, top + 24 + p.height / 2), innerHeight - 24 - p.height / 2);
          const m = new DOMMatrix(getComputedStyle(document.querySelector('.peek-track')).transform);
          return [pk.classList.contains('is-on'), Math.round(p.left - col), Math.round(p.top + p.height / 2 - exp), Math.round(m.m42 + 2 * p.height), new DOMMatrix(getComputedStyle(pk).transform).b]; })()""")
        idle = pg.evaluate("() => new Promise(res => { let c = 0; const o = window.requestAnimationFrame; window.requestAnimationFrame = f => { if (!String(f).includes('lenis.raf')) c++; return o(f); }; setTimeout(() => { window.requestAnimationFrame = o; res(c); }, 700); })")
        pg.keyboard.press('i'); pg.wait_for_timeout(200)
        pg.mouse.move(r[0], r[1] - 70); pg.mouse.move(r[0], r[1], steps=3); pg.wait_for_timeout(500)
        ins = pg.evaluate("document.querySelector('.peek').classList.contains('is-on')")
        pg.keyboard.press('i'); pg.wait_for_timeout(200)
        ok = d[0] and abs(d[1]) <= 1 and abs(d[2]) <= 2 and abs(d[3]) <= 1 and d[4] == 0 and idle == 0 and not ins and not pg.errs
        return ok, f'on/dx col9/dy centre/reel offset/rot={d} extra rAF idle={idle} peek in inspect={ins} errs={pg.errs[:2]}'
    check('P6 desktop: peek on column 9 facing the hovered row, reel on its cover, loop stops, hidden in Inspect', p6_peek)
    def p6_list_case():
        # list: only 'en ligne' tags (3), no DS/Web/App/Brand; case hero: a 16:9 canvas (site in a browser window) centred on the
        # sheet columns, Figma caption (the real capture's domain) and live size
        t = pg.evaluate("""(() => [[...document.querySelectorAll('.work-row .ttl')].map(e => e.textContent).join('|'),
          document.querySelectorAll('.work-row .live-tag').length])()""")
        pg.goto(BASE + Q + '#wei', wait_until='load'); pg.wait_for_timeout(1500)
        c = pg.evaluate("""(() => { const f = document.querySelector('.case .frame').getBoundingClientRect(), m = document.querySelector('.case-hero').getBoundingClientRect();
          return [+(f.width / f.height).toFixed(3), Math.round(Math.abs((m.left + m.right) / 2 - (document.querySelector('.case-cols').getBoundingClientRect().left + document.querySelector('.case-cols').getBoundingClientRect().right) / 2)),
                  document.querySelector('.frame-label span').textContent, document.querySelector('.frame-size').textContent]; })()""")
        import re as _re
        ok = not _re.search(r'\b(DS|Web|App|Brand)\b', t[0]) and t[1] == 3 and abs(c[0] - 16 / 9) <= .01 and c[1] <= 1 and c[2] == 'wei-go.fr' \
            and _re.match(r'^\d+\u00a0×\u00a0\d+$', c[3]) is not None and not pg.errs
        return ok, f'titles={t[0][:80]} live tags={t[1]} frame ratio/canvas vs cols/caption/size={c}'
    check('P6: list shows only en ligne tags; case hero 16:9 canvas with caption and size', p6_list_case)
    ctx.close()
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(2600)
    def p6_touch():
        # touch list: 56 px 4:5 thumbs (real WebP covers, the 200 px file), the row at the viewport centre alone gets .is-focus
        y = pg.evaluate("(() => { const r = document.querySelectorAll('.work-row')[3].getBoundingClientRect(); return r.top + scrollY + r.height / 2 - innerHeight / 2; })()")
        pg.evaluate("y => window.__lenis ? __lenis.scrollTo(y, {immediate: true, force: true}) : scrollTo(0, y)", y); pg.wait_for_timeout(600)
        d = pg.evaluate("""(() => { const rows = [...document.querySelectorAll('.work-row')];
          const im = [...document.querySelectorAll('.thumb img')].filter(i => i.complete && i.naturalWidth > 0);
          return [rows.map(r => { const t = r.querySelector('.thumb'); return t ? t.offsetWidth + 'x' + t.offsetHeight : 'none'; }),
                  rows.map((r, i) => r.classList.contains('is-focus') ? i : -1).filter(i => i >= 0),
                  im.length > 0 && im.every(i => i.currentSrc.endsWith('/cover-200.webp') && i.alt === '')]; })()""")
        ok = all(x == '56x70' for x in d[0]) and d[1] == [3] and d[2] and not pg.errs
        return ok, f'thumbs={set(d[0])} focused={d[1]} loaded 200px covers, alt empty={d[2]} errs={pg.errs[:2]}'
    check('P6 mobile: 56 px thumbs, single centre-focus row, real 200 px covers', p6_touch)
    ctx.close()
    def p6_honest():
        # no invented labels; removed projects are gone; every image of the 8 sheets has alt, width and height
        import os as _os
        pj = open('C:/Users/quent/Projects/portfolio-quentin/projects.js', encoding='utf-8').read()
        cvp = 'C:/Users/quent/Projects/portfolio-quentin/covers.css'
        cv = open(cvp, encoding='utf-8').read() if _os.path.exists(cvp) else ''
        bad = [s for s in ['142', 'arrivés', 'Bus 1', 'KEDGE', 'Montaigne', 'Mission 3', '12 questions', '8 min', 'WEI<br>2026', 'Math.random',
                           'Chapitre 02', '45%', 'Le poulet du jour', 'backdrop-filter'] if s in pj or s in cv]
        qua = any('radial-gradient' in l for l in cv.splitlines() if 'cv-qua' in l)
        gone = [s for s in ["id: 'springbreak'", "id: 'zecheck'", "id: 'poulettes'", 'Rôtisserie', 'ZE CHECK'] if s in pj]
        c2 = b.new_context(viewport={'width': 1440, 'height': 900}); m = c2.new_page(); load(m); m.wait_for_timeout(800)
        noattr = []
        for pid in ['wei', 'lezgo', 'livre-blanc', 'one-piece', 'quasar', 'lco', 'pop-mart-bumi', 'meoow']:
            m.evaluate(f"location.hash = '#{pid}'"); m.wait_for_timeout(500)
            noattr += m.evaluate("[...document.querySelectorAll('.case-body img')].filter(i => !i.hasAttribute('alt') || !i.getAttribute('width') || !i.getAttribute('height')).map(i => i.src)")
        c2.close()
        return not bad and not qua and not gone and not noattr, f'invented strings={bad} radial in .cv-qua={qua} removed projects left={gone} img without alt/size={noattr[:3]}'
    check('P6: honest data (no invented labels, removed projects gone, alt and size on every image)', p6_honest)

    # ---------------- P7 case sheet ----------------
    ctx, pg = ctx_page(b, mobile=True)
    load(pg, '#wei'); pg.wait_for_timeout(1200)
    def p7_fit():
        # 390: every title fits its mask; bar shows the position, no Esc key on touch
        bad, seen = [], []
        for k in range(8):
            if k: pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(600)
            seen.append(pg.evaluate("document.querySelector('#case-title').textContent"))
            if pg.evaluate("[...document.querySelectorAll('.case-title .ln > span')].some(s => s.scrollWidth > s.clientWidth + 1)"): bad.append(seen[-1])
        idx = pg.evaluate("[document.querySelector('.case-idx').textContent.slice(0, 7), getComputedStyle(document.querySelector('.case-close kbd')).display]")
        return not bad and len(set(seen)) == 8 and idx == ['08 / 08', 'none'] and not pg.errs, f'overflow={bad} idx/kbd={idx} errs={pg.errs[:2]}'
    check('P7 mobile: 8 fitted case titles, position in the bar, Esc hidden on touch', p7_fit)
    ctx.close()
    ctx, pg = ctx_page(b)
    load(pg, '#wei'); pg.wait_for_timeout(1200)
    def p7_desk():
        # site pill, copy link, directional swap, 60 px drag springs back, 320 px drag closes
        site = pg.evaluate("document.querySelector('.case-bar a.case-site')?.getAttribute('href')")
        pg.click('.case-share'); pg.wait_for_timeout(150)
        clip = pg.evaluate("navigator.clipboard.readText()") == pg.evaluate("location.origin + location.pathname + '#wei'")
        lbl = pg.evaluate("document.querySelector('.case-share-lbl').textContent")
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(90)
        mid = pg.evaluate("+getComputedStyle(document.querySelector('.case-body')).opacity")
        pg.wait_for_timeout(1100)
        after = pg.evaluate("[location.hash, +getComputedStyle(document.querySelector('.case-body')).opacity, !!document.querySelector('.case-site')]")
        x, y = pg.evaluate("(() => { const r = document.querySelector('.case-idx').getBoundingClientRect(); return [r.right + 40, r.top + r.height / 2]; })()")
        pg.mouse.move(x, y); pg.mouse.down()
        for i in range(1, 13): pg.mouse.move(x, y + 5 * i); pg.wait_for_timeout(25)
        pg.wait_for_timeout(150); pg.mouse.up(); pg.wait_for_timeout(700)
        back = pg.evaluate("[getComputedStyle(document.querySelector('.case-sheet')).transform, document.querySelector('.case').hidden]")
        pg.mouse.move(x, y); pg.mouse.down()
        for i in range(1, 17): pg.mouse.move(x, y + 20 * i); pg.wait_for_timeout(16)
        pg.mouse.up(); pg.wait_for_timeout(1000)
        closed = pg.evaluate("[document.querySelector('.case').hidden, location.hash]")
        ok = site == 'https://wei-go.fr' and clip and lbl == 'Copié' and mid < 1 and after == ['#quasar', 1, True] and back == ['none', False] and closed == [True, ''] and not pg.errs
        return ok, f'site={site} clip={clip} lbl={lbl} mid={mid} after={after} back={back} closed={closed} errs={pg.errs[:2]}'
    check('P7 desktop: site pill, copy link, directional swap, drag back and drag to close', p7_desk)
    ctx.close()

    # ---------------- P7v additions ----------------
    ctx, pg = ctx_page(b, mobile=True)
    pg.set_viewport_size({'width': 360, 'height': 740})
    load(pg, '#wei'); pg.wait_for_timeout(1200)
    def p7v_small():
        # 360: every title fits, the bar stays on one line with the short site label, arrows carry one glyph each
        bad, bars = [], []
        for k in range(8):
            if k: pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(600)
            r = pg.evaluate("""(() => { const bar = document.querySelector('.case-bar');
              return [document.querySelector('#case-title').textContent,
                [...document.querySelectorAll('.case-title .ln > span')].some(s => s.scrollWidth > s.clientWidth + 1),
                bar.scrollWidth <= bar.clientWidth, Math.round(bar.getBoundingClientRect().height)]; })()""")
            if r[1]: bad.append(r[0])
            bars.append(r[2] and r[3] <= 64)
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(800)   # back to WEI & GO
        site = pg.evaluate("[...document.querySelector('.case-site').childNodes].filter(n => n.nodeType === 3 || (getComputedStyle(n).display !== 'none' && !n.classList.contains('sr-only'))).map(n => n.textContent).join('').replace(/[ \\n]+/g, ' ').trim()")
        arrows = pg.evaluate("[...document.querySelectorAll('.case-nav [data-step]')].map(e => e.querySelectorAll('svg').length + e.textContent.trim() + '|' + getComputedStyle(e, '::before').content)")
        # touch targets: 44 px+ tall, and the edges of each pill belong to that pill (no stolen taps)
        hits = pg.evaluate("""[...document.querySelectorAll('.case-nav > *')].every(e => { const r = e.getBoundingClientRect(), y = r.top + r.height / 2, x = r.left + r.width / 2;
          const own = (px, py) => document.elementFromPoint(px, py)?.closest('.case-nav > *') === e;
          return own(r.left + 1, y) && own(r.right - 1, y) && own(x, r.top - 5.5) && own(x, r.bottom + 5.5); })""")
        return not bad and all(bars) and site == 'Site' and arrows == ['1|none', '1|none'] and hits and not pg.errs, f'overflow={bad} bar one line={bars} site={site!r} arrows={arrows} hit areas own={hits} errs={pg.errs[:2]}'
    check('P7v 360: fitted titles, one-line bar, short site label, one glyph per arrow, own hit areas', p7v_small)
    ctx.close()
    ctx, pg = ctx_page(b)
    load(pg, '#lco'); pg.wait_for_timeout(1200)
    def p7v_links():
        # every project has a link (no mailto block); Behance: pill « Behance », one « Lien : Behance » cell in the facts, no duplicate
        z = pg.evaluate("[!!document.querySelector('.case-site'), !!document.querySelector('.case-ask')]")
        dd = pg.evaluate("[...document.querySelectorAll('.case-meta dd')].map(d => { const c = d.cloneNode(true); c.querySelectorAll('.sr-only').forEach(x => x.remove()); return c.textContent; })")
        pill = pg.evaluate("[...document.querySelector('.case-site').childNodes].filter(n => n.nodeType === 3 || (getComputedStyle(n).display !== 'none' && !n.classList.contains('sr-only'))).map(n => n.textContent).join('').replace(/[ \\n]+/g, ' ').trim()")
        return z == [True, False] and dd.count('Behance') == 1 and dd[-1] == 'Behance' and pill == 'Behance', f'lco pill/ask={z} dd={dd} pill={pill!r}'
    check('P7v: Behance pill, one Behance link in the facts, no mailto block', p7v_links)
    def p7v_rapid():
        # three quick arrows land on the 3rd next project with nothing stuck; progress fills and resets on reopen
        load(pg, '#wei'); pg.wait_for_timeout(1200)
        for _ in range(3): pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(40)
        pg.wait_for_timeout(1800)
        r = pg.evaluate("[location.hash, document.querySelector('.case-idx').textContent.slice(0, 7), [...document.querySelector('.case-body').children].every(c => getComputedStyle(c).opacity === '1'), getComputedStyle(document.querySelector('.case-body')).opacity]")
        pg.evaluate("document.querySelector('.case-sheet').scrollTop = 1e6"); pg.wait_for_timeout(250)
        full = pg.evaluate("getComputedStyle(document.querySelector('.case-bar'), '::after').transform")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(1100)
        pg.locator('.work-row').nth(1).scroll_into_view_if_needed(); pg.wait_for_timeout(500)
        pg.locator('.work-row').nth(1).click(); pg.wait_for_timeout(1200)
        reset = pg.evaluate("getComputedStyle(document.querySelector('.case-bar'), '::after').transform")
        sx = lambda m: float(m.split('(')[1].split(',')[0])
        ok = r == ['#lezgo', '04 / 08', True, '1'] and sx(full) >= .98 and sx(reset) <= .02 and not pg.errs
        return ok, f'rapid={r} progress bottom={full} after reopen={reset} errs={pg.errs[:2]}'
    check('P7v desktop: rapid ArrowRight x3 lands on 04, reading progress fills and resets', p7v_rapid)
    ctx.close()
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    load(pg, '#wei'); pg.wait_for_timeout(600)
    def p7v_reduce():
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(40)
        r = pg.evaluate("[location.hash, [...document.querySelector('.case-body').children].every(c => getComputedStyle(c).opacity === '1')]")
        return r == ['#quasar', True] and not pg.errs, f'{r} errs={pg.errs[:2]}'
    check('P7v reduced motion: arrow swap is instant', p7v_reduce)
    ctx.close()

    # P8: lab outputs, contrast readout, reset, contexts
    ctx, pg = ctx_page(b)
    load(pg); pg.evaluate("document.querySelector('.lab').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(1400)
    def p8_lab():
        import json as _json
        pg.click('.seg--tabs [data-fmt="json"]')
        j = _json.loads(pg.evaluate("document.querySelector('#lab-out').textContent"))
        pg.evaluate("(() => { const i = document.querySelector('[data-token=radius]'); i.value = 20; i.dispatchEvent(new Event('input', { bubbles: true })); })()")
        pg.click('.seg--tabs [data-fmt="tw"]')
        tw = pg.evaluate("document.querySelector('#lab-out').textContent")
        pg.click('.swatches [data-fill="accent"]'); pg.wait_for_timeout(100)
        ro = pg.evaluate("document.querySelector('.contrast').textContent")
        pg.click('.lab-reset'); pg.wait_for_timeout(550)
        v = pg.evaluate("[...document.querySelectorAll('[data-token]')].map(i => +i.value)")
        ok = j['button']['primary']['radius']['$value'] == '10px' and 'rounded-[20px]' in tw and tw.startswith('@theme {') and ro.startswith('Contraste 6,9:1 · AA') and v == [10, 26, 650, 100]
        return ok and not pg.errs, f'json radius={j["button"]["primary"]["radius"]} tw={tw[:12]!r} readout={ro!r} reset={v} errs={pg.errs[:2]}'
    check('P8: lab JSON (DTCG), Tailwind, contrast readout, reset', p8_lab)
    def c1_states_css():
        # C1 : onglet CSS valide pour Survol, Focus et Inactif (accolades, sélecteur, pas de ': {'),
        # Copier = texte affiché ; C5 : Inactif sans ratio + aria-disabled ; C17 : AAA au-delà de 7:1
        import re as _re
        pg.click('.seg--tabs [data-fmt="css"]'); bad = []
        for st in ['hover', 'focus', 'disabled']:
            pg.click(f'.lab-props .seg [data-state="{st}"]'); pg.wait_for_timeout(80)
            t = pg.evaluate("document.querySelector('#lab-out').textContent")
            if not (t.count('{') == t.count('}') and _re.search(r':(hover|focus-visible|disabled) \{\n', t) and ': {' not in t): bad.append((st, t[-90:]))
            pg.click('.lab-copy'); pg.wait_for_timeout(120)
            if pg.evaluate('navigator.clipboard.readText()').replace('\r\n', '\n') != t: bad.append((st, 'clipboard'))
        dis = [pg.evaluate("document.querySelector('.contrast').textContent"), pg.get_attribute('.demo-btn', 'aria-disabled')]
        pg.click('.lab-props .seg [data-state="default"]'); pg.wait_for_timeout(80)
        dflt = [pg.evaluate("document.querySelector('.contrast').textContent"), pg.get_attribute('.demo-btn', 'aria-disabled')]
        ok = not bad and dis == ['Inactif · contraste non requis', 'true'] and dflt[0].endswith(':1 · AAA') and dflt[1] is None
        return ok and not pg.errs, f'bad={bad} disabled={dis} default={dflt} errs={pg.errs[:2]}'
    check('C1/C5/C17: lab CSS states valid and copied as shown, Inactif readout, AAA', c1_states_css)
    def p8_contexts():
        r = pg.evaluate("[document.querySelectorAll('.steps').length, document.querySelectorAll('.contexts li').length]")
        pg.evaluate("document.querySelector('.contexts').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(1200)
        pg.click('.contexts [data-case="wei"]'); pg.wait_for_timeout(900)
        h = pg.evaluate('location.hash')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
        f = pg.evaluate("document.activeElement.dataset.case")
        return r == [0, 3] and h == '#wei' and f == 'wei' and not pg.errs, f'steps/rows={r} hash={h} focus back={f} errs={pg.errs[:2]}'
    check('P8: contexts replace the steps, WEI & GO opens #wei, Esc returns focus', p8_contexts)
    ctx.close()

    # ---------------- P8v additions ----------------
    # keyboard: the tablist is one Tab stop, arrows switch format; Focus state draws the ring and outputs :focus-visible
    ctx, pg = ctx_page(b)
    load(pg); pg.evaluate("document.querySelector('.lab').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(1400)
    def p8v_keys():
        pg.click('.lab-props .seg [data-state="focus"]'); pg.wait_for_timeout(80)
        ow = pg.evaluate("getComputedStyle(document.querySelector('.demo-btn')).outlineWidth")
        css = pg.evaluate("document.querySelector('#lab-out').textContent")
        pg.evaluate("document.querySelector('.demo-btn').focus()")
        seq = []
        for _ in range(4):
            pg.keyboard.press('Tab'); seq.append(pg.evaluate("document.activeElement.getAttribute('role') || document.activeElement.tagName"))
        pg.evaluate("document.querySelector('.seg--tabs [aria-selected=true]').focus()"); pg.keyboard.press('ArrowRight')
        t = pg.evaluate("[document.activeElement.dataset.fmt, document.querySelector('#lab-out').getAttribute('aria-labelledby')]")
        ok = ow == '2px' and ':focus-visible' in css and seq.count('tab') == 1 and t == ['json', 'tab-json']
        return ok and not pg.errs, f'outline={ow} focus-visible={":focus-visible" in css} tabseq={seq} arrow={t} errs={pg.errs[:2]}'
    check('P8v desktop: Focus state, tablist is one Tab stop, ArrowRight switches format', p8v_keys)
    ctx.close()
    # narrow panels: Propriétés never wider than the lab (was clipped at 320/360), indicators sit on their option
    def p8v_fit():
        bad = []
        for vw, mob in [(320, True), (1180, False)]:
            c2 = b.new_context(viewport={'width': vw, 'height': 800}, is_mobile=mob, has_touch=mob)
            p2 = c2.new_page(); p2.goto(BASE + Q, wait_until='load'); p2.wait_for_selector('html.is-ready', state='attached'); p2.wait_for_timeout(900)
            p2.evaluate("""() => { document.querySelector('.lab-props .seg [data-state="disabled"]').click(); document.querySelector('.swatches [data-fill="outline"]').click(); document.querySelector('.seg--tabs [data-fmt="tw"]').click(); const d = document.querySelector('.lab-details'); if (d) d.open = true; }""")   # touch folds the code: measure it as the visitor sees it, unfolded
            p2.wait_for_timeout(700)
            r = p2.evaluate("""(() => { const lab = document.querySelector('.lab').getBoundingClientRect();
              const over = [...document.querySelectorAll('.lab-panel')].filter(x => x.getBoundingClientRect().right > lab.right + 1).length;
              const ind = [...document.querySelectorAll('.seg')].map(s => { const i = s.querySelector('.seg-ind').getBoundingClientRect(); const o = s.querySelector('[aria-checked=true],[aria-selected=true]').getBoundingClientRect(); return Math.max(Math.abs(i.left - o.left), Math.abs(i.width - o.width)); });
              const clipped = [...document.querySelectorAll('.lab .seg button')].filter(x => x.scrollWidth > x.clientWidth + 1).length;
              return [over, Math.max(...ind), clipped]; })()""")
            if r[0] or r[1] > 1 or r[2]: bad.append((vw, r))
            c2.close()
        return not bad, f'bad={bad}'
    check('P8v 320 + 1180: Propriétés inside the lab, seg indicators on their option, no clipped labels', p8v_fit)
    # mobile: details folded, sticky canvas keeps the button visible while the Rayon slider is in view
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(600)
    def p8v_mobile():
        det = pg.evaluate("document.querySelector('.lab-details').open")
        pg.evaluate("document.querySelector('[data-token=radius]').scrollIntoView({ block: 'end' })"); pg.wait_for_timeout(1300)
        r = pg.evaluate("""(() => { const d = document.querySelector('.demo-btn').getBoundingClientRect(); const s = document.querySelector('[data-token=radius]').getBoundingClientRect();
          return [d.top >= 0 && d.bottom <= innerHeight, s.top >= 0 && s.bottom <= innerHeight, document.querySelector('[data-token=radius]').getBoundingClientRect().height]; })()""")
        return det is False and r == [True, True, 44] and not pg.errs, f'details open={det} [demo visible, slider visible, range h]={r} errs={pg.errs[:2]}'
    check('P8v 390 touch: code folded, sticky canvas visible with the Rayon slider, 44px ranges', p8v_mobile)
    ctx.close()

    # ---------------- P9v : parcours et contact ----------------
    def p9_goto(pg, sel, off=0):
        pg.evaluate(f"""(() => {{ const y = document.querySelector('{sel}').getBoundingClientRect().top + scrollY - {off};
          window.__lenis ? window.__lenis.scrollTo(y, {{immediate:true}}) : scrollTo(0, y); }})()""")
        pg.wait_for_timeout(1300)
    ctx, pg = ctx_page(b)
    load(pg); pg.wait_for_timeout(2200)
    def p9v_path():
        want = [['2021', '2021'], ['2022', '2022'], ['2022-12', 'déc.\u00a02022|sept.\u00a02023'], ['2023-09', 'sept.\u00a02023|juil.\u00a02024'],
                ['2024-01', 'janv.\u00a02024|août\u00a02024'], ['2024-09', 'sept.\u00a02024'], ['2024-11', 'nov.\u00a02024|sept.\u00a02025'], ['2025-09', 'sept.\u00a02025|sept.\u00a02026']]
        got = pg.evaluate("""[...document.querySelectorAll('.timeline time')].map(t => [t.getAttribute('datetime'),
             [...t.children].filter(s => !s.classList.contains('sr-only')).map(s => s.textContent).join('|')])""")
        p9_goto(pg, '#parcours')
        g = pg.evaluate("""(() => { const c = [...document.querySelectorAll('.grid-overlay .grid12 > span')].map(i => i.getBoundingClientRect());
          const rail = document.querySelector('.rail').getBoundingClientRect();
          return [Math.max(...[...document.querySelectorAll('.timeline time')].map(t => Math.abs(t.getBoundingClientRect().right - c[4].right))),
                  Math.abs(rail.left + rail.width / 2 - c[5].left), Math.abs(document.querySelector('.kit-table').getBoundingClientRect().left - c[4].left),
                  document.querySelector('.cv-card').getBoundingClientRect().right <= document.querySelector('.timeline').getBoundingClientRect().left]; })()""")
        cv = pg.evaluate("""(() => { const c = document.querySelector('.cv-card'), t = c.querySelector('a.cv-thumb'), d = [...c.querySelectorAll('a')].find(a => a.textContent.trim().startsWith('Télécharger'));   // A3: the name adds (PDF, 339 Ko) in sr-only
          return [t.target, t.hasAttribute('download'), !!d && d.hasAttribute('download'), c.querySelector('.cv-meta').textContent.includes('PDF · 1 page · 339 Ko'), document.querySelectorAll('.chips, .kit-skills').length]; })()""")
        ok = got == want and g[0] <= 2 and g[1] <= 2 and g[2] <= 2 and g[3] and cv == ['_blank', False, True, True, 0]
        return ok, f'dates ok={got == want} geo(time,rail,kit dev; cv clear)={[round(x, 2) if not isinstance(x, bool) else x for x in g]} cv={cv}'
    check('P9v 1440: CV-exact dates (no-break spaces), timeline and kit on the 12-col grid, CV card links', p9v_path)
    def p9v_ripple():
        p9_goto(pg, '#contact')
        pg.evaluate("navigator.clipboard.writeText('x')")
        box = pg.locator('.mail-txt').bounding_box()
        pg.mouse.click(box['x'] + box['width'] * .3, box['y'] + box['height'] / 2)
        pg.wait_for_timeout(150)
        mid = pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].some(c => (c.style.getPropertyValue('--w') || '100') !== '100')")
        pg.mouse.move(5, 5); pg.wait_for_timeout(1500)
        end = pg.evaluate("[...document.querySelectorAll('.mail-txt .ch')].every(c => (c.style.getPropertyValue('--w') || '100') === '100')")
        clip = pg.evaluate("navigator.clipboard.readText()")
        lab = pg.evaluate("[document.querySelector('.mail').getAttribute('aria-label'), getComputedStyle(document.querySelector('.mail-hint .only-touch')).display]")
        return mid and end and clip == 'quentinlouis97400@gmail.com' and lab[0].startswith('Écrivez-moi\u202f: copier') and lab[1] == 'none' and not pg.errs, f'ripple={mid} rest={end} clip={clip} label={lab} errs={pg.errs[:2]}'
    check('P9v desktop: ÉCRIVEZ-MOI click copies and ripples, then rests; fine-pointer label', p9v_ripple)
    ctx.close()
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(2000)
    def p9v_mobile():
        p9_goto(pg, '#contact', 60)
        r = pg.evaluate("""(() => { const l = document.querySelector('.links'); const tops = new Set([...l.querySelectorAll('a')].map(a => Math.round(a.getBoundingClientRect().top)));
          return [getComputedStyle(l).display, getComputedStyle(l).gridTemplateColumns.split(' ').length, tops.size, getComputedStyle(document.querySelector('.mail-sub')).flexDirection,
            getComputedStyle(document.querySelector('.mail-hint .only-fine')).display, document.querySelector('.mail').getAttribute('aria-label').startsWith('Écrivez-moi\u202f: écrire'),
            document.documentElement.scrollWidth <= innerWidth]; })()""")
        return r == ['grid', 2, 2, 'column', 'none', True, True] and not pg.errs, f'{r} errs={pg.errs[:2]}'
    check('P9v 390 touch: links 2x2 grid, stacked address, touch hint and label', p9v_mobile)
    ctx.close()

    # ---------------- P10 (motion language) ----------------
    VT_HOOK = """(() => { window.__vt = 0; const o = document.startViewTransition;
      if (o) document.startViewTransition = function (...a) { window.__vt++; return o.apply(document, a); }; })()"""
    def p10_y(pg, y):
        pg.evaluate(f"window.__lenis ? window.__lenis.scrollTo({y}, {{immediate:true, force:true}}) : scrollTo(0,{y})")
    def p10_top(pg, sel):
        return pg.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top + scrollY")
    ctx, pg = ctx_page(b)
    load(pg); pg.evaluate(VT_HOOK); pg.wait_for_timeout(2200)
    def p10_btn():
        n = pg.evaluate("document.querySelectorAll('[data-magnetic]').length")
        js = "(() => { const a = document.querySelector('.hero .btn--accent'), g = document.querySelector('.hero .btn--ghost'); return [a.offsetWidth, g.getBoundingClientRect().x, getComputedStyle(a).transform, getComputedStyle(a.querySelector('.lbl')).getPropertyValue('--bw').trim()]; })()"
        pg.mouse.move(5, 400); pg.wait_for_timeout(300)
        b0 = pg.evaluate(js)
        bx = pg.locator('.hero .btn--accent').bounding_box()
        pg.mouse.move(bx['x'] + bx['width'] * .8, bx['y'] + bx['height'] * .3, steps=4); pg.wait_for_timeout(550)
        b1 = pg.evaluate(js)
        pg.mouse.move(5, 400)
        ok = n == 0 and b1[3] == '112' and abs(b1[0] - b0[0]) <= .5 and abs(b1[1] - b0[1]) <= .5 and b1[2] == 'none'
        return ok, f'magnetic={n} before={b0} hover={b1}'
    check('P10 desktop: no magnetic buttons, width hover (--bw 112) without layout shift', p10_btn)
    def p10_scroll():
        mt = p10_top(pg, '#methode .sec-title')
        p10_y(pg, mt - 900 * .9); pg.wait_for_timeout(400)
        a = pg.evaluate("getComputedStyle(document.querySelector('#methode .sec-title')).getPropertyValue('--swd').trim()")
        p10_y(pg, mt - 900 * .4); pg.wait_for_timeout(400)
        c = pg.evaluate("getComputedStyle(document.querySelector('#methode .sec-title')).getPropertyValue('--swd').trim()")
        p10_y(pg, p10_top(pg, '.contact') - 900 * .85); pg.wait_for_timeout(400)
        e = pg.evaluate("getComputedStyle(document.querySelector('.mail-txt')).getPropertyValue('--wb').trim()")
        p10_y(pg, 99999); pg.wait_for_timeout(600)
        m = pg.evaluate("""(() => { const cs = document.querySelectorAll('.mail-txt .ch'); const w = document.querySelector('.contact .wrap');
          return [getComputedStyle(document.querySelector('.mail-txt')).getPropertyValue('--wb').trim(), w.getBoundingClientRect().right - parseFloat(getComputedStyle(w).paddingRight) - (cs[cs.length - 1].getBoundingClientRect().right - (parseFloat(getComputedStyle(document.querySelector('.mail-txt')).getPropertyValue('--rsb')) || 0) * parseFloat(getComputedStyle(document.querySelector('.mail-txt')).fontSize))]; })()""")
        ok = int(a) < 86 and c == '86' and int(e) < 100 and m[0] == '100' and -0.5 <= m[1] <= 2
        return ok, f'title swd 90%={a} 40%={c}; mail wb entry={e} settled={m[0]} gap={m[1]:.2f}px'
    check('P10 desktop: section title opens on scroll (62 to 86), ÉCRIVEZ-MOI ends flush at --wb 100', p10_scroll)
    def p10_morph():
        p10_y(pg, p10_top(pg, '#travaux') - 100); pg.wait_for_timeout(700)
        rb = pg.locator('.work-row').nth(0).bounding_box()
        pg.mouse.move(rb['x'] + rb['width'] * .3, rb['y'] + rb['height'] / 2, steps=5); pg.wait_for_timeout(900)
        pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(150)
        mid = pg.evaluate("document.getAnimations().some(a => a.effect && /view-transition-group\\(case-frame\\)/.test(a.effect.pseudoElement || ''))")
        pg.wait_for_timeout(1100)
        end = pg.evaluate("""[window.__vt, location.hash, document.querySelector('.case-body').classList.contains('is-in'), document.activeElement.id,
          document.querySelector('.peek-in').style.viewTransitionName + (document.querySelector('.case-hero .frame') || {style: {}}).style.viewTransitionName + document.querySelector('.case-sheet').style.viewTransitionName]""")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(1100)
        p10_y(pg, p10_top(pg, '#travaux') - 100); pg.mouse.move(3, 3); pg.wait_for_timeout(600)
        pg.evaluate("document.querySelectorAll('.work-row')[1].focus()")
        pg.keyboard.press('Enter'); pg.wait_for_timeout(1200)
        kb = pg.evaluate("[window.__vt, location.hash, document.querySelector('.case-body').classList.contains('is-in'), document.activeElement.id]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(1000)
        ok = mid and end == [1, '#wei', True, 'case-title', ''] and kb == [1, '#quasar', True, 'case-title'] and not pg.errs
        return ok, f'frame morph running={mid} end={end} keyboard={kb} errs={pg.errs[:2]}'
    check('P10 desktop: mouse open from the preview morphs (view transition), keyboard open does not', p10_morph)
    ctx.close()
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.evaluate(VT_HOOK); pg.wait_for_timeout(2000)
    def p10_mobile():
        p10_y(pg, 99999); pg.wait_for_timeout(700)
        m = pg.evaluate("""(() => { const cs = document.querySelectorAll('.mail-txt .ch'); const w = document.querySelector('.contact .wrap');
          return [getComputedStyle(document.querySelector('.mail-txt')).getPropertyValue('--wb').trim(), w.getBoundingClientRect().right - parseFloat(getComputedStyle(w).paddingRight) - (cs[cs.length - 1].getBoundingClientRect().right - (parseFloat(getComputedStyle(document.querySelector('.mail-txt')).getPropertyValue('--rsb')) || 0) * parseFloat(getComputedStyle(document.querySelector('.mail-txt')).fontSize)), document.documentElement.scrollWidth <= innerWidth]; })()""")
        p10_y(pg, p10_top(pg, '#travaux')); pg.wait_for_timeout(800)
        rb = pg.locator('.work-row').nth(0).bounding_box()
        pg.touchscreen.tap(rb['x'] + rb['width'] / 2, rb['y'] + rb['height'] / 2); pg.wait_for_timeout(1200)
        t = pg.evaluate("[window.__vt, document.querySelector('.case').classList.contains('is-open')]")
        ok = m[0] == '100' and -0.5 <= m[1] <= 2 and m[2] and t == [0, True] and not pg.errs
        return ok, f'mail wb={m[0]} gap={m[1]:.2f}px noHScroll={m[2]} tap(vt,open)={t} errs={pg.errs[:2]}'
    check('P10 390 touch: ÉCRIVEZ-MOI flush, tap opens the sheet without view transition', p10_mobile)
    ctx.close()
    # ---------------- P11 Inspecter v2 ----------------
    ctx, pg = ctx_page(b)
    load(pg); pg.wait_for_timeout(2200)
    def p11_enter_select():
        pg.mouse.move(700, 880)
        c = "(()=>{const c=[...document.querySelectorAll('.hero .name-line')].pop().querySelectorAll('.ch');return c[c.length-1].getBoundingClientRect().right})()"
        r0 = pg.evaluate(c)
        pg.keyboard.press('i'); pg.wait_for_timeout(650)
        e = pg.evaluate("""(() => { const d1 = m => m === 'none' || Math.abs(new DOMMatrix(m).d - 1) < 1e-6;
          const L = [...document.querySelectorAll('.spec-label')].map(s => s.getBoundingClientRect()); let bad = 0;
          for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) { const a = L[i], b = L[j]; if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) bad++; }
          return [[...document.querySelectorAll('.grid-overlay .grid12 > span')].every(i => d1(getComputedStyle(i).transform)),
            getComputedStyle(document.querySelector('.ruler-x')).transform, getComputedStyle(document.querySelector('.ruler-y')).transform, L.length, bad,
            [...document.querySelectorAll('.ruler-nums span')].some(s => s.textContent === '1400')]; })()""")
        r1 = pg.evaluate(c)
        pg.evaluate("document.querySelector('.work-row').scrollIntoView({block:'center'})"); pg.wait_for_timeout(900)
        rb = pg.locator('.work-row').first.bounding_box()
        pg.mouse.click(rb['x'] + 300, rb['y'] + rb['height'] / 2); pg.wait_for_timeout(600)
        s = pg.evaluate("[document.querySelector('.case').hidden, document.querySelector('.sel-box').classList.contains('is-on'), !document.querySelector('.inspect-panel').hidden && document.querySelector('.inspect-panel').innerText.includes('Mise en page')]")
        pops = []; ctx.on('page', lambda x: pops.append(x.url))
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(600)
        gb = pg.locator('.hero .cta-row a').nth(1).bounding_box()
        pg.mouse.click(gb['x'] + gb['width'] / 2, gb['y'] + gb['height'] / 2); pg.wait_for_timeout(900)
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        k1 = pg.evaluate("[document.documentElement.classList.contains('has-sel'), document.documentElement.classList.contains('is-inspect')]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
        k2 = pg.evaluate("document.documentElement.classList.contains('is-inspect')")
        ok = e[0] and e[1] == 'none' and e[2] == 'none' and e[3] >= 8 and e[4] == 0 and e[5] and abs(r1 - r0) <= .5 and s == [True, True, True] and not pops and k1 == [False, True] and k2 is False and not pg.errs
        return ok, f'cols/rx/ry/labels/collisions/1400={e} nameShift={r1 - r0:.2f} row(caseHidden,sel,panel)={s} popups={pops} esc1={k1} esc2 on={k2} errs={pg.errs[:2]}'
    check('P11 desktop: I entrance, numbered rulers, labels apart, click selects (no case, no popup), Esc twice', p11_enter_select)
    def p11_panel():
        pg.keyboard.press('i'); pg.wait_for_timeout(600)
        pg.evaluate("document.querySelector('.demo-btn').scrollIntoView({block:'center'})"); pg.wait_for_timeout(900)
        bb = pg.locator('.demo-btn').first.bounding_box()
        pg.mouse.move(bb['x'] + 20, bb['y'] + 20); pg.wait_for_timeout(550)
        tag = pg.evaluate("document.querySelector('.probe-tag').textContent")
        pg.mouse.click(bb['x'] + 20, bb['y'] + 20); pg.wait_for_timeout(400)
        pg.locator('.ip-copy').hover(); pg.wait_for_timeout(800)   # hover ends: panel re-reads the resting fill
        p = pg.evaluate("""[document.querySelector('.ip-colors').innerText, document.querySelector('.ip-code').innerText,
          getComputedStyle(document.querySelector('.demo-btn')).backgroundColor]""")
        pg.locator('.ip-copy').click(); pg.wait_for_timeout(300)
        clip = pg.evaluate("navigator.clipboard.readText()").replace('\r', '')
        pg.keyboard.press('Shift+Enter'); pg.wait_for_timeout(300)
        up = pg.evaluate("document.querySelector('.ip-name').textContent")
        pg.keyboard.press('Escape'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        # fix D14 : une ligne par span dans le bloc affiché, d'où innerText (lignes comprises)
        ok = 'fill #233df4' in tag and '--ink' in p[0] and 'background: var(--ink)' in p[1] and clip == p[1] and up == 'div.stage' and not pg.errs
        return ok, f'probe after hover={tag.splitlines()[-2:]} colours={p[0]!r} bg={p[2]} copied==shown {clip == p[1]} parent={up} errs={pg.errs[:2]}'
    check('P11 desktop: probe waits for the hover fill, panel tokens follow the resting state, Copier le CSS, Shift+Enter', p11_panel)
    ctx.close()
    ctx, pg = ctx_page(b, mobile=True)
    load(pg); pg.wait_for_timeout(2200)
    def p11_touch():
        v = pg.evaluate("[getComputedStyle(document.querySelector('.inspect-touch')).display, getComputedStyle(document.querySelector('.inspect-btn')).display]")
        pg.tap('.inspect-touch'); pg.wait_for_timeout(800)
        on = pg.evaluate("""[[...document.querySelectorAll('.grid-overlay .grid12 > span')].filter(i => getComputedStyle(i).display !== 'none').length,
          getComputedStyle(document.querySelector('.inspect-chip')).visibility, getComputedStyle(document.querySelector('.ruler-x')).display]""")
        pg.evaluate("document.querySelector('.lede').scrollIntoView({block:'center'})"); pg.wait_for_timeout(700)
        lb = pg.locator('.lede').bounding_box()
        pg.touchscreen.tap(lb['x'] + 40, lb['y'] + 10); pg.wait_for_timeout(900)
        sh = pg.evaluate("""(() => { const p = document.querySelector('.inspect-panel'); return [!p.hidden, Math.round(p.getBoundingClientRect().bottom) === innerHeight,
          !p.querySelector('.ip-typo').hidden, document.querySelector('.dock').getBoundingClientRect().top >= innerHeight, document.querySelector('.case').hidden]; })()""")
        pg.tap('.inspect-chip button'); pg.wait_for_timeout(700)
        off = pg.evaluate("[document.documentElement.classList.contains('is-inspect'), document.querySelector('.inspect-panel').hidden]")
        ok = v[0] != 'none' and v[1] == 'none' and on == [4, 'visible', 'none'] and sh == [True, True, True, True, True] and off == [False, True] and not pg.errs
        return ok, f'touch/fine btn={v} cols/chip/ruler={on} sheet(shown,bottom,typo,dockAway,noCase)={sh} quit={off} errs={pg.errs[:2]}'
    check('P11 390 touch: Inspecter button, 4 columns + chip, tap opens the bottom sheet, dock away, Quitter', p11_touch)
    ctx.close()
    ctx = b.new_context(viewport={'width': 320, 'height': 640}, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    load(pg); pg.wait_for_timeout(1800)
    def p11_small():
        br = pg.evaluate("[document.querySelector('.brand').getBoundingClientRect().height, document.querySelector('.brand').getBoundingClientRect().right, document.querySelector('.topbar .btn').getBoundingClientRect().left + 5]")
        pg.tap('.inspect-touch'); pg.wait_for_timeout(800)
        r = pg.evaluate("""[document.querySelector('.inspect-chip').getBoundingClientRect().left, document.querySelector('.inspect-chip').getBoundingClientRect().right,
          Math.max(...[...document.querySelectorAll('.spec-label')].map(s => s.getBoundingClientRect().right)), innerWidth]""")
        ok = br[0] < 30 and br[2] - br[1] >= 8 and r[0] >= 0 and r[1] <= r[3] and r[2] <= r[3] and not pg.errs
        return ok, f'brand h/right, CV left={br} chip l/r, widest label right, vw={r} errs={pg.errs[:2]}'
    check('P11 320 touch: name on one line beside three buttons, chip and block names inside the screen', p11_small)
    ctx.close()

    # ---- P12 : raccourcis, impression, images ----
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    load(pg); pg.wait_for_timeout(1800)
    def p12_keys():
        pg.focus('.hero .btn--accent'); pg.keyboard.press('Shift+Slash'); pg.wait_for_timeout(400)
        rows = pg.evaluate("document.querySelectorAll('.keys-list li').length") if pg.is_visible('.keys') else 0
        pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
        back = not pg.is_visible('.keys') and pg.evaluate("document.activeElement.matches('.hero .btn--accent')")
        pg.keyboard.press('3'); pg.wait_for_timeout(2000)
        sec = pg.evaluate("[Math.round(document.querySelector('#parcours').getBoundingClientRect().top), document.activeElement.id]")
        img = pg.evaluate("document.querySelector('.name-photo img').currentSrc.split('/').pop()")
        ok = rows == 8 and back and abs(sec[0] - 60) <= 2 and sec[1] == 'parcours' and img == 'quentin-band-800.webp' and not pg.errs
        return ok, f'rows={rows} focusBack={back} key3={sec} portrait={img} errs={pg.errs[:2]}'
    check('P12 desktop: ? opens 8 shortcuts, Esc returns focus, 3 jumps to Parcours, WebP portrait', p12_keys)
    def p12_print():
        pg.emulate_media(media='print'); pg.wait_for_timeout(300)
        v = pg.evaluate("""[[...document.querySelectorAll('.reveal, .work-row')].filter(e => getComputedStyle(e).opacity !== '1').length,
          getComputedStyle(document.body).backgroundColor, getComputedStyle(document.querySelector('.topbar')).display]""")
        pg.emulate_media(media='screen')
        return v == [0, 'rgb(255, 255, 255)', 'none'], f'hidden reveals, body bg, topbar={v}'
    check('P12 print: white page, every reveal in its final state, no top bar', p12_print)
    ctx.close()

    # ---- P12v : interrupteur des raccourcis, fiche ouverte, 404, image mobile, mouvement réduit ----
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page(); pg.errs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    load(pg); pg.wait_for_timeout(1800)
    def p12v_switch():
        pg.click('.foot-keys'); pg.wait_for_timeout(350); pg.click('.keys-switch')
        ls = pg.evaluate("localStorage.getItem('ql-keys')")
        pg.reload(wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached'); pg.wait_for_timeout(1500)
        th0 = pg.evaluate("document.documentElement.dataset.theme || ''")
        pg.keyboard.press('i'); pg.keyboard.press('t'); pg.wait_for_timeout(400)
        dead = pg.evaluate("[document.documentElement.classList.contains('is-inspect'), document.documentElement.dataset.theme || '', getComputedStyle(document.querySelector('.inspect-btn kbd')).opacity]")
        pg.click('.inspect-btn'); pg.wait_for_timeout(400)
        btn = pg.evaluate("document.documentElement.classList.contains('is-inspect')")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        pg.evaluate("localStorage.removeItem('ql-keys')")
        ok = ls == 'off' and dead == [False, th0, '0.4'] and btn and not pg.errs
        return ok, f'ls={ls} after reload I/T -> inspect,theme,kbd opacity={dead} (theme before {th0!r}) button works={btn} errs={pg.errs[:2]}'
    check('P12v desktop: switch off persists, I and T do nothing, Inspect button still works', p12v_switch)
    def p12v_case():
        pg.reload(wait_until='load'); pg.wait_for_selector('html.is-ready', state='attached'); pg.wait_for_timeout(1500)
        pg.evaluate("document.querySelector('.work-row').focus()"); pg.keyboard.press('Enter'); pg.wait_for_timeout(1200)
        th0 = pg.evaluate("document.documentElement.dataset.theme || ''"); i0 = pg.evaluate("document.querySelector('.case-idx').textContent.slice(0,2)")
        pg.keyboard.press('t'); pg.keyboard.press('Shift+Slash'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(900)
        v = pg.evaluate("[document.documentElement.dataset.theme || '', document.querySelector('.case-idx').textContent.slice(0,2), document.querySelector('.keys').classList.contains('is-open')]")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(1000)
        ok = v[0] == th0 and i0 == '01' and v[1] == '02' and not v[2] and not pg.errs
        return ok, f'open sheet: T/? ignored, arrow moves {i0}->{v[1]}, theme={v[0]!r}, keys open={v[2]}'
    check('P12v desktop: on an open sheet only arrows and Esc act', p12v_case)
    ctx.close()
    def p12v_extra():
        c2 = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        m = c2.new_page(); errs = []
        m.on('pageerror', lambda e: errs.append(str(e)))
        load(m); m.wait_for_timeout(800)
        img = m.evaluate("[document.querySelector('.name-photo img').currentSrc.split('/').pop(), getComputedStyle(document.querySelector('.foot-keys')).display]")
        r = m.goto(BASE + '404.html', wait_until='load'); m.wait_for_timeout(600)
        f = m.evaluate("[document.documentElement.scrollWidth, innerWidth, !!document.querySelector('a.btn[href=\"/\"]')]")
        c2.close()
        c3 = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        rm = c3.new_page(); load(rm); rm.keyboard.press('3'); rm.wait_for_timeout(500)
        t = rm.evaluate("[Math.round(document.querySelector('#parcours').getBoundingClientRect().top), document.activeElement.id]")
        c3.close()
        ok = img == ['quentin-band-800.webp', 'none'] and r.status == 200 and f[0] <= f[1] and f[2] and abs(t[0] - 59) <= 2 and t[1] == 'parcours' and not errs
        return ok, f'390 portrait/foot-keys={img} 404 status={r.status} width={f} reduced-motion key 3={t} errs={errs[:2]}'
    check('P12v 390 WebP 480 portrait, no shortcut button on touch, 404 page, reduced-motion key 3 under the bar', p12v_extra)

    # ---------------- fix group A (hero, topbar, global) ----------------
    def fa_small_phones():
        # A1: CTAs fully visible, dock away at the top; A5: each live link owns its centre and lower quarter (no stolen taps)
        out, ok = {}, True
        for w, h in ((320, 640), (360, 740), (375, 812)):
            c2 = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True)
            m = c2.new_page(); load(m); m.wait_for_timeout(1800)
            r = m.evaluate("""(() => { const d = document.querySelector('.dock');
              const cta = Math.max(...[...document.querySelectorAll('.cta-row .btn')].map(e => e.getBoundingClientRect().bottom));
              return [Math.round(cta), innerHeight, d.classList.contains('dock-hidden')]; })()""")
            m.evaluate("window.scrollTo(0, document.querySelector('.hero .live').getBoundingClientRect().top + scrollY - 300)"); m.wait_for_timeout(700)
            live = m.evaluate("""[...document.querySelectorAll('.hero .live a')].map(a => { const r = a.getBoundingClientRect();
              return [r.left + r.width / 2, r.left + 2, r.right - 2].every(x => [.5, .75, .95].every(k => document.elementFromPoint(x, r.top + r.height * k)?.closest('a') === a)); })""")
            out[w] = r + [live]
            ok = ok and r[0] <= r[1] and r[2] and all(live)
            c2.close()
        return ok, f'[cta bottom, vh, dock away, live links own their taps] = {out}'
    check('Fix A1/A5: small phones show both hero CTAs, dock away, live links keep their taps', fa_small_phones)
    def fa_topbar_fine():
        # A3: at 320 CSS px with a mouse (400% zoom) the theme button is on screen and works; A13: aria-current follows the section
        c2 = b.new_context(viewport={'width': 320, 'height': 640})
        m = c2.new_page(); load(m); m.wait_for_timeout(1200)
        hit = m.evaluate("(() => { const r = document.querySelector('.theme-btn').getBoundingClientRect(); return !!document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)?.closest('.theme-btn'); })()")
        t0 = m.evaluate("document.documentElement.dataset.theme || 'dark'"); m.click('.theme-btn', timeout=3000); m.wait_for_timeout(600)
        t1 = m.evaluate("document.documentElement.dataset.theme || 'dark'")
        c2.close()
        c3 = b.new_context(viewport={'width': 1440, 'height': 900})
        d = c3.new_page(); load(d); d.wait_for_timeout(1000)
        d.evaluate("window.__lenis ? __lenis.scrollTo(document.querySelector('#parcours'), {immediate: true}) : document.querySelector('#parcours').scrollIntoView()"); d.wait_for_timeout(800)
        cur = d.evaluate("[...document.querySelectorAll('.nav a[aria-current], .dock a[aria-current]')].map(a => a.getAttribute('href') + '=' + a.getAttribute('aria-current'))")
        sp = d.evaluate("getComputedStyle(document.documentElement).scrollPaddingTop")
        c3.close()
        ok = hit and t0 != t1 and cur == ['#parcours=location', '#parcours=location'] and sp != 'auto'
        return ok, f'theme hit={hit} {t0}->{t1} aria-current={cur} scroll-padding-top={sp}'
    check('Fix A2/A3/A13: theme button reachable at 320 with a mouse, aria-current, scroll-padding', fa_topbar_fine)

    # ---------------- fix group B (travaux, fiche projet) ----------------
    AE = "(() => { const a = document.activeElement; return a.tagName + (a.dataset.i ? '[i=' + a.dataset.i + ']' : '') + (a.dataset.case ? '[case=' + a.dataset.case + ']' : ''); })()"
    def fb_focus_return():
        # B2: after a nav/dock jump (#travaux, #methode), closing the sheet gives focus back to its opener; Tab goes on
        out, ok = {}, True
        for mob in (False, True):
            c2 = b.new_context(viewport={'width': 390, 'height': 844} if mob else {'width': 1440, 'height': 900}, is_mobile=mob, has_touch=mob)
            m = c2.new_page(); load(m); m.wait_for_timeout(1500)
            nav = '.dock' if mob else '.nav'
            m.evaluate(f"document.querySelector('{nav} a[href=\"#travaux\"]').click()"); m.wait_for_timeout(1700)
            m.evaluate("document.querySelectorAll('.work-row')[1].focus()"); m.keyboard.press('Enter'); m.wait_for_timeout(1100)
            m.keyboard.press('Escape'); m.wait_for_timeout(800)
            r = [m.evaluate(AE)]; m.keyboard.press('Tab'); r.append(m.evaluate(AE))
            m.evaluate(f"document.querySelector('{nav} a[href=\"#methode\"]').click()"); m.wait_for_timeout(1700)
            m.evaluate("document.querySelector('[data-case=wei]').focus()"); m.keyboard.press('Enter'); m.wait_for_timeout(1100)
            m.keyboard.press('Escape'); m.wait_for_timeout(800)
            r.append(m.evaluate(AE))
            out[390 if mob else 1440] = r
            ok = ok and r == ['BUTTON[i=1]', 'BUTTON[i=2]', 'BUTTON[case=wei]']
            c2.close()
        return ok, f'[after close, next Tab, methode] = {out}'
    check('Fix B2: focus returns to the opener after a section jump (1440 + 390)', fb_focus_return)
    def fb_list_case():
        # B1/B15: the hero is captioned with the capture's real domain (label hidden from AT, the image has its alt); B3: hover never reflows the list;
        # B5: Escape dismisses the peek; B6: bar arrows announce the new project
        c2 = b.new_context(viewport={'width': 1440, 'height': 900})
        m = c2.new_page(); load(m); m.wait_for_timeout(1500)
        m.evaluate("document.querySelector('.nav a[href=\"#travaux\"]').click()"); m.wait_for_timeout(1700)
        H = "[...document.querySelectorAll('.work-row')].map(r => Math.round(r.getBoundingClientRect().height))"
        m.mouse.move(5, 5); base = m.evaluate(H); moved = []
        for n in (2, 6):   # the two longest titles, each scrolled to mid-screen first
            m.mouse.move(5, 5)
            m.evaluate(f"(() => {{ const y = document.querySelectorAll('.work-row')[{n}].getBoundingClientRect().top + scrollY - innerHeight / 2; window.__lenis ? __lenis.scrollTo(y, {{immediate: true, force: true}}) : scrollTo(0, y); }})()"); m.wait_for_timeout(400)
            c = m.evaluate(f"(() => {{ const r = document.querySelectorAll('.work-row')[{n}].getBoundingClientRect(); return [r.left + 150, r.top + r.height / 2]; }})()")
            m.mouse.move(c[0], c[1] - 3); m.mouse.move(*c); m.wait_for_timeout(900)
            if m.evaluate(H) != base: moved.append(n)
        on = m.evaluate("document.querySelector('.peek').classList.contains('is-on')")
        m.keyboard.press('Escape'); m.wait_for_timeout(600)
        off = m.evaluate("[document.querySelector('.peek').classList.contains('is-on'), getComputedStyle(document.querySelectorAll('.work-row')[6].querySelector('.kind')).opacity]")
        m.mouse.move(5, 5)
        m.evaluate("document.querySelectorAll('.work-row')[0].click()"); m.wait_for_timeout(1300)
        cap = m.evaluate("[document.querySelector('.frame-label span').textContent, document.querySelector('.case-hero .frame').getAttribute('role'), document.querySelector('.frame-label').getAttribute('aria-hidden')]")
        m.evaluate("document.querySelector('.case-bar [data-step=\"1\"]').focus()"); m.keyboard.press('Enter'); m.wait_for_timeout(900)
        ann = m.evaluate("document.querySelector('.case-announce').textContent")
        c2.close()
        ok = not moved and on and off[0] is False and float(off[1]) > .95 and cap == ['wei-go.fr', None, 'true'] and ann == 'Projet 2 sur 8\u202f: QUASAR'
        return ok, f'rows reflowed on hover={moved} peek on/after Esc={on}/{off} caption/role/cover hidden={cap} announce={ann!r}'
    check('Fix B1/B3/B5/B6/B15: honest caption, no hover reflow, Esc closes the peek, arrows announced', fb_list_case)
    def fb_bar_fit():
        # B4/B17: the sheet bar stays on one row with Fermer inside the sheet, touch and mouse, 320 to 559 px
        bad = []
        for mob in (True, False):
            for w in (320, 375, 412, 430, 520):
                c2 = b.new_context(viewport={'width': w, 'height': 700}, is_mobile=mob, has_touch=mob)
                m = c2.new_page()
                for pid in ('wei', 'quasar'):
                    m.goto(BASE + Q + '#' + pid, wait_until='load'); m.wait_for_timeout(700)
                    r = m.evaluate("""(() => { const sh = document.querySelector('.case-sheet'), c = document.querySelector('.case-close').getBoundingClientRect();
                      return [Math.round(document.querySelector('.case-bar').getBoundingClientRect().height), Math.round(c.right - sh.getBoundingClientRect().left - sh.clientWidth)]; })()""")
                    if r[0] > 61 or r[1] > 0: bad.append([mob, w, pid, r])
                c2.close()
        kbd = open('C:/Users/quent/Projects/portfolio-quentin/index.html', encoding='utf-8').read().count('<kbd class="only-fine">\u00c9chap</kbd>')
        return not bad and kbd == 1, f'bars over one row or Fermer clipped={bad} Echap kbd={kbd}'
    check('Fix B4/B17: case bar on one row, Fermer visible, 320-520 px touch and mouse; Echap label', fb_bar_fit)

    # ---------------- Fix E (code, perf) ----------------
    def fe_error_fallback():
        # E1: a runtime error before the name entrance (no ResizeObserver) shows everything at once;
        # E4: fiche, lede and CTAs paint without main.js (blocked, seen before the 4 s fallback), the name waits for it
        out = []
        c2 = b.new_context(viewport={'width': 1440, 'height': 900}); m = c2.new_page()
        m.add_init_script("delete window.ResizeObserver;")
        m.goto(BASE + Q + '&e1', wait_until='load'); m.wait_for_timeout(1200)
        out.append(m.evaluate("[document.documentElement.classList.contains('js'), getComputedStyle(document.querySelector('.hero .name')).visibility, getComputedStyle(document.querySelector('.work-row')).opacity, document.querySelectorAll('.work-row').length]"))
        c2.close()
        c2 = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); m = c2.new_page()
        m.route('**/main.js*', lambda route: route.abort())
        m.goto(BASE + Q + '&e4', wait_until='load'); m.wait_for_timeout(300)
        out.append(m.evaluate("['.lede', '.brief-cell', '.cta-row', '.hero .name'].map(s => { const e = document.querySelector(s), c = getComputedStyle(e); return c.visibility + '/' + c.opacity; })"))
        c2.close()
        ok = out[0] == [False, 'visible', '1', 8] and out[1] == ['visible/1', 'visible/1', 'visible/1', 'hidden/1']
        return ok, f'no RO -> js/name/row opacity/rows={out[0]} ; main.js held: lede/brief/cta/name={out[1]}'
    check('Fix E1/E4: error before the entrance shows the page; hero text paints before main.js', fe_error_fallback)
    def fe_idle_loop():
        # E2: no animation frame is requested while idle (Lenis loop on demand), wheel still scrolls smoothly and stops
        c2 = b.new_context(viewport={'width': 1440, 'height': 900}); m = c2.new_page()
        m.add_init_script("(() => { const o = window.requestAnimationFrame.bind(window); window.__rafN = 0; window.requestAnimationFrame = cb => o(t => { window.__rafN++; cb(t); }); })();")
        m.goto(BASE + Q + '&e2', wait_until='load'); m.wait_for_timeout(4000)
        n0 = m.evaluate('window.__rafN'); m.wait_for_timeout(1500); idle = m.evaluate('window.__rafN') - n0
        m.mouse.move(700, 500)
        m.evaluate("window.__ys = []; (function f(){ window.__ys.push(Math.round(scrollY)); if (window.__ys.length < 120) requestAnimationFrame(f); })()")
        m.mouse.wheel(0, 800); m.wait_for_timeout(1800)
        ys = m.evaluate('window.__ys'); n1 = m.evaluate('window.__rafN'); m.wait_for_timeout(1000); after = m.evaluate('window.__rafN') - n1
        lenis = m.evaluate('!!window.__lenis')
        c2.close()
        ok = lenis and idle <= 3 and after <= 3 and len(set(ys)) > 30 and ys[-1] >= 780   # 780 : la fin du défilement doux varie de quelques px
        return ok, f'lenis={lenis} rAF idle 1.5s={idle} distinct wheel positions={len(set(ys))} end={ys[-1]} rAF 1s after={after}'
    check('Fix E2: idle page requests no frames, wheel scroll still smooth', fe_idle_loop)
    def fe_reduce_lock():
        # E3: reduced motion (no Lenis): with a case open, a wheel over the scrim strip does not scroll the page
        c2 = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); m = c2.new_page()
        m.goto(BASE + Q + '&e3#lco', wait_until='load'); m.wait_for_timeout(1200)
        m.mouse.move(700, 8); m.mouse.wheel(0, 2000); m.wait_for_timeout(600)
        r = m.evaluate("[scrollY, getComputedStyle(document.documentElement).overflowY, !!window.__lenis, !document.querySelector('.case').hidden]")
        c2.close()
        return r == [0, 'hidden', False, True], f'scrollY/html overflow/lenis/case open={r}'
    check('Fix E3: reduced motion, open case locks the page scroll', fe_reduce_lock)
    def fe_thumbs():
        # E9: 390 DPR3 list thumbnails load the 200 px covers (56 px x 3), never the 400/800 files
        c2 = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True); m = c2.new_page()
        got = []
        m.on('requestfinished', lambda r: '/assets/projects/' in r.url and got.append('/'.join(r.url.split('?')[0].split('/')[-2:])))
        m.goto(BASE + Q + '&e9', wait_until='load'); m.wait_for_timeout(1500)
        m.evaluate("document.querySelector('#travaux').scrollIntoView()"); m.wait_for_timeout(2000)
        c2.close()
        return len(got) > 0 and all(g.endswith('/cover-200.webp') for g in got), f'requests={sorted(set(got))}'
    check('Fix E9: mobile thumbnails use their own small image files', fe_thumbs)
    b.close()

n_fail = results.count(False)
print(f'{len(results) - n_fail}/{len(results)} checks passed')
sys.exit(1 if n_fail else 0)
