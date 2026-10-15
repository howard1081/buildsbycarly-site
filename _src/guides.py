import json, re, urllib.parse
from bs4 import BeautifulSoup
import build3 as G
from build import FOOTER_NODE
esc, im, plain, words, tc = G.esc, G.im, G.plain, G.words, G.tc
D3 = json.load(open('content3.json'))
GUIDES = [('gatlinburg', 'Gatlinburg'), ('pigeon-forge', 'Pigeon Forge'), ('sevierville', 'Sevierville'), ('smoky-mountains', 'Smoky Mountains')]
FIX = {'FOBIDDEN': 'FORBIDDEN', 'APPALACIAN': 'APPALACHIAN', 'APALACHIAN': 'APPALACHIAN', 'PRIVATLEY': 'PRIVATELY', 'MNTS': 'MOUNTAINS'}
def fix(t):
    for a, b in FIX.items(): t = t.replace(a, b)
    return t
QL = {'GOV WEBSITE': ('landmark', 'Official website'), 'RESTAURANTS': ('utensils', 'Find restaurants'), 'MUSEUMS': ('building-columns', 'Find museums'),
      'THINGS TO DO': ('map-location-dot', 'Things to do'), 'TRANSIT': ('bus', 'Transit stations')}
FACT_ICONS = ['star', 'lightbulb', 'compass', 'mountain-sun', 'clock-rotate-left', 'heart', 'tree', 'flag']
def bg(r):
    m = re.search(r'url\("([^"]+)"\)', r['bg'] or ''); return im(m.group(1)) if m else ''
def real(u):
    if 'google.com/url' in u: return urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get('q', [u])[0]
    return u
def data(key):
    rows = [r for r in D3[key]['rows'] if r['node'] != FOOTER_NODE]
    d = {'key': key, 'hero': bg(rows[0])}
    r0 = list(G.flat(rows[0]))
    rts = [G.plain(m['html']) for m in r0 if m['type'] == 'rich-text']
    d['intro'] = next((t for t in rts if len(t) > 60), '')
    d['links'] = [(m['text'].strip(), real(m['href'])) for m in r0 if m['type'] == 'button']
    w = next((m for m in r0 if m['type'] == 'html' and 'weatherwidget' in m.get('html', '')), None)
    d['weather'] = re.search(r'href="([^"]+)"', w['html']).group(1) if w else None
    tabs = next((m for m in G.flat(rows[1]) if m['type'] == 'advanced-tabs'), None)
    d['facts'] = []
    if tabs:
        s = BeautifulSoup(tabs['html'], 'html.parser')
        for sec in s.select('.uabb-content-wrap > .section'):
            t = sec.select_one('.uabb-tab-title'); c = sec.select_one('.uabb-content')
            if t and c: d['facts'].append((fix(t.get_text(strip=True)), G.clean(c.decode_contents())))
    items = []; cur = None; pending = None
    for m in G.flat(rows[2]):
        if m['type'] == 'heading' and m['text'].strip() == 'LANDMARKS':
            cur = {'name': '', 'desc': '', 'href': None, 'photo': pending}; pending = None; items.append(cur)
        elif m['type'] == 'rich-text' and cur is not None:
            t = G.plain(m['html'])
            if not cur['name'] and len(t) < 40: cur['name'] = fix(t)
            else: cur['desc'] += t + ' '
        elif m['type'] == 'button' and cur is not None: cur['href'] = m['href']
        elif m['type'] in ('photo', 'uabb-photo'):
            if cur is not None and not cur['photo']: cur['photo'] = m['src']
            else: pending = m['src']
    d['landmarks'] = items
    return d
GD = {k: data(k) for k, _ in GUIDES}
CARD_PHOTO = {'gatlinburg': 1, 'pigeon-forge': 0, 'sevierville': 0, 'smoky-mountains': 1}
for k, d in GD.items(): d['card'] = im(d['landmarks'][CARD_PHOTO[k]]['photo']) if d['landmarks'] else d['hero']

def guide(key, name):
    d = GD[key]
    def ql(t, u):
        icn, lab = QL.get(t, ('arrow-up-right-from-square', G.sc(t)))
        if t == 'GOV WEBSITE' and key == 'smoky-mountains': lab = 'National Park Service'
        return f'<li><a href="{esc(u)}" rel="noopener">{G.ic(icn)} {esc(lab)}</a></li>'
    links = ''.join(ql(t, u) for t, u in d['links'])
    if d['weather']: links += f'<li><a href="{esc(d["weather"])}" rel="noopener">{G.ic("cloud-sun")} {esc(name)} weather</a></li>'
    place = 'Great Smoky Mountains National Park' if key == 'smoky-mountains' else 'Sevier County, Tennessee'
    kind = 'National park guide' if key == 'smoky-mountains' else 'Area guide'
    glance = [('map-pin', f'{len(d["landmarks"])}', 'landmarks to explore'), ('lightbulb', f'{len(d["facts"])}', 'fun facts'), ('location-dot', 'TN', place)]
    gl = ''.join(f'<li data-reveal><span class="icon-chip">{G.ic(i)}</span><span><strong>{esc(v)}</strong> {esc(t)}</span></li>' for i, v, t in glance)
    lm = ''
    for i, x in enumerate(d['landmarks'], 1):
        nm = tc(x['name'])
        btn = f'<a class="button button-secondary" href="{esc(x["href"])}" rel="noopener">Visit {esc(nm)}{G.ARROW}</a>' if x['href'] else ''
        lm += f'''<article class="lm-row" data-reveal><figure class="lm-media"><img src="{esc(im(x['photo']))}" alt="{esc(nm)}" loading="lazy" width="800" height="600"><span class="lm-num">{i:02d}</span></figure>
<div class="lm-body"><span class="label">Landmark {i:02d} of {len(d['landmarks']):02d}</span><h3>{esc(nm)}</h3><p>{esc(x['desc'].strip())}</p>{btn}</div></article>'''
    facts = ''.join(f'<article class="fact-card" data-reveal><span class="icon-chip">{G.ic(FACT_ICONS[i % len(FACT_ICONS)])}</span><h3>{esc(tc(t))}</h3><div class="prose">{c}</div></article>' for i, (t, c) in enumerate(d['facts']))
    tiles = ''.join(f'<a class="area-tile" href="{k}.html" data-reveal><img src="{esc(GD[k]["card"])}" alt="" loading="lazy" width="800" height="600"><span class="area-tile-text"><span class="label">{"National park guide" if k == "smoky-mountains" else "Area guide"}</span><strong>{esc(n)}</strong><span class="area-go">Explore {esc(n)}{G.ARROW}</span></span></a>' for k, n in GUIDES if k != key)
    hero = d['hero'].replace('assets/', '', 1)
    body = f'''<section class="guide-hero" style="--bg:url('{esc(hero)}')"><div class="container guide-hero-in"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li><a href="area-overview.html">Area overview</a></li><li aria-current="page">{esc(name)}</li></ol></nav>
<p class="eyebrow light">{G.ic("location-dot")} {kind}</p><h1>{esc(name)}</h1><p class="guide-place">{esc(place)}</p></div>{G.RIDGE.replace('class="ridge"', 'class="ridge ridge-bottom"')}</section>
<section class="guide-intro"><div class="container"><div class="guide-panel" data-reveal><p class="lead">{esc(d['intro'])}</p><ul class="quick-links">{links}</ul></div><ul class="glance">{gl}</ul></div></section>
<section class="section"><div class="container"><div class="section-head"><div><p class="eyebrow">{G.ic("map-location-dot")} Explore</p><h2>Landmarks and attractions</h2></div></div><div class="landmarks">{lm}</div></div></section>
{f'<section class="section facts-section"><div class="container"><p class="eyebrow light">{G.ic("lightbulb")} Did you know?</p><h2>{esc(name)} fun facts</h2><div class="fact-cards">{facts}</div></div></section>' if facts else ''}
<section class="section"><div class="container"><div class="section-head"><h2>More areas to explore</h2>{G.tlink("Area overview", "area-overview.html")}</div><div class="area-tiles">{tiles}</div></div></section>
{G.closing_cta(f'Build in {name}' if key != 'smoky-mountains' else 'Build near the Smokies')}'''
    return G.shell(f'{key}.html', f'{name} area guide | Builds by Carly', body, words(d['intro'], 26), d['hero'])

def pages(): return {f'{k}.html': guide(k, n) for k, n in GUIDES}
