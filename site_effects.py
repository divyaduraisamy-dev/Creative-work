"""Interactive scrapbook features for Streamlit pages.

Each function drops one feature into the page with one call:

    import site_effects as fx
    fx.logo_loader()   # full-screen logo draw-in (first page load of a session only)
    fx.pet_head()      # grabbable, tilting dog drawing
    fx.wave_field()    # cream wave lines that bend under the cursor, with the required credit

The markup, styles and JavaScript live in ui-scrapbook/ (see ui-scrapbook/FEATURES.md).
Scripts run directly in the page through st.html(..., unsafe_allow_javascript=True),
which needs Streamlit 1.40 or newer. Only trusted local files are injected.
"""

from __future__ import annotations

import base64
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
    mime = "image/png" if path.suffix == ".png" else "image/svg+xml"
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


def wave_field(line_color: str = "#f2ead3", height: str = "clamp(260px, 45vh, 520px)") -> None:
    """Black band of cream lines that bend away from the cursor, plus the CC BY-NC credit line."""
    markup = _component("custom-features/wave-field.html")
    markup = markup.replace("--color-line: #f2ead3;", f"--color-line: {line_color};", 1)
    markup = markup.replace("--layout-wave-height: clamp(260px, 45vh, 520px);", f"--layout-wave-height: {height};", 1)
    start = 'WodWaves.init("c-wave-field"); WodWaves.enableCursor("c-wave-field");'
    st.html(markup + _script(["wodniack-dev/interactions.js"], start, needs_gsap=True), unsafe_allow_javascript=True)
