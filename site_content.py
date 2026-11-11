"""Your site's pages and text, in one place.

Both versions of the site read this file:
  - the Streamlit app (app.py), live at heyitskovu.streamlit.app
  - the plain web version (build_static.py), for your own domain later

Edit the text here. Each page is a list of blocks, shown top to bottom:
    Title("...")                 big page heading
    Text("...")                  a paragraph
    Heading("...", anchor="x")   section heading; anchor="about" is where the About link scrolls
    Photo()                      the edge-to-edge photo (Photo(image="file.jpg", alt="...") for another)
    Pet(caption="...")           KOVU, grabbable; Pet(caption="", still=True) for a still drawing
    Torch(hint="...")            hold-and-drag light around KOVU (put it right after Pet)
                                 frames="folder" plays that folder's pictures (in name order) each press
    WalkButton("...")            a pill button you can grab and stretch
    WalkPlanner()                city -> next 12 hours of dog heat risk; opens when WalkButton is pulled
                                 (Streamlit only; the plain version's button goes to STREAMLIT_URL)
    Waves()                      the wave lines with their credit line
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# The Streamlit site (the plain version sends the walk button here, for the walk planner).
STREAMLIT_URL = "https://heyitskovu.streamlit.app"
LINKEDIN = "https://www.linkedin.com/in/divya-duraisamy-936b94260/"
# Your email, stored scrambled so bots reading the code don't see it.
# Make a new code with: uv run python -c "import site_effects as fx; print(fx.encode_email('you@example.com'))"
EMAIL_CODE = "bW9jLmxpYW1nQGtyb3d5bWFzaWFydWRheXZpZA=="


@dataclass
class Title:
    text: str


@dataclass
class Text:
    text: str


@dataclass
class Heading:
    text: str
    anchor: str | None = None


@dataclass
class Photo:
    image: str | None = None  # file path; None = ui-scrapbook/custom-features/assets/home-photo.jpg
    alt: str = "A person in pink walking across a green field toward tall trees under a blue sky"


@dataclass
class Pet:
    caption: str = "Pull me"  # "" for no caption
    still: bool = False       # True: the drawing stays put (no grab, stretch or tilt)


@dataclass
class Torch:
    hint: str | None = "Hold and drag around KOVU"
    image: str | None = None  # file path; None = a pattern made from your logo
    frames: str | None = None  # folder of pictures played in name order on each press (wins over image)
    match_drawing: bool = True  # line the pictures up under KOVU's drawing (see DRAWING_BOX)


@dataclass
class WalkButton:
    text: str = "What time should we go on a walk?"


@dataclass
class WalkPlanner:
    pass


@dataclass
class Waves:
    pass


# Where KOVU's drawing (kovu-placeholder.png, the whole image) sits on your paintings, as shares of
# the painting's width and height: [left, top, right, bottom]. Measured from kovujustline.png, the
# line layer of the same canvas (4828 x 6250), so the drawing's lines land on the painted dog.
DRAWING_BOX = [0.007724, 0.047027, 0.959611, 0.793613]


def frame_files(folder: str | Path) -> list[Path]:
    """The pictures in a folder, in name order (frame-04, frame-05, ...)."""
    kinds = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in kinds)


@dataclass
class Page:
    title: str      # browser tab title
    path: str       # web address after the domain: "" (home), "work", "kovu"
    blocks: list = field(default_factory=list)


# The first page is the home page. The header's links are Work and KOVU (plus About and Contact).
PAGES = {
    "home": Page("Welcome!", "", [
        Title("Welcome to the site of Divya Duraisamy"),
        Text("I wanted a space to display my creative work and thoughts."),
        Photo(),
        Heading("I look forward to engaging your mind"),
        Text("Take your time to work through the page and learn more about me."),
        Heading("About", anchor="about"),
        Text("Placeholder: a few sentences about you."),
        Waves(),
    ]),
    "work": Page("Work", "work", [
        Title("Work"),
        Text("I hope to document the work I’ve done to enhance health equity. I want to document my perspective and reveal how it changes over time. Maybe it will lead me to understand why I think the way I do. I want this to serve as a mix between a collection of memories and life work."),
        Waves(),
    ]),
    "kovu": Page("KOVU", "kovu", [
        Title("KOVU"),
        Pet(caption="", still=True),
        Torch(frames="ui-scrapbook/custom-features/assets/kovu-reveal"),
        WalkButton(),
        WalkPlanner(),
        Waves(),
    ]),
}
