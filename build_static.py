"""Build the plain web version of the site (no Streamlit) into docs/.

    uv run python build_static.py

Reads the same pages and text as the Streamlit app (site_content.py) and the same feature files
(ui-scrapbook/custom-features, plus the wave code from ui-scrapbook/wodniack-dev). Writes:
    docs/index.html          home
    docs/work/index.html     Work
    docs/kovu/index.html     KOVU
    docs/assets/...          images, fonts are from Google Fonts, scripts
GitHub Pages can serve docs/ as the site for your own domain.

Preview it on this computer:
    uv run python -m http.server 8600 --directory docs
then open http://localhost:8600
"""

from __future__ import annotations

import html
import json
import re
import shutil
from functools import cache
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PIL import Image

import site_content as content
from site_content import (Comic, Gallery, Heading, Page, Pet, Photo, Project, Text, ThoughtsList, Title, Torch, WalkButton,
                          WalkPlanner, Waves)

ROOT = Path(__file__).resolve().parent
SCRAPBOOK = ROOT / "ui-scrapbook"
CUSTOM = SCRAPBOOK / "custom-features"
OUT = ROOT / "docs"
# The custom domain GitHub Pages serves docs/ at (written to docs/CNAME on every build).
CUSTOM_DOMAIN = "divyaduraisamy.org"
# Search engines: the domain version puts the owner's name in each tab title.
# The Streamlit site keeps the plain titles from site_content.py.
OWNER_NAME = "Divya Duraisamy"
SITE_URL = f"https://{CUSTOM_DOMAIN}/"
# The short summary search engines show under the link (never shown on the page), by page path.
DESCRIPTIONS = {
    "": "Divya Duraisamy combines public health and data science to build human centered projects "
        "that help people regain autonomy over their health.",
    "work": "Divya Duraisamy's work on health equity, and how that perspective changes over time.",
    "moments": "Seen & Captured: illustrations, photos, stories and cartoons by Divya Duraisamy.",
    "kovu": "Projects inspired by Divya Duraisamy's dog, Kovu, including a tool that checks whether "
            "it's too hot to take a dog for a walk.",
    "thoughts": "Thought pieces by Divya Duraisamy on philosophy, ethics and reflection, and how that "
                "perspective changes over time.",
}

# Thought pieces: one text file each in thoughts/ (format in thoughts/README.md).
THOUGHTS = ROOT / "thoughts"


@dataclass
class Piece:
    slug: str           # web address: /thoughts/<slug>/
    title: str
    day: date
    description: str
    paragraphs: list[str]
    full: bool = False  # "Show: full": the Thoughts list shows the whole piece, not a preview


def read_piece(path: Path) -> Piece | None:
    """One piece: "Title:", "Date:" (and optional "Description:", "Draft:", "Show:") lines, a blank line, the text."""
    head, _, body = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip().partition("\n\n")
    fields = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise SystemExit(f"{path.name}: the lines before the first blank line need to look like 'Title: ...'")
        fields[key.strip().lower()] = value.strip()
    if fields.get("draft", "").lower() in {"yes", "true"}:
        print(f"skipped {path.relative_to(ROOT)} (draft)")
        return None
    missing = [k for k in ("title", "date") if not fields.get(k)]
    if missing:
        raise SystemExit(f"{path.name}: add a {' and '.join(missing)} line at the top")
    try:
        day = date.fromisoformat(fields["date"])
    except ValueError:
        raise SystemExit(f"{path.name}: write the date as year-month-day, e.g. 2026-11-20")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not paragraphs:
        raise SystemExit(f"{path.name}: the piece has no text after the blank line")
    words = " ".join(paragraphs[0].split())
    description = fields.get("description") or (words if len(words) <= 155 else words[:152].rsplit(" ", 1)[0] + "…")
    slug = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")
    show = fields.get("show", "preview").lower()
    if show not in {"full", "preview"}:
        raise SystemExit(f"{path.name}: write 'Show: full' to show the whole piece on the Thoughts page, or leave the line out")
    return Piece(slug, fields["title"], day, description, paragraphs, full=show == "full")


@cache
def pieces() -> list[Piece]:
    """Published pieces, newest first."""
    found = [read_piece(f) for f in sorted(THOUGHTS.glob("*.txt"))] if THOUGHTS.exists() else []
    return sorted((p for p in found if p), key=lambda p: (p.day, p.title), reverse=True)


def long_date(day: date) -> str:
    return f"{day:%B} {day.day}, {day.year}"


def piece_page(piece: Piece) -> Page:
    """The page for one piece (its blocks are filled in by render_page)."""
    return Page(piece.title, f"thoughts/{piece.slug}", [Waves()], only="domain")


def page_url(page: Page) -> str:
    return SITE_URL + (page.path + "/" if page.path else "")


def search_tags(page: Page, piece: Piece | None = None) -> str:
    """Head tags only search engines read: summary, main address, and who the site or piece is by."""
    summary = piece.description if piece else DESCRIPTIONS[page.path]
    tags = [f'<meta name="description" content="{esc(summary)}">',
            f'<link rel="canonical" href="{page_url(page)}">']
    if piece:
        article = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": piece.title,
                   "datePublished": piece.day.isoformat(), "description": piece.description,
                   "url": page_url(page), "author": {"@type": "Person", "name": OWNER_NAME, "url": SITE_URL}}
        tags.append(f'<script type="application/ld+json">{json.dumps(article)}</script>')
    if page.path == "":
        person = {"@context": "https://schema.org", "@type": "Person", "name": OWNER_NAME,
                  "url": SITE_URL, "description": DESCRIPTIONS[""], "sameAs": [content.LINKEDIN]}
        tags.append(f'<script type="application/ld+json">{json.dumps(person)}</script>')
    return "\n".join(tags)
# Stretch settings for the walk button (same as site_effects.WALK_OPTIONS).
WALK_OPTIONS = {"maxTilt": 0, "hoverScale": 1.03, "maxPull": 110, "maxStretch": 0.3}
GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"
FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Londrina+Solid:wght@100;300;400;900"
    "&family=Rubik:ital,wght@0,300..900;1,300..900&display=swap"
)


def component(relative: str) -> str:
    """A feature's markup and styles, without its documentation comment."""
    text = (SCRAPBOOK / relative).read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def logo_path() -> str:
    match = re.search(r'<path[^>]*\sd="([^"]+)"', (CUSTOM / "assets" / "logo.svg").read_text(encoding="utf-8"))
    return match.group(1) if match else ""


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def copy_asset(source: Path, folder: str = "") -> str:
    """Copy a file into docs/assets (or a folder inside it); return its path from the site root."""
    relative = f"{folder}/{source.name}" if folder else source.name
    target = OUT / "assets" / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return f"assets/{relative}"


# Page-wide styles: what Streamlit's theme gave the app (black page, cream text, Londrina Solid
# headings, Rubik body text, the wide layout), plus the light colour scheme.
PAGE_CSS = """
  :root { color-scheme: dark; --page-bg: #000000; --page-fg: #f2ead3; }
  :root[data-site-theme="light"] { color-scheme: light; --page-bg: #f2ead3; --page-fg: #000000; }
  *, *::before, *::after { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    background: var(--page-bg);
    color: var(--page-fg);
    font: 400 1rem/1.6 "Rubik", sans-serif;
    overflow-x: hidden;
  }
  .s-main { padding: 0 5rem 1rem; }
  .s-main > * + * { margin-top: 1rem; }
  .s-main h1, .s-main h2 {
    margin: 0;
    font-family: "Londrina Solid", sans-serif;
    font-weight: 400;
    line-height: 1.2;
  }
  .s-main h1 { font-size: 2.75rem; padding: 1.25rem 0 0.5rem; }
  .s-main h2 { font-size: 2.25rem; padding: 1rem 0 0.25rem; scroll-margin-top: 1rem; }
  .s-main p { margin: 0; }
  @media (max-width: 640px) {
    .s-main { padding: 0 1rem 1rem; }
    .s-main h1 { font-size: 2.25rem; }
    .s-main h2 { font-size: 1.85rem; }
  }

  :root .c-site-header { --font-ui: "Rubik", sans-serif; }
  .c-pet__caption, .c-torch__hint, .c-walk__btn, .c-waves__credit, .c-loader__hint { font-family: "Rubik", sans-serif !important; }

  :root[data-site-theme="light"] .c-pet { --color-bg: #f2ead3; --color-text: #000000; }
  :root[data-site-theme="light"] .c-pet__img { filter: brightness(0); }
  :root[data-site-theme="light"] .c-waves { --color-bg: #f2ead3; --color-text: #000000; --color-line: #000000; }

  /* Thoughts: the list of pieces, and one piece (a narrower column for easier reading). */
  .s-main .s-thoughts { list-style: none; margin: 2rem 0 1rem; padding: 0; max-width: 46rem; }
  .s-thoughts li { padding: 1.25rem 0; border-top: 1px solid color-mix(in srgb, var(--page-fg) 25%, transparent); }
  .s-thoughts li:last-child { border-bottom: 1px solid color-mix(in srgb, var(--page-fg) 25%, transparent); }
  .s-thoughts a { color: inherit; text-decoration: none; }
  .s-thoughts__title { font: 400 1.75rem/1.2 "Londrina Solid", sans-serif; }
  .s-thoughts a:hover .s-thoughts__title, .s-thoughts a:focus-visible .s-thoughts__title { text-decoration: underline; text-underline-offset: 0.2em; }
  .s-thoughts li > p + p { margin-top: 0.9rem; }
  .s-thoughts time, .s-piece__date { display: block; margin: 0.25rem 0 0.5rem; font-size: 0.875rem; opacity: 0.7; }
  .s-piece { max-width: 42rem; }
  .s-piece > p + p { margin-top: 1.1rem; }
  .s-piece { font-size: 1.075rem; line-height: 1.75; }
  .s-piece .s-piece__date { margin-bottom: 1.5rem; }
  .s-piece .s-piece__back { margin-top: 2.5rem; font-size: 0.95rem; }
  .s-piece__back a { color: inherit; }

  /* Photo caption (home): sits under the edge-to-edge photo, lined up with the page text. */
  .s-photo__caption { padding: 0.6rem 5rem 0; font-size: 0.875rem; line-height: 1.5; }
  .s-photo__title { display: block; font: 400 1.25rem/1.25 "Londrina Solid", sans-serif; font-style: normal; }
  .s-photo__details { display: block; opacity: 0.7; }
  @media (max-width: 640px) { .s-photo__caption { padding: 0.5rem 1rem 0; } }

  /* Comic: panels in reading order, three across (two on tablets, one on phones). The drawing is
     a mask over the page's text colour, so the lines are cream on black or black on cream. */
  .s-comic { padding-top: 2rem; }
  .s-main .s-comic__date { margin: 0.25rem 0 1.5rem; font-size: 0.875rem; opacity: 0.7; }
  .s-comic__panels {
    list-style: none; margin: 0; padding: 0;
    display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.5rem;
  }
  .s-comic__panels li { margin: 0; }
  .s-comic__panel {
    display: block;
    aspect-ratio: 1197 / 1500;
    background: var(--page-fg);
    -webkit-mask: var(--panel) center / contain no-repeat;
    mask: var(--panel) center / contain no-repeat;
  }
  @media (max-width: 900px) { .s-comic__panels { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  @media (max-width: 560px) { .s-comic__panels { grid-template-columns: 1fr; gap: 1rem; } }

  /* Gallery (Moments): pictures in columns (three on wide screens, one on phones), each with a
     title, date, place and note.
     Pictures keep their own shape and colours. */
  .s-gallery { padding-top: 1.5rem; }
  .s-gallery__items { list-style: none; margin: 1rem 0 0; padding: 0; columns: 3 18rem; column-gap: 2rem; }
  .s-gallery__items li { margin: 0 0 2.25rem; break-inside: avoid; }
  .s-gallery__items figure { margin: 0; }
  .s-gallery__items img { display: block; width: 100%; height: auto; }
  .s-gallery__items figcaption { padding-top: 0.6rem; font-size: 0.875rem; line-height: 1.5; }
  .s-gallery__title { display: block; font: 400 1.25rem/1.25 "Londrina Solid", sans-serif; font-style: normal; }
  .s-gallery__date, .s-gallery__note { display: block; }
  .s-gallery__date { opacity: 0.7; }
  .s-gallery__note { margin-top: 0.25rem; }

  /* Project: a link to something built, with a line about it. */
  .s-project { padding-top: 1.5rem; }
  .s-project__title { margin-bottom: 0.25rem; }
  .s-project__title a { color: inherit; text-decoration: underline; text-underline-offset: 0.2em; }
  .s-project__arrow { display: inline-block; transition: transform 0.25s ease; }
  .s-project__title a:hover .s-project__arrow, .s-project__title a:focus-visible .s-project__arrow { transform: translate(0.15em, -0.15em); }
  @media (prefers-reduced-motion: reduce) { .s-project__arrow { transition: none; } }
  .s-visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

  /* Next: the link to the following page, at the end of each page. */
  .s-main .s-next-wrap { margin: 3rem 0 1rem; text-align: right; }
  .s-next {
    display: inline-block; padding: 0; border: 0; background: none; color: inherit; cursor: pointer;
    font: 400 1.75rem/1.2 "Londrina Solid", sans-serif; text-decoration: none;
  }
  .s-next__arrow { display: inline-block; transition: transform 0.25s ease; }
  .s-next:hover, .s-next:focus-visible { text-decoration: underline; text-underline-offset: 0.2em; }
  .s-next:hover .s-next__arrow, .s-next:focus-visible .s-next__arrow { transform: translateX(0.3em); }
  @media (prefers-reduced-motion: reduce) { .s-next__arrow { transition: none; } }

  /* The opening loader only plays on the first page of a visit. */
  :root[data-logo-loader-seen] .c-loader { display: none; }

  /* Arriving from another page mid-transition: frost from the first paint until the script
     takes over (CustomPageTransition.arrive). */
  :root[data-arriving] .c-site-header__mark { opacity: 0; }
  :root[data-arriving] body::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 2147482499;
    background: rgba(0, 0, 0, 0.35);
    -webkit-backdrop-filter: blur(18px);
    backdrop-filter: blur(18px);
  }
  :root[data-arriving][data-site-theme="light"] body::after { background: rgba(242, 234, 211, 0.35); }
"""

# Runs before the page paints: colour scheme, loader already seen, arriving mid-transition.
HEAD_JS = """
(function () {
  var root = document.documentElement;
  try { var t = localStorage.getItem("site-theme"); if (t === "light" || t === "dark") root.dataset.siteTheme = t; } catch (e) {}
  try {
    if (sessionStorage.getItem("custom-logo-loader-seen")) root.dataset.logoLoaderSeen = "";
    if (sessionStorage.getItem("site-page-arrive")) root.dataset.arriving = "";
  } catch (e) {}
})();
"""


SEASON_MONTH = {"winter": 1, "spring": 4, "summer": 7, "fall": 10, "autumn": 10}


def art_date(text: str) -> tuple[str, str, str]:
    """A piece's date as (shown, for <time datetime>, sort key): "2022-12-17" -> December 17, 2022;
    "2021-06" -> June 2021; "Fall 2019" stays as written."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return long_date(date.fromisoformat(text)), text, text
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return date.fromisoformat(text + "-01").strftime("%B %Y"), text, text + "-00"
    season, _, year = text.partition(" ")
    if season.lower() in SEASON_MONTH and re.fullmatch(r"\d{4}", year):
        return text, year, f"{year}-{SEASON_MONTH[season.lower()]:02d}-00"
    raise ValueError(f'Date "{text}": use 2022-12-17, 2021-06 or Fall 2019')


def image_size(path: Path) -> tuple[int, int]:
    """Width and height, so the page doesn't jump while pictures load."""
    with Image.open(path) as im:
        return im.size


def next_link(name: str, pages: dict[str, str]) -> str:
    """The "Next" link at the end of a page: the following page in PAGES order, or Contact after the last."""
    names = list(domain_pages())
    after = names[names.index(name) + 1] if name in names and names.index(name) + 1 < len(names) else None
    if after:
        label = domain_pages()[after].title
        return (f'<p class="s-next-wrap"><a class="s-next" id="s-next" href="{pages[after]}" data-go="{after}">'
                f'Next: {esc(label)} <span class="s-next__arrow" aria-hidden="true">→</span></a></p>')
    return ('<p class="s-next-wrap"><button class="s-next" id="s-next" type="button" data-open-contact>'
            'Next: Contact <span class="s-next__arrow" aria-hidden="true">→</span></button></p>')


def domain_pages() -> dict[str, Page]:
    return {n: p for n, p in content.PAGES.items() if content.shown_on(p, "domain")}


def render_page(name: str, page: Page, piece: Piece | None = None) -> str:
    depth = page.path.count("/") + 1 if page.path else 0
    prefix = "../" * depth
    pages = {n: (prefix + (p.path + "/" if p.path else "")) or "./" for n, p in domain_pages().items()}

    body: list[str] = []
    start: list[str] = []
    styles_done: set[str] = set()

    def once(relative: str, markup: str) -> str:
        """Feature styles only need to appear once per page."""
        if relative in styles_done:
            return re.sub(r"<style>.*?</style>", "", markup, flags=re.S)
        styles_done.add(relative)
        return markup

    if piece:
        body.append(f'<article class="s-piece"><h1>{esc(piece.title)}</h1>'
                    f'<p class="s-piece__date"><time datetime="{piece.day.isoformat()}">{long_date(piece.day)}</time></p>'
                    + "".join(f"<p>{esc(par).replace(chr(10), '<br>')}</p>" for par in piece.paragraphs)
                    + f'<p class="s-piece__back"><a href="{pages["thoughts"]}">← All thoughts</a></p></article>')

    for block in page.blocks:
        if not content.shown_on(block, "domain"):
            continue
        if isinstance(block, Comic):
            # Each panel is a mask filled with the page's text colour, so it follows the theme.
            panels = "".join(
                f'<li><span class="s-comic__panel" role="img" aria-label="{esc(alt)}" '
                f'style="--panel: url(\'{prefix}{copy_asset(path, Path(block.folder).name)}\')"></span></li>'
                for path, alt in zip(content.frame_files(block.folder), block.alts, strict=True))
            day = date.fromisoformat(block.date)
            body.append(f'<section class="s-comic" aria-labelledby="s-comic-{esc(block.title.lower())}">'
                        f'<h2 id="s-comic-{esc(block.title.lower())}">{esc(block.title)}</h2>'
                        f'<p class="s-comic__date"><time datetime="{day.isoformat()}">{long_date(day)}</time></p>'
                        f'<ol class="s-comic__panels">{panels}</ol></section>')
        elif isinstance(block, Gallery):
            # Newest first; a section with nothing in it yet is left out.
            def caption(art) -> str:
                shown, machine, _ = art_date(art.date)
                details = f'<time datetime="{machine}">{esc(shown)}</time>' + (f" · {esc(art.place)}" if art.place else "")
                return ((f'<cite class="s-gallery__title">{esc(art.title)}</cite>' if art.title else "")
                        + f'<span class="s-gallery__date">{details}</span>'
                        + (f'<span class="s-gallery__note">{esc(art.note)}</span>' if art.note else ""))
            items = "".join(
                f'<li><figure><img src="{prefix}{copy_asset(ROOT / art.image, "moments")}" '
                f'alt="{esc(art.alt or art.title)}" loading="lazy" decoding="async"'
                + "".join(f' {k}="{v}"' for k, v in zip(("width", "height"), image_size(ROOT / art.image)))
                + f'><figcaption>{caption(art)}</figcaption></figure></li>'
                for art in sorted(block.pieces, key=lambda a: art_date(a.date)[2], reverse=True))
            if items:
                slug = re.sub(r"[^a-z0-9]+", "-", block.heading.lower()).strip("-")
                body.append(f'<section class="s-gallery" aria-labelledby="s-gallery-{slug}">'
                            f'<h2 id="s-gallery-{slug}">{esc(block.heading)}</h2>'
                            f'<ul class="s-gallery__items">{items}</ul></section>')
        elif isinstance(block, Project):
            if block.drawing:
                # The drawing is the link: pull it (or click) to open the project in a new tab.
                art = prefix + copy_asset(ROOT / block.drawing)
                markup = component("custom-features/recipe-bowl.html")
                markup = markup.replace("url('assets/recipe-bowl.webp')", f"url('{art}')")
                markup = markup.replace('href="#"', f'href="{esc(block.url)}"', 1)
                title = f'<h2 class="s-project__title">{esc(block.title)}</h2>' + once("recipe-bowl", markup)
                start.append(f'CustomPetHead.init("c-recipe-bowl", {json.dumps(WALK_OPTIONS)});')
                start.append('CustomLinkPull.init("c-recipe-bowl");')
            else:
                title = (f'<h2 class="s-project__title"><a href="{esc(block.url)}" target="_blank" rel="noopener">'
                         f'{esc(block.title)} <span class="s-project__arrow" aria-hidden="true">↗</span>'
                         f'<span class="s-visually-hidden"> (opens in a new tab)</span></a></h2>')
            body.append(f'<section class="s-project">{title}'
                        + (f"<p>{esc(block.text)}</p>" if block.text else "") + "</section>")
        elif isinstance(block, ThoughtsList):
            items = "".join(
                f'<li><a href="{prefix}thoughts/{pc.slug}/"><span class="s-thoughts__title">{esc(pc.title)}</span></a>'
                f'<time datetime="{pc.day.isoformat()}">{long_date(pc.day)}</time>'
                + ("".join(f"<p>{esc(par).replace(chr(10), '<br>')}</p>" for par in pc.paragraphs) if pc.full
                   else f"<p>{esc(pc.description)}</p>")
                + "</li>"
                for pc in pieces())
            if items:
                body.append(f'<ul class="s-thoughts">{items}</ul>')
        elif isinstance(block, Title):
            body.append(f"<h1>{esc(block.text)}</h1>")
        elif isinstance(block, Text):
            body.append(f"<p>{esc(block.text)}</p>")
        elif isinstance(block, Heading):
            anchor = f' id="{esc(block.anchor)}"' if block.anchor else ""
            body.append(f"<h2{anchor}>{esc(block.text)}</h2>")
        elif isinstance(block, Photo):
            src = copy_asset(Path(block.image) if block.image else CUSTOM / "assets" / "home-photo.jpg")
            markup = component("custom-features/home-photo.html")
            markup = markup.replace('src="assets/home-photo.jpg"', f'src="{prefix}{src}"')
            markup = re.sub(r'alt="[^"]*"', f'alt="{esc(block.alt)}"', markup, count=1)
            details = [long_date(date.fromisoformat(block.date))] if block.date else []
            details += [block.place] if block.place else []
            if block.title or details:
                caption = (f'<cite class="s-photo__title">{esc(block.title)}</cite>' if block.title else "")
                if details:
                    when = block.date and f'<time datetime="{esc(block.date)}">{esc(details[0])}</time>'
                    rest = [when] + [esc(d) for d in details[1:]] if block.date else [esc(d) for d in details]
                    caption += f'<span class="s-photo__details">{" · ".join(rest)}</span>'
                markup = markup.replace("</figure>", f'<figcaption class="s-photo__caption">{caption}</figcaption></figure>', 1)
            body.append(once("photo", markup))
        elif isinstance(block, Pet):
            src = copy_asset(CUSTOM / "assets" / "kovu-placeholder.png")
            markup = component("custom-features/pet-head.html")
            markup = markup.replace('src="assets/kovu-placeholder.png"', f'src="{prefix}{src}"')
            if block.caption:
                markup = markup.replace("Placeholder caption: grab me", esc(block.caption))
            else:
                markup = re.sub(r"\s*<figcaption.*?</figcaption>", "", markup, flags=re.S)
            if block.still:
                markup = markup.replace('class="c-pet"', 'class="c-pet c-pet--still"', 1)
            body.append(once("pet", markup))
            if not block.still:
                start.append('CustomPetHead.init("c-pet-head");')
        elif isinstance(block, Torch):
            body.append(once("torch", component("custom-features/torch-reveal.html")))
            options = {"hint": block.hint, "bleed": True, "logoPath": logo_path()}
            if block.frames:
                options["frames"] = [prefix + copy_asset(p, Path(block.frames).name)
                                     for p in content.frame_files(block.frames)]
                if block.match_drawing:
                    # The drawn walk button (.c-walkdraw) sits in this area: pressing it doesn't paint.
                    options.update(alignTo=".c-pet__img", alignBox=content.DRAWING_BOX, extendEdges=True,
                                   over=True, ignore=".c-walkdraw", busyWhen=None)
            elif block.image:
                options["image"] = prefix + copy_asset(Path(block.image))
            start.append(f'CustomTorchReveal.init("c-pet-head", {json.dumps(options)});')
        elif isinstance(block, WalkButton) and block.drawing:
            # The hand-drawn bubble goes inside KOVU's figure (the torch area), to his left.
            art = prefix + copy_asset(ROOT / block.drawing)
            markup = component("custom-features/walk-drawing.html")
            markup = markup.replace("url('assets/walk-button.webp')", f"url('{art}')")
            markup = markup.replace('aria-label="What time should we go on a walk?"', f'aria-label="{esc(block.text)}"')
            pet = next((i for i, part in enumerate(body) if 'id="c-pet-head"' in part), None)
            if pet is None:
                body.append(once("walk-drawing", markup))
            else:
                head, _, tail = body[pet].rpartition("</figure>")
                body[pet] = f"{head}{once('walk-drawing', markup)}</figure>{tail}"
            if any(isinstance(b, WalkPlanner) for b in page.blocks):
                # Same stretch as the pill; pulling and letting go, or clicking, opens the planner.
                start.append(f'CustomPetHead.init("c-walk-drawing", {json.dumps(WALK_OPTIONS)});')
                start.append('CustomWalkPlanner.init("c-walk-drawing", {"panel": "#c-walk-forecast", "everyTime": true});')
        elif isinstance(block, WalkButton):
            markup = component("custom-features/walk-button.html")
            markup = markup.replace(">What time should we go on a walk?<", f">{esc(block.text)}<", 1)
            body.append(once("walk", markup))
            start.append(f'CustomPetHead.init("c-walk-button", {json.dumps(WALK_OPTIONS)});')
            if any(isinstance(b, WalkPlanner) for b in page.blocks):
                # Pulling the button opens the in-page planner below (walk-forecast.html).
                start.append('CustomWalkPlanner.init("c-walk-button", {"panel": "#c-walk-forecast"});')
        elif isinstance(block, WalkPlanner):
            # No Python here: the planner runs in the page from the precomputed model
            # (build_walk_table.py -> walk-table.json). The Streamlit site keeps walk_planner.py.
            table = prefix + copy_asset(CUSTOM / "assets" / "walk-table.json")
            body.append(once("walk-forecast", component("custom-features/walk-forecast.html")))
            start.append(f'CustomWalkForecast.init("c-walk-forecast", {json.dumps({"table": table})});')
        elif isinstance(block, Waves):
            if not piece:
                body.append(next_link(name, pages))
                start.append('CustomNextLink.init("s-next");')
            body.append(once("waves", component("custom-features/wave-field.html")))
            start.append('WodWaves.init("c-wave-field"); WodWaves.enableCursor("c-wave-field");')

    header_options = {
        "linkedin": content.LINKEDIN,
        "email": content.EMAIL_CODE,
        "page": name,
        "pages": pages,
    }
    scripts = [
        'CustomLogoLoader.init("c-logo-loader");',
        f'CustomSiteHeader.init("c-site-header", {json.dumps(header_options)});',
        *start,
    ]
    needs_waves = any(isinstance(b, Waves) for b in page.blocks)
    script_tags = []
    if needs_waves:
        script_tags.append(f'<script src="{GSAP_URL}"></script>')
        script_tags.append(f'<script src="{prefix}assets/js/wodniack-interactions.js"></script>')
    script_tags.append(f'<script src="{prefix}assets/js/interactions.js"></script>')

    return f"""<!doctype html>
<html lang="en" data-site-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(OWNER_NAME if page.path == "" else f"{page.title} · {OWNER_NAME}")}</title>
{search_tags(page, piece)}
<link rel="icon" href="{prefix}assets/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_URL}">
<script>{HEAD_JS}</script>
<style>{PAGE_CSS}</style>
</head>
<body>
{component("custom-features/logo-loader.html")}
{component("custom-features/site-header.html")}
<main class="s-main">
{chr(10).join(body)}
</main>
{chr(10).join(script_tags)}
<script>
{chr(10).join(scripts)}
</script>
</body>
</html>
"""


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "js").mkdir(parents=True)
    shutil.copyfile(CUSTOM / "interactions.js", OUT / "assets" / "js" / "interactions.js")
    shutil.copyfile(SCRAPBOOK / "wodniack-dev" / "interactions.js", OUT / "assets" / "js" / "wodniack-interactions.js")
    copy_asset(CUSTOM / "assets" / "logo.svg")
    published = pieces()
    for name, page, piece in ([(n, p, None) for n, p in domain_pages().items()]
                              + [(f"thought-{pc.slug}", piece_page(pc), pc) for pc in published]):
        folder = OUT / page.path if page.path else OUT
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(render_page(name, page, piece), encoding="utf-8")
        print(f"wrote {(folder / 'index.html').relative_to(ROOT)}")
    # GitHub Pages: serve the files as they are (no Jekyll processing).
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    # GitHub Pages: the custom domain. Rebuilding clears docs/, so it is written here every time.
    (OUT / "CNAME").write_text(CUSTOM_DOMAIN, encoding="utf-8")
    # Search engines: the list of pages, and permission to read them all.
    urls = "".join(f"  <url><loc>{page_url(p)}</loc></url>\n" for p in domain_pages().values())
    urls += "".join(f"  <url><loc>{page_url(piece_page(pc))}</loc><lastmod>{pc.day.isoformat()}</lastmod></url>\n"
                    for pc in published)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     f"{urls}</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n",
                                    encoding="utf-8")


if __name__ == "__main__":
    main()
