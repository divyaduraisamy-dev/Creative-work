"""Interactive scrapbook features for Streamlit pages.

Each function drops one feature into the page with one call:

    import site_effects as fx
    fx.logo_loader()   # full-screen logo draw-in (first page load of a session only)
    fx.site_header()   # hairline header: logo, About, Work, Contact (email reveal), LinkedIn, colour toggle
    fx.corner_logo()   # (alternative to the header) your logo pinned top-left
    fx.pet_head()      # grabbable, tilting dog drawing
    fx.torch_reveal()  # hold and drag around the dog: a light shows a hidden picture
    fx.home_photo()    # a photo running edge to edge
    fx.wave_field()    # cream wave lines that bend under the cursor, with the required credit

The markup, styles and JavaScript live in ui-scrapbook/ (see ui-scrapbook/FEATURES.md).
Scripts run directly in the page through st.html(..., unsafe_allow_javascript=True),
which needs Streamlit 1.40 or newer. Only trusted local files are injected.
"""

from __future__ import annotations

import base64
import html
import json
import re
from functools import lru_cache
from pathlib import Path

import streamlit as st

SCRAPBOOK = Path(__file__).resolve().parent / "ui-scrapbook"
CUSTOM = SCRAPBOOK / "custom-features"
GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"


@lru_cache(maxsize=None)
def _read(relative: str) -> str:
    return (SCRAPBOOK / relative).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def _component(relative: str) -> str:
    """Component markup without its documentation comment (keeps the page small)."""
    return re.sub(r"<!--.*?-->", "", _read(relative), flags=re.S).strip()


@lru_cache(maxsize=None)
def _data_uri(path: Path) -> str:
    types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
    mime = types.get(path.suffix.lower(), "image/svg+xml")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _script(script_files: list[str], start_js: str, needs_gsap: bool = False) -> str:
    """Run feature code in the page.

    Streamlit's HTML cleaner drops any script containing "<" directly followed by a character
    (e.g. `i<n`), so the code is sent base64-encoded and decoded in the browser. It runs inside
    its own function scope (safe if Streamlit re-renders it), after GSAP has loaded when needed.
    The wrapper below deliberately contains no "<" characters.
    """
    code = "\n".join(_read(f) for f in script_files) + "\n" + start_js
    encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
    return f"""
<script>
(function () {{
  var source = new TextDecoder().decode(Uint8Array.from(atob("{encoded}"), function (c) {{ return c.charCodeAt(0); }}));
  function run() {{
    try {{ new Function(source)(); }}
    catch (err) {{ console.warn("[site_effects] could not start:", err); }}
  }}
  function loadGsap() {{
    if (window.gsap) return Promise.resolve();
    if (!window.__scrapbookGsap) {{
      window.__scrapbookGsap = new Promise(function (resolve, reject) {{
        var s = document.createElement("script");
        s.src = {json.dumps(GSAP_URL)};
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
      }});
    }}
    return window.__scrapbookGsap;
  }}
  ({"loadGsap()" if needs_gsap else "Promise.resolve()"}).then(run)
    .catch(function (err) {{ console.warn("[site_effects] could not load GSAP:", err); }});
}})();
</script>"""


def _split_svg(markup: str) -> tuple[str, str]:
    """Streamlit strips inline <svg>, so pull it out; JavaScript puts it back after render."""
    match = re.search(r"<svg\b.*?</svg>", markup, flags=re.S)
    if not match:
        return markup, ""
    return markup[: match.start()] + "<div data-svg-slot></div>" + markup[match.end():], match.group(0)


def logo_loader(once_per_session: bool = True, speed: float = 1.0) -> None:
    """Full-screen black cover where the logo draws itself, then lifts away.

    Call it first in the script. It is only rendered on the first run of a Streamlit session
    (button clicks re-run the script but won't replay it); the JavaScript also skips it if it
    already played in this browser tab.
    """
    if once_per_session:
        if st.session_state.get("_site_effects_logo_loader"):
            return
        st.session_state["_site_effects_logo_loader"] = True
    markup, svg = _split_svg(_component("custom-features/logo-loader.html"))
    options = json.dumps({"oncePerSession": once_per_session, "speed": speed})
    restore_svg = (
        'var slot = document.querySelector("#c-logo-loader [data-svg-slot]");\n'
        f"if (slot) slot.outerHTML = {json.dumps(svg)};\n"
    )
    start = restore_svg + f'CustomLogoLoader.init("c-logo-loader", {options});'
    st.html(markup + _script(["custom-features/interactions.js"], start), unsafe_allow_javascript=True)


def corner_logo(color: str = "#f2ead3", hover_color: str = "#000000") -> None:
    """Your logo pinned to the top-left corner.

    `color` is the logo on the page; on hover a badge in that colour fills in and the logo turns
    `hover_color`. Clicking scrolls back to the top. Call it right after logo_loader(): when the
    loader plays, its logo glides into this spot.
    """
    markup, svg = _split_svg(_component("custom-features/corner-logo.html"))
    markup = markup.replace("--color-logo: #f2ead3;", f"--color-logo: {color};", 1)
    markup = markup.replace("--color-badge: #f2ead3;", f"--color-badge: {color};", 1)
    markup = markup.replace("--color-logo-hover: #000000;", f"--color-logo-hover: {hover_color};", 1)
    restore_svg = (
        'var slot = document.querySelector("#c-corner-logo [data-svg-slot]");\n'
        f"if (slot) slot.outerHTML = {json.dumps(svg)};\n"
    )
    start = restore_svg + 'CustomCornerLogo.init("c-corner-logo", { waitForLoader: "c-logo-loader" });'
    st.html(markup + _script(["custom-features/interactions.js"], start), unsafe_allow_javascript=True)


def encode_email(address: str) -> str:
    """Scramble an email for site_header(email_code=...): base64 of the reversed address.

    Keeps the plain address out of the code and the page; it is only assembled when a visitor
    clicks Contact. Make a code with:
        uv run python -c "import site_effects as fx; print(fx.encode_email('you@example.com'))"
    """
    return base64.b64encode(address[::-1].encode("utf-8")).decode("ascii")


# Page-wide styles the header needs inside Streamlit: hide Streamlit's own top bar, let the header
# run edge to edge at the very top, and the light colour scheme for the page and the features.
_PAGE_CSS = """
<style>
  [data-testid="stHeader"] { display: none; }
  [data-testid="stMainBlockContainer"] { padding-top: 0 !important; }
  [data-testid="stMain"] { overflow-x: hidden; }
  .stElementContainer:has(> .stHtml > #c-logo-loader),
  .stElementContainer:has(#site-effects-page-css) { margin-bottom: -1rem; }
  .c-site-header { width: 100vw; margin-left: calc(50% - 50vw); }
  /* Hidden page links the header clicks to change page without a reload. */
  .st-key-site-nav { display: none !important; }

  /* The features use the page's body font (set in .streamlit/config.toml). */
  :root .c-site-header { --font-ui: "Rubik", sans-serif; }
  .c-pet__caption, .c-torch__hint, .c-waves__credit, .c-loader__hint { font-family: "Rubik", sans-serif !important; }

  .stApp { transition: none; }
  :root[data-site-theme="light"] .stApp { background-color: #f2ead3; color: #000000; }
  :root[data-site-theme="light"] .stApp h1,
  :root[data-site-theme="light"] .stApp h2,
  :root[data-site-theme="light"] .stApp h3,
  :root[data-site-theme="light"] .stApp [data-testid="stMarkdownContainer"],
  :root[data-site-theme="light"] .stApp [data-testid="stHeadingWithActionElements"] { color: #000000; }
  :root[data-site-theme="light"] .c-pet { --color-bg: #f2ead3; --color-text: #000000; }
  :root[data-site-theme="light"] .c-pet__img { filter: brightness(0); }
  :root[data-site-theme="light"] .c-waves { --color-bg: #f2ead3; --color-text: #000000; --color-line: #000000; }
</style>
"""


def site_header(
    linkedin: str = "https://www.linkedin.com/",
    email_code: str = "",
    page: str = "home",
    pages: dict | None = None,
    transition_logo: str = "solid",
) -> None:
    """Header row inspired by wodniack.dev: logo | About · Work · Contact | LinkedIn | colour toggle.

    The hairlines bend away from the cursor. Contact inverts the page and shows the email from
    `email_code` (see encode_email). The toggle inverts the page and remembers it.

    Pages: `page` is the name of the page this header is on ("home", "work" or "kovu"). `pages` maps those
    names to the st.Page objects from st.navigation; Work / KOVU then open their pages and the logo
    goes back home, both with the logo taking over the screen in between. About scrolls to
    st.header(..., anchor="about") on the home page (from Work it goes home first).
    `transition_logo`: how the logo looks while it takes over the screen: "solid", "outline"
    (thin lines that draw themselves) or "alternate" (switches every time, for comparing).
    Call it at the top of every page, right after logo_loader().
    """
    markup, svg = _split_svg(_component("custom-features/site-header.html"))
    restore_svg = (
        'var slot = document.querySelector("#c-site-header [data-svg-slot]");\n'
        f"if (slot) slot.outerHTML = {json.dumps(svg)};\n"
    )
    options = json.dumps({"linkedin": linkedin, "email": email_code, "page": page,
                          "transition": {"logoStyle": transition_logo}})
    start = restore_svg + f'CustomSiteHeader.init("c-site-header", {options});'
    page_css = _PAGE_CSS.replace("<style>", '<style id="site-effects-page-css">', 1)
    st.html(page_css + markup + _script(["custom-features/interactions.js"], start), unsafe_allow_javascript=True)
    if pages:
        # One hidden in-app link per page (hidden by _PAGE_CSS); the header clicks them.
        with st.container(key="site-nav"):
            for name, target in pages.items():
                with st.container(key=f"site-nav-{name}"):
                    st.page_link(target, label=name)


def pet_head(image: str | Path | None = None, caption: str = "Placeholder caption: grab me", titles: dict | None = None) -> None:
    """The grabbable dog drawing. `image` defaults to the cream KOVU placeholder.

    titles: optional browser-tab titles per mood, e.g. {"idle": "Kovu :D", "hover": "Kovu :o", "grab": "Kovu x/"}.
    """
    img_path = Path(image) if image else CUSTOM / "assets" / "kovu-placeholder.png"
    markup = _component("custom-features/pet-head.html")
    markup = markup.replace('src="assets/kovu-placeholder.png"', f'src="{_data_uri(img_path)}"')
    markup = markup.replace("Placeholder caption: grab me", caption)
    options = json.dumps({"titles": titles} if titles else {})
    start = f'CustomPetHead.init("c-pet-head", {options});'
    st.html(markup + _script(["custom-features/interactions.js"], start), unsafe_allow_javascript=True)


@lru_cache(maxsize=None)
def _logo_path() -> str:
    """Path data of your logo (assets/logo.svg), for the torch pattern."""
    match = re.search(r'<path[^>]*\sd="([^"]+)"', (CUSTOM / "assets" / "logo.svg").read_text(encoding="utf-8"))
    return match.group(1) if match else ""


def torch_reveal(
    on: str = "c-pet-head",
    image: str | Path | None = None,
    hint: str | None = "Placeholder: hold and drag around KOVU",
    full_width: bool = True,
) -> None:
    """Hold the mouse (or a finger) and move: a soft light shows a hidden picture underneath.

    `on` is the element it lives on (default: the KOVU area from pet_head(); KOVU himself can still
    be grabbed). `image` is the hidden picture; without one it is a pattern made from your logo, in
    the page's text colour. `hint` is a small line of text under it (None for none).
    Call it after the element it lives on.
    """
    markup = _component("custom-features/torch-reveal.html")
    options = {"hint": hint, "bleed": full_width, "logoPath": _logo_path()}
    if image:
        options["image"] = _data_uri(Path(image))
    start = f"CustomTorchReveal.init({json.dumps(on)}, {json.dumps(options)});"
    st.html(markup + _script(["custom-features/interactions.js"], start), unsafe_allow_javascript=True)


def home_photo(
    image: str | Path | None = None,
    alt: str = "A person in pink walking across a green field toward tall trees under a blue sky",
) -> None:
    """A photo that runs edge to edge and keeps its shape. `image` defaults to assets/home-photo.jpg."""
    img_path = Path(image) if image else CUSTOM / "assets" / "home-photo.jpg"
    markup = _component("custom-features/home-photo.html")
    markup = markup.replace('src="assets/home-photo.jpg"', f'src="{_data_uri(img_path)}"')
    markup = re.sub(r'alt="[^"]*"', 'alt="' + html.escape(alt, quote=True) + '"', markup, count=1)
    st.html(markup)


def wave_field(line_color: str = "#f2ead3", height: str = "clamp(260px, 45vh, 520px)") -> None:
    """Black band of cream lines that bend away from the cursor, plus the CC BY-NC credit line."""
    markup = _component("custom-features/wave-field.html")
    markup = markup.replace("--color-line: #f2ead3;", f"--color-line: {line_color};", 1)
    markup = markup.replace("--layout-wave-height: clamp(260px, 45vh, 520px);", f"--layout-wave-height: {height};", 1)
    start = 'WodWaves.init("c-wave-field"); WodWaves.enableCursor("c-wave-field");'
    st.html(markup + _script(["wodniack-dev/interactions.js"], start, needs_gsap=True), unsafe_allow_javascript=True)
