import json, re, html as H
from bs4 import BeautifulSoup

D = json.load(open('content2.json'))
import os
IMG = json.load(open('imgmap.json')) if os.path.exists('imgmap.json') else {}
def im(u): return IMG.get(u, u)
WEBHOOK = "https://hwoard1081.app.n8n.cloud/webhook/bbc-form"
BASE = "https://buildsbycarly.com"
PAGES = {  # key in content2 -> (file, nav title)
 'home':('index.html','Home'), 'juniper':('juniper.html','Juniper'), 'lily':('lily.html','Lily'),
 'laurel-loft':('laurel-loft.html','Laurel Loft'), 'azalea':('azalea.html','Azalea'), 'iris':('iris.html','Iris'),
 'why-tiny-homes':('why-tiny-homes.html','Why Tiny Homes'), 'tourism-breakdown':('tourism-breakdown.html','Tourism Breakdown'),
 'rental-metrics':('rental-metrics.html','Rental Metrics'), 'area-overview-2':('area-overview.html','Area Overview'),
 'financing':('financing.html','Financing & Pricing'), 'about-bbc':('about-bbc.html','About Builds By Carly'),
 'contact':('contact.html','Contact'), 'get-on-our-list':('get-on-our-list.html','Get On Our List'),
 'b_about-wallace-2':('about-wallace.html','About Wallace'),
}
SLUG = {'':'index.html','juniper':'juniper.html','lily':'lily.html','laurel-loft':'laurel-loft.html','azalea':'azalea.html',
 'iris':'iris.html','why-tiny-homes':'why-tiny-homes.html','tourism-breakdown':'tourism-breakdown.html','rental-metrics':'rental-metrics.html',
 'area-overview-2':'area-overview.html','area-overview':'area-overview.html','financing':'financing.html','about-bbc':'about-bbc.html',
 'contact':'contact.html','get-on-our-list':'get-on-our-list.html','b/about-wallace-2':'about-wallace.html'}
NAV = [('Home','index.html',None),
 ('Our Models',None,[('Juniper','juniper.html'),('Lily','lily.html'),('Laurel Loft','laurel-loft.html'),('Azalea','azalea.html'),('Iris','iris.html')]),
 ('Investment Opportunity',None,[('Why Tiny Homes','why-tiny-homes.html'),('The Process','get-on-our-list.html')]),
 ('Location Insights',None,[('Tourism Breakdown','tourism-breakdown.html'),('Rental Metrics','rental-metrics.html'),('Area Overview','area-overview.html')]),
 ('Financing & Pricing','financing.html',None),
 ('About',None,[('About Builds By Carly','about-bbc.html'),('About Wallace','about-wallace.html')]),
 ('Contact','contact.html',None)]
FOOTER_NODE = 'h3sbdol2pw9g'

def link(h):
    if not h: return h
    m = re.match(r'^(?:https?://(?:www\.)?buildsbycarly\.com)?/?([^?#]*)', h)
    if h.startswith(('http','/')) and m and ('buildsbycarly.com' in h or h.startswith('/')):
        s = m.group(1).strip('/')
        if s in SLUG: return SLUG[s]
        if h.startswith('/'): return BASE + h
    return h

def clean(h):
    s = BeautifulSoup(h or '', 'html.parser')
    for t in s.find_all(True):
        for a in list(t.attrs):
            if a not in ('href','src','alt','target','colspan','rowspan'): del t[a]
        if t.name == 'a' and t.get('href'): t['href'] = link(t['href'])
        if t.name == 'img' and t.get('src'): t['src'] = im(t['src'])
        if t.name in ('span','font'): t.unwrap()
    out = str(s)
    out = re.sub(r'<div>(\s|&nbsp;|\xa0)*</div>', '', out)
    out = re.sub(r'<p>(\s|&nbsp;|\xa0)*</p>', '', out)
    return out.strip()

def esc(t): return H.escape(t or '', quote=True)
def is_dark(c):
    n = [float(x) for x in re.findall(r'[\d.]+', c or '')]
    if len(n) < 3 or (len(n) > 3 and n[3] == 0): return None
    return (0.299*n[0]+0.587*n[1]+0.114*n[2]) < 110
def fpx(font):
    m = re.search(r'([\d.]+)px', font or ''); return float(m.group(1)) if m else 16

FA = {'ua-icon ua-icon-edit':'fa-solid fa-pen-to-square','ua-icon ua-icon-map':'fa-solid fa-map-location-dot','ua-icon ua-icon-home':'fa-solid fa-house',
 'ua-icon ua-icon-envelope':'fa-solid fa-envelope','ua-icon ua-icon-pencil':'fa-solid fa-pencil','ua-icon ua-icon-tools-2':'fa-solid fa-screwdriver-wrench',
 'fab fa-stumbleupon':'fa-solid fa-bath','fas fa-tshirt':'fa-solid fa-shirt','fas fa-hamburger':'fa-solid fa-utensils'}
def icon(c):
    c = FA.get(c, c or ''); return f'<i class="{esc(c)}" aria-hidden="true"></i>' if c else ''

CTX = {}
def mod(m):
    t = m['type']
    if t in ('photo','uabb-photo'):
        src = m.get('src') or ''
        if not src: return ''
        img = f'<img src="{esc(im(src))}" alt="{esc(m.get("alt") or "")}" loading="lazy">'
        cls = 'logo-img' if 'Logo' in src else 'photo'
        if 'Logo_Website' in src: img = img.replace(esc(im(src)), 'assets/Logo_Website.png')
        if m.get('href'): img = f'<a href="{esc(link(m["href"]))}">{img}</a>'
        return f'<figure class="{cls}">{img}</figure>'
    if t == 'heading':
        txt = esc(m['text']); px = fpx(m.get('font'))
        if 'Great Vibes' in (m.get('font') or ''): return f'<p class="script">{txt}</p>'
        if px >= 40: return f'<p class="big-number">{txt}</p>'
        if m['text'].isupper() or px <= 18: return f'<p class="eyebrow">{txt}</p>'
        return f'<p class="kicker">{txt}</p>'
    if t == 'dual-color-heading':
        tag = 'h1' if not CTX.get('h1') else 'h2'; CTX['h1'] = True
        a, b = esc(m.get('a','').strip()), esc(m.get('b','').strip())
        return f'<{tag} class="title">{a}{" " if a and b else ""}<span>{b}</span></{tag}>'
    if t == 'rich-text':
        h = clean(m.get('html'))
        if not h: return ''
        if fpx(m.get('font')) >= 36: return f'<div class="display">{h}</div>'
        if fpx(m.get('font')) >= 22: return f'<div class="lead">{h}</div>'
        return f'<div class="prose">{h}</div>'
    if t == 'button':
        return f'<a class="btn" href="{esc(link(m["href"]))}">{esc(m["text"])}</a>'
    if t == 'uabb-separator': return '<hr class="sep">'
    if t == 'list-icon':
        return '<ul class="features">' + ''.join(f'<li>{icon(m.get("icon"))}<span>{esc(i)}</span></li>' for i in m['items']) + '</ul>'
    if t == 'info-box':
        h = clean(m.get('html'))
        ttl = f'<h3>{esc(m["title"])}</h3>' if m.get('title') else ''
        pre = f'<p class="eyebrow">{esc(m["prefix"])}</p>' if m.get('prefix') else ''
        btn = f'<a class="btn" href="{esc(link(m["href"]))}">Learn more</a>' if m.get('href') and not ttl and False else ''
        return f'<div class="info">{icon(m.get("icon"))}{pre}{ttl}<div class="prose">{h}</div>{btn}</div>'
    if t == 'icon':
        return f'<div class="icon-badge">{icon(m.get("icon"))}</div>'
    if t == 'icon-group':
        return '<div class="stars" aria-label="5 stars">' + '★'*len(m['icons']) + '</div>'
    if t in ('numbers','uabb-numbers'):
        lines = [x.strip() for x in (m.get('text') or '').split('\n') if x.strip()]
        if not lines: return ''
        return f'<div class="stat"><span class="stat-num">{esc(lines[0])}</span><span class="stat-label">{esc(" ".join(lines[1:]))}</span></div>'
    if t == 'uabb-video':
        vid = re.search(r'youtube\.com/embed/([\w-]+)', m.get('raw',''))
        if not vid: return ''
        v = vid.group(1)
        return (f'<div class="video" data-yt="{v}"><img src="https://i.ytimg.com/vi/{v}/maxresdefault.jpg" alt="Video tour" loading="lazy">'
                f'<button class="play" aria-label="Play video"><i class="fa-solid fa-play"></i></button></div>')
    if t == 'gallery':
        return '<div class="gallery">' + ''.join(f'<a href="{esc(im(i))}" class="g-item"><img src="{esc(im(i))}" alt="" loading="lazy"></a>' for i in m['imgs']) + '</div>'
    if t == 'widget':
        if 'mx-form' in (m.get('html') or '') or 'NAME' in (m.get('text') or ''): return contact_form()
        return ('<div class="search-cta"><p>Search homes for sale across East Tennessee.</p>'
                '<a class="btn" href="https://buildsbycarly.com/available-properties">Search Properties</a></div>')
    if t == 'html':
        if 'docs.google.com/forms' in (m.get('html') or '') or CTX['page'] == 'get-on-our-list': return list_form()
        return clean(m.get('html'))
    if t == 'uabb-image-carousel':
        s = BeautifulSoup(m['html'], 'html.parser'); seen = []; out = []
        for a in s.select('.uabb-image-carousel-item:not(.slick-cloned) a'):
            img = a.find('img'); src = img and (img.get('data-src') or img.get('src'))
            if src and src not in seen:
                seen.append(src); out.append(f'<a href="{esc(a.get("href"))}" target="_blank" rel="noopener"><img src="{esc(im(src))}" alt="{esc(img.get("alt"))}" loading="lazy"></a>')
        return '<div class="partners">' + ''.join(out) + '</div>'
    if t == 'testimonials':
        s = BeautifulSoup(m['html'], 'html.parser')
        qs = [q for q in s.select('.fl-testimonial') if 'bx-clone' not in (q.get('class') or [])]
        return '<div class="quotes">' + ''.join(f'<blockquote>{clean(str(q.decode_contents()))}</blockquote>' for q in qs) + '</div>'
    return clean(m.get('html',''))

def col(c):
    inner = ''.join(mod(m) for m in c['mods'])
    # group consecutive buttons
    inner = re.sub(r'((?:<a class="btn"[^>]*>.*?</a>){2,})', r'<div class="btn-row">\1</div>', inner)
    for sg in c.get('sub', []): inner += group(sg)
    if not inner.strip(): return '<div class="col col-empty"></div>'
    return f'<div class="col">{inner}</div>'

def group(g):
    ws = [max(c['wpct'],1) for c in g]
    cols = ' '.join(f'{w}fr' for w in ws)
    n = len(g)
    kind = 'grid-1' if n == 1 else ('grid-2' if n == 2 else f'grid-n')
    return f'<div class="grid {kind}" style="--cols:{cols};--n:{n}">' + ''.join(col(c) for c in g) + '</div>'

def section(r, i):
    bg = r['bg'] if r['bg'] and r['bg'] != 'none' else ''
    img = re.search(r'url\("([^"]+)"\)', bg)
    dark = is_dark(r['bgColor'])
    cls = ['sec']
    style = ''
    if img:
        cls.append('sec-image'); style = f' style="--bg:url(\'{im(img.group(1))}\')"'
    elif dark: cls.append('sec-dark')
    elif i % 2: cls.append('sec-tint')
    if i == 0 and img: cls.append('sec-hero')
    body = ''.join(group(g) for g in r['groups'])
    return f'<section class="{" ".join(cls)}"{style}><div class="wrap">{body}</div></section>'

def nav(cur):
    out = []
    for t, h, sub in NAV:
        if sub:
            active = ' active' if any(x[1]==cur for x in sub) else ''
            items = ''.join(f'<li><a href="{x[1]}"{" aria-current=page" if x[1]==cur else ""}>{esc(x[0])}</a></li>' for x in sub)
            out.append(f'<li class="has-sub{active}"><button type="button" aria-expanded="false">{esc(t)}<i class="fa-solid fa-chevron-down"></i></button><ul>{items}</ul></li>')
        else:
            out.append(f'<li{" class=active" if h==cur else ""}><a href="{h}">{esc(t)}</a></li>')
    return ''.join(out)

def footer():
    return f'''<footer class="site-footer"><div class="wrap">
<div class="f-top"><a href="index.html" class="f-logo"><img src="assets/Footer-Logo.png" alt="Builds By Carly"></a>
<a class="f-phone" href="tel:8655050514">(865) 505-0514</a>
<p class="f-office">WEST OFFICE | 865-693-1111 | info@wallacetn.com | 106 N. Peters Road | Knoxville, TN 37923</p></div>
<div class="f-logos">
<img src="https://brokerage.agent.wallacetn.com/files/2023/09/Wallace-Footer-Logo-300x214-1.png" alt="Wallace Real Estate" loading="lazy">
<img src="https://brokerage.agent.wallacetn.com/files/2023/09/Wallace-Luxury-Footer-Logo.png" alt="Wallace Luxury" loading="lazy">
<img src="https://brokerage.agent.wallacetn.com/files/2023/09/LeadingRE-Footer-Logo-1536x646-1.png" alt="Leading Real Estate Companies of the World" loading="lazy">
<img src="https://images-static.moxiworks.com/static/images/br/images/eho-89x83.png" alt="Equal Housing Opportunity" loading="lazy">
<img src="https://images-static.moxiworks.com/static/images/br/images/realtor_white-71x83.png" alt="Realtor" loading="lazy"></div>
<div class="f-legal"><p>©2023 Wallace Real Estate. All Rights Reserved. Not intended as a solicitation if your property is already listed by another broker. Affiliated real estate agents are independent contractor sales associates, not employees. Wallace fully supports the principles of the Fair Housing Act and the Equal Opportunity Act.</p>
<p><a href="{BASE}/terms-of-use">Terms Of Use</a> | <a href="{BASE}/privacy-policy">Privacy Policy</a> | <a href="{BASE}/accessibility-statement/">Accessibility Statement</a> | <a href="{BASE}/fair-housing-notice/">Fair Housing Notice</a></p></div>
</div></footer>'''

CONSENT = ('By checking the “Ok to Contact” box, I provide my consent and electronic signature authorizing , its affiliates and real estate agents to deliver or cause to be delivered: email messages, telephonic sales calls, text messages, or voicemails, to me at the email address or number above by any means, including automated systems. I understand that I am not required to directly or indirectly consent as a condition of purchasing any property, goods, or services, and that I can opt out of text messages by texting “stop” (message fees may apply), and emails by selecting “unsubscribe”.')
def hp(): return '<input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">'
def contact_form():
    return f'''<form class="bbc-form card" data-form="Contact form" novalidate>
<h2 class="form-title">Get started with me today</h2>
<p>Connect with me to get answers to all your questions. You can call or email me.</p>
<a class="btn btn-outline" href="tel:8655050514"><i class="fa-solid fa-phone"></i> CALL</a>
<p class="muted">Or send me a message.</p>
<div class="fields">
<label>Name<input name="name" autocomplete="name"></label>
<label>Email *<input name="email" type="email" required autocomplete="email"></label>
<label>Phone Number<input name="phone" type="tel" autocomplete="tel"></label>
<label class="full">Message *<textarea name="message" rows="5" required></textarea></label>
</div>
<label class="check"><input type="checkbox" name="ok_to_contact" value="Yes" required> OK TO CONTACT *</label>
{hp()}<button class="btn" type="submit">SEND</button>
<p class="fine">{CONSENT}</p><p class="status" role="status"></p></form>'''

def radios(name, label, opts, req=False, kind='radio'):
    r = ' required' if req and kind=='radio' else ''
    o = ''.join(f'<label class="opt"><input type="{kind}" name="{name}" value="{esc(x)}"{r}> {esc(x)}</label>' for x in opts)
    return f'<fieldset class="full"><legend>{esc(label)}{" *" if req else ""}</legend>{o}</fieldset>'
def list_form():
    return f'''<form class="bbc-form card" data-form="Exclusive List Application" novalidate>
<h2 class="form-title">Builds by Carly Exclusive List Application</h2>
<div class="fields">
<label>Please enter your name *<input name="name" required autocomplete="name"></label>
<label>Please enter your phone number *<input name="phone" type="tel" required autocomplete="tel"></label>
<label class="full">Email<input name="email" type="email" autocomplete="email"></label>
{radios('owned_rental','Have you ever owned a short term rental or long term rental?',['Yes','No'])}
{radios('financing','Do you know how you plan to finance the purchase of a Builds by Carly home?',['Yes - cash','Yes - mortgage','Yes - other financial means','No'])}
{radios('deposit_ready','Do you have your $15,000 construction deposit ready?',['Yes','No'])}
{radios('locations','Locations of interest',['Gatlinburg','Pigeon Forge','Sevierville','Wears Valley','Townsend','Other areas in Sevier and Cocke county'],kind='checkbox')}
{radios('model','Tiny home model',['Lily','Juniper','Laurel Loft','Azalea','Any of the above'],kind='checkbox')}
<label class="full">Is there anything else you would like us to know?<textarea name="message" rows="4"></textarea></label>
</div>{hp()}<button class="btn" type="submit">Submit Application</button><p class="status" role="status"></p></form>'''

def page(key):
    fn, title = PAGES[key]; CTX.clear(); CTX['page'] = key
    rows = [r for r in D[key]['rows'] if r['node'] != FOOTER_NODE]
    body = ''.join(section(r, i) for i, r in enumerate(rows))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Builds By Carly</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Great+Vibes&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="assets/site.css"></head><body class="page-{esc(key)}">
<header class="site-header"><div class="wrap hdr">
<a class="brand" href="index.html"><img src="assets/Footer-Logo.png" alt="Builds By Carly"></a>
<button class="menu-toggle" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
<nav class="main-nav"><ul>{nav(fn)}</ul><a class="btn btn-sm nav-cta" href="get-on-our-list.html">Get on Our List</a></nav>
</div></header>
<main>{body}</main>{footer()}
<div class="lightbox" hidden><button class="lb-close" aria-label="Close">&times;</button><button class="lb-prev" aria-label="Previous">&#8249;</button><img alt=""><button class="lb-next" aria-label="Next">&#8250;</button></div>
<script>window.BBC_FORM_ENDPOINT="{WEBHOOK}";</script><script src="assets/site.js"></script></body></html>'''

if __name__=='__main__':
  for k in PAGES:
    open('site/' + PAGES[k][0], 'w').write(page(k))
  print('built', len(PAGES))
