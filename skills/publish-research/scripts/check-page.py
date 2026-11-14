#!/usr/bin/env python3
"""Check a published research page's structure against the Page Template.

Usage: check-page.py <page.html> [--styles <stylesheet.css>] [--pre-images]

The template is the single source of structural truth: the expected element for
each class is read from references/page-template.html, so the rules here do not
need updating when the template changes. Exits 1 and lists every problem found.

--styles      the site's shared stylesheet, used to recognise classes the template
              does not show. Default: ../../shared/styles.css relative to the page.
--pre-images  allows the {{..._IMG_URL}} markers the image step fills later.
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "references" / "page-template.html"
REQUIRED_IDS = ["picks", "criteria", "compare", "all-products", "tradeoffs", "ruled-out", "evidence"]
# Elements a <p> cannot contain; browsers close the <p> early and the layout breaks.
BLOCK_TAGS = {"div", "p", "table", "blockquote", "ul", "ol", "li", "dl", "pre", "figure", "details",
              "section", "article", "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "hr"}
PICK_IDS = {"pick-best", "pick-budget", "pick-premium"}
# Classes that /shared/nav.js adds at runtime; a page that hard-codes them gets them twice.
RUNTIME_CLASSES = {"allp__controls", "allp__arrow"}
PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}")
IMAGE_PLACEHOLDER = re.compile(r"\{\{[A-Z_]*IMG_URL\}\}")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.class_tags = {}      # class -> set of tags it appears on
        self.ids = set()
        self.pick_ids = set()
        self.inline_script = ""
        self.in_inline_script = False
        self.fragment_links = []  # (line, href)
        self.tldr_links = []      # (line, href)
        self.deep_dives = []      # (line, target id)
        self.problems = []
        self.stylesheets = set()
        self.script_srcs = set()
        self.open_p_line = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        classes = (a.get("class") or "").split()

        if tag in BLOCK_TAGS and self.open_p_line is not None:
            self.problems.append(f"line {line}: <{tag}> inside the <p> opened on line {self.open_p_line}")
            self.open_p_line = None
        if tag == "p":
            self.open_p_line = line

        for c in classes:
            if "{{" not in c and "}}" not in c and "|" not in c:
                self.class_tags.setdefault(c, set()).add(tag)
        if a.get("id"):
            if a["id"] in self.ids:
                self.problems.append(f'line {line}: duplicate id="{a["id"]}"')
            self.ids.add(a["id"])
        if tag == "article" and "pick" in classes:
            if a.get("id") in PICK_IDS:
                self.pick_ids.add(a["id"])
            else:
                self.problems.append(f'line {line}: article.pick needs id pick-best, pick-budget or pick-premium')
        for c in RUNTIME_CLASSES.intersection(classes):
            self.problems.append(f'line {line}: class "{c}" is added by nav.js at runtime; remove it from the page')
        if tag == "script" and "src" not in a:
            self.in_inline_script = True
        if "style" in a:
            self.problems.append(f"line {line}: inline style attribute on <{tag}>")
        if tag == "style":
            self.problems.append(f"line {line}: embedded <style> element")

        href = a.get("href")
        if href:
            if tag == "link" and "stylesheet" in (a.get("rel") or ""):
                self.stylesheets.add(href)
            if tag == "a" and href.startswith("#") and len(href) > 1:
                self.fragment_links.append((line, href[1:]))
                if "tldr__row" in classes:
                    self.tldr_links.append((line, href[1:]))
        if tag == "script" and a.get("src"):
            self.script_srcs.add(a["src"])
        if a.get("data-deep-dive"):
            self.deep_dives.append((line, a["data-deep-dive"]))

        if tag == "img":
            src = a.get("src") or ""
            if a.get("loading") != "lazy":
                self.problems.append(f'line {line}: <img> without loading="lazy"')
            if "img.youtube.com" not in src and a.get("referrerpolicy") != "no-referrer":
                self.problems.append(f'line {line}: product <img> without referrerpolicy="no-referrer"')

    def handle_endtag(self, tag):
        if tag == "p":
            self.open_p_line = None
        if tag == "script":
            self.in_inline_script = False

    def handle_data(self, data):
        if self.in_inline_script:
            self.inline_script += data


def parse(path):
    page = Page()
    page.feed(path.read_text(encoding="utf-8"))
    return page


def main():
    argv = sys.argv[1:]
    pre_images = "--pre-images" in argv
    styles_arg = None
    if "--styles" in argv:
        index = argv.index("--styles")
        if index + 1 >= len(argv):
            sys.exit(__doc__)
        styles_arg = argv[index + 1]
        del argv[index:index + 2]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    page_path = Path(args[0]).resolve()
    styles_path = Path(styles_arg).resolve() if styles_arg else page_path.parent.parent / "shared" / "styles.css"
    for needed in (page_path, TEMPLATE, styles_path):
        if not needed.exists():
            sys.exit(f"check-page: {needed} not found")

    template = parse(TEMPLATE)
    page = parse(page_path)
    css = styles_path.read_text(encoding="utf-8")
    problems = list(page.problems)

    for cls, tags in sorted(page.class_tags.items()):
        expected = template.class_tags.get(cls)
        if expected is None:
            if not re.search(r"\." + re.escape(cls) + r"(?![\w-])", css):
                problems.append(f'class "{cls}" is in neither the template nor shared/styles.css')
        elif not tags <= expected:
            wrong = ", ".join(f"<{t}>" for t in sorted(tags - expected))
            right = " or ".join(f"<{t}>" for t in sorted(expected))
            problems.append(f'class "{cls}" is on {wrong}; the template uses {right}')

    for required in REQUIRED_IDS:
        if required not in page.ids:
            problems.append(f'missing section anchor id="{required}"')
    for line, target in page.fragment_links:
        if target not in page.ids:
            problems.append(f'line {line}: link to #{target}, which does not exist')
    for line, target in page.tldr_links:
        if target in page.ids and target not in page.pick_ids:
            problems.append(f'line {line}: TL;DR row links to #{target}, which is not an article.pick')
    if not page.pick_ids:
        problems.append("page has no article.pick")
    for pick_id in sorted(page.pick_ids - {target for _, target in page.tldr_links}):
        problems.append(f"#{pick_id} has no TL;DR row linking to it")
    for line, target in page.deep_dives:
        if target not in page.ids:
            problems.append(f'line {line}: data-deep-dive="{target}" has no matching id')

    # Assets the template names literally must be loaded; placeholder paths are site config.
    for href in sorted(h for h in template.stylesheets if h.startswith("/") and "{{" not in h):
        if href not in page.stylesheets:
            problems.append(f"page does not load {href}")
    for src in sorted(s for s in template.script_srcs if s.startswith("/") and "{{" not in s):
        if src not in page.script_srcs:
            problems.append(f"page does not load {src}")
    if not page.stylesheets:
        problems.append("page loads no stylesheet")
    if template.inline_script.strip():
        if "data-deep-dive" not in page.inline_script or "data-video-id" not in page.inline_script:
            problems.append("the template's page script (chip nav, video embeds, cross-references) is missing")
    elif page.inline_script.strip():
        problems.append("page has an inline <script>; the template loads its scripts from files")

    text = page_path.read_text(encoding="utf-8")
    for number, line_text in enumerate(text.splitlines(), 1):
        for marker in PLACEHOLDER.findall(line_text):
            if pre_images and IMAGE_PLACEHOLDER.fullmatch(marker):
                continue
            problems.append(f"line {number}: unfilled placeholder {marker}")

    if problems:
        print(f"{page_path}: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print(f"{page_path}: structure matches the template")


if __name__ == "__main__":
    main()
