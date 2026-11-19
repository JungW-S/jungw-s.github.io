"""Render the CV's four bibliography sections from the shared paper records."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ("preprints", "preparation", "accepted", "proceedings")
TEX_ESCAPES = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$",
    "&": r"\&", "#": r"\#", "_": r"\_", "%": r"\%",
    "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
}


def escape(text):
    return "".join(TEX_ESCAPES.get(char, char) for char in text)


def format_title(paper):
    settings = paper["documents"]
    title = settings.get("title", paper["title"])
    math = settings.get("math", {})
    if not math:
        return escape(title)
    for literal in math:
        if not literal or literal not in title:
            raise ValueError(f"Math expression {literal!r} missing from title {title!r}")
    parts = re.split("(" + "|".join(map(re.escape, math)) + ")", title)
    return "".join(math[p] if p in math else escape(p) for p in parts)


def author_credit(paper):
    if "authors" not in paper:
        return ""
    names = re.split(r",\s*(?:and\s+)?|\s+and\s+", paper["authors"])
    names.remove("Woo-Seok Jung")
    if len(names) < 3:
        credit = " and ".join(names)
    else:
        credit = ", ".join(names[:-1]) + ", and " + names[-1]
    return f" (with {escape(credit)})" if credit else ""


def arxiv(paper):
    url = urlsplit(paper["arxiv"])
    # The CV's \arxiv macro uses this canonical URL.
    if url.scheme != "https" or url.netloc != "arxiv.org" or url.query or url.fragment:
        raise ValueError(f"Unsupported arXiv URL: {url.geturl()}")
    match = re.fullmatch(r"/abs/([\w.\-/]+)", url.path)
    if not match:
        raise ValueError(f"Unsupported arXiv path: {url.path}")
    return r"\arxiv{" + match[1] + "}"


def render_item(paper, entry):
    section = entry["section"]
    title = format_title(paper)
    start = r"\item \emph{" + title + "}" + author_credit(paper)
    if section in ("accepted", "proceedings"):
        item = f"{start}, " + entry["citation_tex"]
        if entry.get("print_arxiv"):
            year = entry.get("cv_arxiv_year")
            item += " " + arxiv(paper) + (f" ({year})" if year else "") + "."
    else:
        item = f"{start}, {entry['year']}."
        if section == "preprints":
            if entry.get("cv_status"):
                item += " " + escape(entry["cv_status"])
            item += " " + arxiv(paper) + "."
    return item


def main(directory):
    papers = json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8"))
    sections = {key: [] for key in SECTIONS}
    for paper in papers.values():
        for entry in paper.get("documents", {}).get("entries", []):
            sections[entry["section"]].append(render_item(paper, entry))
    for section, items in sections.items():
        body = [r"\begin{itemize}", *items, r"\end{itemize}"] if items else []
        path = directory / f"cv-{section}.generated.tex"
        path.write_text("\n".join(body) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
