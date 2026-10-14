import json, re, os, html as H
import build as B
from bs4 import BeautifulSoup
D, esc, im, link, clean, fpx, icon = B.D, B.esc, B.im, B.link, B.clean, B.fpx, B.icon
MODELS = [('juniper','Juniper'),('lily','Lily'),('laurel-loft','Laurel Loft'),('azalea','Azalea'),('iris','Iris')]
SMALL = {'a','an','and','the','of','for','to','in','on','by','at','or','your','our'}
KEEP = {'ADR','STR','GSMNP','RE','TN','LTM','BR','1–2BR','#1','MNTS'}
def tc(t):
    if not t or not t.isupper(): return t
    out = []
    for i, w in enumerate(t.split(' ')):
        core = w.strip(':,.!?()“”"')
        if core in KEEP: out.append(w)
        elif i and w.lower() in SMALL: out.append(w.lower())
        else: out.append('-'.join(p[:1].upper()+p[1:].lower() for p in w.split('-')))
    return ' '.join(out)
def plain(h): return BeautifulSoup(h or '', 'html.parser').get_text(' ', strip=True)
def lines(h):
    s = BeautifulSoup((h or '').replace('<br>', '\n').replace('<br/>', '\n'), 'html.parser')
    for p in s.find_all(['p','div']): p.append('\n')
    return [x.strip() for x in s.get_text().split('\n') if x.strip()]
def title(a, b='', tag='h2', cls='title'):
    a, b = esc(tc(a.strip())), esc(tc(b.strip()))
    return f'<{tag} class="{cls} rv">{a}{" " if a and b else ""}{"<em>"+b+"</em>" if b else ""}</{tag}>'
def flat(r):
    for g in r['groups']:
        for c in g:
            for m in c['mods']: yield m
            for sg in c.get('sub', []):
                for cc in sg:
                    for m in cc['mods']: yield m
ARROW = '<svg class="arr" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
def btn(text, href, cls='btn'):
    t = re.sub(r'\s*→\s*$', '', text.strip())
    t = tc(t) if t.isupper() else t
    return f'<a class="{cls}" href="{esc(link(href))}"><span>{esc(t)}</span>{ARROW}</a>'

CTX = B.CTX
ORIG_MOD = B.mod
def mod(m):
    t = m['type']
    if t == 'heading':
        txt = m['text'].strip(); px = fpx(m.get('font')); f = m.get('font') or ''
        if 'Great Vibes' in f: return f'<p class="name rv">{esc(txt)}</p>'
        if 'Alex Brush' in f: return f'<p class="eyebrow">{esc(txt)}</p>'
        if 'Cormorant' in f or px >= 40:
            if px >= 40 and not re.match(r'^[\$#\d]', txt): return f'<h2 class="title rv">{esc(tc(txt))}</h2>'
            return f'<p class="price rv">{esc(txt)}</p>'
        if txt.isupper() and px <= 26: return f'<p class="eyebrow">{esc(txt)}</p>'
        if px >= 26: return f'<h3 class="h3">{esc(tc(txt))}</h3>'
        if px <= 18 and txt.isupper(): return f'<p class="eyebrow">{esc(txt)}</p>'
        return f'<p class="kicker">{esc(txt)}</p>'
    if t == 'dual-color-heading':
        tag = 'h1' if not CTX.get('h1') else 'h2'; CTX['h1'] = True
        return title(m.get('a',''), m.get('b',''), tag)
    if t == 'rich-text':
        h = clean(m.get('html')); px = fpx(m.get('font'))
        if not h: return ''
        txt = plain(h); ls = lines(m.get('html'))
        if txt.isupper() and len(txt) < 48 and len(ls) <= 3:
            tag = 'h1' if not CTX.get('h1') else 'h2'; CTX['h1'] = True
            if len(ls) >= 2: return title(' '.join(ls[:-1]), ls[-1], tag)
            return title(txt, '', tag)
        if px >= 36:
            tag = 'h1' if not CTX.get('h1') else 'h2'; CTX['h1'] = True
            return f'<{tag} class="title rv">{esc(tc(txt))}</{tag}>'
        if px >= 20: return f'<div class="lead rv">{h}</div>'
        if txt.startswith(('MICRO-NOTES', 'Sources:')): return f'<div class="notes rv">{h}</div>'
        return f'<div class="prose rv">{h}</div>'
    if t == 'button': return btn(m['text'], m['href'])
    if t == 'uabb-separator': return ''
    if t == 'list-icon':
        return '<ul class="specs">' + ''.join(f'<li>{icon(m.get("icon"))}<span>{esc(i)}</span></li>' for i in m['items']) + '</ul>'
    if t == 'info-box':
        ls = lines(m.get('html'))
        if 1 < len(ls) <= 4 and len(ls[0]) < 30 and re.match(r'^[\$\d]', ls[1]):
            return f'<div class="metric rv"><span class="m-label">{esc(ls[0].rstrip(":"))}</span><span class="m-num" data-count>{esc(ls[1])}</span><span class="m-note">{esc(" ".join(ls[2:]))}</span></div>'
        return ORIG_MOD(m).replace('class="info"', 'class="info rv"')
    if t in ('numbers', 'uabb-numbers'):
        ls = [x.strip() for x in (m.get('text') or '').split('\n') if x.strip()]
        if not ls: return ''
        return f'<div class="stat rv"><span class="stat-num" data-count>{esc(ls[0])}</span><span class="stat-label">{esc(" ".join(ls[1:]))}</span></div>'
    if t == 'gallery':
        return '<div class="gallery">' + ''.join(f'<a href="{esc(im(i))}" class="g-item rv"><img src="{esc(im(i))}" alt="" loading="lazy"></a>' for i in m['imgs'] if im(i) != i or not i.startswith(B.BASE)) + '</div>'
    if t in ('photo','uabb-photo') and 'Logo_Website' in (m.get('src') or ''): return ''
    return ORIG_MOD(m)
B.mod = mod

def col(c):
    inner = ''.join(mod(m) for m in c['mods'])
    inner = re.sub(r'((?:<a class="btn"[^>]*>.*?</a>){2,})', r'<div class="btn-row">\1</div>', inner)
    for sg in c.get('sub', []): inner += group(sg)
    if not inner.strip(): return ''
    media = all(m['type'] in ('photo','uabb-photo','uabb-video') for m in c['mods']) and not c.get('sub')
    return f'<div class="col{" col-media" if media else ""}">{inner}</div>'
def group(g):
    cols = [col(c) for c in g]; cols = [x for x in cols if x]
    n = len(cols)
    if n == 0: return ''
    if n == 1: return f'<div class="grid g1">{cols[0]}</div>'
    media = sum('col-media' in x for x in cols)
    if n == 2 and media == 1:
        first = 'media-first' if 'col-media' in cols[0] else 'media-last'
        return f'<div class="grid split {first}">' + ''.join(cols) + '</div>'
    return f'<div class="grid cards" style="--n:{min(n,4)}">' + ''.join(cols) + '</div>'
B.group = group; B.col = col

def section(r, i, extra=''):
    img = re.search(r'url\("([^"]+)"\)', r['bg'] or '')
    dark = B.is_dark(r['bgColor'])
    cls = ['sec']
    style = ''
    if img: cls.append('sec-image'); style = f' style="--bg:url(\'{im(img.group(1))}\')"'
    elif dark: cls.append('sec-dark')
    elif i % 2: cls.append('sec-tint')
    if i == 0: cls.append('sec-hero')
    body = ''.join(group(g) for g in r['groups'])
    return f'<section class="{" ".join(cls)} {extra}"{style}><div class="wrap">{body}</div></section>'

def marquee(words):
    s = ''.join(f'<span>{esc(w)}</span><i aria-hidden="true">✦</i>' for w in words)
    return f'<div class="marquee" aria-hidden="true"><div class="mq-track">{s}{s}</div></div>'
PLACES = ['Gatlinburg','Pigeon Forge','Sevierville','Wears Valley','Townsend','Site-built in the Smokies']

def home(rows):
    out = []
    h = list(flat(rows[0]))
    dual = next(m for m in h if m['type']=='dual-color-heading')
    sub = next(m['text'] for m in h if m['type']=='heading')
    txt = next(clean(m['html']) for m in h if m['type']=='rich-text')
    btns = ''.join(btn(m['text'], m['href'], 'btn' if k else 'btn btn-light') for k, m in enumerate(m for m in h if m['type']=='button'))
    bg = im(re.search(r'url\("([^"]+)"\)', rows[0]['bg']).group(1))
    out.append(f'''<section class="hero" style="--bg:url('{bg}')"><div class="hero-media"></div><div class="wrap hero-in">
<p class="eyebrow light">Builds by Carly · Sevier County, Tennessee</p>
<h1 class="hero-title"><span class="ln">{esc(tc(dual['a']))}</span> <span class="ln"><em>{esc(tc(dual['b']))}</em></span></h1>
<div class="hero-foot"><p class="hero-sub">{esc(sub)}</p><div class="hero-copy">{txt}<div class="btn-row">{btns}</div></div></div>
</div><div class="scroll-cue" aria-hidden="true"><span></span></div></section>''')
    out.append(marquee(PLACES))
    items = []; photo = ''
    for k, r in enumerate(rows[1:5], 1):
        ms = list(flat(r)); d = next(m for m in ms if m['type']=='dual-color-heading')
        eb = next(m['text'] for m in ms if m['type']=='heading')
        body = next(clean(m['html']) for m in ms if m['type']=='rich-text')
        b = next(m for m in ms if m['type']=='button')
        photo = photo or next(m['src'] for m in ms if m['type']=='photo')
        items.append(f'<li class="feat rv"><span class="feat-n">0{k}</span><div><p class="eyebrow">{esc(eb)}</p>{title(d["a"], d["b"], "h2" if k>1 else "h2", "feat-title")}<div class="prose">{body}</div>{btn(b["text"], b["href"], "link")}</div></li>')
    out.append(f'''<section class="sec features"><div class="wrap feat-grid"><div class="feat-media"><figure class="sticky-fig"><img src="{esc(im(photo))}" alt="Builds by Carly site-built tiny home"><figcaption>Fig. 01 — Site-built in the Smoky Mountains</figcaption></figure></div><ol class="feat-list">{''.join(items)}</ol></div></section>''')
    ms = list(flat(rows[5])); d = next(m for m in ms if m['type']=='dual-color-heading')
    intro = next(clean(m['html']) for m in ms if m['type']=='rich-text')
    models = []; cur = None; photos = {}
    for m in ms:
        if m['type']=='photo':
            src = m['src']; slug = 'iris' if 'iris' in src else link(m.get('href') or '').replace('.html','')
            photos[slug] = src
        if m['type']=='heading' and 'Great Vibes' in (m.get('font') or ''):
            cur = {'name': m['text']}; models.append(cur)
        elif cur is not None:
            if m['type']=='dual-color-heading': cur['price'] = (m.get('a','')+' '+m.get('b','')).replace('PRICING','').strip()
            elif m['type']=='rich-text' and 'desc' not in cur: cur['desc'] = clean(m['html'])
            elif m['type']=='button': cur['btn'] = m
    cards = []
    for k, mo in enumerate(models, 1):
        slug = mo['name'].lower().replace(' ', '-')
        cards.append(f'''<article class="model rv"><a class="model-img" href="{slug}.html"><img src="{esc(im(photos.get(slug,'')))}" alt="The {esc(mo['name'])}" loading="lazy"><span class="model-no">No. 0{k} / 0{len(models)}</span></a>
<div class="model-body"><h3 class="model-name">{esc(mo['name'])}</h3><p class="model-price"><span>Pricing</span>{esc(mo.get('price',''))}</p><div class="prose">{mo.get('desc','')}</div>{btn(mo['btn']['text'], mo['btn']['href'], 'link')}</div></article>''')
    out.append(f'''<section class="sec sec-dark models-sec"><div class="wrap models-head"><div><p class="eyebrow light">The Collection</p>{title(d['a'], d['b'])}</div><div class="prose rv">{intro}</div>
<div class="rail-nav"><button class="rail-btn" data-dir="-1" aria-label="Previous models">{ARROW}</button><button class="rail-btn" data-dir="1" aria-label="Next models">{ARROW}</button></div></div>
<div class="rail">{''.join(cards)}</div></section>''')
    ms = list(flat(rows[6])); d = next(m for m in ms if m['type']=='dual-color-heading')
    eb = next(m['text'] for m in ms if m['type']=='heading'); body = next(clean(m['html']) for m in ms if m['type']=='rich-text')
    paras = re.findall(r'<(p|div)>(.*?)</\1>', body, re.S)
    first = paras[0][1] if paras else body; rest = ''.join(f'<p>{p[1]}</p>' for p in paras[1:])
    out.append(f'''<section class="sec story"><div class="wrap story-grid"><figure class="story-fig rv"><img src="{esc(im('https://buildsbycarly.com/files/2023/12/Carly-Bowlen.jpg'))}" alt="Carly Bowlen"><figcaption>Carly Bowlen — Founder</figcaption></figure>
<div class="story-text"><p class="eyebrow">{esc(tc(eb))}</p>{title(d['a'], d['b'])}<p class="pull rv">{first}</p><div class="prose cols2 rv">{rest}</div></div></div></section>''')
    ms = list(flat(rows[7])); qs = []
    for m in ms:
        if m['type']=='rich-text':
            ls = lines(m['html']); qs.append((ls[0], ' '.join(ls[1:])))
    q = ''.join(f'<figure class="quote rv"><span class="q-mark" aria-hidden="true">“</span><blockquote>{esc(t.strip(chr(34)+"“”"))}</blockquote><figcaption><span class="stars" aria-label="5 stars">★★★★★</span>{esc(n)}</figcaption></figure>' for n, t in qs)
    out.append(f'<section class="sec sec-tint quotes-sec"><div class="wrap"><p class="eyebrow">In their words</p><div class="quotes3">{q}</div></div></section>')
    out.append(section(rows[8], 2, 'band'))
    out.append(cta(rows[9]))
    return ''.join(out)

def cta(r):
    ms = list(flat(r))
    tt = next((m for m in ms if m['type'] in ('dual-color-heading','rich-text')), None)
    if tt['type']=='dual-color-heading': hd = title(tt['a'], tt['b'])
    else: hd = f'<h2 class="title rv">{esc(tc(plain(tt["html"])))}</h2>'
    body = ''.join(f'<div class="prose rv">{clean(m["html"])}</div>' for m in ms if m['type']=='rich-text' and m is not tt)
    bs = ''.join(btn(m['text'], m['href'], 'btn') for m in ms if m['type']=='button')
    img = re.search(r'url\("([^"]+)"\)', r['bg'] or '')
    st = f' style="--bg:url(\'{im(img.group(1))}\')"' if img else ''
    return f'<section class="cta-sec{" has-img" if img else ""}"{st}><div class="wrap cta-in">{hd}<div>{body}<div class="btn-row">{bs}</div></div></div></section>'

def model_hero(r, key):
    ms = list(flat(r)); k = [m[0] for m in MODELS].index(key) + 1
    name = next(m['text'] for m in ms if m['type']=='heading' and 'Great Vibes' in (m.get('font') or ''))
    info = next((clean(m['html']) for m in ms if m['type']=='info-box'), '')
    price = next((m['text'] for m in ms if m['type']=='heading' and 'Cormorant' in (m.get('font') or '')), '')
    start = next((m['text'] for m in ms if m['type']=='heading' and 'Alex Brush' in (m.get('font') or '')), 'Starting at')
    specs = ''.join(f'<li>{icon(m.get("icon"))}<span>{esc(i)}</span></li>' for m in ms if m['type']=='list-icon' for i in m['items'])
    bs = ''.join(btn(m['text'], m['href'], 'btn') for m in ms if m['type']=='button')
    latin = re.search(r'<i>([^<]+)</i>', info)
    bg = im(re.search(r'url\("([^"]+)"\)', r['bg']).group(1))
    return f'''<section class="m-hero"><div class="m-hero-media" style="--bg:url('{bg}')"><span class="model-no">No. 0{k} / 05</span></div>
<div class="m-hero-panel"><p class="eyebrow">Welcome to</p><h1 class="m-name">{esc(name)}</h1>{f'<p class="latin">{esc(latin.group(1))}</p>' if latin else ''}
<div class="m-price"><span class="eyebrow">{esc(start)}</span><span class="price">{esc(price)}</span></div>
<div class="prose">{info}</div><ul class="specs">{specs}</ul><div class="btn-row">{bs}</div></div></section>'''

def page_hero(r):
    ms = list(flat(r))
    img = re.search(r'url\("([^"]+)"\)', r['bg'] or '')
    if not img or any(m['type'] in ('dual-color-heading','info-box','widget','uabb-numbers') for m in ms): return None
    tt = [m for m in ms if m['type']=='rich-text']
    if not tt or fpx(tt[0].get('font')) < 36: return None
    CTX['h1'] = True
    rest = ''.join(mod(m) for m in ms if m is not tt[0])
    return f'''<section class="p-hero" style="--bg:url('{im(img.group(1))}')"><div class="wrap p-hero-in"><p class="eyebrow light">Builds by Carly</p><h1 class="p-title">{esc(tc(plain(tt[0]["html"])))}</h1><div class="p-hero-copy">{rest}</div></div></section>'''

def page(key):
    fn, ttl = B.PAGES[key]; CTX.clear(); CTX['page'] = key
    rows = [r for r in D[key]['rows'] if r['node'] != B.FOOTER_NODE]
    if key == 'home': body = home(rows)
    else:
        out = []
        last = rows[-1]; lm = list(flat(last))
        is_cta = len(lm) <= 4 and any(m['type']=='button' for m in lm) and not any(m['type'] in ('photo','widget','html') for m in lm)
        body_rows = rows[:-1] if is_cta and len(rows) > 1 else rows
        for i, r in enumerate(body_rows):
            if i == 0 and key in dict(MODELS): out.append(model_hero(r, key)); continue
            if i == 0:
                ph = page_hero(r)
                if ph: out.append(ph); continue
            out.append(section(r, i))
            if i == 0 and key not in ('contact',): out.append(marquee(PLACES))
        if is_cta and len(rows) > 1: out.append(cta(last))
        body = ''.join(out)
    head = B.page(key).split('<main>')[0]
    head = head.replace(re.search(r'<link href="https://fonts.googleapis.com/css2[^>]+>', head).group(0),
        '<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT@0,9..144,300..600,50;1,9..144,300..600,50&family=Instrument+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')
    head = head.replace('<header class="site-header">', '<a class="skip" href="#main">Skip to content</a><header class="site-header">')
    foot = footer()
    out = f'{head}<main id="main">{body}</main>{foot}' + B.page(key).split('</footer>',1)[1]
    out = re.sub(r'https://brokerage.agent.wallacetn.com/files/2023/09/([\w.-]+)', lambda m: 'assets/img/wallace-'+m.group(1) if os.path.getsize('site/assets/img/wallace-'+m.group(1)) > 500 else m.group(0), out)
    return re.sub(r"--bg:url\('assets/", "--bg:url('", out)

def footer():
    cols = []
    for t, h, sub in B.NAV:
        if sub: cols.append(f'<div><p class="eyebrow light">{esc(t)}</p><ul>' + ''.join(f'<li><a href="{x[1]}">{esc(x[0])}</a></li>' for x in sub) + '</ul></div>')
    f = B.footer()
    logos = re.search(r'<div class="f-logos">.*?</div>', f, re.S).group(0)
    legal = re.search(r'<div class="f-legal">.*?</div>', f, re.S).group(0)
    return f'''<footer class="site-footer"><div class="wrap">
<div class="f-top"><div class="f-brand"><a href="index.html" class="f-logo"><img src="assets/Footer-Logo.png" alt="Builds By Carly"></a>
<a class="f-phone" href="tel:8655050514">(865) 505-0514</a><a class="f-mail" href="mailto:info@buildsbycarly.com">info@buildsbycarly.com</a></div>
<nav class="f-nav" aria-label="Footer">{''.join(cols)}</nav></div>
<p class="f-office">WEST OFFICE | 865-693-1111 | info@wallacetn.com | 106 N. Peters Road | Knoxville, TN 37923</p>
{logos}{legal}</div></footer>'''

if __name__ == '__main__':
    for k in B.PAGES: open('site/' + B.PAGES[k][0], 'w').write(page(k))
    print('built', len(B.PAGES))
