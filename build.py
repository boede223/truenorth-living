#!/usr/bin/env python3
"""
TrueNorth Living — static site builder.

Reads JSON from content/, writes finished HTML into _site/.
No dependencies beyond the Python standard library.

    python3 build.py            build once
    python3 build.py --serve    build, then serve _site/ at http://localhost:8000

You almost never need to touch this file. Site copy lives in content/*.json,
which the admin panel at /admin/ edits for you.
"""

import html
import json
import os
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
CONTENT = ROOT / "content"
OUT = ROOT / "_site"

# --------------------------------------------------------------------------
# Content loading
# --------------------------------------------------------------------------

def load(name):
    with open(CONTENT / f"{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


SITE = HOME = HOMES = ABOUT = COSTS = FAQ = APPLY = None
DOMAIN = ""


def reload_content():
    """(Re)read every content file.

    Called at startup and again on each rebuild in --serve mode — without
    this, the watcher would rebuild using whatever JSON was loaded when the
    process started and your edits would never show up.
    """
    global SITE, HOME, HOMES, ABOUT, COSTS, FAQ, APPLY, DOMAIN
    SITE = load("site")
    HOME = load("home")
    HOMES = load("homes")
    ABOUT = load("about")
    COSTS = load("costs")
    FAQ = load("faq")
    APPLY = load("apply")
    DOMAIN = SITE.get("domain", "").rstrip("/")


reload_content()

# The site is one scrolling page, so the nav points at sections rather than
# separate documents. The old page URLs still resolve — see the redirects in
# main() — so any link already out in the world lands in the right place.
NAV = [
    ("/#houses", "Houses"),
    ("/#cost", "Cost"),
    ("/#about", "About"),
    ("/#faq", "FAQ"),
]

# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def e(text):
    """Escape for HTML text nodes and attributes."""
    return html.escape(str(text if text is not None else ""), quote=True)


def tel(number):
    """Build a dialable tel: value.

    (214) 555-0134  -> +12145550134
    1-800-662-4357  -> +18006624357
    988             -> 988

    Short codes like 988 are NOT real phone numbers and must be dialed
    verbatim — prefixing a country code gives '+988', which fails to
    connect. This is the crisis line, so it has to be right.
    """
    digits = re.sub(r"\D", "", str(number or ""))
    if not digits:
        return ""
    if len(digits) <= 6:          # short code (988, 911, 211, …)
        return digits
    if len(digits) == 10:         # US number missing its country code
        return "+1" + digits
    return "+" + digits


def paragraphs(text, cls=""):
    """Split a text blob on blank lines into <p> tags."""
    chunks = [c.strip() for c in re.split(r"\n\s*\n", str(text or "")) if c.strip()]
    attr = f' class="{cls}"' if cls else ""
    return "\n".join(f"<p{attr}>{e(c)}</p>" for c in chunks)


def clip(text, limit):
    """Shorten to a word boundary. Slicing mid-word looks like a bug."""
    t = " ".join(str(text or "").split())
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return cut + "…"


# Anything the brochure had to cut gets recorded here and reported at the end
# of the build, so a too-long field is a visible warning rather than a silent
# "…" on a document you hand to someone.
BROCHURE_OVERFLOW = []


def fit(text, limit, label, short=None):
    """Use the purpose-written short version if there is one.

    Falls back to the full text when it already fits. Only truncates as a last
    resort, and says so when it does.
    """
    t = " ".join(str(short or "").split()) or " ".join(str(text or "").split())
    if len(t) <= limit:
        return t
    BROCHURE_OVERFLOW.append((label, len(t), limit))
    return clip(t, limit)


def is_placeholder(text):
    return "PLACEHOLDER" in str(text or "")


def ph_class(text, extra=""):
    """Add a dashed outline to anything still holding placeholder copy."""
    classes = [c for c in [extra, "ph" if is_placeholder(text) else ""] if c]
    return f' class="{" ".join(classes)}"' if classes else ""


# --------------------------------------------------------------------------
# Inline SVG
# --------------------------------------------------------------------------

# "Doorway" — a lit doorway with the north star cut out of it. The star is a
# hole, not a shape, so it picks up whatever sits behind the mark and the logo
# works on any background without a second colourway.
DOORWAY_PATH = ("M22 90 L22 48 A28 28 0 0 1 78 48 L78 90 Z "
                "M50 28 Q51.3 52 68 56 Q51.3 60 50 83 Q48.7 60 32 56 Q48.7 52 50 28 Z")

LOGO = (f'<svg viewBox="20 18 60 74" aria-hidden="true">'
        f'<path fill-rule="evenodd" fill="#E8A33D" d="{DOORWAY_PATH}"/></svg>')

ROSE = """<svg class="cta-rose" viewBox="0 0 200 200" aria-hidden="true" fill="none" stroke="currentColor">
  <circle cx="100" cy="100" r="96" stroke-width=".6"/>
  <circle cx="100" cy="100" r="74" stroke-width=".6"/>
  <circle cx="100" cy="100" r="46" stroke-width=".6"/>
  <path d="M100 4v192M4 100h192M32 32l136 136M168 32 32 168" stroke-width=".6"/>
  <path d="M100 18 111 89l71 11-71 11-11 71-11-71-71-11 71-11z" stroke-width="1"/>
</svg>"""

ICON_PHONE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
              'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></svg>')

ICON_HOUSE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" '
              'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
              '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.8V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.8"/>'
              '<path d="M10 21v-6h4v6"/></svg>')

PILLAR_ICONS = [
    '<svg class="pillar-mark" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="16" cy="16" r="13"/><circle cx="16" cy="16" r="5"/></svg>',
    '<svg class="pillar-mark" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" aria-hidden="true"><path d="M4 8h24M4 16h24M4 24h16"/></svg>',
    '<svg class="pillar-mark" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="5"/><circle cx="22" cy="20" r="5"/><path d="M14.5 14.5 18.5 16.5"/></svg>',
    '<svg class="pillar-mark" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 3v26M23 9.5c0-2.5-3-4-7-4s-6.5 1.3-6.5 3.8c0 5.7 14 2.8 14 9 0 2.6-3 4.2-7.5 4.2s-7-1.6-7-4"/></svg>',
]

STATUS_LABEL = {
    "open": "Beds open now",
    "waitlist": "Waitlist",
    "full": "Currently full",
}


# --------------------------------------------------------------------------
# Availability
# --------------------------------------------------------------------------

# Each house sets its own billing period, so the rate has to carry its unit
# with it everywhere it appears.
RATE_PERIOD = {
    "weekly":   ("week",    "/wk"),
    "biweekly": ("2 weeks", "/2 wks"),
    "monthly":  ("month",   "/mo"),
}


def rate_of(house, short=False):
    """Render a house's rate with its period, or "" if no rate is set."""
    amount = str(house.get("rate") or "").strip()
    if not amount:
        return ""
    long_unit, short_unit = RATE_PERIOD.get(house.get("rate_period", "weekly"),
                                            RATE_PERIOD["weekly"])
    return f"${e(amount)}<small>{short_unit if short else '/' + long_unit}</small>"


def published_homes():
    """Houses with 'Show on website' turned on.

    A house can exist in the admin — half filled in, still being set up —
    without appearing anywhere public. Everything user-facing goes through
    this function, so an unpublished house is invisible site-wide.
    """
    return [h for h in HOMES.get("homes", []) if h.get("published", True)]


def availability():
    """Aggregate open beds across all houses for the hero pill."""
    homes = published_homes()

    # Pre-launch: no houses are live yet. Say that plainly rather than
    # implying we have houses that happen to be full.
    if not homes:
        return "soon", HOMES.get("prelaunch_pill", "Now taking applications")

    open_beds = 0
    cities = []
    for h in homes:
        try:
            n = int(h.get("beds_open") or 0)
        except (TypeError, ValueError):
            n = 0
        if h.get("status") == "open" and n > 0:
            open_beds += n
            city = str(h.get("city", "")).split(",")[0].strip()
            if city and city not in cities:
                cities.append(city)

    if open_beds > 0:
        noun = "bed" if open_beds == 1 else "beds"
        where = " · " + ", ".join(cities) if cities else ""
        return "open", f"{open_beds} {noun} open tonight{where}"
    return "waitlist", "All houses full — join the waitlist"


# --------------------------------------------------------------------------
# Structured data
# --------------------------------------------------------------------------

def local_business_ld():
    data = {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "Organization"],
        "name": SITE["org_name"],
        "description": HOME["meta_description"],
        "url": DOMAIN + "/",
        "telephone": SITE["phone"],
        "email": SITE["email"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": SITE["street"],
            "addressLocality": SITE["city"],
            "addressRegion": SITE["state"],
            "postalCode": SITE["zip"],
            "addressCountry": "US",
        },
        "areaServed": [
            {"@type": "City", "name": c}
            for c in ["Dallas", "Denton", "Arlington", "Fort Worth", "Plano", "Irving"]
        ],
        "knowsAbout": ["sober living", "recovery housing", "transitional housing"],
    }
    return data


def faq_ld():
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
            }
            for f in FAQ.get("faqs", [])
        ],
    }


def ld_script(data):
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + "</script>")


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------

def shell(*, title, description, path, body, head_extra=""):
    phone_href = tel(SITE["phone"])
    canonical = DOMAIN + path

    nav_links = "\n".join(
        f'<a href="{href}">{e(label)}</a>' for href, label in NAV
    )
    nav_links += '\n<a class="nav-apply" href="/apply/">Apply</a>'

    # With no houses live yet, the footer column would be an empty heading.
    live = published_homes()
    if live:
        footer_houses = f"""      <div>
        <h2>Houses</h2>
        <ul>{"".join(
            f'<li><a href="/#{slugify(h["name"])}">{e(h["name"])}</a></li>'
            for h in live
        )}</ul>
      </div>"""
    else:
        footer_houses = ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta name="theme-color" content="#0C141C">

<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['org_name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(DOMAIN)}/assets/img/social-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(SITE['org_name'])} — {e(SITE['tagline'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{e(DOMAIN)}/assets/img/social-card.png">

<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<!-- iOS ignores SVG for home-screen icons, so this one has to be a PNG. -->
<link rel="apple-touch-icon" sizes="180x180" href="/assets/img/apple-touch-icon.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..700&family=Inter:wght@400..700&display=swap">
<link rel="stylesheet" href="/assets/css/site.css">
{head_extra}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>

<div class="crisis">
  <div class="wrap">
    <b>{e(SITE['crisis_label'])}</b>
    <span>Call or text <a href="tel:{e(tel(SITE['crisis_line']))}">{e(SITE['crisis_line'])}</a> — {e(SITE['crisis_line_label'])}</span>
    <span>SAMHSA helpline <a href="tel:{e(tel(SITE['samhsa_line']))}">{e(SITE['samhsa_line'])}</a></span>
  </div>
</div>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/">
      {LOGO}
      <span><b>True</b><i>North</i></span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav" aria-label="Menu">
      <span></span>
    </button>
    <nav class="nav" id="primary-nav" aria-label="Primary">
      {nav_links}
    </nav>
    <div class="header-cta">
      <a class="header-phone" href="tel:{e(phone_href)}">{ICON_PHONE}{e(SITE['phone'])}</a>
      <a class="btn" href="/apply/">Apply</a>
    </div>
  </div>
</header>

<main id="main">
{body}
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="brand" href="/">{LOGO}<span><b>True</b><i>North</i></span></a>
        <p>{e(SITE['tagline'])}. Serving Dallas, Denton, Arlington and the wider Metroplex.</p>
      </div>
{footer_houses}
      <div>
        <h2>Site</h2>
        <ul>
          <li><a href="/#houses">Our houses</a></li>
          <li><a href="/#about">About us</a></li>
          <li><a href="/#cost">Cost &amp; payment</a></li>
          <li><a href="/#faq">FAQ</a></li>
          <li><a href="/apply/">Apply for a bed</a></li>
          <li><a href="/brochure/">Printable info sheet</a></li>
        </ul>
      </div>
      <div>
        <h2>Reach us</h2>
        <ul>
          <li><a href="tel:{e(phone_href)}">{e(SITE['phone'])}</a></li>
          <li><a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a></li>
          <li>{e(SITE['hours'])}</li>
          <li{ph_class(SITE['street'])}>{e(SITE['street'])}<br>{e(SITE['city'])}, {e(SITE['state'])} {e(SITE['zip'])}</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p class="footer-legal">{e(SITE['footer_note'])}</p>
      <p>&copy; {date.today().year} {e(SITE['org_name'])}</p>
    </div>
  </div>
</footer>

<div class="call-bar">
  <a class="btn btn--ghost" href="tel:{e(phone_href)}">{ICON_PHONE} Call now</a>
  <a class="btn" href="/apply/">Apply</a>
</div>

{ld_script(local_business_ld())}
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s or "item"


def cta_band(title, body, button, href="/apply/"):
    return f"""
<section class="cta-band">
  {ROSE}
  <div class="wrap">
    <h2 class="reveal">{e(title)}</h2>
    <p class="reveal">{e(body)}</p>
    <div class="btn-row reveal">
      <a class="btn btn--lg" href="{e(href)}">{e(button)}</a>
      <a class="btn btn--lg btn--ghost" href="tel:{e(tel(SITE['phone']))}">{ICON_PHONE} {e(SITE['phone'])}</a>
    </div>
  </div>
</section>"""


def page_hero(eyebrow, title, body):
    return f"""
<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{e(eyebrow)}</p>
    <h1>{e(title)}</h1>
    <p{ph_class(body, "lede")}>{e(body)}</p>
  </div>
</section>"""


# --------------------------------------------------------------------------
# House card (shared by home + homes pages)
# --------------------------------------------------------------------------

def house_card(h, level=3):
    """`level` keeps the heading hierarchy correct: house cards sit under a
    section <h2> on the homepage (so h3), but directly under the page <h1>
    on /homes/ (so h2)."""
    status = h.get("status", "open")
    label = STATUS_LABEL.get(status, "Ask us")
    try:
        open_n = int(h.get("beds_open") or 0)
    except (TypeError, ValueError):
        open_n = 0
    if status == "open" and open_n > 0:
        label = f"{open_n} of {e(h.get('beds_total', '?'))} beds open"

    photo = h.get("photo") or ""
    if photo:
        media = (f'<div class="house-photo">'
                 f'<img src="{e(photo)}" alt="{e(h["name"])} — {e(h.get("city",""))}" loading="lazy" decoding="async">')
    else:
        media = ('<div class="house-photo house-photo--empty">'
                 f'<div class="house-photo-note">{ICON_HOUSE}<span>Add a photo</span></div>')

    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in h.get("highlights", []))
    rate = rate_of(h, short=True)
    rate_html = f'<span class="house-rate">{rate}</span>' if rate else ""

    return f"""
<article class="house reveal" id="{slugify(h['name'])}">
  {media}
    <span class="house-status"><i class="dot dot--{e(status)}"></i>{label}</span>
  </div>
  <div class="house-body">
    <div class="house-head">
      <h{level}>{e(h['name'])}</h{level}>
      {rate_html}
    </div>
    <div class="house-meta">
      <span>{e(h.get('city',''))}</span>
      <span>{e(h.get('gender',''))}</span>
      <span>{e(h.get('beds_total','?'))} beds</span>
    </div>
    <p>{e(h.get('description',''))}</p>
    <div class="house-tags">{tags}</div>
  </div>
</article>"""


def houses_block(level=3, limit=None):
    """Render the house grid, or a pre-launch notice if nothing is live yet."""
    homes = published_homes()
    if limit:
        homes = homes[:limit]

    if homes:
        return '<div class="houses">' + "\n".join(
            house_card(h, level) for h in homes
        ) + "</div>"

    return f"""
<div class="empty-state reveal">
  <div class="empty-mark">{ICON_HOUSE}</div>
  <h{level}>{e(HOMES.get('empty_title', 'Houses coming soon.'))}</h{level}>
  <p>{e(HOMES.get('empty_body', ''))}</p>
  <div class="btn-row">
    <a class="btn" href="/apply/">{e(HOMES.get('empty_cta', 'Get on the list'))}</a>
    <a class="btn btn--ghost" href="tel:{e(tel(SITE['phone']))}">{ICON_PHONE} {e(SITE['phone'])}</a>
  </div>
</div>"""


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def build_index():
    """The whole site as one scrolling page.

    Sections carry ids so the nav, the footer and the old multi-page URLs can
    all deep-link into them: #houses, #cost, #about, #faq.
    """
    hero = HOME["hero"]
    status, avail_text = availability()
    has_homes = bool(published_homes())

    if hero.get("video"):
        media = (f'<video autoplay muted loop playsinline '
                 f'poster="{e(hero.get("poster",""))}" aria-hidden="true">'
                 f'<source src="{e(hero["video"])}" type="video/mp4"></video>')
    elif hero.get("poster"):
        media = f'<img src="{e(hero["poster"])}" alt="" fetchpriority="high" decoding="async">'
    else:
        # No media uploaded yet — the CSS night sky carries the hero alone.
        media = ""

    # Split the headline so the last word can carry the italic accent.
    words = hero["title"].rsplit(" ", 1)
    heading = f'{e(words[0])} <em>{e(words[1])}</em>' if len(words) == 2 else e(hero["title"])

    steps = "\n".join(
        f"""
      <div class="path-step">
        <span class="path-num">{i + 1:02d}</span>
        <h3>{e(s['label'])}</h3>
        <p>{e(s['detail'])}</p>
      </div>"""
        for i, s in enumerate(HOME.get("path", []))
    )

    pillars = "\n".join(
        f"""
      <div class="pillar reveal">
        {PILLAR_ICONS[i % len(PILLAR_ICONS)]}
        <h3>{e(p['title'])}</h3>
        <p>{e(p['body'])}</p>
      </div>"""
        for i, p in enumerate(HOME.get("pillars", []))
    )

    rates = "\n".join(
        f"""
      <div class="card reveal">
        <h3>{e(h['name'])}</h3>
        <p class="house-rate" style="font-size:var(--t-2xl);display:block;margin:.4rem 0">
          {rate_of(h) or '—'}
        </p>
        <p>{e(h.get('city',''))} · {e(h.get('gender',''))} · {e(h.get('beds_total','?'))} beds</p>
      </div>"""
        for h in published_homes()
    ) or f"""
      <div class="card reveal">
        <h3>Rates are being set now</h3>
        <p>{e(COSTS.get('rates_empty',''))}</p>
      </div>"""

    included = "\n".join(f"<li>{e(i)}</li>" for i in COSTS.get("included", []))
    not_included = "\n".join(f"<li>{e(i)}</li>" for i in COSTS.get("not_included", []))

    assistance = "\n".join(
        f"""
      <div{ph_class(a["body"], "card reveal")}>
        <h3>{e(a['title'])}</h3>
        <p>{e(a['body'])}</p>
      </div>"""
        for a in COSTS.get("assistance", [])
    )

    values = "\n".join(
        f"""
      <div class="card reveal">
        <h3>{e(v['title'])}</h3>
        <p>{e(v['body'])}</p>
      </div>"""
        for v in ABOUT.get("values", [])
    )

    standards = "\n".join(
        f"""
      <div{ph_class(s["body"], "card reveal")}>
        <h3>{e(s['title'])}</h3>
        <p>{e(s['body'])}</p>
      </div>"""
        for s in ABOUT.get("standards", [])
    )

    people = "\n".join(
        f"""
      <div class="person reveal">
        <div class="person-photo">{f'<img src="{e(p["photo"])}" alt="{e(p["name"])}" loading="lazy">' if p.get("photo") else ICON_HOUSE}</div>
        <h3{ph_class(p['name'])}>{e(p['name'])}</h3>
        <p class="role">{e(p['role'])}</p>
        <p>{e(p['bio'])}</p>
      </div>"""
        for p in ABOUT.get("team", [])
    )

    quotes = "\n".join(
        f"""
      <figure{ph_class(q.get("note",""), "quote reveal")}>
        <blockquote>{e(q['quote'])}</blockquote>
        <cite>{e(q['attribution'])}</cite>
      </figure>"""
        for q in HOME.get("testimonials", [])
    )

    faqs = "\n".join(
        f"""
      <details class="faq-item">
        <summary>{e(f['q'])}</summary>
        <div{ph_class(f["a"], "faq-answer")}>{paragraphs(f['a'])}</div>
      </details>"""
        for f in FAQ.get("faqs", [])
    )

    body = f"""
<section class="hero" id="top">
  <div class="hero-media">{media}</div>
  <div class="wrap hero-inner">
    <p class="eyebrow">{e(hero['eyebrow'])}</p>
    <h1>{heading}</h1>
    <p class="lede">{e(hero['subtitle'])}</p>
    <div class="btn-row">
      <a class="btn btn--lg" href="{e(hero['primary_cta_href'])}">{e(hero['primary_cta'])}</a>
      <a class="btn btn--lg btn--ghost" href="#houses">{e(hero['secondary_cta'])}</a>
    </div>
    <p style="margin-top:var(--sp-5)">
      <a class="avail-pill" href="#houses">
        <i class="dot dot--{status}"></i>{e(avail_text)}
      </a>
    </p>
  </div>
  <div class="scroll-hint"><span>Scroll</span><i></i></div>
</section>

<section class="section path" id="path">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">The path north</p>
      <h2>{e(HOME['path_title'])}</h2>
      <p class="lede">{e(HOME['path_intro'])}</p>
    </div>
    <div class="path-grid">
      <div class="path-rail"></div>
      <div class="path-trace"></div>
      {steps}
    </div>
  </div>
</section>

<section class="section section--bone" id="approach">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">Our approach</p>
      <h2>{e(HOME['pillars_title'])}</h2>
    </div>
    <div class="pillars">
      {pillars}
    </div>
  </div>
</section>

<section class="section" id="houses">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">{"Available now" if has_homes else "Opening soon"}</p>
      <h2>{e(HOMES['intro_title'])}</h2>
      <p class="lede">{e(HOMES['intro_body'])}</p>
    </div>
    {houses_block(level=3)}
  </div>
</section>

<section class="section section--bone" id="cost">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">Cost &amp; payment</p>
      <h2>{e(COSTS['hero_title'])}</h2>
      <p class="lede">{e(COSTS['hero_body'])}</p>
    </div>
    <div class="cards">
      {rates}
    </div>
    <div class="split" style="margin-top:var(--sp-6)">
      <div class="reveal">
        <p class="eyebrow">{e(COSTS['included_title'])}</p>
        <h3 style="margin-block:var(--sp-3)">In the rate</h3>
        <ul class="checklist">{included}</ul>
      </div>
      <div class="reveal">
        <p class="eyebrow">{e(COSTS['not_included_title'])}</p>
        <h3 style="margin-block:var(--sp-3)">On you</h3>
        <ul class="checklist checklist--minus">{not_included}</ul>
      </div>
    </div>
    <div class="reveal" style="margin-top:var(--sp-6);max-width:62ch">
      <p class="eyebrow">{e(COSTS['insurance_title'])}</p>
      <h3 style="margin-block:var(--sp-3)">Does insurance cover this?</h3>
      <p>{e(COSTS['insurance_body'])}</p>
    </div>
    <div style="margin-top:var(--sp-6)">
      <div class="section-head reveal">
        <p class="eyebrow">Financial help</p>
        <h3>{e(COSTS['assistance_title'])}</h3>
        <p class="lede">{e(COSTS['assistance_body'])}</p>
      </div>
      <div class="cards">
        {assistance}
      </div>
    </div>
  </div>
</section>

<section class="section" id="about">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">About TrueNorth</p>
      <h2>{e(ABOUT['hero_title'])}</h2>
      <p class="lede"{ph_class(ABOUT['hero_body'])}>{e(ABOUT['hero_body'])}</p>
    </div>
    <div class="wrap-narrow prose reveal" style="margin-inline:0;width:auto;max-width:68ch">
      <h3>{e(ABOUT['story_title'])}</h3>
      <div{ph_class(ABOUT['story_body'])}>{paragraphs(ABOUT['story_body'])}</div>
    </div>
    <div style="margin-top:var(--sp-6)">
      <div class="section-head reveal">
        <p class="eyebrow">Values</p>
        <h3>{e(ABOUT['values_title'])}</h3>
      </div>
      <div class="cards">{values}</div>
    </div>
    <div style="margin-top:var(--sp-6)">
      <div class="section-head reveal">
        <p class="eyebrow">Accountability</p>
        <h3>{e(ABOUT['standards_title'])}</h3>
        <p class="lede">{e(ABOUT['standards_body'])}</p>
      </div>
      <div class="cards">{standards}</div>
    </div>
    <div style="margin-top:var(--sp-6)">
      <div class="section-head reveal">
        <p class="eyebrow">The team</p>
        <h3>{e(ABOUT['team_title'])}</h3>
      </div>
      <div class="people">{people}</div>
    </div>
  </div>
</section>

<section class="section section--bone" id="proof">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">{e(HOME['proof_title'])}</p>
      <h2>You don't have to take our word for it.</h2>
    </div>
    <div class="quotes">
      {quotes}
    </div>
  </div>
</section>

<section class="section" id="faq">
  <div class="wrap-narrow">
    <div class="section-head reveal">
      <p class="eyebrow">FAQ</p>
      <h2>{e(FAQ['hero_title'])}</h2>
      <p class="lede">{e(FAQ['hero_body'])}</p>
    </div>
    <div class="faq-list">
      {faqs}
    </div>
  </div>
</section>

{cta_band(HOME['cta_title'], HOME['cta_body'], HOME['cta_button'])}
"""
    return shell(
        title=HOME["meta_title"],
        description=HOME["meta_description"],
        path="/",
        body=body,
        head_extra=ld_script(faq_ld()),
    )


def build_apply():
    house_options = "\n".join(
        f'<option value="{e(h["name"])}">{e(h["name"])} — {e(h.get("city",""))} ({e(h.get("gender",""))})</option>'
        for h in published_homes()
    )

    # A "Which house?" dropdown with nothing in it just wastes the applicant's
    # attention, so it only appears once at least one house is live.
    house_field = f"""<div class="field">
              <label for="house">Which house?</label>
              <select id="house" name="house">
                <option value="">No preference — help me choose</option>
                {house_options}
              </select>
            </div>""" if house_options else ""

    reassurance = "\n".join(f"<li>{e(r)}</li>" for r in APPLY.get("reassurance", []))

    after = "\n".join(
        f"""
      <div class="card reveal">
        <p class="eyebrow">{e(a['step'])}</p>
        <p style="margin-top:.6rem">{e(a['detail'])}</p>
      </div>"""
        for a in APPLY.get("after", [])
    )

    body = f"""
{page_hero("Apply", APPLY["hero_title"], APPLY["hero_body"])}

<section class="section">
  <div class="wrap">
    <div class="split" style="grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr)">
      <div>
        <div class="form-status" hidden></div>

        <div data-success hidden>
          <div class="note">
            <h2 style="font-size:var(--t-xl);margin-bottom:.5rem">{e(APPLY['success_title'])}</h2>
            <p>{e(APPLY['success_body'])}</p>
            <p style="margin-top:var(--sp-3)">
              <a class="btn" href="tel:{e(tel(SITE['phone']))}">{ICON_PHONE} {e(SITE['phone'])}</a>
            </p>
          </div>
        </div>

        <form class="form" name="application" method="POST" action="/apply/"
              data-ajax data-phone="{e(SITE['phone'])}"
              data-netlify="true" netlify-honeypot="company-website">
          <input type="hidden" name="form-name" value="application">
          <p class="hp">
            <label>Do not fill this in <input name="company-website" tabindex="-1" autocomplete="off"></label>
          </p>

          <fieldset style="border:0;padding:0;margin:0">
            <legend class="eyebrow" style="margin-bottom:var(--sp-3)">Who is this for?</legend>
            <div class="radio-row">
              <label class="radio-chip"><input type="radio" name="applying_for" value="Myself" checked><span>Myself</span></label>
              <label class="radio-chip"><input type="radio" name="applying_for" value="A family member"><span>A family member</span></label>
              <label class="radio-chip"><input type="radio" name="applying_for" value="A client"><span>A client</span></label>
            </div>
          </fieldset>

          <div class="form-grid">
            <div class="field">
              <label for="name">Your name <span class="req">*</span></label>
              <input id="name" name="name" type="text" required autocomplete="name">
            </div>
            <div class="field">
              <label for="phone">Phone <span class="req">*</span></label>
              <input id="phone" name="phone" type="tel" required autocomplete="tel" inputmode="tel" placeholder="(214) 555-0134">
            </div>
          </div>

          <div class="form-grid">
            <div class="field">
              <label for="email">Email</label>
              <input id="email" name="email" type="email" autocomplete="email">
            </div>
            <div class="field">
              <label for="resident_name">Name of the person moving in</label>
              <input id="resident_name" name="resident_name" type="text">
              <span class="hint">Leave blank if that's you.</span>
            </div>
          </div>

          <div class="form-grid">
            {house_field}
            <div class="field">
              <label for="move_in">How soon?</label>
              <select id="move_in" name="move_in">
                <option>Today or tomorrow</option>
                <option selected>Within a week</option>
                <option>Within a month</option>
                <option>Just gathering information</option>
              </select>
            </div>
          </div>

          <div class="form-grid">
            <div class="field">
              <label for="sober_since">Approximate sobriety date</label>
              <input id="sober_since" name="sober_since" type="text" placeholder="e.g. 3 weeks, or March 2026">
            </div>
            <div class="field">
              <label for="treatment">Coming from</label>
              <select id="treatment" name="treatment">
                <option value="">Select one</option>
                <option>Detox</option>
                <option>Inpatient / residential treatment</option>
                <option>Another sober living home</option>
                <option>Incarceration</option>
                <option>Hospital</option>
                <option>Home / on my own</option>
                <option>Other</option>
              </select>
            </div>
          </div>

          <div class="field">
            <label for="notes">Anything we should know?</label>
            <textarea id="notes" name="notes" placeholder="Work schedule, court requirements, medications, MAT, pets, whatever matters. Nothing here disqualifies you automatically."></textarea>
          </div>

          <label class="form-consent">
            <input type="checkbox" name="consent" required>
            <span>I understand TrueNorth Living will contact me about this application, and that my information will not be shared with third parties. <span class="req">*</span></span>
          </label>

          <div>
            <button class="btn btn--lg" type="submit">Send my application</button>
          </div>
          <p class="hint" style="color:var(--text-dim);font-size:var(--t-xs)">
            This is not a medical form. If you are in immediate danger, call 911 or {e(SITE['crisis_line'])}.
          </p>
        </form>
      </div>

      <aside>
        <div class="card reveal">
          <h3>{e(APPLY['reassurance_title'])}</h3>
          <ul class="checklist" style="margin-top:var(--sp-3);font-size:var(--t-sm)">{reassurance}</ul>
          <p style="margin-top:var(--sp-4)">
            <a class="btn btn--ghost" href="tel:{e(tel(SITE['phone']))}" style="width:100%">{ICON_PHONE} {e(SITE['phone'])}</a>
          </p>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="section section--bone">
  <div class="wrap">
    <div class="section-head reveal">
      <p class="eyebrow">Next</p>
      <h2>{e(APPLY['after_title'])}</h2>
    </div>
    <div class="cards">
      {after}
    </div>
  </div>
</section>
"""
    return shell(
        title=APPLY["meta_title"],
        description=APPLY["meta_description"],
        path="/apply/",
        body=body,
    )


def brochure_shell(body):
    """A bare document shell — no site nav, no crisis bar, no footer.

    The brochure is a thing you print or attach to an email, so it carries its
    own contact details and stands entirely on its own.
    """
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(SITE['org_name'])} — Information Sheet</title>
<meta name="description" content="Printable information sheet for {e(SITE['org_name'])}, sober living in North Texas.">
<!-- Kept out of search so it never competes with the main site. -->
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{e(DOMAIN)}/brochure/">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..700&family=Inter:wght@400..700&display=swap">
<link rel="stylesheet" href="/assets/css/brochure.css">
</head>
<body>
<div class="toolbar">
  <b>Information sheet</b>
  <span>Two pages · prints on US Letter</span>
  <button class="primary" type="button" onclick="window.print()">Print or save as PDF</button>
  <a href="/">Back to the website</a>
</div>
<main>
{body}
</main>
</body>
</html>
"""


def build_brochure():
    """A two-page printable sheet, built from the same content as the site.

    Because it reads content/*.json, it can never drift out of date: change a
    rate or a phone number in the admin panel and the brochure changes too.
    """
    status, avail_text = availability()
    live = published_homes()

    brand = f"""
    <div class="brandblock">
      {LOGO}
      <div>
        <div class="name">True<i>North</i> Living</div>
        <div class="sub">{e(SITE['tagline'])}</div>
      </div>
    </div>"""

    contact = f"""
    <div class="contact">
      <span class="tel">{e(SITE['phone'])}</span>
      <span>{e(SITE['email'])}</span><br>
      <span>{e(DOMAIN.replace("https://", ""))}</span><br>
      <span>{e(SITE['hours'])}</span>
    </div>"""

    words = HOME["hero"]["title"].rsplit(" ", 1)
    lede_title = (f'{e(words[0])} <em>{e(words[1])}</em>'
                  if len(words) == 2 else e(HOME["hero"]["title"]))

    pillars = "".join(
        f"""
      <div class="pt">
        <h3>{e(p['title'])}</h3>
        <p>{e(p['body'])}</p>
      </div>"""
        for p in HOME.get("pillars", [])[:4]
    )

    steps = "".join(
        f"""
      <div class="step">
        <div class="step-n">{i + 1:02d}</div>
        <div>
          <h3>{e(s['label'])}</h3>
          <p>{e(s['detail'])}</p>
        </div>
      </div>"""
        for i, s in enumerate(HOME.get("path", []))
    )

    if live:
        rates = "".join(
            f"""
      <div class="rate-card">
        <h3>{e(h['name'])}</h3>
        <span class="n">{rate_of(h) or '—'}</span>
        <p>{e(h.get('city',''))} · {e(h.get('gender',''))} · {e(h.get('beds_total','?'))} beds</p>
      </div>"""
            for h in live[:3]
        )
    else:
        rates = f"""
      <div class="rate-card" style="grid-column:1/-1">
        <h3>Rates are being set now</h3>
        <p style="margin-top:3pt">{e(COSTS.get('rates_empty',''))}</p>
      </div>"""

    included = "".join(f"<li>{e(i)}</li>" for i in COSTS.get("included", [])[:4])
    excluded = "".join(f"<li>{e(i)}</li>" for i in COSTS.get("not_included", [])[:3])

    standards = "".join(
        f"""
      <div{ph_class(s["body"], "pt")}>
        <h3>{e(s['title'])}</h3>
        <p>{e(fit(s['body'], 108, 'About → Standards → ' + s['title'], s.get('short')))}</p>
      </div>"""
        for s in ABOUT.get("standards", [])[:4]
    )

    # Prefer finished answers, so the brochure is as complete as it can be —
    # but keep any placeholder visible and flagged rather than hiding it.
    faqs = FAQ.get("faqs", [])
    ordered = ([f for f in faqs if not is_placeholder(f["a"])]
               + [f for f in faqs if is_placeholder(f["a"])])
    qa = "".join(
        f"""
      <div>
        <p class="q">{e(f['q'])}</p>
        <p{ph_class(f["a"], "a")}>{e(fit(f['a'], 140, 'FAQ → ' + f['q'], f.get('short')))}</p>
      </div>"""
        for f in ordered[:1]
    )

    cta = f"""
    <div class="cta">
      <div>
        <h2>{e(HOMES.get('empty_cta','Get on the list')) if not live else 'There may be a bed tonight.'}</h2>
        <p>{e(fit(HOMES.get('empty_body',''), 165, 'Houses → pre-launch message', HOMES.get('empty_short'))) if not live else 'Call and we will tell you exactly what is open right now — no sales pitch, no pressure.'}</p>
      </div>
      <div class="num">{e(SITE['phone'])}<small>{e(SITE['hours'])}</small></div>
    </div>"""

    body = f"""
<section class="sheet">
  <div class="masthead">
    {brand}
    {contact}
  </div>

  <span class="status"><i></i>{e(avail_text)}</span>

  <div>
    <h1 class="lede-title">{lede_title}</h1>
    <p class="lede-body">{e(HOME['hero']['subtitle'])}</p>
  </div>

  <div class="sec">
    <h2 class="eyebrow">How we run a house</h2>
    <div class="four">{pillars}</div>
  </div>

  <div class="sec">
    <h2 class="eyebrow">What the first ninety days look like</h2>
    <div class="steps">{steps}</div>
  </div>

  {cta}
  <div class="pagemark">{e(SITE['org_name'])} · page 1 of 2</div>
</section>

<section class="sheet">
  <div class="masthead">
    {brand}
    <div class="contact">
      <span class="tel">{e(SITE['phone'])}</span>
      <span>{e(DOMAIN.replace("https://", ""))}</span>
    </div>
  </div>

  <div class="sec">
    <h2 class="eyebrow">Cost</h2>
    <h2>{e(COSTS['hero_title'])}</h2>
    <div class="three" style="margin-top:.14in">{rates}</div>
  </div>

  <div class="two">
    <div class="sec">
      <h2 class="eyebrow">In the rate</h2>
      <ul class="list">{included}</ul>
    </div>
    <div class="sec">
      <h2 class="eyebrow">Not included</h2>
      <ul class="list list--no">{excluded}</ul>
    </div>
  </div>

  <div class="callout">
    <b>Does insurance cover this?</b> {e(fit(COSTS['insurance_body'], 175, 'Cost → insurance', COSTS.get('insurance_short')))}
  </div>

  <div class="sec">
    <h2 class="eyebrow">Standards &amp; accountability</h2>
    <div class="four">{standards}</div>
  </div>

  <div class="sec">
    <h2 class="eyebrow">Common questions</h2>
    <div class="qa">{qa}</div>
  </div>

  {cta}

  <div class="crisisline">
    <span><b>{e(SITE['crisis_label'])}</b> Call or text {e(SITE['crisis_line'])} · SAMHSA {e(SITE['samhsa_line'])}</span>
    <span>{e(fit(SITE['footer_note'], 92, 'Settings → footer note', SITE.get('legal_short')))}</span>
  </div>
  <div class="pagemark">{e(SITE['org_name'])} · page 2 of 2</div>
</section>
"""
    return brochure_shell(body)


def build_404():
    body = f"""
{page_hero("404", "This page went for a walk.", "The link's broken, but the phone still works. Try one of these instead.")}
<section class="section">
  <div class="wrap">
    <div class="btn-row">
      <a class="btn btn--lg" href="/">Back to the start</a>
      <a class="btn btn--lg btn--ghost" href="/#houses">See our houses</a>
      <a class="btn btn--lg btn--ghost" href="tel:{e(tel(SITE['phone']))}">{ICON_PHONE} {e(SITE['phone'])}</a>
    </div>
  </div>
</section>
"""
    return shell(
        title="Page not found — TrueNorth Living",
        description="That page doesn't exist.",
        path="/404.html",
        body=body,
    )


# --------------------------------------------------------------------------
# Static extras
# --------------------------------------------------------------------------

FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" rx="22" fill="#0C141C"/>'
    # Artwork centres on y=55, the box on y=50 — nudge up so it sits optically true.
    f'<g transform="translate(50 50) scale(.86) translate(-50 -55)">'
    f'<path fill-rule="evenodd" fill="#E8A33D" d="{DOORWAY_PATH}"/></g>'
    "</svg>"
)


def sitemap():
    # Only real documents belong in a sitemap — the old section URLs now
    # redirect, and listing redirects here would be a crawl error.
    paths = ["/", "/apply/"]
    today = date.today().isoformat()
    urls = "\n".join(
        f"  <url><loc>{DOMAIN}{p}</loc><lastmod>{today}</lastmod>"
        f"<priority>{'1.0' if p == '/' else '0.8'}</priority></url>"
        for p in paths
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'


def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {DOMAIN}/sitemap.xml\n"


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

PAGES = {
    "index.html": build_index,
    # The application form keeps its own page: it's the conversion destination,
    # worth linking and tracking on its own, and a long form under a long page
    # is a bad combination.
    "apply/index.html": build_apply,
    # Printable two-page information sheet. Built from the same JSON as the
    # site, so it can't drift out of date.
    "brochure/index.html": build_brochure,
    "404.html": build_404,
}


def write(relpath, text):
    dest = OUT / relpath
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


# Injected only when running with --serve, never into a deployed build.
# Polls the build id and reloads the page when it changes, so saving in the
# admin panel refreshes the site by itself.
LIVERELOAD = """
<script>
(function () {
  var current = null;
  setInterval(function () {
    fetch("/__buildid", { cache: "no-store" })
      .then(function (r) { return r.text(); })
      .then(function (id) {
        if (current === null) { current = id; return; }
        if (id !== current) location.reload();
      })
      .catch(function () {});
  }, 1000);
})();
</script>
"""


def main(dev=False):
    reload_content()

    # Empty the output directory without removing the directory itself — a
    # running `--serve` process has chdir'd into it, and deleting it would
    # kill the preview server every time you rebuild.
    OUT.mkdir(parents=True, exist_ok=True)
    for child in OUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for relpath, fn in PAGES.items():
        write(relpath, fn())

    # Static assets
    shutil.copytree(ROOT / "assets", OUT / "assets")
    write("assets/img/favicon.svg", FAVICON)

    # Admin panel ships with the site
    if (ROOT / "admin").exists():
        shutil.copytree(ROOT / "admin", OUT / "admin")

    # Content JSON is served too, so the CMS can read it and so nothing is
    # locked away from you.
    shutil.copytree(CONTENT, OUT / "content")

    write("sitemap.xml", sitemap())
    write("robots.txt", robots())

    # The site used to be five pages. Those URLs are in Google's index and may
    # be in someone's bookmarks, so send each one to its section on the
    # one-pager rather than to a 404.
    write("_redirects", "\n".join([
        "/homes/       /#houses   301",
        "/homes.html   /#houses   301",
        "/about/       /#about    301",
        "/about.html   /#about    301",
        "/costs/       /#cost     301",
        "/costs.html   /#cost     301",
        "/cost/        /#cost     301",
        "/faq/         /#faq      301",
        "/faq.html     /#faq      301",
        "/apply.html   /apply/    301",
        "/contact      /apply/    301",
    ]) + "\n")

    if dev:
        build_id = str(time.time())
        write("__buildid", build_id)
        for page in OUT.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            page.write_text(text.replace("</body>", LIVERELOAD + "</body>"), encoding="utf-8")

    pages = len(PAGES)
    placeholders = sum(
        1 for p in OUT.rglob("*.html")
        for _ in re.finditer(r"PLACEHOLDER", p.read_text(encoding="utf-8"))
    )
    print(f"✓ Built {pages} pages into {OUT.relative_to(ROOT)}/")
    for label, actual, limit in BROCHURE_OVERFLOW:
        print(f"  ! brochure had to shorten “{label}” "
              f"({actual} chars, {limit} fits) — trim it and the “…” goes away")
    if placeholders:
        print(f"  {placeholders} placeholder(s) still to replace — they're outlined in orange on the site.")
    return placeholders


def watch_signature():
    """A cheap fingerprint of everything a build depends on."""
    parts = []
    for base in (CONTENT, ROOT / "assets", ROOT / "admin"):
        if not base.exists():
            continue
        for f in sorted(base.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                parts.append(f"{f}:{f.stat().st_mtime_ns}")
    bp = ROOT / "build.py"
    parts.append(f"{bp}:{bp.stat().st_mtime_ns}")
    return hash(tuple(parts))


if __name__ == "__main__":
    serve = "--serve" in sys.argv
    if serve:
        # Line buffering, so watcher messages appear as they happen rather
        # than sitting in a buffer while you wonder if anything is working.
        sys.stdout.reconfigure(line_buffering=True)
    main(dev=serve)

    if serve:
        import http.server
        import socketserver
        import threading

        os.chdir(OUT)

        class Handler(http.server.SimpleHTTPRequestHandler):
            """Serve /foo/ from foo/index.html and use 404.html for misses."""

            def end_headers(self):
                # Never cache during local editing, or you'll refresh and see
                # the old page and think the build is broken.
                self.send_header("Cache-Control", "no-store, must-revalidate")
                super().end_headers()

            def send_error(self, code, message=None, explain=None):
                if code == 404 and Path("404.html").exists():
                    body = Path("404.html").read_bytes()
                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                super().send_error(code, message, explain)

            def log_message(self, fmt, *args):
                pass  # keep the console clear for build output

        def watcher():
            """Rebuild whenever content, assets, or build.py change."""
            last = watch_signature()
            while True:
                time.sleep(1)
                try:
                    now = watch_signature()
                except OSError:
                    continue
                if now == last:
                    continue
                last = now
                here = os.getcwd()
                try:
                    os.chdir(ROOT)
                    print("\n↻ change detected — rebuilding")
                    main(dev=True)
                    print("→ browser will refresh itself")
                except Exception as exc:            # noqa: BLE001 - keep serving
                    print(f"✗ build failed: {exc}")
                    print("  the last good version is still being served")
                finally:
                    os.chdir(here)

        threading.Thread(target=watcher, daemon=True).start()

        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", 8000), Handler) as httpd:
            print("→ http://localhost:8000        the site")
            print("→ http://localhost:8000/admin/ the editor")
            print("  watching for changes — edit and the page refreshes itself")
            print("  (ctrl-c to stop)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nstopped")
