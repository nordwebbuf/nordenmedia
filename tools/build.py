"""Builds every page of the site, in Swedish and English.

    python tools/build.py

Page content lives in src/sv/<page>.html (Swedish) and src/en/<page>.html
(English, written by hand). Header, footer and <head> are shared and defined
here; their English text comes from the tables in tools/i18n*.py. The script
lists any Swedish text left in the English pages.

Texts and images that are edited in Sveltia CMS (/admin/) live in content/:
content/<lang>/<page>.json and content/<lang>/shared.json. They are written
into the pages last, see tools/cms.py. After adding new elements to src/,
run `python tools/cms_setup.py` so they get keys and show up in the CMS.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n import T as T1, ALLOWED, SITE  # noqa: E402
from i18n_pages import T2  # noqa: E402
from i18n_v3 import T3  # noqa: E402
from i18n_v4 import T4  # noqa: E402
from i18n_v5 import T5  # noqa: E402
from i18n_v6 import T6  # noqa: E402
import cms  # noqa: E402

T = T6 + T5 + T4 + T1 + T3 + T2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOCIAL = {"instagram": "https://www.instagram.com/nordenmediauf/", "facebook": "#"}


def social_items(link_class=""):
    """Instagram and Facebook links. Their addresses come from the CMS; an empty address hides the link."""
    cls = f' class="social-link {link_class}"'.replace(" \"", "\"")
    return (f'<li><a href="{SOCIAL["instagram"]}"{cls} target="_blank" rel="noopener" aria-label="Norden Media UF på Instagram" '
            f'data-cms="social_instagram" data-cms-attrs="href,aria-label"><i class="ph-light ph-instagram-logo" aria-hidden="true"></i></a></li>'
            f'<li><a href="{SOCIAL["facebook"]}"{cls} target="_blank" rel="noopener" aria-label="Norden Media UF på Facebook" '
            f'data-cms="social_facebook" data-cms-attrs="href,aria-label"><i class="ph-light ph-facebook-logo" aria-hidden="true"></i></a></li>')


def content(lang, name):
    """Nested content of content/<lang>/<name>.json (empty if the file does not exist)."""
    return cms.load(os.path.join(ROOT, "content", lang, f"{name}.json"))

# key: (sv file, en file, sv title, en title, sv description, en description)
PAGES = {
    "index": ("index.html", "index.html",
              "Hemsidor för företag i Boden | Norden Media UF",
              "Websites for businesses in Boden | Norden Media UF",
              "Vi bygger hemsidor som syns på Google och ger fler kunder, och sköter domän, mejl och drift. Fast pris, och ni betalar först när ni är nöjda.",
              "We build websites that get found on Google and win more customers, and handle domain, email and hosting. Fixed price, and you only pay when you are happy."),
    "webbtjanster": ("webbtjanster.html", "web-services.html",
                     "Hemsidor, Google-synlighet och mejl | Norden Media UF",
                     "Websites, Google visibility and email | Norden Media UF",
                     "Hemsida, egen webbadress, företagsmejl, synlighet på Google och bokningar som sköter sig själva. Vi bygger och sköter allt, ni slipper tekniken.",
                     "Website, your own web address, business email, visibility on Google and bookings that run themselves. We build and run it all, you skip the tech."),
    "livesandning": ("livesandning.html", "live-streaming.html",
                     "Livesändning av evenemang och möten | Norden Media UF",
                     "Live streaming of events and meetings | Norden Media UF",
                     "Vi livesänder konferenser, föreläsningar, årsmöten och evenemang med flera kameror, grafik och inspelning, till er hemsida eller sociala medier.",
                     "We live stream conferences, lectures, AGMs and events with multiple cameras, graphics and recording, to your website or social media."),
    "priser": ("priser.html", "pricing.html",
               "Priser för hemsida, från 195 kr/mån | Norden Media UF",
               "Website pricing, from SEK 195/month | Norden Media UF",
               "Tre paket med fast startkostnad och fast månadsavgift för hemsida, mejl, synlighet och drift. Ni betalar först när hemsidan är klar och ni är nöjda.",
               "Three packages with a fixed start-up cost and a fixed monthly fee for website, email, visibility and hosting. You only pay once you are happy."),
    "om-oss": ("om-oss.html", "about.html",
               "Om oss, UF-företag från Boden | Norden Media UF",
               "About us, a student company from Boden | Norden Media UF",
               "Norden Media UF drivs av elever på Björknäsgymnasiet i Boden. Vi bygger hemsidor och livesänder evenemang, med en kontaktperson hela vägen.",
               "Norden Media UF is run by students at Björknäsgymnasiet in Boden. We build websites and live stream events, with one contact person all the way."),
    "kontakt": ("kontakt.html", "contact.html",
                "Kontakta oss och boka ett samtal | Norden Media UF",
                "Contact us and book a call | Norden Media UF",
                "Berätta om ert företag så hör vi av oss och bokar ett kort samtal. Det kostar ingenting att fråga. Mejla hej@nordenmedia.se eller fyll i formuläret.",
                "Tell us about your business and we will get in touch to book a short call. It costs nothing to ask. Email hej@nordenmedia.se or fill in the form."),
    "integritetspolicy": ("integritetspolicy.html", "privacy.html",
                          "Integritetspolicy | Norden Media UF",
                          "Privacy policy | Norden Media UF",
                          "Så hanterar Norden Media UF de personuppgifter som du lämnar via vår hemsida, och vilka rättigheter du har.",
                          "How Norden Media UF handles the personal data you provide through our website, and what rights you have."),
    "404": ("404.html", None, "Sidan hittades inte | Norden Media UF", None, "Sidan finns inte.", None),
}

NAV = ["webbtjanster", "livesandning", "priser", "om-oss"]
NAV_LABEL = {"webbtjanster": "Hemsidor", "livesandning": "Livesändning", "priser": "Priser", "om-oss": "Om oss"}


def cta(key, title, text, primary, secondary_href, secondary_label, label="Kontakta oss"):
    return f'''    <!-- CTA -->
    <section class="cta-band-wrap" aria-label="{label}">
      <div class="container">
        <div class="cta-band reveal">
          <div>
            <h2 class="cta-title" data-cms="{key}_title">{title}</h2>
            <p data-cms="{key}_text">{text}</p>
          </div>
          <div class="cta-actions">
            <a href="{{{{p}}}}kontakt.html" class="btn btn-light" data-cms="{key}_primary">{primary} <i class="ph-light ph-arrow-right" aria-hidden="true"></i></a>
            <a href="{{{{p}}}}{secondary_href}" class="btn btn-ghost-light" data-cms="{key}_secondary">{secondary_label}</a>
          </div>
        </div>
      </div>
    </section>'''


CTAS = {
    "{{CTA}}": cta("cta", "Lägg tiden på verksamheten. Vi tar hand om resten.", "Boka ett kort samtal så tar vi det därifrån. Det kostar ingenting att fråga.", "Boka ett samtal", "priser.html", "Se priser"),
    "{{CTA_ALT}}": cta("cta_alt", "Osäkra på vilket paket som passar?", "Berätta om ert företag så hjälper vi er att välja. Det kostar ingenting att fråga.", "Boka ett samtal", "webbtjanster.html", "Se vad som ingår"),
    "{{CTA_LIVE}}": cta("cta_live", "Har ni ett evenemang på gång?", "Berätta om det så återkommer vi med ett förslag och ett fast pris.", "Boka ett samtal", "webbtjanster.html", "Vi bygger även hemsidor"),
}
CTAS_EN = {
    "{{CTA}}": cta("cta", "Spend your time on your business. We take care of the rest.", "Book a short call and we will take it from there. It costs nothing to ask.", "Book a call", "priser.html", "See pricing", "Contact us"),
    "{{CTA_ALT}}": cta("cta_alt", "Not sure which package suits you?", "Tell us about your business and we will help you choose. It costs nothing to ask.", "Book a call", "webbtjanster.html", "See what is included", "Contact us"),
    "{{CTA_LIVE}}": cta("cta_live", "Have an event coming up?", "Tell us about it and we will come back with a proposal and a fixed price.", "Book a call", "webbtjanster.html", "We also build websites", "Contact us"),
}


def head(key, lang, p):
    sv_file, en_file, sv_title, en_title, sv_desc, en_desc = PAGES[key]
    title, desc = (sv_title, sv_desc) if lang == "sv" else (en_title, en_desc)
    seo = content(lang, key).get("seo", {})
    title = html_attr(seo.get("seo_title") or title)
    desc = html_attr(seo.get("seo_description") or desc)
    shared = cms.flatten(content("sv", "shared"))
    same_as = json.dumps([u for u in (shared.get("social_instagram_href", SOCIAL["instagram"]),
                                      shared.get("social_facebook_href", SOCIAL["facebook"])) if u and u != "#"])
    def url(l):
        f = sv_file if l == "sv" else en_file
        f = "" if f == "index.html" else f
        return f"{SITE}/{f}" if l == "sv" else f"{SITE}/en/{f}"
    alt = "" if not en_file else f'''
  <link rel="alternate" hreflang="sv" href="{url("sv")}">
  <link rel="alternate" hreflang="en" href="{url("en")}">
  <link rel="alternate" hreflang="x-default" href="{url("sv")}">'''
    robots = "noindex" if key == "404" else "index, follow, max-image-preview:large"
    og_image = f"{SITE}/assets/og-image{'' if lang == 'sv' else '-en'}.jpg"
    og_alt = ("Norden Media UF: hemsidor för företag och organisationer" if lang == "sv"
              else "Norden Media UF: websites for businesses and organisations")
    hero_preload = ""
    labels = {"sv": {"webbtjanster": "Hemsidor", "livesandning": "Livesändning", "priser": "Priser", "om-oss": "Om oss",
                     "kontakt": "Kontakt", "integritetspolicy": "Integritetspolicy"},
              "en": {"webbtjanster": "Websites", "livesandning": "Live streaming", "priser": "Pricing", "om-oss": "About us",
                     "kontakt": "Contact", "integritetspolicy": "Privacy policy"}}[lang]
    home_url = f"{SITE}/" if lang == "sv" else f"{SITE}/en/"
    crumbs = "" if key in ("index", "404") else f''',
      {{
        "@type": "BreadcrumbList",
        "itemListElement": [
          {{"@type": "ListItem", "position": 1, "name": "{"Startsida" if lang == "sv" else "Home"}", "item": "{home_url}"}},
          {{"@type": "ListItem", "position": 2, "name": "{labels[key]}", "item": "{url(lang)}"}}
        ]
      }}'''
    org_desc = ("Hemsidor, företagsmejl, synlighet på Google, bokningssystem, drift och livesändningar för företag och organisationer."
                if lang == "sv" else
                "Websites, business email, visibility on Google, booking systems, hosting and live streaming for businesses and organisations.")
    price = "Från 195 kr/mån" if lang == "sv" else "From SEK 195/month"
    return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="{robots}">
  <meta name="theme-color" content="#F5F6F9" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#070B16" media="(prefers-color-scheme: dark)">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="{"sv_SE" if lang == "sv" else "en_GB"}">
  <meta property="og:site_name" content="Norden Media UF">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url(lang)}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{og_alt}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{og_image}">
  <link rel="canonical" href="{url(lang)}">{alt}
  <link rel="icon" type="image/png" sizes="256x256" href="{p}assets/favicon.png">
  <link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png">
  <link rel="manifest" href="{p}site.webmanifest">{hero_preload}
  <link rel="preload" href="{p}assets/fonts/outfit-latin-3.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="{p}assets/fonts/geist-latin-1.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{p}css/fonts.css">
  <link rel="stylesheet" href="{p}assets/icons/phosphor-light.css">
  <link rel="stylesheet" href="{p}css/styles.css">
  <link rel="stylesheet" href="{p}css/v3.css">
  <script>
    (function () {{
      var d = document.documentElement; d.classList.add('js');
      try {{ var t = localStorage.getItem('theme'); if (t === 'light' || t === 'dark') d.setAttribute('data-theme', t); }} catch (e) {{}}
    }})();
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "ProfessionalService",
        "@id": "{SITE}/#business",
        "name": "Norden Media UF",
        "url": "{SITE}/",
        "logo": "{SITE}/assets/apple-touch-icon.png",
        "image": "{og_image}",
        "email": "hej@nordenmedia.se",
        "description": "{org_desc}",
        "priceRange": "{price}",
        "address": {{"@type": "PostalAddress", "addressLocality": "Boden", "addressRegion": "Norrbottens län", "addressCountry": "SE"}},
        "areaServed": [{{"@type": "AdministrativeArea", "name": "Norrbottens län"}}, {{"@type": "Country", "name": "Sverige"}}],
        "knowsLanguage": ["sv", "en"],
        "sameAs": {same_as}
      }},
      {{
        "@type": "WebSite",
        "@id": "{SITE}/#website",
        "name": "Norden Media UF",
        "alternateName": "Norden Media",
        "url": "{SITE}/",
        "inLanguage": ["sv-SE", "en-GB"],
        "publisher": {{"@id": "{SITE}/#business"}}
      }}{crumbs}
    ]
  }}
  </script>
{{{{HEAD_EXTRA}}}}</head>'''


def chrome(key, lang, p, body):
    sv_file, en_file = PAGES[key][0], PAGES[key][1]
    home = "./"
    if lang == "sv":
        switch_href = f"en/{en_file if en_file != 'index.html' else ''}" if en_file else "en/"
        switch = f'<a class="tool-btn lang-switch" href="{switch_href}" hreflang="en" lang="en" aria-label="Switch to English">EN</a>'
        foot_lang = f'<li><a href="{switch_href}" hreflang="en" lang="en">English</a></li>'
    else:
        back = "../" + (sv_file if sv_file != "index.html" else "")
        switch = f'<a class="tool-btn lang-switch" href="{back}" hreflang="sv" lang="sv" aria-label="Byt till svenska">SV</a>'
        foot_lang = f'<li><a href="{back}" hreflang="sv" lang="sv">Svenska</a></li>'

    def nav_items(cls):
        out = []
        for k in NAV:
            cur = ' aria-current="page"' if k == key else ""
            out.append(f'<li><a href="{p}{PAGES[k][0]}"{cur} data-cms="nav_{k.replace("-", "_")}">{NAV_LABEL[k]}</a></li>')
        return "\n          ".join(out)

    contact_cur = ' aria-current="page"' if key == "kontakt" else ""
    mobile_cta = "" if key in ("kontakt", "404", "integritetspolicy") else f'''
  <div class="mobile-cta" data-mobile-cta aria-hidden="true">
    <a href="{p}kontakt.html" class="btn btn-primary btn-block" tabindex="-1" data-cms="book_call">Boka ett samtal <i class="ph-light ph-arrow-right" aria-hidden="true"></i></a>
  </div>
'''
    return f'''
<body>
  <a class="skip-link" href="#main" data-cms="skip_link">Hoppa till innehållet</a>
  <div class="top-sentinel" aria-hidden="true"></div>

  <header class="site-header" data-header>
    <div class="progress" aria-hidden="true"></div>
    <div class="container header-inner">
      <a href="{home}" class="brand" aria-label="NordenMedia, till startsidan">
        <span class="logo" aria-hidden="true"></span>
      </a>

      <nav class="nav" aria-label="Huvudmeny">
        <ul class="nav-list">
          {nav_items("nav")}
        </ul>
      </nav>

      <div class="header-tools">
        <ul class="header-social" aria-label="Sociala medier">{social_items("tool-btn")}</ul>
        {switch}
        <button class="tool-btn" type="button" data-theme-toggle aria-label="Byt till mörkt läge">
          <i class="ph-light ph-moon" data-theme-icon aria-hidden="true"></i>
        </button>
      </div>

      <a href="{p}kontakt.html" class="btn btn-primary btn-sm header-cta"{contact_cur} data-cms="contact">Kontakt</a>

      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="mobile-menu" data-menu-toggle>
        <span class="sr-only">Öppna menyn</span>
        <span class="menu-icon" aria-hidden="true"><span></span><span></span></span>
      </button>
    </div>
  </header>

  <div class="mobile-menu" id="mobile-menu" data-mobile-menu hidden>
    <nav class="container" aria-label="Mobilmeny">
      <ul class="mobile-list">
          {nav_items("mobile")}
      </ul>
      <a href="{p}kontakt.html" class="btn btn-primary btn-block"{contact_cur} data-cms="contact">Kontakt <i class="ph-light ph-arrow-right" aria-hidden="true"></i></a>
      <ul class="mobile-social" aria-label="Sociala medier">{social_items()}</ul>
    </nav>
  </div>

  <main id="main">
{body}
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-top">
        <nav class="footer-cols" aria-label="Sidfot">
          <div>
            <p class="footer-head" data-cms="footer_head_services">Tjänster</p>
            <ul>
              <li><a href="{p}webbtjanster.html" data-cms="nav_webbtjanster">Hemsidor</a></li>
              <li><a href="{p}livesandning.html" data-cms="nav_livesandning">Livesändning</a></li>
              <li><a href="{p}priser.html" data-cms="nav_priser">Priser</a></li>
            </ul>
          </div>
          <div>
            <p class="footer-head" data-cms="footer_head_company">Norden Media UF</p>
            <ul>
              <li><a href="{p}om-oss.html" data-cms="nav_om_oss">Om oss</a></li>
              <li><a href="{p}kontakt.html" data-cms="contact">Kontakt</a></li>
              <li><a data-cms="footer_privacy" href="{p}integritetspolicy.html">Integritetspolicy</a></li>
            </ul>
          </div>
          <div>
            <p class="footer-head" data-cms="footer_head_contact">Kontakt</p>
            <ul>
              <li><a href="mailto:hej@nordenmedia.se" data-cms="footer_email" data-cms-attrs="href">hej@nordenmedia.se</a></li>
              <li><a href="{p}kontakt.html" data-cms="book_call">Boka ett samtal</a></li>
            </ul>
          </div>
          <ul class="footer-social" aria-label="Sociala medier">
            {social_items()}
          </ul>
        </nav>
      </div>
      <span class="logo logo-xl" role="img" aria-label="NordenMedia"></span>
      <div class="footer-bottom">
        <p data-cms="copyright">© <span data-year>2026</span> Norden Media UF</p>
        <ul class="footer-legal">
          {foot_lang}
          <li><a href="#top" class="to-top" data-cms="to_top">Till toppen <i class="ph-light ph-arrow-up" aria-hidden="true"></i></a></li>
        </ul>
      </div>
    </div>
  </footer>
{mobile_cta}
  <script src="{p}js/main.js" defer></script>
  <script src="{p}js/v3.js" defer></script>
</body>
</html>
'''


def render(key, lang):
    p = "" if lang == "sv" else "../"
    src = os.path.join(ROOT, "src", lang, f"{key}.html")
    if not os.path.exists(src):
        src = os.path.join(ROOT, "src", "sv", f"{key}.html")
    body = open(src, encoding="utf-8").read()
    extra = ""
    m = re.search(r"<!--HEAD-->(.*?)<!--/HEAD-->", body, re.S)
    if m:
        extra, body = m.group(1).strip("\n") + "\n", body.replace(m.group(0), "")
    for k, v in (CTAS if lang == "sv" else CTAS_EN).items():
        body = body.replace(k, v)
    html = head(key, lang, p).replace("{{HEAD_EXTRA}}", extra) + chrome(key, lang, p, body.rstrip())
    if key == "404":
        p = "/"  # served from any URL depth
        html = html.replace('href="./"', 'href="/"')
    html = html.replace("{{p}}", p)
    if key == "404":
        html = re.sub(r'(href|src)="(?!/|https?:|#|mailto:)', r'\1="/', html)
    return bust_cache(add_logo(html))


LOGO = json.load(open(os.path.join(ROOT, "tools", "logo_paths.json"), encoding="utf-8"))


def html_attr(text):
    """Text from the CMS, safe inside an attribute and <title>."""
    import html
    return html.escape(html.unescape(text), quote=True)


# Same in every language, so they are only edited once (in the Swedish settings)
LANGUAGE_NEUTRAL = {"footer_email", "copyright", "copyright_2"}


def finalize(html, key, lang):
    """Write the CMS content into a finished page and rebuild the FAQ structured data."""
    p = "/" if key == "404" else ("" if lang == "sv" else "../")
    values = cms.flatten(content(lang, "shared"))
    sv_shared = cms.flatten(content("sv", "shared"))
    values.update({k: v for k, v in sv_shared.items() if k in LANGUAGE_NEUTRAL or k.endswith("_href")})
    page = content(lang, key)
    values.update(cms.flatten(page))
    hidden = {name for name, sec in page.items() if isinstance(sec, dict) and sec.get("visa") is False}
    if hidden:
        start = html.index('<main id="main">') + len('<main id="main">')
        end = html.index("</main>")
        html = html[:start] + cms.hide_sections(html[start:end], hidden) + html[end:]
    html = cms.apply(html, values, p)
    html = re.sub(r'<li><a href=""[^>]*class="social-link[^"]*"[^>]*>.*?</a></li>', "", html)
    # "#" is a placeholder: the icon shows but the link goes nowhere and does not open a new tab
    html = re.sub(r'(<a href="#"[^>]*class="social-link[^"]*") target="_blank" rel="noopener"', r'\1', html)
    return cms.faq_jsonld(html)


def bust_cache(html):
    """Add a content hash to local CSS/JS links so browsers always load the latest version."""
    import hashlib

    def ver(m):
        attr, prefix, path = m.group(1), m.group(2), m.group(3)
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            return m.group(0)
        h = hashlib.md5(open(full, "rb").read()).hexdigest()[:8]
        return f'{attr}="{prefix}{path}?v={h}"'
    return re.sub(r'(href|src)="((?:\.\./|/)?)((?:css|js|assets/icons)/[\w./-]+\.(?:css|js))"', ver, html)


def add_logo(html):
    """Embed the NordenMedia logo once per page and reference it wherever <span class="logo..."> is used."""
    symbol = open(os.path.join(ROOT, "tools", "logo_symbol.svg"), encoding="utf-8").read()
    # The symbol's own viewBox crops the artwork; the outer <svg> just needs the same size from 0 0
    w, h = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', symbol).groups()
    vb = f"0 0 {w} {h}"
    html = re.sub(r'<span class="(logo[^"]*)"([^>]*)></span>',
                  rf'<svg class="\1" viewBox="{vb}"\2 focusable="false"><use href="#nm-logo"/></svg>', html)
    # The icon is a raster image: a navy version and a white one, toggled with --nm-icon-color / --nm-icon-white
    sprite = f'<svg class="nm-sprite" aria-hidden="true" focusable="false"><defs>{symbol}</defs></svg>'
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n  " + sprite, html, count=1)


def translate(key, html):
    if os.path.exists(os.path.join(ROOT, "src", "en", f"{key}.html")):
        # The body is already English (src/en); translate only the shared header, footer and <head>
        start, end = html.index('<main id="main">'), html.index("</main>")
        outside = [html[:start], html[end:]]
        for sv, en in T:
            outside = [part.replace(sv, en) for part in outside]
        html = outside[0] + html[start:end] + outside[1]
    else:
        for sv, en in T:
            html = html.replace(sv, en)
    # Pages in /en/ are siblings: ../kontakt.html -> contact.html
    for k, (sv_file, en_file, *_rest) in PAGES.items():
        if en_file:
            html = html.replace(f'href="../{sv_file}', f'href="{en_file}')
    return html


def leftovers(html):
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    for a in ALLOWED:
        text = text.replace(a, "")
    return [ln.strip() for ln in text.splitlines() if re.search(r"[åäöÅÄÖ]", ln)]


TODAY = __import__('datetime').date.today().isoformat()


def sitemap():
    rows = []
    for key, (sv_file, en_file, *_rest) in PAGES.items():
        if not en_file:
            continue
        sv = f"{SITE}/" + ("" if sv_file == "index.html" else sv_file)
        en = f"{SITE}/en/" + ("" if en_file == "index.html" else en_file)
        for loc in (sv, en):
            rows.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{TODAY}</lastmod>
    <xhtml:link rel="alternate" hreflang="sv" href="{sv}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
  </url>""")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(xml)


def main():
    problems = 0
    os.makedirs(os.path.join(ROOT, "en"), exist_ok=True)
    for key, (sv_file, en_file, *_rest) in PAGES.items():
        sv_html = finalize(render(key, "sv"), key, "sv")
        open(os.path.join(ROOT, sv_file), "w", encoding="utf-8", newline="\n").write(sv_html)
        if not en_file:
            continue
        en_html = finalize(translate(key, render(key, "en")), key, "en")
        # language switch back to Swedish must keep ../
        sv_target = "../" + (sv_file if sv_file != "index.html" else "")
        en_html = re.sub(r'(<a class="tool-btn lang-switch" href=")[^"]*(" hreflang="sv")', rf"\g<1>{sv_target}\2", en_html)
        en_html = re.sub(r'(<li><a href=")[^"]*(" hreflang="sv" lang="sv">Svenska)', rf"\g<1>{sv_target}\2", en_html)
        open(os.path.join(ROOT, "en", en_file), "w", encoding="utf-8", newline="\n").write(en_html)
        left = leftovers(en_html)
        if left:
            problems += 1
            print(f"en/{en_file}: untranslated text")
            for ln in left:
                print("   ", ln)
    sitemap()
    print("Built", len(PAGES), "Swedish and", sum(1 for v in PAGES.values() if v[1]), "English pages")
    # On Netlify the check only warns: a CMS edit should never stop the site from being published
    return 1 if problems and not os.environ.get("NETLIFY") else 0


if __name__ == "__main__":
    sys.exit(main())
