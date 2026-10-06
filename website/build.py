#!/usr/bin/env python3
"""Baut die statische Website PGH-Brandschutz.

src/layout.html          gemeinsamer Rahmen (Kopf, Navigation, Fuß)
src/pages/*.html         Seiteninhalte, Metadaten im Kopfkommentar
static/                  wird 1:1 nach dist/ kopiert
dist/                    Ergebnis (nicht im Git), wird per SFTP hochgeladen

Aufruf:  python3 build.py            -> dist/
         python3 build.py --check    -> zusätzlich offene [OFFEN: ...]-Stellen auflisten
"""
import re, shutil, sys, datetime
from pathlib import Path

BASE = Path(__file__).parent
SITE = "https://www.pgh-brandschutz.de"
NAV = [("/", "Start"), ("/leistungen/", "Leistungen"), ("/hausverwaltungen/", "Für Hausverwaltungen"),
       ("/ratgeber/", "Ratgeber"), ("/ueber-mich/", "Über mich"), ("/kontakt/", "Kontakt")]

def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"<!--(.*?)-->\s*", text, re.S)
    meta = dict(l.split(":", 1) for l in m.group(1).strip().splitlines() if ":" in l)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    meta["content"] = text[m.end():]
    return meta

def nav_html(current):
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return "\n          ".join(items)

def main():
    layout = (BASE / "src/layout.html").read_text(encoding="utf-8")
    dist = BASE / "dist"
    shutil.rmtree(dist, ignore_errors=True)
    shutil.copytree(BASE / "static", dist)
    urls = []
    for p in sorted((BASE / "src/pages").glob("*.html")):
        meta = parse(p)
        path = meta["path"]
        out = dist / path.strip("/") / "index.html" if path.endswith("/") else dist / path.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        jsonld_file = BASE / "src" / (p.stem + ".jsonld")
        jsonld = f'<script type="application/ld+json">\n{jsonld_file.read_text(encoding="utf-8")}\n</script>' if jsonld_file.exists() else ""
        robots = meta.get("robots", "index,follow")
        html = (layout.replace("{{title}}", meta["title"])
                      .replace("{{description}}", meta["description"])
                      .replace("{{canonical}}", SITE + path)
                      .replace("{{robots}}", robots)
                      .replace("{{nav}}", nav_html(path))
                      .replace("{{jsonld}}", jsonld)
                      .replace("{{year}}", str(datetime.date.today().year))
                      .replace("{{content}}", meta["content"]))
        out.write_text(html, encoding="utf-8")
        if robots.startswith("index") and path != "/404.html":
            urls.append(path)
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls]
    sm.append("</urlset>")
    (dist / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    print(f"gebaut: {len(urls)} Seiten in die Sitemap, Ausgabe {dist}")
    if "--check" in sys.argv:
        offen = []
        for f in sorted(dist.rglob("*.html")):
            for m in re.finditer(r"\[OFFEN:([^\]]*)\]", f.read_text(encoding="utf-8")):
                offen.append(f"{f.relative_to(dist)}: {m.group(1).strip()}")
        print(f"{len(offen)} offene Stellen" + (":" if offen else ""))
        for o in offen: print("  -", o)

if __name__ == "__main__":
    main()
