"""Editable content for Sveltia CMS.

Every element in src/<lang>/<page>.html (and in the shared header, footer and
CTA bands in build.py) that has its own text carries a data-cms="<key>"
attribute. Its text lives in content/<lang>/<page>.json (or shared.json) and
build.py writes it back into the page, then removes the attributes.

Field names in the JSON files:
  <key>          first text in the element
  <key>_2, _3    further texts in the same element (around links, <strong> etc.)
  <key>_src      image file (<img>), <key>_alt its alt text
  <key>_photo    image file of a team photo (data-photo)
  <key>_<attr>   an attribute listed in data-cms-attrs, e.g. href

Only text and attributes are edited; the markup around them stays as it is.
"""
import html
import json
import os
import re

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
RAW = {"script", "style", "textarea"}
SKIP_TAGS = {"svg", "template", "title", "head", "noscript"}
# Elements whose text is written by JavaScript, so editing it would have no effect
SKIP_ATTRS = {"data-count", "data-year", "data-submit-label", "data-logo", "data-plural", "data-out", "data-res",
              "data-report-month", "data-kpi", "data-kpi-delta", "data-demo-log", "data-dest-count", "data-cms-skip"}
SKIP_CLASSES = {"report-note"}

TOKEN = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][\w:-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>|[^<]+|<", re.S)
ATTR = re.compile(r"([^\s=/>]+)(?:\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s\"'>]+))?")


def parse_attrs(s):
    out = {}
    for m in ATTR.finditer(s or ""):
        v = m.group(2)
        if v is None:
            v = ""
        elif v[:1] in "\"'":
            v = v[1:-1]
        out[m.group(1).lower()] = html.unescape(v)
    return out


def _skipped(tag, attrs):
    if tag in SKIP_TAGS or attrs.get("aria-hidden") == "true":
        return True
    if any(a in attrs for a in SKIP_ATTRS):
        return True
    return bool(SKIP_CLASSES & set(attrs.get("class", "").split()))


def walk(src):
    """Yield (kind, data) events: ('open', node), ('close', node), ('text', (node, start, end)), ('comment', (text, depth))."""
    pos, stack = 0, []
    while pos < len(src):
        m = TOKEN.match(src, pos)
        tok = m.group(0)
        if tok.startswith("<!--"):
            yield "comment", (tok[4:-3].strip(), len(stack))
        elif m.group(2):
            closing, tag = m.group(1) == "/", m.group(2).lower()
            if closing:
                if any(n["tag"] == tag for n in stack):
                    while stack:
                        n = stack.pop()
                        yield "close", n
                        if n["tag"] == tag:
                            break
            else:
                attrs = parse_attrs(m.group(3))
                parent = stack[-1] if stack else None
                node = {"tag": tag, "attrs": attrs, "start": m.start(), "end": m.end(), "attr_src": m.group(3),
                        "skip": (parent and parent["skip"]) or _skipped(tag, attrs), "texts": 0}
                yield "open", node
                if tag in RAW:
                    close = src.lower().find(f"</{tag}", m.end())
                    close = len(src) if close < 0 else close
                    end = src.find(">", close)
                    pos = len(src) if end < 0 else end + 1
                    yield "close", node
                    continue
                if tag in VOID or m.group(4) == "/":
                    yield "close", node
                else:
                    stack.append(node)
        else:
            if stack and tok.strip():
                yield "text", (stack[-1], m.start(), m.end())
        pos = m.end()


def _editable_attrs(node):
    """(field suffix, attribute, widget) for the attributes of this element that can be edited."""
    a, out = node["attrs"], []
    if node["tag"] == "img":
        out += [("src", "src", "image"), ("alt", "alt", "string")]
    if "data-photo" in a:
        out.append(("photo", "data-photo", "image"))
    for name in filter(None, (x.strip() for x in a.get("data-cms-attrs", "").split(","))):
        out.append((re.sub(r"\W", "_", name), name, "string"))
    return out


# ---------- 1. tag: add data-cms keys to elements that do not have one yet ----------

def tag(src, prefix, used):
    """Return src with data-cms="<prefix><n>" added to every editable element without a key."""
    inserts, n = [], [0]

    def new_key():
        while True:
            n[0] += 1
            k = f"{prefix}{n[0]}"
            if k not in used:
                used.add(k)
                return k

    def add(node):
        # mark the node itself: id() of finished nodes is reused, so it cannot identify them
        if node.get("tagged") or "data-cms" in node["attrs"] or node["skip"]:
            return
        node["tagged"] = True
        close = node["end"] - (2 if src[node["end"] - 2:node["end"]] == "/>" else 1)
        inserts.append((close, f' data-cms="{new_key()}"'))

    for kind, data in walk(src):
        if kind == "open" and not data["skip"] and (data["tag"] == "img" or "data-photo" in data["attrs"]):
            add(data)
        elif kind == "text" and not data[0]["skip"]:
            add(data[0])
    for at, text in sorted(inserts, reverse=True):
        src = src[:at] + text + src[at:]
    return src


def keys_in(src):
    return set(re.findall(r'data-cms="([^"]+)"', src))


# ---------- 2. extract: the current text of every field, grouped by section ----------

def _plain(s):
    """Decoded text with runs of ordinary whitespace collapsed (no-break spaces are kept)."""
    return re.sub(r"[ \t\r\n\f]+", " ", html.unescape(s)).strip(" \t\r\n\f")


def _label(node, value):
    kinds = {"h1": "Rubrik", "h2": "Rubrik", "h3": "Underrubrik", "h4": "Underrubrik", "p": "Text", "li": "Punkt",
             "a": "Länk", "button": "Knapp", "summary": "Fråga", "label": "Fält", "dt": "Rubrik", "dd": "Text",
             "strong": "Markerad text", "b": "Fetstil", "em": "Kursiv", "option": "Val", "th": "Tabellrubrik",
             "td": "Tabellcell", "figcaption": "Bildtext", "blockquote": "Citat", "small": "Liten text"}
    cls = node["attrs"].get("class", "")
    kind = kinds.get(node["tag"], "Text")
    if "eyebrow" in cls:
        kind = "Etikett"
    elif "btn" in cls:
        kind = "Knapp"
    short = value if len(value) <= 48 else value[:46].rstrip() + "…"
    return f"{kind}: {short}" if short else kind


def site_path(value):
    """Local image path as the CMS stores it: '/assets/...' whatever the page depth ({{p}}, ../ or /)."""
    if re.match(r"^(https?:|data:)", value):
        return value
    return "/" + re.sub(r"^(\{\{p\}\}|(\.\./)+|/)", "", value)


def extract(src, strip_prefix="{{p}}"):
    """Ordered list of sections: {'name', 'label', 'fields': [{name, label, widget, value}]}."""
    sections, cur = [], None

    def section(label):
        nonlocal cur
        slug = re.sub(r"[^a-z0-9]+", "_", label.lower().translate(str.maketrans("åäöé", "aaoe"))).strip("_") or "innehall"
        names = {s["name"] for s in sections}
        base, i = slug, 1
        while slug in names:
            i += 1
            slug = f"{base}_{i}"
        cur = {"name": slug, "label": label, "fields": []}
        sections.append(cur)

    seen = set()
    for kind, data in walk(src):
        if kind == "comment":
            text, depth = data
            if depth <= 1 and text and not text.startswith(("HEAD", "/HEAD")) and len(text) < 60:
                section(text)
        elif kind == "open" and "data-cms" in data["attrs"]:
            key = data["attrs"]["data-cms"]
            for suffix, attr, widget in _editable_attrs(data):
                if f"{key}_{suffix}" in seen:
                    continue
                seen.add(f"{key}_{suffix}")
                if cur is None:
                    section("Innehåll")
                value = data["attrs"].get(attr, "")
                if widget == "image":
                    value = site_path(value)
                label = {"src": "Bild", "photo": "Foto", "href": "Länkadress",
                         "aria_label": "Beskrivning för skärmläsare"}.get(suffix, suffix)
                if suffix == "alt":
                    label = f"Bildbeskrivning: {_plain(value)[:40]}"
                cur["fields"].append({"name": f"{key}_{suffix}", "label": label, "widget": widget, "value": value})
        elif kind == "text":
            node = data[0]
            key = node["attrs"].get("data-cms")
            if not key:
                continue
            node["texts"] += 1
            name = key if node["texts"] == 1 else f"{key}_{node['texts']}"
            if name in seen:  # the same shared text used twice on a page (menu and footer)
                continue
            seen.add(name)
            value = _plain(src[data[1]:data[2]])
            if cur is None:
                section("Innehåll")
            widget = "text" if len(value) > 90 else "string"
            cur["fields"].append({"name": name, "label": _label(node, value), "widget": widget, "value": value})
    return [s for s in sections if s["fields"]]


# ---------- 3. apply: write content into the page and remove the data-cms attributes ----------

def _set_attr(attr_src, name, value):
    esc = html.escape(value, quote=True)
    pat = re.compile(r'(\s' + re.escape(name) + r'\s*=\s*)("[^"]*"|\'[^\']*\'|[^\s"\'>]+)', re.I)
    if pat.search(attr_src):
        return pat.sub(lambda m: f'{m.group(1)}"{esc}"', attr_src, count=1)
    return attr_src + f' {name}="{esc}"'


def apply(src, content, p=""):
    """Replace texts and attributes from the flat dict `content`, then drop data-cms*."""
    edits = []  # (start, end, replacement)
    for kind, data in walk(src):
        if kind == "open" and ("data-cms" in data["attrs"] or "data-cms-attrs" in data["attrs"]):
            key = data["attrs"].get("data-cms")
            attr_src = data["attr_src"]
            if key:
                for suffix, attr, widget in _editable_attrs(data):
                    value = content.get(f"{key}_{suffix}")
                    if value is None:
                        continue
                    if widget == "image" and value and not re.match(r"^(https?:|data:)", value):
                        value = p + value.lstrip("/")
                    attr_src = _set_attr(attr_src, attr, value)
            attr_src = re.sub(r'\s+data-cms(?:-attrs)?="[^"]*"', "", attr_src)
            tag = src[data["start"]:data["end"]]
            head = tag[:1 + len(data["tag"]) + (0 if tag[1] != "/" else 1)]
            tail = "/>" if tag.endswith("/>") else ">"
            edits.append((data["start"], data["end"], head + attr_src + tail))
        elif kind == "text":
            node = data[0]
            key = node["attrs"].get("data-cms")
            if not key:
                continue
            node["texts"] += 1
            name = key if node["texts"] == 1 else f"{key}_{node['texts']}"
            value = content.get(name)
            if value is None:
                continue
            raw = src[data[1]:data[2]]
            if _plain(raw) == str(value):
                continue  # unchanged: keep the original markup (entities, line breaks)
            ws = " \t\r\n\f"
            lead = raw[:len(raw) - len(raw.lstrip(ws))]
            trail = raw[len(raw.rstrip(ws)):]
            text = html.escape(str(value), quote=False).replace("\u00a0", "&nbsp;")
            edits.append((data[1], data[2], lead + text + trail))
    out, last = [], 0
    for start, end, rep in sorted(edits):
        out.append(src[last:start])
        out.append(rep)
        last = end
    out.append(src[last:])
    return "".join(out)


# ---------- content files ----------

def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten(data):
    """{'section': {'field': 'value'}} -> {'field': 'value'} (seo and other groups included)."""
    flat = {}
    for v in data.values():
        if isinstance(v, dict):
            for k, x in v.items():
                if isinstance(x, (str, int, float)):
                    flat[k] = str(x)
    return flat


def faq_jsonld(page_html):
    """Rebuild the FAQPage structured data from the questions on the page, so it always matches them."""
    items = re.findall(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>", page_html, re.S)
    if not items:
        return page_html

    def text(s):
        return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split()).replace(" .", ".").replace(" ,", ",")

    qa = [{"@type": "Question", "name": text(q), "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in items]
    body = "\n".join("      " + json.dumps(x, ensure_ascii=False) + ("," if i < len(qa) - 1 else "") for i, x in enumerate(qa))
    block = ('<script type="application/ld+json">\n  {\n    "@context": "https://schema.org",\n    "@type": "FAQPage",\n'
             '    "mainEntity": [\n' + body + "\n    ]\n  }\n  </script>")
    return re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "FAQPage".*?</script>',
                  lambda m: block, page_html, count=1, flags=re.S)
