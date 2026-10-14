"""P12 : raccourcis, impression, images, 404. python p12test.py"""
import time, json, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(errors='backslashreplace')   # accents et espaces fines : pas de plantage sur une console redirigée

OUT = 'C:/Users/quent/AppData/Local/Temp/claude/C--Users-quent/7ecaec2d-9cac-488a-8694-2aeea20012bb/scratchpad/'
BASE = 'http://localhost:5178/'
res = []


def ok(name, cond, info=''):
    res.append((name, bool(cond), info))
    print(('PASS ' if cond else 'FAIL ') + name + (' | ' + str(info) if info else ''))


def page(b, w=1440, h=900, mob=False, theme=None, keys=None, reduce=False, js=True):
    ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob,
                        reduced_motion='reduce' if reduce else 'no-preference', java_script_enabled=js)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    init = "sessionStorage.setItem('ql-intro','1');"
    init += f"localStorage.setItem('ql-theme','{theme}');" if theme else "localStorage.removeItem('ql-theme');"
    if keys is not None:
        init += f"localStorage.setItem('ql-keys','{keys}');" if keys else "localStorage.removeItem('ql-keys');"
    if js:
        pg.add_init_script(init)
    return ctx, pg, errs


def go(pg, q=''):
    pg.goto(BASE + '?t=' + str(time.time()) + q, wait_until='networkidle')
    pg.wait_for_timeout(1800)


with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')

    for theme in ('dark', 'light'):
        # 1. ? ouvre, 8 lignes, Échap ferme et rend le focus
        ctx, pg, errs = page(b, theme=theme, keys='')
        go(pg)
        pg.focus('.hero .btn--accent')
        pg.keyboard.press('Shift+Slash')
        pg.wait_for_timeout(400)
        vis = pg.is_visible('.keys')
        rows = pg.evaluate("document.querySelectorAll('.keys-list li').length")
        ok(f'[{theme}] ? opens popover with 8 rows', vis and rows == 8, (vis, rows))
        pg.wait_for_function("document.querySelector('.keys').getAnimations().every(a => a.playState !== 'running')", timeout=3000)
        box = pg.evaluate("(()=>{const r=document.querySelector('.keys').getBoundingClientRect(), t=document.querySelector('.theme-btn').getBoundingClientRect();return {top:r.top,right:r.right,w:r.width,tr:t.right}})()")
        ok(f'[{theme}] popover under the tools, right edge = tools edge, 320 wide', abs(box['top'] - 68) < 1 and abs(box['right'] - box['tr']) < 1.5 and abs(box['w'] - 320) < 1, box)
        # touche enfoncée : T bascule le thème, sa touche s'allume
        before = pg.evaluate("document.documentElement.dataset.theme || 'dark'")
        pg.keyboard.press('t')
        pr = pg.evaluate("document.querySelector('.keys kbd[data-k=\"t\"]').classList.contains('is-press')")
        bg = pg.evaluate("getComputedStyle(document.querySelector('.keys kbd[data-k=\"t\"]')).backgroundColor")
        pg.wait_for_timeout(250)
        pr2 = pg.evaluate("document.querySelector('.keys kbd[data-k=\"t\"]').classList.contains('is-press')")
        after = pg.evaluate("document.documentElement.dataset.theme")
        ok(f'[{theme}] T toggles theme, kbd pressed 120 ms', before != after and pr and not pr2, (before, after, pr, pr2, bg))
        pg.wait_for_timeout(700)
        pg.screenshot(path=f'{OUT}p12_keys_{theme}.png')
        pg.keyboard.press('t')   # thème d'origine
        pg.wait_for_timeout(700)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(400)
        hid = not pg.is_visible('.keys')
        foc = pg.evaluate("document.activeElement.matches('.hero .btn--accent')")
        ok(f'[{theme}] Escape hides and returns focus', hid and foc, (hid, foc))
        # bouton du pied de page
        pg.click('.foot-keys')
        pg.wait_for_timeout(400)
        exp = pg.get_attribute('.foot-keys', 'aria-expanded')
        ok(f'[{theme}] footer button opens popover', pg.is_visible('.keys') and exp == 'true', exp)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(350)
        ok(f'[{theme}] focus back on footer button', pg.evaluate("document.activeElement.matches('.foot-keys')"))
        # clic ailleurs
        pg.click('.foot-keys'); pg.wait_for_timeout(350)
        pg.mouse.click(700, 300); pg.wait_for_timeout(400)
        ok(f'[{theme}] outside click closes', not pg.is_visible('.keys'))
        ok(f'[{theme}] no errors (keys)', not errs, errs)
        ctx.close()

    # 2. interrupteur coupé, rechargement, I ne fait rien ; le bouton marche
    ctx, pg, errs = page(b)
    go(pg)
    pg.keyboard.press('Shift+Slash'); pg.wait_for_timeout(350)
    pg.click('.keys-switch'); pg.wait_for_timeout(200)
    chk = pg.get_attribute('.keys-switch', 'aria-checked')
    stored = pg.evaluate("localStorage.getItem('ql-keys')")
    pg.screenshot(path=f'{OUT}p12_keys_off.png')
    ok('switch off stores ql-keys=off', chk == 'false' and stored == 'off', (chk, stored))
    pg.goto(BASE + '?t=' + str(time.time()), wait_until='networkidle'); pg.wait_for_timeout(1800)
    pg.keyboard.press('i'); pg.wait_for_timeout(300)
    no = pg.evaluate("!document.documentElement.classList.contains('is-inspect')")
    pg.keyboard.press('t'); pg.keyboard.press('3'); pg.keyboard.press('Shift+Slash'); pg.wait_for_timeout(400)
    none = pg.evaluate("!document.documentElement.dataset.theme && scrollY < 5") and not pg.is_visible('.keys')
    pg.click('.inspect-btn'); pg.wait_for_timeout(500)
    yes = pg.evaluate("document.documentElement.classList.contains('is-inspect')")
    ok('keys off after reload: I/T/3/? inert, Inspect button works', no and none and yes, (no, none, yes))
    pg.click('.inspect-btn'); pg.wait_for_timeout(300)
    pg.click('.foot-keys'); pg.wait_for_timeout(350)
    ok('keys off: switch shows off, rows dimmed', pg.evaluate("document.querySelector('.keys').classList.contains('is-off') && getComputedStyle(document.querySelector('.is-single .keys-k')).opacity < .5"))
    pg.click('.keys-switch'); pg.wait_for_timeout(100)
    ok('switch back on stores on', pg.evaluate("localStorage.getItem('ql-keys')") == 'on')
    ok('no errors (switch)', not errs, errs)
    ctx.close()

    # 3. touche 3 : Parcours sous la barre, focus sur la section
    ctx, pg, errs = page(b, keys='')
    go(pg)
    pg.keyboard.press('3'); pg.wait_for_timeout(2000)
    d = pg.evaluate("({top: document.querySelector('#parcours').getBoundingClientRect().top, tb: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--topbar')), a: document.activeElement.id, h: location.hash})")
    ok('3 scrolls to #parcours and focuses it', abs(d['top'] - d['tb']) <= 2 and d['a'] == 'parcours', d)
    pg.keyboard.press('1'); pg.wait_for_timeout(2000)
    d = pg.evaluate("({top: document.querySelector('#travaux').getBoundingClientRect().top, a: document.activeElement.id})")
    ok('1 scrolls to #travaux', abs(d['top'] - 60) <= 2 and d['a'] == 'travaux', d)
    # modificateurs, champs, fiche ouverte
    pg.keyboard.press('Control+t') if False else None
    pg.keyboard.down('Alt'); pg.keyboard.press('2'); pg.keyboard.up('Alt'); pg.wait_for_timeout(600)
    ok('Alt+2 ignored', pg.evaluate("document.activeElement.id") == 'travaux')
    # les curseurs du playground ne sont pas une saisie de texte : T y bascule le thème (typing(), main.js)
    pg.focus('input[data-token="radius"]'); pg.keyboard.press('t'); pg.wait_for_timeout(200)
    ok('T works inside a range input (not a text field)', pg.evaluate("document.documentElement.dataset.theme") == 'light')
    pg.evaluate("document.activeElement.blur()")
    pg.click('.work-row[data-i="0"]'); pg.wait_for_timeout(1200)
    th0 = pg.evaluate("document.documentElement.dataset.theme || ''")
    pg.keyboard.press('t'); pg.keyboard.press('4'); pg.wait_for_timeout(300)
    t_open = pg.evaluate("document.documentElement.dataset.theme || ''") == th0
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(900)
    idx = pg.evaluate("document.querySelector('.case-idx').textContent")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1000)
    ok('case open: T/4 ignored, arrows and Esc work', t_open and idx.startswith('02') and pg.evaluate("document.querySelector('.case').hidden"), (t_open, idx))
    # C en mode Inspecter avec sélection
    pg.keyboard.press('i'); pg.wait_for_timeout(700)
    pg.click('.contact-kicker'); pg.wait_for_timeout(500)
    pg.keyboard.press('c'); pg.wait_for_timeout(300)
    ok('C copies CSS in Inspect mode', 'CSS copié' in pg.evaluate("document.querySelector('.toast').textContent"))
    pg.keyboard.press('Escape'); pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    ok('no errors (keys nav)', not errs, errs)
    ctx.close()

    # 4-5. impression
    for theme in ('dark', 'light'):
        ctx, pg, errs = page(b, theme=theme)
        go(pg)
        pg.emulate_media(media='print')
        pg.wait_for_timeout(300)
        op = pg.evaluate("[...document.querySelectorAll('.reveal, .work-row')].map(e => +getComputedStyle(e).opacity).filter(o => o !== 1).length")
        n = pg.evaluate("document.querySelectorAll('.reveal, .work-row').length")
        ok(f'[{theme}] print: every .reveal/.work-row opacity 1', op == 0, f'{n} checked, {op} not 1')
        bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        ok(f'[{theme}] print: white body', bg == 'rgb(255, 255, 255)', bg)
        pg.pdf(path=f'{OUT}p12_print_{theme}.pdf', format='A4', print_background=True)
        pg.screenshot(path=f'{OUT}p12_printshot_{theme}.png', full_page=True)
        ok(f'[{theme}] no errors (print)', not errs, errs)
        ctx.close()

    # 6. images au téléphone
    ctx, pg, errs = page(b, 390, 844, True)
    sizes = {}
    def onresp(r):
        if r.request.resource_type == 'image':
            try:
                sizes[r.url.split('?')[0]] = len(r.body())
            except Exception:
                sizes[r.url] = -1
    pg.on('response', onresp)
    pg.goto(BASE + '?t=' + str(time.time()), wait_until='networkidle'); pg.wait_for_timeout(2500)
    cur = pg.evaluate("document.querySelector('.name-photo img').currentSrc")
    tot = sum(v for v in sizes.values() if v > 0)
    ok('390: portrait is quentin-480.webp', cur.endswith('quentin-480.webp') and any(k.endswith('quentin-480.webp') for k in sizes), cur)
    ok('390: image bytes on first load < 150 KB', tot < 150 * 1024, {k.split('/')[-1]: v for k, v in sizes.items()} | {'total': tot})
    ok('no errors (390)', not errs, errs)
    ctx.close()
    ctx, pg, errs = page(b)
    sizes.clear(); pg.on('response', onresp)
    go(pg)
    cur = pg.evaluate("document.querySelector('.name-photo img').currentSrc")
    ok('1440: portrait is quentin-700.webp', cur.endswith('quentin-700.webp'), cur)
    pg.evaluate("document.querySelector('.cv-card').scrollIntoView()"); pg.wait_for_timeout(1500)
    ok('1440: CV preview is cv-apercu-800.webp', pg.evaluate("document.querySelector('.cv-thumb img').currentSrc").split('?')[0].endswith('cv-apercu-800.webp'))
    pg.evaluate("window.__lenis && window.__lenis.scrollTo('#travaux',{immediate:true})"); pg.wait_for_timeout(800)
    pg.hover('.work-row[data-i="4"]'); pg.wait_for_timeout(1200)
    src = pg.evaluate("[...document.querySelectorAll('.peek img')].map(i=>i.currentSrc.split('/').pop())")
    ok('1440: peek uses poulettes webp', any(s.endswith('.webp') for s in src), src)
    pg.screenshot(path=f'{OUT}p12_peek_poul.png')
    ok('no errors (1440 images)', not errs, errs)
    ctx.close()

    # 7. 404
    ctx, pg, errs = page(b)
    r = pg.goto(BASE + '404.html?t=' + str(time.time()), wait_until='networkidle'); pg.wait_for_timeout(500)
    txt = pg.inner_text('body')
    ok('404 page served with button and line', r.status == 200 and 'Retour à l’accueil' in txt and 'Cette page n’existe pas.' in txt, r.status)
    ok('404 no errors', not errs, errs)
    ctx.close()
    r = urlopen = None
    import urllib.request
    rb = urllib.request.urlopen(BASE + 'robots.txt').read().decode()
    ok('robots.txt', 'User-agent: *' in rb and 'Allow: /' in rb and 'Sitemap' not in rb, rb)

    # mobile : pas de bouton des raccourcis, ? inerte
    ctx, pg, errs = page(b, 390, 844, True, keys='')
    go(pg)
    ok('390 touch: footer shortcuts button hidden', not pg.is_visible('.foot-keys'))
    pg.keyboard.press('Shift+Slash'); pg.wait_for_timeout(300)
    ok('390 touch: ? does not open', not pg.is_visible('.keys'))
    ok('no errors (390 keys)', not errs, errs)
    ctx.close()
    b.close()

fails = [r for r in res if not r[1]]
print(f'\n{len(res) - len(fails)}/{len(res)} pass')
for f in fails:
    print('FAIL', f[0], f[2])
