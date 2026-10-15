import json, re, os, html as H
import build as B, build2 as B2
D, esc, im, clean, link = B.D, B.esc, B.im, B.clean, B.link
flat, lines, tc = B2.flat, B2.lines, B2.tc
def plain(h): return re.sub(r'\s+([,.;:!?])', r'\1', B2.plain(h))
MODELS = [('juniper','Juniper'),('lily','Lily'),('laurel-loft','Laurel Loft'),('azalea','Azalea'),('iris','Iris')]
PROPER = ['Juniper','Lily','Laurel Loft','Azalea','Iris','Carly','Builds by Carly','Gatlinburg','Pigeon Forge','Sevierville','Smoky','Tennessee','Wallace','Sevier']
AC = ' aria-current="page"'
EX = ' class="extra"'
ARROW = '<svg class="arrow" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="2"/></svg>'

def sc(t):
    t = re.sub(r'\s*[→!]+\s*$', '', (t or '').strip())
    if t.isupper() or t.istitle():
        t = t.lower(); t = t[:1].upper() + t[1:]
        for p in PROPER: t = re.sub(r'\b' + re.escape(p.lower()) + r'\b', p, t)
    return t
def button(text, href, kind='primary', arrow=False):
    return f'<a class="button button-{kind}" href="{esc(href)}">{esc(sc(text))}{ARROW if arrow else ""}</a>'
def tlink(text, href):
    return f'<a class="text-link" href="{esc(href)}">{esc(sc(text))}{ARROW}</a>'
def words(t, n):
    w = t.split()
    if len(w) <= n: return t
    cut = ' '.join(w[:n]); m = re.match(r'(.*[.!?])\s', cut + ' ')
    return m.group(1) if m and len(m.group(1).split()) > n * .5 else cut + '…'

# patch the generic renderer (build2) for non-pilot pages
def _btn(text, href, cls='btn'):
    kind = {'btn': 'primary', 'btn btn-light': 'secondary'}.get(cls)
    return tlink(text, link(href)) if kind is None else button(text, link(href), kind)
def _title(a, b='', tag='h2', cls='title'):
    t = ' '.join(x for x in (tc(a.strip()), tc(b.strip())) if x)
    return f'<{tag} class="{"h1" if tag == "h1" else "h2"}">{esc(t)}</{tag}>'
B2.btn = _btn; B2.title = _title; B2.marquee = lambda w: ''

# ---------- shared data ----------
def fin_prices():
    ms = [m for m in flat(D['financing']['rows'][1]) if m['type'] == 'heading'][4:]
    out = {}
    for i in range(0, len(ms) - 3, 4):
        n = ms[i]['text'].strip().title().replace('Laurel Loft', 'Laurel Loft')
        out[n] = {'block': ms[i+1]['text'].strip(), 'elevated': ms[i+2]['text'].strip(), 'deposit': ms[i+3]['text'].strip()}
    return out
PRICES = fin_prices()
MIN_PRICE = min((p['block'] for p in PRICES.values()), key=lambda v: int(re.sub(r'\D', '', v)))
TERMS = clean(next(m['html'] for m in flat(D['financing']['rows'][2]) if m['type'] == 'rich-text')).replace('Build by Carly', 'Builds by Carly').replace('Mountain View’s', 'mountain views').replace("Mountain View's", 'mountain views').replace('forward..', 'forward.')
TERMS_LI = ''.join(f'<li><span class="icon-chip"><i class="fa-solid fa-{ic}"></i></span><div>{t}</div></li>' for ic, t in zip(['file-contract', 'circle-info', 'circle-check'], [x for x in re.findall(r'<p[^>]*>(.*?)</p>', TERMS, re.S) if x.strip()] or [TERMS]))

def home_cards():
    ms = list(flat(D['home']['rows'][5])); cards = {}; cur = None; photos = {}
    for m in ms:
        if m['type'] == 'photo':
            src = m['src']; slug = 'iris' if 'iris' in src else link(m.get('href') or '').replace('.html', '')
            photos[slug] = src
        if m['type'] == 'heading' and 'Great Vibes' in (m.get('font') or ''):
            cur = {'name': m['text'].strip()}; cards[cur['name'].lower().replace(' ', '-')] = cur
        elif cur is not None and m['type'] == 'rich-text' and 'desc' not in cur:
            cur['desc'] = plain(m['html'])
    for s, c in cards.items():
        c['photo'] = photos.get(s, '')
        c['desc'] = re.sub(r'\s*Price coming soon\.?', '.', c.get('desc', '')).replace('..', '.')
    return cards
CARDS = home_cards()

def yt(m):
    r = re.search(r'data-yt="([^"]+)"', B2.ORIG_MOD(m)); return r.group(1) if r else None

def model_data(key, name):
    rows = [r for r in D[key]['rows'] if r['node'] != B.FOOTER_NODE]
    ms = list(flat(rows[0]))
    d = {'key': key, 'name': name, 'card': CARDS.get(key, {}), 'price': PRICES.get(name, {})}
    d['info'] = next((clean(m['html']) for m in ms if m['type'] == 'info-box'), '')
    d['specs'] = [(m.get('icon'), i) for m in ms if m['type'] == 'list-icon' for i in m['items']]
    d['hero'] = im(re.search(r'url\("([^"]+)"\)', rows[0]['bg']).group(1))
    d['area'] = next((i for _, i in d['specs'] if 'sq' in i.lower()), '').replace('Sq Ft', 'sq ft')
    if key == 'iris' and '602' in d['info'] and '123' in d['info']: d['area'] = '602 sq ft main floor + 123 sq ft loft'
    if key == 'laurel-loft': d['area'] = '384 sq ft main floor + loft (525 sq ft listed)'
    d['galleries'] = []; d['features'] = None; lab = desc = None
    for r in rows[1:]:
        ms = list(flat(r)); duals = [m for m in ms if m['type'] == 'dual-color-heading']
        if duals and 'PROPERTY' in duals[0].get('a', ''):
            if d['features'] is None:
                f = []; cur = None
                for m in ms:
                    if m['type'] == 'heading': cur = [m['text'].strip(), '']; f.append(cur)
                    elif m['type'] == 'rich-text' and cur: cur[1] += clean(m['html'])
                d['features'] = f
            continue
        if any(m['type'] == 'heading' and 'AREA OVERVIEW' in m['text'] for m in ms): continue
        gal = [m for m in ms if m['type'] == 'gallery']
        if gal:
            v = next((yt(m) for m in ms if m['type'] == 'uabb-video'), None)
            d['galleries'].append({'label': lab, 'desc': desc, 'imgs': [im(i) for i in gal[0]['imgs'] if im(i) != i or not i.startswith(B.BASE)], 'video': v})
            lab = desc = None
        elif duals:
            lab = ' '.join(x for x in (duals[0].get('a', ''), duals[0].get('b', '')) if x).strip()
            desc = ''.join(clean(m['html']) for m in ms if m['type'] == 'rich-text')
    if key == 'iris' and d['features']:
        d['features'] = [[h, re.sub(r'[^.<>]*\b330\b[^.<>]*\.\s*', '', t)] for h, t in d['features']]
    return d
MD = {k: model_data(k, n) for k, n in MODELS}

# ---------- shell ----------
NAV = [('Models', None, [(n, f'{k}.html') for k, n in MODELS] + [('Compare all models', 'financing.html')]),
       ('How it works', 'get-on-our-list.html', None),
       ('Pricing & financing', 'financing.html', None),
       ('Resources', None, [('Why tiny homes', 'why-tiny-homes.html'), ('Rental metrics', 'rental-metrics.html'), ('Tourism', 'tourism-breakdown.html'), ('Area overview', 'area-overview.html')]),
       ('About', None, [('About Builds by Carly', 'about-bbc.html'), ('About Wallace', 'about-wallace.html')]),
       ('Contact', 'contact.html', None)]
def nav(cur):
    out = []
    for i, (t, h, sub) in enumerate(NAV):
        if sub:
            act = any(x[1] == cur for x in sub)
            items = ''.join(f'<li><a href="{x[1]}"{AC if x[1] == cur else ""}>{esc(x[0])}</a></li>' for x in sub)
            out.append(f'<li class="has-sub{" is-active" if act else ""}"><button type="button" aria-expanded="false" aria-controls="sub-{i}">{esc(t)}<svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true"><path d="m2 4 4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button><ul id="sub-{i}" class="submenu">{items}</ul></li>')
        else:
            out.append(f'<li><a href="{h}"{AC if h == cur else ""}>{esc(t)}</a></li>')
    return ''.join(out)

def footer():
    f = B.footer()
    logos = re.search(r'<div class="f-logos">(.*?)</div>', f, re.S).group(1)
    logos = re.sub(r'https://brokerage.agent.wallacetn.com/files/2023/09/([\w.-]+)', r'assets/img/wallace-\1', logos).replace(' loading="lazy"', '')
    legal = re.search(r'<div class="f-legal">(.*?)</div>', f, re.S).group(1)
    legal = legal.replace('>Fair Housing Notice<', '>Fair Housing Notice (PDF)<')
    def grp(t, items): return f'<div><h2 class="footer-heading">{t}</h2><ul>' + ''.join(f'<li><a href="{h}">{esc(n)}</a></li>' for n, h in items) + '</ul></div>'
    return f'''<footer class="site-footer"><div class="container">
<div class="footer-top"><div class="footer-brand"><a href="index.html" class="footer-logo"><img src="assets/Footer-Logo.png" alt="Builds by Carly home" width="160" height="60"></a>
<p>Site-built luxury tiny homes in Sevier County, Tennessee.</p></div>
{grp('Models', [(n, f'{k}.html') for k, n in MODELS])}
{grp('Resources', [('Why tiny homes', 'why-tiny-homes.html'), ('Rental metrics', 'rental-metrics.html'), ('Tourism', 'tourism-breakdown.html'), ('Area overview', 'area-overview.html')])}
{grp('Company', [('About Builds by Carly', 'about-bbc.html'), ('About Wallace', 'about-wallace.html'), ('How it works', 'get-on-our-list.html'), ('Pricing & financing', 'financing.html')])}
<div><h2 class="footer-heading">Contact</h2><ul><li><a href="tel:8655050514">(865) 505-0514</a></li><li><a href="mailto:info@buildsbycarly.com">info@buildsbycarly.com</a></li><li><a href="contact.html">Contact Carly</a></li></ul></div></div>
<div class="brokerage"><div class="brokerage-logos">{logos}</div><p>WEST OFFICE | 865-693-1111 | <a href="mailto:info@wallacetn.com">info@wallacetn.com</a> | 106 N. Peters Road | Knoxville, TN 37923</p></div>
<div class="legal">{legal}</div></div></footer>'''

def describe(body):
    t = re.sub(r'\s+', ' ', plain(' '.join(re.findall(r'<p[^>]*>(.*?)</p>', body, re.S)[:3]))).strip()
    return words(t, 26)[:155] if t else 'Site-built luxury tiny homes in the Smoky Mountains by Builds by Carly.'

def shell(fn, title, body, desc=None, og=None):
    desc = desc or describe(body)
    og = og or 'assets/img/buildsbycarly-2025-08-Carly-Bowlen-Homepage-Banner-02.jpg'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="noindex, nofollow">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{esc(og)}">
<link rel="icon" href="assets/favicon.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="container header-inner">
<a class="brand" href="index.html"><img src="assets/Footer-Logo.png" alt="Builds by Carly home" width="132" height="50"></a>
<button class="menu-button" type="button" aria-expanded="false" aria-controls="site-nav"><span class="menu-icon" aria-hidden="true"></span><span class="menu-label">Menu</span></button>
<nav id="site-nav" class="site-nav" aria-label="Main"><ul class="nav-list">{nav(fn)}</ul><a class="button button-primary header-cta" href="get-on-our-list.html#application">Start your project</a></nav>
</div></header>
<main id="main" tabindex="-1">{body}</main>{footer()}
<dialog class="lightbox" aria-label="Photo viewer"><figure><img alt=""><figcaption></figcaption></figure>
<button type="button" class="lb-btn lb-prev" aria-label="Previous photo">&#8249;</button><button type="button" class="lb-btn lb-next" aria-label="Next photo">&#8250;</button><button type="button" class="lb-btn lb-close" aria-label="Close photo viewer">&times;</button></dialog>
<script>window.BBC_FORM_ENDPOINT="{B.WEBHOOK}";</script><script src="assets/site.js"></script></body></html>'''

# ---------- components ----------
def closing_cta(title='Discuss your build', model=None):
    href = f'contact.html?model={model.replace(" ", "+")}' if model else 'contact.html'
    return f'''<section class="section closing-cta">{RIDGE}<div class="container cta-grid"><h2>{esc(title)}</h2><div>
<p>Tell Carly which model, area and timing you have in mind. She can walk you through land options, foundation choices, pricing and the next steps for your project.</p>
<div class="button-row">{button("Contact Carly", href)}{button("Start your project", "get-on-our-list.html#application", "secondary-light")}</div></div></div></section>'''

def model_card(d, h='h3'):
    p = d['price']; c = d['card']
    feat = words(c.get('desc', ''), 18)
    return f'''<article class="model-card"><img src="{esc(im(c.get('photo') or d['hero']))}" alt="{esc(d['name'])} tiny home" loading="lazy" width="800" height="600">
<div class="model-card-body"><{h} class="card-title"><a href="{d['key']}.html">{esc(d['name'])}</a></{h}><p class="model-feature">{esc(feat)}</p>
<p class="model-facts">{esc(d['area'])} · Block or elevated foundation</p>
<p class="model-price"><span class="label">From</span> <span class="price">{esc(p.get('block', ''))}</span> <span class="qualifier">block foundation</span></p>
<span class="text-link" aria-hidden="true">View {esc(d['name'])}{ARROW}</span></div></article>'''

def gallery(g, name, gi):
    imgs = g['imgs']; n = len(imgs); label = sc(g['label'] or 'Photo gallery'); show = 4
    if label.lower() == 'image gallery': label = 'Photo gallery'
    items = ''
    for i, u in enumerate(imgs):
        cls = f'g-tile g{i + 1}' if i < show else 'g-tile extra'
        more = f'<span class="g-more"><strong>+{n - show}</strong> photos</span>' if i == show - 1 and n > show else ''
        cap = f'{name} — {label}, photo {i + 1} of {n}'
        items += f'<li class="{cls}"><a href="{esc(u)}" data-caption="{esc(cap)}" aria-label="Open {esc(name)} photo {i + 1} of {n}"><img src="{esc(u)}" alt="{esc(name)} — {esc(label.lower())}, photo {i + 1}" loading="lazy" width="800" height="600"><span class="g-zoom" aria-hidden="true"><i class="fa-solid fa-expand"></i></span>{more}</a></li>'
    desc = f'<div class="prose">{g["desc"]}</div>' if g['desc'] else ''
    if g['video']:
        v = g['video']
        top = f'''<div class="tour" data-reveal><div class="tour-frame"><div class="video" data-yt="{v}"><img src="https://i.ytimg.com/vi/{v}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><button type="button" class="play" aria-label="Play the {esc(name)} video tour"><i class="fa-solid fa-play"></i></button><a class="video-fallback" href="https://www.youtube.com/watch?v={v}">Watch on YouTube</a></div></div>
<div class="tour-copy"><span class="pill"><i class="fa-solid fa-film"></i> Video tour</span><h3>{esc(label)}</h3>{desc}<p class="tour-count"><i class="fa-regular fa-images"></i> {n} photos · tap any photo to open the viewer</p></div></div>'''
    else:
        top = f'<div class="tour tour-text" data-reveal><div class="tour-copy"><span class="pill"><i class="fa-regular fa-images"></i> {n} photos</span><h3>{esc(label)}</h3>{desc}</div></div>'
    return f'<div class="gallery-block">{top}<ul class="gallery mosaic" id="g{gi}" aria-label="{esc(name)} {esc(label.lower())}">{items}</ul></div>'

def model_page(key):
    d = MD[key]; name = d['name']; p = d['price']; q = name.replace(' ', '+')
    facts = ''.join(f'<li><i class="fa-solid fa-{i}" aria-hidden="true"></i> {esc(x)}</li>' for i, x in zip(['ruler-combined', 'layer-group', 'location-dot'], [d['area'], 'Block or elevated foundation', 'Site-built in Sevier County']) if x)
    specs = ''.join(f'<li>{B.icon(ic)}<span>{esc(t)}</span></li>' for ic, t in d['specs'])
    gals = ''.join(gallery(g, name, i) for i, g in enumerate(d['galleries']))
    feats = d['features'] or []
    shared = [f for f in feats if f[0] in ('Finishes & Flexibility', 'Systems & Comfort', 'Foundation Options', 'Land Included')]
    unique = [f for f in feats if f not in shared]
    hi = ''.join(f'<article class="card"><h3 class="card-title">{esc(h)}</h3><div class="prose">{t}</div></article>' for h, t in unique)
    acc = ''.join(f'<details class="accordion"><summary>{esc(h)}</summary><div class="prose">{t}</div></details>' for h, t in shared)
    rel = [MD[k] for k, _ in MODELS if k != key]
    i = [k for k, _ in MODELS].index(key); rel = [MD[MODELS[(i + 1) % 5][0]], MD[MODELS[(i + 2) % 5][0]]]
    body = f'''<nav class="breadcrumb container" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li><a href="index.html#models">Models</a></li><li aria-current="page">{esc(name)}</li></ol></nav>
<section class="model-hero container"><div class="model-hero-info"><h1>{esc(name)}</h1>
<p class="lead">{esc(words(d['card'].get('desc', ''), 30))}</p><ul class="quick-facts">{facts}</ul>
<div class="price-block"><span class="label">Starting at</span><span class="price">{esc(p.get('block', ''))}</span><span class="qualifier">Block foundation · Elevated foundation {esc(p.get('elevated', ''))}</span></div>
<div class="button-row">{button('Ask about this model', f'contact.html?model={q}')}{button('Compare pricing', 'financing.html', 'secondary')}</div></div>
<figure class="model-hero-media"><img src="{esc(d['hero'])}" alt="The {esc(name)} tiny home by Builds by Carly" width="1600" height="1200" fetchpriority="high"></figure></section>
<section class="section"><div class="container split-even"><div><h2>About the {esc(name)}</h2><div class="prose">{d['info']}</div></div>
<div><h2 class="h3">Specifications as published</h2><ul class="spec-list">{specs}</ul><p class="note">Confirm exact dimensions, provisions and inclusions with Carly before you commit.</p></div></div></section>
<section class="section gallery-section"><div class="container"><h2>Photos and tour</h2>{gals}</div></section>
<section class="section"><div class="container"><div class="section-head"><h2>Pricing</h2>{tlink('Full pricing and terms', 'financing.html')}</div><div class="pricing-grid">
<div class="price-cards"><article class="price-card"><span class="icon-chip"><i class="fa-solid fa-cubes"></i></span><span class="label">Block foundation</span><span class="price">{esc(p.get('block', ''))}</span><span class="note">Starting price</span></article>
<article class="price-card price-card-alt"><span class="icon-chip"><i class="fa-solid fa-tree"></i></span><span class="label">Elevated tree-house foundation</span><span class="price">{esc(p.get('elevated', ''))}</span><span class="note">Starting price</span></article>
<article class="deposit-card"><span class="icon-chip"><i class="fa-solid fa-hand-holding-dollar"></i></span><div><span class="label">Construction deposit</span><span class="price">{esc(p.get('deposit', ''))}</span></div><span class="note">Credited toward the final purchase</span></article></div>
<aside class="terms-panel" data-reveal><h3>Terms at a glance</h3><ul class="terms-list">{TERMS_LI}</ul></aside></div></div></section>
{f'<section class="section section-soft"><div class="container"><h2>What sets the {esc(name)} apart</h2><div class="card-grid cols-{min(len(unique), 3) or 1}">{hi}</div></div></section>' if unique else ''}
{f'<section class="section"><div class="container narrow"><h2>Construction details</h2>{acc}</div></section>' if acc else ''}
<section class="section section-soft"><div class="container"><div class="section-head"><h2>Related models</h2>{tlink('Explore build areas', 'area-overview.html')}</div><div class="card-grid cols-2">{''.join(model_card(r) for r in rel)}</div></div></section>
{closing_cta(f'Ask about the {name}', name)}'''
    return shell(f'{key}.html', f'{name} tiny home | Builds by Carly', body, f'The {name}: {words(d["card"].get("desc", ""), 18)} Starting at {p.get("block", "")}.', d['hero'])

def home():
    rows = [r for r in D['home']['rows'] if r['node'] != B.FOOTER_NODE]
    h = list(flat(rows[0])); txt = plain(next(m['html'] for m in h if m['type'] == 'rich-text'))
    hero_img = im(re.search(r'url\("([^"]+)"\)', rows[0]['bg']).group(1))
    intro = plain(next(m['html'] for m in flat(rows[5]) if m['type'] == 'rich-text'))
    feats = []
    for r in rows[1:5]:
        ms = list(flat(r)); feats.append(plain(next(m['html'] for m in ms if m['type'] == 'rich-text')))
    hero_sent = re.split(r'(?<=[.!?])\s+', txt)
    guest = next((s for s in hero_sent if 'short-term rental' in s), '')
    dif = [('Site-built construction', words(feats[0], 50), 'About our builds', 'about-bbc.html'),
           ('Foundation options', words(feats[1], 50), 'Compare foundation pricing', 'financing.html'),
           ('Land selection support', words(feats[2], 50), 'See how it works', 'get-on-our-list.html'),
           ('Design for guest use', guest, 'Why tiny homes', 'why-tiny-homes.html')]
    difh = ''.join(f'<article class="card"><h3 class="card-title">{t}</h3><p>{esc(b)}</p>{tlink(l, u)}</article>' for t, b, l, u in dif)
    steps = [('Discuss the project', 'Tell Carly about your goals, budget and timing, then apply to get started.'),
             ('Match land and model', 'Carly’s team runs a personalized land search and helps you choose the model that fits the lot.'),
             ('Build and prepare for ownership', 'Sign your agreement and construction begins on your site-built home.')]
    stepsh = ''.join(f'<li class="step"><span class="step-no">{i}</span><h3 class="card-title">{t}</h3><p>{b}</p></li>' for i, (t, b) in enumerate(steps, 1))
    ms = list(flat(rows[6])); body = next(m['html'] for m in ms if m['type'] == 'rich-text')
    carly = words(plain(body), 115)
    qs = []
    for m in flat(rows[7]):
        if m['type'] == 'rich-text':
            ls = lines(m['html']); qs.append((ls[0], ' '.join(ls[1:]).strip('"“” ')))
    qh = ''.join(f'<figure class="card testimonial"><blockquote><p>“{esc(t)}”</p></blockquote><figcaption>{esc(n.title())}</figcaption></figure>' for n, t in qs)
    fin = plain(next(m['html'] for m in flat(rows[8]) if m['type'] == 'rich-text'))
    cards = ''.join(model_card(MD[k]) for k, _ in MODELS) + '<article class="model-card compare-card"><div class="model-card-body"><h3 class="card-title"><a href="financing.html">Compare all models</a></h3><p>See block and elevated foundation prices for all five homes side by side.</p><span class="text-link" aria-hidden="true">Compare pricing' + ARROW + '</span></div></article>'
    body = f'''<section class="home-hero"><div class="container home-hero-grid"><div class="home-hero-text">
<p class="eyebrow">Builds by Carly</p><h1 class="home-title">Luxury tiny homes in the Smoky Mountains</h1>
<p class="lead">{esc(words(txt, 40))}</p><div class="button-row">{button('Explore the models', '#models')}{button('View pricing', 'financing.html', 'secondary')}</div>
<p class="fact-line">Site-built homes in Sevier County, Tennessee</p></div>
<figure class="home-hero-media"><img src="{esc(hero_img)}" alt="A completed Builds by Carly A-frame tiny home in the Smoky Mountains" width="1600" height="1200" fetchpriority="high"><div class="hero-badge"><span class="icon-chip"><i class="fa-solid fa-house-chimney" aria-hidden="true"></i></span><span><span class="label">5 models from</span><span class="price">{esc(MIN_PRICE)}</span></span></div></figure></div></section>
<section class="section" id="models"><div class="container"><div class="section-head"><div><h2>Find your model</h2><p class="intro">{esc(intro)}</p></div></div><div class="card-grid cols-3 model-grid">{cards}</div></div></section>
<section class="section section-soft"><div class="container"><h2>Why Builds by Carly</h2><div class="card-grid cols-4">{difh}</div></div></section>
<section class="section"><div class="container"><div class="section-head"><h2>How it works</h2>{tlink('See the full process', 'get-on-our-list.html')}</div><ol class="steps">{stepsh}</ol></div></section>
<section class="section section-soft"><div class="container founder"><img src="{esc(im('https://buildsbycarly.com/files/2023/12/Carly-Bowlen.jpg'))}" alt="Carly Bowlen, founder of Builds by Carly" width="600" height="760">
<div><h2>Working with Carly Bowlen</h2><p>{esc(carly)}</p>{tlink('About Builds by Carly', 'about-bbc.html')}</div></div></section>
<section class="section"><div class="container"><h2>What owners say</h2><div class="card-grid cols-3">{qh}</div></div></section>
<section class="section section-soft"><div class="container split-even align-center"><div><h2>Financing that fits</h2><p>{esc(fin)}</p><p class="note">Options depend on eligibility and project details.</p></div><div>{button('Explore pricing & financing', 'financing.html')}</div></div></section>
{closing_cta()}'''
    return shell('index.html', 'Builds by Carly | Luxury tiny homes in the Smoky Mountains', body, words(txt, 26), hero_img)

def financing():
    r0 = list(flat(D['financing']['rows'][0]))
    logo = next(m['src'] for m in r0 if m['type'] in ('photo', 'uabb-photo'))
    rt = [plain(m['html']) for m in r0 if m['type'] == 'rich-text']
    bt = [m for m in r0 if m['type'] == 'button']
    lbl = {'APPLY': 'Apply with the lender', 'CALL US': 'Call the lender', 'EMAIL US': 'Email the lender'}
    lb = ''.join(button(lbl.get(m['text'].strip(), m['text']), link(m['href']), 'primary' if i == 0 else 'secondary') for i, m in enumerate(bt))
    rows = ''.join(f'<tr data-reveal><th scope="row"><div class="pt-model"><img src="{esc(im(MD[k]["card"].get("photo") or MD[k]["hero"]))}" alt="" width="120" height="90" loading="lazy"><div><a href="{k}.html">{esc(n)}</a><span class="row-area">{esc(MD[k]["area"])}</span></div></div></th><td data-label="Block foundation"><span class="pt-price">{esc(PRICES[n]["block"])}</span></td><td data-label="Elevated tree-house foundation"><span class="pt-price">{esc(PRICES[n]["elevated"])}</span></td><td data-label="Construction deposit"><span class="pt-deposit">{esc(PRICES[n]["deposit"])}</span></td><td class="pt-action"><a class="button button-secondary" href="contact.html?model={n.replace(" ", "+")}">Ask about {esc(n)}</a></td></tr>' for k, n in MODELS)
    body = f'''<section class="page-intro"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li aria-current="page">Pricing &amp; financing</li></ol></nav>
<h1>Pricing &amp; financing</h1><p class="lead">Compare the starting price of all five models on a block or elevated tree-house foundation, plus the construction deposit. Financing options from our lending partner follow the pricing.</p>
<p>{tlink('See lender options', '#lender')}</p></div></section>
<section class="section section-tight"><div class="container"><h2 class="h2">Model pricing</h2><div class="table-wrap"><table class="price-table"><caption class="visually-hidden">Model pricing</caption>
<thead><tr><th scope="col">Model</th><th scope="col"><i class="fa-solid fa-cubes"></i> Block foundation</th><th scope="col"><i class="fa-solid fa-tree"></i> Elevated tree-house</th><th scope="col"><i class="fa-solid fa-hand-holding-dollar"></i> Deposit</th><th scope="col"><span class="visually-hidden">Inquiry</span></th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="terms-panel terms-wide" data-reveal><h3>Price terms</h3><ul class="terms-list">{TERMS_LI}</ul></div></div></section>
<section class="section section-soft" id="lender"><div class="container lender"><div class="card lender-card"><div class="lender-logo-wrap"><img src="{esc(im(logo))}" alt="Foundation Mortgage logo" width="300" height="300"></div>
<div class="lender-body"><span class="pill"><i class="fa-solid fa-building-columns"></i> Lending partner</span><h2>{esc(rt[0] if rt else 'Financing')}</h2>{''.join(f'<p>{esc(t)}</p>' for t in rt[1:])}<p class="note">Lending is provided by a third party. Program terms depend on eligibility and project details. The application opens the lender’s site.</p><div class="button-row">{lb}</div></div></div></div></section>
<section class="section"><div class="container split-even align-center"><div><h2>Talk through your budget</h2><p>Questions about what is included, foundation choices or deposit timing? Carly can walk you through them.</p></div><div class="button-row">{button('Discuss my budget', 'contact.html')}{button('Explore models', 'index.html#models', 'secondary')}</div></div></section>'''
    return shell('financing.html', 'Pricing & financing | Builds by Carly', body, 'Starting prices for the Juniper, Lily, Laurel Loft, Azalea and Iris on block and elevated foundations, plus deposit terms and financing.')

def model_select():
    return '<option value="">Not sure yet</option>' + ''.join(f'<option>{n}</option>' for _, n in MODELS)
def field(label, inp, hint='', cls=''):
    return f'<div class="field {cls}"><label for="{inp[1]}">{label}{hint}</label>{inp[0]}<p class="field-error" id="{inp[1]}-err" hidden></p></div>'
REQ = ' <span class="req">(required)</span>'; OPT = ' <span class="opt-tag">(optional)</span>'
def contact_form():
    return f'''<form class="bbc-form card form-card" data-form="Contact form" novalidate><h2>Send a message</h2>
<p class="note">Fields marked required must be filled in.</p>
{field('Full name' + REQ, ('<input id="cf-name" name="name" required autocomplete="name">', 'cf-name'))}
{field('Email' + REQ, ('<input id="cf-email" name="email" type="email" required autocomplete="email">', 'cf-email'))}
{field('Phone' + OPT, ('<input id="cf-phone" name="phone" type="tel" autocomplete="tel">', 'cf-phone'))}
{field('Model of interest' + OPT, (f'<select id="cf-model" name="model">{model_select()}</select>', 'cf-model'))}
{field('How can we help?' + REQ, ('<textarea id="cf-message" name="message" required></textarea>', 'cf-message'))}
<div class="field"><label class="check"><input type="checkbox" name="ok_to_contact" value="Yes" required> Builds by Carly may contact me about this inquiry{REQ}</label></div>
{B.hp()}<button class="button button-primary submit" type="submit">Send inquiry</button>
<p class="note">We use your details only to reply to this inquiry. See the <a href="https://buildsbycarly.com/privacy-policy">Privacy Policy</a>.</p>
<p class="status" role="status" aria-live="polite"></p></form>'''
def checks(name, legend, opts, kind='checkbox', req=False, note=''):
    r = ' required' if req and kind == 'radio' else ''
    notep = f'<p class="note">{note}</p>' if note else ''
    o = ''.join(f'<label class="check"><input type="{kind}" name="{name}" value="{esc(x)}"{r}> {esc(x)}</label>' for x in opts)
    return f'<fieldset class="field choice"><legend>{esc(legend)}{REQ if req else OPT}</legend>{notep}<div class="choices">{o}</div></fieldset>'
def list_form():
    return f'''<form class="bbc-form card form-card" id="application" data-form="Project application" novalidate><h2>Start your project</h2>
<p>Tell us about your plans. Carly will review your answers and contact you to talk through land, models and next steps.</p>
<fieldset class="group"><legend class="group-title">Your details</legend>
{field('Full name' + REQ, ('<input id="lf-name" name="name" required autocomplete="name">', 'lf-name'))}
{field('Email' + REQ, ('<input id="lf-email" name="email" type="email" required autocomplete="email">', 'lf-email'))}
{field('Phone' + REQ, ('<input id="lf-phone" name="phone" type="tel" required autocomplete="tel">', 'lf-phone'))}</fieldset>
<fieldset class="group"><legend class="group-title">Project preferences</legend>
{checks('model', 'Preferred model', [n for _, n in MODELS] + ['Not sure yet'], note='Select all that apply.')}
{checks('locations', 'Preferred area', ['Gatlinburg', 'Pigeon Forge', 'Sevierville', 'Wears Valley', 'Townsend', 'Other areas in Sevier and Cocke county'], note='Select all that apply.')}
{checks('owned_rental', 'Have you owned a short-term or long-term rental?', ['Yes', 'No'], 'radio')}</fieldset>
<fieldset class="group"><legend class="group-title">Financing readiness</legend>
{checks('financing', 'How do you plan to fund the purchase?', ['Cash', 'Mortgage', 'Other', 'Exploring options'], 'radio')}
{checks('deposit_ready', 'The $15,000 construction deposit', ['Ready', 'Need to discuss', 'Not sure'], 'radio')}</fieldset>
{field('Anything else we should know?' + OPT, ('<textarea id="lf-message" name="message"></textarea>', 'lf-message'))}
{B.hp()}<button class="button button-primary submit" type="submit">Submit application</button>
<p class="note">We use your details only to discuss your project. See the <a href="https://buildsbycarly.com/privacy-policy">Privacy Policy</a>.</p>
<p class="status" role="status" aria-live="polite"></p></form>'''
B.contact_form = contact_form; B.list_form = list_form

def contact():
    body = f'''<section class="section contact-page"><div class="container contact-grid">
<div class="contact-intro"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li aria-current="page">Contact</li></ol></nav>
<h1>Contact Carly</h1><p class="lead">Connect with me to get answers to all your questions. You can call or email me.</p>
<ul class="contact-actions"><li><span class="label">Call Carly</span><a href="tel:8655050514">(865) 505-0514</a></li><li><span class="label">Email Carly</span><a href="mailto:info@buildsbycarly.com">info@buildsbycarly.com</a></li></ul>
<p>Ready for a detailed brief? {tlink('Start your project', 'get-on-our-list.html#application')}</p></div>
<div class="contact-form">{contact_form()}</div>
<figure class="contact-photo"><img src="{esc(im('https://buildsbycarly.com/files/2023/12/Carly-Bowlen.jpg'))}" alt="Carly Bowlen, founder of Builds by Carly" loading="lazy" width="600" height="760"></figure></div></section>'''
    return shell('contact.html', 'Contact Carly | Builds by Carly', body, 'Call, email or message Carly Bowlen at Builds by Carly about site-built luxury tiny homes in the Smoky Mountains.')

def process():
    r0 = list(flat(D['get-on-our-list']['rows'][0]))
    intro = plain(next(m['html'] for m in r0 if m['type'] == 'rich-text' and len(plain(m['html'])) > 60))
    steps = []; cur = None
    for m in r0:
        if m['type'] == 'heading' and m['text'].strip().upper().startswith('STEP'): cur = [m['text'].strip().title(), '']; steps.append(cur)
        elif m['type'] == 'rich-text' and cur and not cur[1]: cur[1] = plain(m['html'])
    sh = ''.join(f'<li class="t-step" data-reveal><span class="t-node">{i}</span><div class="t-card"><h2 class="card-title">{esc(t)}</h2><span class="label">{esc(n)}</span></div></li>' for i, (n, t) in enumerate(steps, 1))
    r1 = list(flat(D['get-on-our-list']['rows'][1]))
    fi = plain(next(m['html'] for m in r1 if m['type'] == 'rich-text' and len(plain(m['html'])) > 60))
    body = f'''<section class="page-intro"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li aria-current="page">How it works</li></ol></nav>
<h1>How your build comes together</h1><p class="lead">{esc(intro)}</p><div class="button-row">{button('Start your project', '#application')}{button('Compare pricing', 'financing.html', 'secondary')}</div></div></section>
<section class="section section-tight"><div class="container"><ol class="timeline">{sh}</ol></div></section>
<section class="section section-soft"><div class="container form-wrap"><p class="intro">{esc(fi)}</p>{list_form()}</div></section>
{closing_cta()}'''
    return shell('get-on-our-list.html', 'How it works | Builds by Carly', body, words(intro, 26))

import charts as C
def ic(name): return f'<i class="fa-solid fa-{name}" aria-hidden="true"></i>'
def chip(name): return f'<span class="icon-chip">{ic(name)}</span>'
def city_data(r):
    ms = list(flat(r)); d = {}
    dual = next(m for m in ms if m['type'] == 'dual-color-heading')
    d['city'] = tc((dual.get('a', '') + ' ' + dual.get('b', '')).replace('PERFORMANCE', '').strip())
    rt = [m for m in ms if m['type'] == 'rich-text']
    sm = re.match(r'Score\s*(\d+)/100\s*(.*)', plain(rt[0]['html']))
    d['score'], d['summary'] = (int(sm.group(1)), sm.group(2)) if sm else (None, plain(rt[0]['html']))
    d['metrics'] = []
    for m in ms:
        if m['type'] == 'info-box':
            ls = lines(m['html']); d['metrics'].append((ls[0].rstrip(':'), ls[1] if len(ls) > 1 else '', ' '.join(ls[2:]).strip('()')))
    d['photo'] = im(next((m['src'] for m in ms if m['type'] in ('photo', 'uabb-photo')), ''))
    d['stays'] = []
    for m in ms:
        if m['type'] == 'uabb-numbers':
            ls = [x.strip() for x in m['text'].split('\n') if x.strip()]
            d['stays'].append((f'{ls[1]} {ls[2].lower()}', float(ls[0].rstrip('%'))))
    nt = next((m for m in rt if 'MICRO-NOTES' in plain(m['html'])), None)
    d['notes'] = [x for x in lines(nt['html']) if 'MICRO-NOTES' not in x] if nt else []
    return d

def rental():
    cities = [city_data(r) for r in D['rental-metrics']['rows'][:3]]
    MI = {'Annual Revenue': 'sack-dollar', 'Occupancy Rate': 'calendar-check', 'Avg Daily Rate (ADR)': 'tag'}
    cards = ''
    for c in cities:
        mets = ''.join(f'<li>{chip(MI.get(l, "chart-simple"))}<span><span class="label">{esc(l)}</span><span class="metric-value">{esc(v)}</span><span class="note">{esc(n)}</span></span></li>' for l, v, n in c['metrics'])
        ring = C.ring(c['score'], 'Market score as published') if c['score'] else ''
        cards += f'<article class="city-card"><div class="city-photo" style="--bg:url(\'{c["photo"].replace("assets/", "", 1)}\')"><h3>{esc(c["city"])}</h3></div><div class="city-body">{ring}<p>{esc(c["summary"])}</p><ul class="metric-list">{mets}</ul></div></article>'
    def series(i): return [(c['city'], c['metrics'][i][1]) for c in cities if len(c['metrics']) > i]
    bars = C.hbars(series(0), 'Annual revenue, typical 1–2 bedroom') + C.hbars(series(1), 'Occupancy rate') + C.hbars(series(2), 'Average daily rate (ADR)')
    stacks = ''
    for c in cities:
        tot = sum(p for _, p in c['stays'])
        rows = [(l, p, p <= 100) for l, p in c['stays']]
        note = ''
        if any(not ok for _, _, ok in rows): note = 'One published share is above 100%, so it is shown as under review until the source is confirmed.'
        elif abs(tot - 100) > 1.5: note = f'Published shares total {tot:g}%, so the bar is scaled to fit. Source to be confirmed.'
        stacks += C.stacked(rows, f'{c["city"]}: listings by minimum stay', note)
    notes = ''.join(f'<article class="card"><span class="icon-chip">{ic("lightbulb")}</span><h3 class="card-title">{esc(c["city"])} notes</h3><ul class="tick-list">' + ''.join(f'<li>{esc(n)}</li>' for n in c['notes']) + '</ul></article>' for c in cities)
    th = ''.join(f'<th scope="col">{esc(c["city"])}</th>' for c in cities)
    trs = ''.join(f'<tr><th scope="row">{esc(cities[0]["metrics"][i][0])}</th>' + ''.join(f'<td>{esc(c["metrics"][i][1])}</td>' for c in cities) + '</tr>' for i in range(3))
    body = f'''<section class="page-intro data-intro"><div class="container"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li>Resources</li><li aria-current="page">Rental metrics</li></ol></nav>
<p class="eyebrow">{ic("chart-line")} Rental metrics</p><h1>Smoky Mountain rental market snapshot</h1><p class="lead">A side-by-side look at short-term rental performance in Sevierville, Pigeon Forge and Gatlinburg, using the figures Builds by Carly publishes for each market.</p>
<p class="note">Figures as published. Source, reporting period and sample size are being confirmed.</p></div></section>
<section class="section section-tight"><div class="container"><div class="city-grid">{cards}</div></div></section>
<section class="section section-soft"><div class="container"><h2>How the markets compare</h2><div class="chart-grid">{bars}</div>
<div class="table-wrap"><table class="data-table"><caption>Market comparison table</caption><thead><tr><th scope="col">Metric</th>{th}</tr></thead><tbody>{trs}</tbody></table></div></div></section>
<section class="section"><div class="container"><h2>How long guests must stay</h2><p class="intro">The share of listings in each market by minimum-stay requirement. This shows booking rules, not how long guests actually stay.</p><div class="stack-list">{stacks}</div></div></section>
<section class="section section-soft"><div class="container"><h2>Market notes</h2><div class="card-grid cols-3">{notes}</div></div></section>
{closing_cta('Discuss a property scenario')}'''
    return shell('rental-metrics.html', 'Rental metrics | Builds by Carly', body, 'Short-term rental revenue, occupancy, ADR and minimum-stay data for Sevierville, Pigeon Forge and Gatlinburg.')

def short(v):
    x = C.num(v)
    if v.startswith('$') and x >= 1e9: return f'${x/1e9:.2f}B'
    if v.startswith('$') and x >= 1e6: return f'${x/1e6:.0f}M'
    if not v.startswith('$') and x >= 1e4: return f'{x/1e3:.1f}K'
    return v
def tourism():
    R = D['tourism-breakdown']['rows']
    r0 = list(flat(R[0])); intro = plain(next(m['html'] for m in r0 if m['type'] == 'rich-text'))
    photo = im(next(m['src'] for m in r0 if m['type'] in ('photo', 'uabb-photo')))
    btns = ''.join(button(m['text'], link(m['href']), 'primary' if i == 0 else 'secondary') for i, m in enumerate(m for m in r0 if m['type'] == 'button'))
    mets = []; cur = None
    for m in flat(R[1]):
        if m['type'] == 'heading':
            if cur and 'value' in cur and 'sub' not in cur: cur['sub'] = m['text'].strip()
            elif m['text'].strip() not in ('BY THE NUMBERS',): cur = {'label': m['text'].strip()}; mets.append(cur)
        elif m['type'] == 'numbers' and cur: cur['value'] = (m.get('text') or '').strip().split('\n')[0]
    mets = [x for x in mets if 'value' in x]
    src1 = plain(next((m['html'] for m in flat(R[1]) if m['type'] == 'rich-text'), ''))
    pv = re.search(r'([\d.]+M)\s+GSMNP visits\s*\((\d{4})\)', intro)
    MI = {'SPENDING': 'sack-dollar', 'EMPLOYMENT': 'people-group', 'LABOR INCOME': 'money-bill-wave', 'STATE TAXES': 'landmark', 'LOCAL TAXES': 'building-columns', 'COUNTY POSITION': 'trophy'}
    top = [x for x in mets if x['label'] in ('SPENDING', 'EMPLOYMENT')]
    big = ''.join(f'<article class="kpi">{chip(MI[x["label"]])}<span class="label">{esc(sc(x["label"]))}</span><span class="kpi-value">{esc(short(x["value"]))}</span><span class="note">{esc(sc(x.get("sub", "")))} · exact {esc(x["value"])}</span></article>' for x in top)
    if pv: big += f'<article class="kpi">{chip("mountain-sun")}<span class="label">Park visits</span><span class="kpi-value">{pv.group(1)}</span><span class="note">Great Smoky Mountains National Park, {pv.group(2)}</span></article>'
    small = ''.join(f'<li>{chip(MI.get(x["label"], "chart-simple"))}<span><span class="label">{esc(sc(x["label"]))}</span><strong>{esc(short(x["value"]))}</strong> <span class="note">{esc(sc(x.get("sub", "")))}</span></span></li>' for x in mets if x not in top)
    cats = []; cur = None; r2 = list(flat(R[2]))
    for m in r2:
        if m['type'] == 'heading' and not m['text'].strip().startswith('(') and m['text'].strip() not in ('VISITOR SPEND',): cur = [sc(m['text'].strip().rstrip('*')), 0, '']; cats.append(cur)
        elif m['type'] == 'heading' and m['text'].strip().startswith('(') and cur: cur[1] = float(m['text'].strip('()% '))
        elif m['type'] == 'uabb-numbers' and cur: cur[2] = m['text'].strip()
    cats = [c for c in cats if c[1]]
    r2t = [plain(m['html']) for m in r2 if m['type'] == 'rich-text']
    total = next((short(x['value']) for x in mets if x['label'] == 'SPENDING'), '')
    don = C.donut([tuple(c) for c in cats], 'Visitor spending by industry', total, 'visitor spending')
    r4 = list(flat(R[4])); groups = []; cur = None
    for m in r4:
        if m['type'] == 'dual-color-heading': cur = {'title': tc((m.get('a', '') + ' ' + m.get('b', '')).strip()), 'rows': []}; groups.append(cur)
        elif m['type'] == 'uabb-numbers' and cur:
            ls = [x.strip() for x in m['text'].split('\n') if x.strip()]
            cur['rows'].append((ls[1].split()[0], ls[0], 'Est' in ' '.join(ls[1:])))
    gt = {'Spending by Industry': 'Annual visitor spending', 'Tourism Related Taxes': 'Tourism-related taxes'}
    trend = ''.join(C.columns(g['rows'], gt.get(g['title'], g['title'])) for g in groups)
    drv = []; cur = None
    for m in flat(R[3]):
        if m['type'] == 'heading' and m['text'].strip() not in ('DEMAND DRIVERS',): cur = [m['text'].strip(), '', None]; drv.append(cur)
        elif m['type'] == 'rich-text' and cur: cur[1] = plain(m['html'])
        elif m['type'] == 'button' and cur: cur[2] = m
    dintro = plain(next(m['html'] for m in flat(R[3]) if m['type'] == 'rich-text'))
    DI = ['mountain', 'ticket', 'people-roof']
    drvh = ''.join(f'<article class="card">{chip(DI[i % 3])}<h3 class="card-title">{esc(tc(t))}</h3><p>{esc(b)}</p>{tlink("Explore build areas", "area-overview.html")}</article>' for i, (t, b, _) in enumerate(drv) if b)
    r5 = list(flat(R[5]))
    srcs = ''.join(f'<div class="prose">{clean(m["html"]).replace("{{latest official year}}", "latest edition")}</div>' for m in r5 if m['type'] == 'rich-text')
    sb = ''.join(tlink(m['text'], link(m['href'])) for m in r5 if m['type'] == 'button')
    body = f'''<section class="page-intro data-intro"><div class="container split-even align-center"><div><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li>Resources</li><li aria-current="page">Tourism</li></ol></nav>
<p class="eyebrow">{ic("compass")} Tourism breakdown</p><h1>Tourism in the Smokies</h1><p class="lead">{esc(intro)}</p><div class="button-row">{btns}</div></div>
<figure class="intro-media" data-reveal><img src="{esc(photo)}" alt="Smoky Mountains landscape" width="900" height="1200"></figure></div></section>
<section class="section section-tight"><div class="container"><h2>Sevier County visitor economy</h2><div class="kpi-grid">{big}</div><ul class="mini-stats">{small}</ul><p class="note">{esc(src1).replace("{{latest official year}}", "latest edition")}</p></div></section>
<section class="section section-soft"><div class="container split-even align-center">{don}<div><h2>Where visitors spend</h2>{''.join(f'<p>{esc(t)}</p>' for t in r2t[:1])}{''.join(f'<p class="note">{esc(t)}</p>' for t in r2t[1:])}</div></div></section>
<section class="section"><div class="container"><h2>Spending and taxes over time</h2><p class="intro">Striped bars are estimates until the official release.</p><div class="chart-grid cols-2">{trend}</div></div></section>
<section class="section section-soft"><div class="container"><h2>Why visitors keep coming</h2><p class="intro">{esc(dintro)}</p><div class="card-grid cols-3">{drvh}</div></div></section>
<section class="section"><div class="container narrow"><h2>Sources and methodology</h2>{srcs}<div class="button-row">{sb}</div></div></section>
{closing_cta()}'''
    return shell('tourism-breakdown.html', 'Tourism in the Smokies | Builds by Carly', body, words(intro, 26))

ICONS = {'Site-built construction': 'helmet-safety', 'Foundation options': 'layer-group', 'Land selection support': 'map-location-dot', 'Design for guest use': 'key',
         'Discuss the project': 'comments', 'Match land and model': 'map', 'Build and prepare for ownership': 'hammer',
         'Apply to Get Started': 'file-pen', 'Personalized Land Search Begins': 'magnifying-glass-location', 'Land Secured – Initial Deposit Due': 'handshake',
         'Select Your Tiny Home Model': 'house', 'Sign Agreement – Final Deposit Due': 'file-signature', 'Construction Begins': 'person-digging'}
RIDGE = '<svg class="ridge" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true"><path d="M0 120V70l120-38 90 26 140-52 110 40 95-30 160 58 120-44 105 30 150-56 120 46 110-28 120 40V120z" fill="currentColor"/></svg>'

def generic(key):
    fn, title = B.PAGES[key]
    html = B2.page(key)
    body = re.search(r'<main id="main">(.*)</main>', html, re.S).group(1)
    body = re.sub(r'<section class="cta-sec[^"]*"[^>]*>.*?</section>$', '', body, flags=re.S) + closing_cta()
    body = body.replace('href="#"', 'href="contact.html"')
    return shell(fn, f'{title} | Builds by Carly', body)

def post(h):
    for g in ('gatlinburg', 'pigeon-forge', 'sevierville', 'smoky-mountains'):
        h = re.sub(r'href="https?://(?:www\.)?buildsbycarly\.com/' + g + r'/?"', f'href="{g}.html"', h)
    h = h.replace('href="/contact"', 'href="contact.html"')
    for t, n in ICONS.items():
        h = h.replace(f'<h3 class="card-title">{t}<', f'<span class="icon-chip"><i class="fa-solid fa-{n}"></i></span><h3 class="card-title">{t}<')
        h = h.replace(f'<h2 class="card-title">{esc(t)}<', f'<span class="icon-chip"><i class="fa-solid fa-{n}"></i></span><h2 class="card-title">{esc(t)}<')
    h = h.replace('<article class="card"><h3 class="card-title">', '<article class="card"><span class="icon-chip"><i class="fa-solid fa-star"></i></span><h3 class="card-title">')
    h = re.sub(r'<(article|figure) class="(card|model-card|city-card|kpi)', r'<\1 data-reveal class="\2', h)
    h = h.replace('<li class="step">', '<li data-reveal class="step">')
    h = re.sub(r'<div class="col( |")', r'<div data-reveal class="col\1', h)
    h = re.sub(r'<h2(?=[ >])(?![^>]*footer-heading)', '<h2 data-reveal', h)
    h = h.replace('<i class="fa', '<i aria-hidden="true" class="fa').replace('aria-hidden="true" aria-hidden="true"', 'aria-hidden="true"')
    h = re.sub(r'(<i aria-hidden="true" class="[^"]*") aria-hidden="true"', r'\1', h)
    h = re.sub(r"--bg:url\('assets/", "--bg:url('", h)
    return h

if __name__ == '__main__':
    out = {'index.html': home(), 'financing.html': financing(), 'contact.html': contact(), 'get-on-our-list.html': process(), 'rental-metrics.html': rental(), 'tourism-breakdown.html': tourism()}
    for k, n in MODELS: out[f'{k}.html'] = model_page(k)
    for k in B.PAGES:
        fn = B.PAGES[k][0]
        if fn not in out: out[fn] = generic(k)
    import guides; out.update(guides.pages())
    out['404.html'] = shell('404.html', 'Page not found | Builds by Carly', f'<section class="section"><div class="container narrow"><h1>Page not found</h1><p class="lead">That page has moved or no longer exists.</p><div class="button-row">{button("Go to the home page", "index.html")}{button("Contact Carly", "contact.html", "secondary")}</div></div></section>', 'Page not found.')
    for fn, h in out.items(): open('site/' + fn, 'w').write(post(h))
    print('built', len(out))
