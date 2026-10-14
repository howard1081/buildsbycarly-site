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
    links = ''.join(f'<li><a href="{esc(u)}" rel="noopener">{G.ic(QL.get(t, ("arrow-up-right-from-square", t))[0])} {esc(QL.get(t, (None, G.sc(t)))[1] if t != "GOV WEBSITE" or key != "smoky-mountains" else "National Park Service")}</a></li>' for t, u in d['links'])
    if d['weather']: links += f'<li><a href="{esc(d["weather"])}" rel="noopener">{G.ic("cloud-sun")} {esc(name)} weather</a></li>'
    facts = ''.join(f'<details class="accordion fact" data-reveal><summary><span class="icon-chip">{G.ic(FACT_ICONS[i % len(FACT_ICONS)])}</span><span class="fact-title">{esc(tc(t))}</span></summary><div class="prose">{c}</div></details>' for i, (t, c) in enumerate(d['facts']))
    lm = ''.join(f'''<article class="landmark card"><img src="{esc(im(x['photo']))}" alt="{esc(tc(x['name']))}" loading="lazy" width="800" height="600"><div class="landmark-body"><h3 class="card-title">{esc(tc(x['name']))}</h3><p>{esc(x['desc'].strip())}</p>{f'<a class="text-link" href="{esc(x["href"])}" rel="noopener">Visit {esc(tc(x["name"]))}{G.ARROW}</a>' if x['href'] else ''}</div></article>''' for x in d['landmarks'])
    rel = ''.join(f'<article class="model-card"><img src="{esc(GD[k]["card"])}" alt="{esc(n)}" loading="lazy" width="800" height="600"><div class="model-card-body"><h3 class="card-title"><a href="{k}.html">{esc(n)}</a></h3><span class="text-link" aria-hidden="true">Explore {esc(n)}{G.ARROW}</span></div></article>' for k, n in GUIDES if k != key)
    kind = 'National park guide' if key == 'smoky-mountains' else 'Area guide'
    body = f'''<section class="page-intro data-intro"><div class="container split-even align-center"><div><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li><li><a href="area-overview.html">Area overview</a></li><li aria-current="page">{esc(name)}</li></ol></nav>
<p class="eyebrow">{G.ic("location-dot")} {kind}</p><h1>{esc(name)}</h1><p class="lead">{esc(d['intro'])}</p><ul class="quick-links">{links}</ul></div>
<figure class="intro-media" data-reveal><img src="{esc(d['hero'])}" alt="{esc(name)}, Tennessee" width="1200" height="900" fetchpriority="high"></figure></div></section>
<section class="section"><div class="container"><div class="section-head"><div><h2>Landmarks and attractions</h2><p class="intro">Popular places to see and do in and around {esc(name)}.</p></div></div><div class="card-grid cols-3">{lm}</div></div></section>
{f'<section class="section section-soft"><div class="container"><h2>{esc(name)} fun facts</h2><div class="facts-grid">{facts}</div></div></section>' if facts else ''}
<section class="section"><div class="container"><div class="section-head"><h2>More areas to explore</h2>{G.tlink("Area overview", "area-overview.html")}</div><div class="card-grid cols-3">{rel}</div></div></section>
{G.closing_cta(f'Build in {name}' if key != 'smoky-mountains' else 'Build near the Smokies')}'''
    return G.shell(f'{key}.html', f'{name} area guide | Builds by Carly', body, words(d['intro'], 26), d['hero'])

def pages(): return {f'{k}.html': guide(k, n) for k, n in GUIDES}
