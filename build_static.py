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
from pathlib import Path

import site_content as content
from site_content import Heading, Page, Pet, Photo, Text, Title, Torch, WalkButton, WalkPlanner, Waves

ROOT = Path(__file__).resolve().parent
SCRAPBOOK = ROOT / "ui-scrapbook"
CUSTOM = SCRAPBOOK / "custom-features"
OUT = ROOT / "docs"
# The custom domain GitHub Pages serves docs/ at (written to docs/CNAME on every build).
CUSTOM_DOMAIN = "divyaduraisamy.org"
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


def render_page(name: str, page: Page) -> str:
    depth = 1 if page.path else 0
    prefix = "../" * depth
    pages = {n: (prefix + (p.path + "/" if p.path else "")) or "./" for n, p in content.PAGES.items()}

    body: list[str] = []
    start: list[str] = []
    styles_done: set[str] = set()

    def once(relative: str, markup: str) -> str:
        """Feature styles only need to appear once per page."""
        if relative in styles_done:
            return re.sub(r"<style>.*?</style>", "", markup, flags=re.S)
        styles_done.add(relative)
        return markup

    for block in page.blocks:
        if isinstance(block, Title):
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
                    options.update(alignTo=".c-pet__img", alignBox=content.DRAWING_BOX, extendEdges=True,
                                   over=True, ignore=None, busyWhen=None)
            elif block.image:
                options["image"] = prefix + copy_asset(Path(block.image))
            start.append(f'CustomTorchReveal.init("c-pet-head", {json.dumps(options)});')
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
<title>{esc(page.title)}</title>
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
    for name, page in content.PAGES.items():
        folder = OUT / page.path if page.path else OUT
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(render_page(name, page), encoding="utf-8")
        print(f"wrote {(folder / 'index.html').relative_to(ROOT)}")
    # GitHub Pages: serve the files as they are (no Jekyll processing).
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    # GitHub Pages: the custom domain. Rebuilding clears docs/, so it is written here every time.
    (OUT / "CNAME").write_text(CUSTOM_DOMAIN, encoding="utf-8")


if __name__ == "__main__":
    main()
