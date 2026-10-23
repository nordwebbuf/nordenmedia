"""Sets up the content that Sveltia CMS edits.

    python tools/cms_setup.py

1. Gives every editable element in src/<lang>/<page>.html a data-cms key (only
   elements that do not have one yet, so existing keys never change).
2. Adds missing fields to content/<lang>/<page>.json and content/<lang>/shared.json
   with the text currently on the page. Values already in the files (edited in
   the CMS) are kept.
3. Writes admin/config.yml, the field list the CMS shows.

Run it after adding or removing elements in src/, then run tools/build.py.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402
import cms  # noqa: E402

ROOT = build.ROOT
REPO = "nordwebbuf/nordenmedia"
BRANCH = "v4"
LANGS = {"sv": "Svenska", "en": "Engelska (English)"}
PAGE_LABEL = {"index": "Startsidan", "webbtjanster": "Hemsidor", "livesandning": "Livesändning", "priser": "Priser",
              "om-oss": "Om oss", "kontakt": "Kontakt", "integritetspolicy": "Integritetspolicy", "404": "Sidan finns inte (404)"}

# Keys used in the shared header, footer and CTA bands (defined in build.py), grouped for the CMS
SHARED_GROUPS = [
    ("meny", "Meny och knappar", r"^(nav_|contact$|book_call$|skip_link$)"),
    ("sociala_medier", "Instagram och Facebook", r"^social_"),
    ("sidfot", "Sidfot", r"^(footer_|copyright(_\d+)?$|to_top$)"),
    ("cta", "Uppmaning längst ned (de flesta sidor)", r"^cta_(title|text|primary|secondary)"),
    ("cta_alt", "Uppmaning längst ned (Priser)", r"^cta_alt_"),
    ("cta_live", "Uppmaning längst ned (Livesändning)", r"^cta_live_"),
]
SHARED_KEYS = set(re.findall(r'data-cms="\{?(\w+)\}?(?:_\w+)?"', open(os.path.join(ROOT, "tools", "build.py"), encoding="utf-8").read()))


def is_shared(name):
    return any(re.match(rx, name) for _g, _l, rx in SHARED_GROUPS)


def page_langs(key):
    sv_file, en_file = build.PAGES[key][0], build.PAGES[key][1]
    langs = ["sv"]
    if en_file and os.path.exists(os.path.join(ROOT, "src", "en", f"{key}.html")):
        langs.append("en")
    return langs


def rendered(key, lang):
    """The finished page, before the CMS content is applied (keys still in place)."""
    html = build.render(key, lang)
    return build.translate(key, html) if lang == "en" else html


def main_part(html):
    return html[html.index('<main id="main">') + len('<main id="main">'):html.index("</main>")]


def merge(old, sections):
    """New nested dict with the fields of `sections`; values from `old` win."""
    flat_old = cms.flatten(old)
    out = {}
    for s in sections:
        out[s["name"]] = {f["name"]: flat_old.get(f["name"], f["value"]) for f in s["fields"]}
    return out


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def yaml_fields(sections, indent):
    pad = " " * indent
    out = []
    for s in sections:
        out.append(f"{pad}- name: {yaml_str(s['name'])}")
        out.append(f"{pad}  label: {yaml_str(s['label'])}")
        out.append(f"{pad}  widget: object")
        out.append(f"{pad}  collapsed: true")
        out.append(f"{pad}  required: false")
        out.append(f"{pad}  fields:")
        for f in s["fields"]:
            out.append(f"{pad}    - {{ name: {yaml_str(f['name'])}, label: {yaml_str(f['label'])}, widget: {f['widget']}, required: false }}")
    return out


def main():
    used = {}
    # 1. keys in src/
    for key in build.PAGES:
        for lang in page_langs(key):
            path = os.path.join(ROOT, "src", lang, f"{key}.html")
            src = open(path, encoding="utf-8").read()
            taken = cms.keys_in(src) | SHARED_KEYS
            tagged = cms.tag(src, "t", taken)
            if tagged != src:
                open(path, "w", encoding="utf-8", newline="\n").write(tagged)
                print("keys added:", os.path.relpath(path, ROOT))

    # 2. content files
    files = {lang: [] for lang in LANGS}
    shared = {lang: [] for lang in LANGS}
    for key in build.PAGES:
        sv_file, en_file, sv_title, en_title, sv_desc, en_desc = build.PAGES[key]
        for lang in page_langs(key):
            html = rendered(key, lang)
            sections = []
            for s in cms.extract(main_part(html)):
                fields = [f for f in s["fields"] if not is_shared(f["name"])]
                if fields:
                    sections.append(dict(s, fields=fields))
            seo = {"name": "seo", "label": "Sökmotorer och delning (titel och beskrivning)", "fields": [
                {"name": "seo_title", "label": "Sidtitel (visas i fliken och på Google)", "widget": "string",
                 "value": sv_title if lang == "sv" else en_title},
                {"name": "seo_description", "label": "Beskrivning (visas på Google, ca 150 tecken)", "widget": "text",
                 "value": sv_desc if lang == "sv" else en_desc}]}
            sections = [seo] + sections
            path = os.path.join(ROOT, "content", lang, f"{key}.json")
            write_json(path, merge(cms.load(path), sections))
            files[lang].append((key, sections))
            for s in cms.extract(html):
                shared[lang].extend(f for f in s["fields"] if is_shared(f["name"]))

    for lang in LANGS:
        seen, groups = set(), []
        for g, label, rx in SHARED_GROUPS:
            fields = []
            for f in shared[lang]:
                if re.match(rx, f["name"]) and f["name"] not in seen:
                    seen.add(f["name"])
                    fields.append(f)
            if fields:
                groups.append({"name": g, "label": label, "fields": fields})
        if lang != "sv":  # links, e-mail and copyright are entered once, in the Swedish settings
            groups = [dict(g, fields=[f for f in g["fields"] if not (f["name"].endswith("_href") or f["name"] in build.LANGUAGE_NEUTRAL)])
                      for g in groups]
            groups = [g for g in groups if g["fields"]]
        else:
            for g in groups:
                for f in g["fields"]:
                    if f["name"].endswith("_href") or f["name"] in build.LANGUAGE_NEUTRAL:
                        f["label"] += " (gäller båda språken)"
        path = os.path.join(ROOT, "content", lang, "shared.json")
        write_json(path, merge(cms.load(path), groups))
        shared[lang] = groups

    # 3. admin/config.yml
    y = [
        "# Sveltia CMS. Generated by tools/cms_setup.py, edit that script instead of this file.",
        "backend:",
        "  name: github",
        f"  repo: {REPO}",
        f"  branch: {BRANCH}",
        "  commit_messages:",
        "    update: 'Innehåll: {{collection}} \"{{slug}}\" uppdaterat'",
        "    uploadMedia: 'Bild uppladdad: {{path}}'",
        "    deleteMedia: 'Bild borttagen: {{path}}'",
        f"site_url: {build.SITE}",
        f"display_url: {build.SITE}",
        "logo:",
        "  src: /assets/apple-touch-icon.png",
        "media_folder: assets/uploads",
        "public_folder: /assets/uploads",
        "collections:",
    ]
    for lang, lang_label in LANGS.items():
        y += [f"  - name: sidor_{lang}", f"    label: {yaml_str(lang_label + ' sidor')}",
              f"    label_singular: {yaml_str('Sida')}", "    editor: { preview: false }", "    files:"]
        for key, sections in files[lang]:
            y += [f"      - name: {yaml_str(key.replace('-', '_'))}", f"        label: {yaml_str(PAGE_LABEL[key])}",
                  f"        file: content/{lang}/{key}.json", "        fields:"]
            y += yaml_fields(sections, 10)
    y += ["  - name: gemensamt", f"    label: {yaml_str('Meny, sidfot och sociala medier')}",
          "    editor: { preview: false }", "    files:"]
    for lang, lang_label in LANGS.items():
        y += [f"      - name: shared_{lang}", f"        label: {yaml_str(lang_label)}",
              f"        file: content/{lang}/shared.json", "        fields:"]
        y += yaml_fields(shared[lang], 10)
    os.makedirs(os.path.join(ROOT, "admin"), exist_ok=True)
    with open(os.path.join(ROOT, "admin", "config.yml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(y) + "\n")
    n = sum(len(s["fields"]) for lang in LANGS for _k, ss in files[lang] for s in ss) + sum(len(g["fields"]) for lang in LANGS for g in shared[lang])
    print("CMS fields:", n)


if __name__ == "__main__":
    main()
