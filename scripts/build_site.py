#!/usr/bin/env python3
"""Render the academic homepage and its downloadable CV."""
import json
import shutil
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DIST = ROOT / "dist"
PUBLIC_ROOT = "https://jungw-s.github.io/"


def render(template_name, **fields):
    return Template((SITE / template_name).read_text(encoding="utf-8")).substitute(fields)


def link(url, label):
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def bibliography(papers, section):
    items = []
    for paper in papers.values():
        if section not in paper:
            continue
        links = {}
        if "arxiv" in paper:
            url = paper["arxiv"]
            identifier = urlsplit(url).path.rsplit("/", 1)[-1]
            links["arxiv"] = link(url, "arXiv")
            links["arxiv_id"] = link(url, f"arXiv:{identifier}")
        if "journal" in paper:
            links["journal"] = link(paper["journal"], "Journal")
        reference = escape(paper[section], quote=False).format_map(links)
        authors = escape(paper["authors"], quote=False)
        title = escape(paper["title"], quote=False)
        items.append(f'<li><h3>{title}</h3>\n'
                     f'  <p class="authors">{authors}</p>\n'
                     f'  <p class="reference">{reference}</p></li>')
    entries = "\n".join(items)
    return (f'<section class="section" aria-labelledby="{section}">\n'
            f'  <h2 id="{section}">{section.capitalize()}</h2>\n'
            f'  <ul class="papers" role="list">{entries}</ul>\n</section>')


def main():
    papers = json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8"))
    thrall_title = escape(papers["thrall"]["title"])
    home = render("home.html", preprints=bibliography(papers, "preprints"),
                  publications=bibliography(papers, "publications"))
    visualizations = render("visualizations.html", thrall_title=thrall_title,
                            thrall_paper=escape(papers["thrall"]["arxiv"]),
                            ibox_title=escape(papers["i-boxes"]["title"]),
                            ibox_paper=escape(papers["i-boxes"]["arxiv"]))
    sitemap = ElementTree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for route, title, description, body in [
        ("", "Woo-Seok Jung | Mathematics",
         "Woo-Seok Jung · Natural Science Research Institute, University of Seoul. Research interests, education and publications.", home),
        ("visualizations/", "Visualizations · Woo-Seok Jung",
         "Interactive visualizers accompanying papers by Woo-Seok Jung and coauthors.", visualizations),
    ]:
        canonical = PUBLIC_ROOT + route
        entry = ElementTree.SubElement(sitemap, "url")
        ElementTree.SubElement(entry, "loc").text = canonical
        is_home = not route
        current = 'aria-current="page"'
        identity = ('<h1 class="name">Woo-Seok Jung</h1>' if is_home else
                    '<a class="name" href="../index.html" aria-label="Woo-Seok Jung, home">Woo-Seok Jung</a>')
        html = render("layout.html", root="" if is_home else "../", title=title,
                      description=description, identity=identity, canonical=escape(canonical),
                      visual_current="" if is_home else current, body=body)
        output = DIST / route / "index.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")

    ElementTree.ElementTree(sitemap).write(DIST / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    shutil.copyfile(SITE / "style.css", DIST / "style.css")
    downloads = DIST / "documents"
    downloads.mkdir(exist_ok=True)
    cv = ROOT / "documents/CV_Woo-SeokJung.pdf"
    shutil.copyfile(cv, downloads / cv.name)
    # A local rebuild must also retire PDFs removed from the site's downloads.
    for previous in downloads.glob("*.pdf"):
        if previous.name != cv.name:
            previous.unlink()
    print(f"Built {DIST / 'index.html'} and {DIST / 'visualizations/index.html'}")


if __name__ == "__main__":
    main()
