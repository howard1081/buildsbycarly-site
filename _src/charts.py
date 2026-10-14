import re
from build import esc
COLORS = ['#102a33', '#975c35', '#4f7a73', '#c9a27e', '#9fb3ad', '#53615f']
def notep(n): return f'<p class="note">{esc(n)}</p>' if n else ''
def num(s):
    m = re.search(r'[\d.,]+', s or ''); 
    if not m: return 0.0
    v = float(m.group(0).replace(',', '')); u = s.upper()
    if 'B' in u[m.end():m.end()+2]: v *= 1e9
    elif 'M' in u[m.end():m.end()+2]: v *= 1e6
    elif 'K' in u[m.end():m.end()+2]: v *= 1e3
    return v
def hbars(rows, title, note=''):
    mx = max(num(v) for _, v in rows) or 1
    r = ''.join(f'<div class="bar-row"><span class="bar-label">{esc(l)}</span><span class="bar-track"><span class="bar-fill" style="--v:{num(v)/mx:.3f};--c:{COLORS[i % len(COLORS)]}"></span></span><span class="bar-value">{esc(v)}</span></div>' for i, (l, v) in enumerate(rows))
    return f'<figure class="chart" data-reveal><figcaption class="chart-title">{esc(title)}</figcaption><div class="bar-chart">{r}</div>{notep(note)}</figure>'
def columns(rows, title, est_word='Est'):
    mx = max(num(v) for _, v, _ in rows) or 1
    c = ''.join(f'<div class="col-item{" is-est" if est else ""}"><span class="col-value">{esc(v)}</span><span class="col-bar" style="--v:{num(v)/mx:.3f}"></span><span class="col-label">{esc(l)}{"<small>Estimate</small>" if est else ""}</span></div>' for l, v, est in rows)
    return f'<figure class="chart" data-reveal><figcaption class="chart-title">{esc(title)}</figcaption><div class="col-chart">{c}</div></figure>'
def donut(rows, title, center_value, center_label):
    off = 25.0; segs = ''; leg = ''
    for i, (l, pct, amt) in enumerate(rows):
        segs += f'<circle class="donut-seg" cx="21" cy="21" r="15.915" fill="none" stroke="{COLORS[i]}" stroke-width="6" stroke-dasharray="{pct:.2f} {100-pct:.2f}" stroke-dashoffset="{off:.2f}" style="--i:{i};--p:{pct:.2f}"></circle>'
        off -= pct
        leg += f'<li><span class="swatch" style="background:{COLORS[i]}"></span><span class="leg-label">{esc(l)}</span><span class="leg-value">{esc(amt)} <small>({pct:g}%)</small></span></li>'
    return f'''<figure class="chart donut-chart" data-reveal><figcaption class="chart-title">{esc(title)}</figcaption><div class="donut-wrap">
<svg viewBox="0 0 42 42" class="donut" role="img" aria-label="{esc(title)}"><circle cx="21" cy="21" r="15.915" fill="none" stroke="#e8eee9" stroke-width="6"></circle>{segs}
<text x="21" y="20.5" text-anchor="middle" class="donut-value">{esc(center_value)}</text><text x="21" y="25" text-anchor="middle" class="donut-label">{esc(center_label)}</text></svg>
<ul class="legend">{leg}</ul></div></figure>'''
def stacked(rows, title, note=''):
    tot = sum(p for _, p, ok in rows if ok)
    seg = ''; leg = ''
    for i, (l, p, ok) in enumerate(rows):
        if ok: seg += f'<span class="stack-seg" style="--w:{p/max(tot,100)*100:.2f}%;--c:{COLORS[i]}" title="{esc(l)}: {p:g}%"></span>'
        leg += f'<li><span class="swatch{"" if ok else " swatch-flag"}" style="background:{COLORS[i] if ok else "transparent"}"></span>{esc(l)} <strong>{"%g%%" % p if ok else "under review"}</strong></li>'
    if any(not ok for _, _, ok in rows): seg += '<span class="stack-seg stack-unknown" style="--w:auto" title="Unverified"></span>'
    return f'<figure class="chart" data-reveal><figcaption class="chart-title">{esc(title)}</figcaption><div class="stack">{seg}</div><ul class="legend legend-inline">{leg}</ul>{notep(note)}</figure>'
def ring(score, label):
    return f'<div class="ring" data-reveal><svg viewBox="0 0 42 42" aria-hidden="true"><circle cx="21" cy="21" r="15.915" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="4"></circle><circle class="ring-fill" style="--s:{score}" cx="21" cy="21" r="15.915" fill="none" stroke="#e7c9ab" stroke-width="4" stroke-linecap="round" stroke-dasharray="{score} {100-score}" stroke-dashoffset="25"></circle></svg><span class="ring-value">{score}<small>/100</small></span><span class="ring-label">{esc(label)}</span></div>'
