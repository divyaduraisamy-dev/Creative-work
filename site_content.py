"""Your site's pages and text, in one place.

Both versions of the site read this file:
  - the Streamlit app (app.py), live at heyitskovu.streamlit.app
  - the plain web version (build_static.py), live at divyaduraisamy.org

Edit the text here. Each page is a list of blocks, shown top to bottom:
    Title("...")                 big page heading
    Text("...")                  a paragraph
    Heading("...", anchor="x")   section heading; anchor="about" is where the About link scrolls
    Photo()                      the edge-to-edge photo (Photo(image="file.jpg", alt="...") for another;
                                 title=, date=, place= add a caption on the domain)
    Pet(caption="...")           KOVU, grabbable; Pet(caption="", still=True) for a still drawing
    Torch(hint="...")            hold-and-drag light around KOVU (put it right after Pet)
                                 frames="folder" plays that folder's pictures (in name order) each press
    WalkButton("...")            a pill button you can grab and stretch (Streamlit); on the domain,
                                 the hand-drawn bubble beside KOVU (click only)
    WalkPlanner()                city -> next 12 hours of dog heat risk; opens when WalkButton is pulled
                                 (Streamlit runs walk_planner.py; the plain version uses walk-table.json)
    Waves()                      the wave lines with their credit line
    ThoughtsList()               the list of pieces from the thoughts/ folder (plain web version only)
    Comic("Title", "2026-08-27", folder="...", alts=[...])
                                 a comic: the folder's panels in name order, each with its description;
                                 the lines take the page's text colour (plain web version only)
    Gallery("Illustrations", [Artwork("Title", "2022-12-17", "moments/...webp", note="...")])
                                 a section of pictures with a caption under each, newest first; an
                                 empty section is left out (plain web version only)

Each page on divyaduraisamy.org ends with a "Next" link to the page after it, in the order below;
the last one opens Contact.

Text and Page take only="domain" (divyaduraisamy.org only) or only="streamlit" (the Streamlit
site only). Without it, both sites show it.
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
    only: str | None = None  # "domain" or "streamlit": show it on that site only


@dataclass
class Heading:
    text: str
    anchor: str | None = None


@dataclass
class Photo:
    image: str | None = None  # file path; None = ui-scrapbook/custom-features/assets/home-photo.jpg
    alt: str = "A person in pink walking across a green field toward tall trees under a blue sky"
    # Caption under the photo, divyaduraisamy.org only (the Streamlit site shows the photo alone).
    title: str = ""           # name of the work
    date: str = ""            # year-month-day it was taken
    place: str = ""


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
    # divyaduraisamy.org only: the hand-drawn bubble beside KOVU's drawing (transparent line art).
    # The Streamlit site keeps the stretchy pill with the text above.
    drawing: str | None = "ui-scrapbook/custom-features/assets/walk-button.webp"


@dataclass
class WalkPlanner:
    pass


@dataclass
class Waves:
    pass


@dataclass
class ThoughtsList:
    pass


@dataclass
class Comic:
    title: str
    date: str               # year-month-day it was made
    folder: str             # panels as transparent line art (ink = opaque), shown in name order
    alts: list[str] = field(default_factory=list)  # what each panel shows, for screen readers
    only: str | None = "domain"


@dataclass
class Artwork:
    title: str
    date: str               # year-month-day it was made or taken
    image: str              # picture file (metadata stripped; the repository is public)
    note: str = ""          # optional line under the title
    alt: str = ""           # what it shows, for screen readers (the title if empty)


@dataclass
class Gallery:
    heading: str
    pieces: list[Artwork] = field(default_factory=list)
    only: str | None = "domain"


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
    only: str | None = None  # "domain": only on divyaduraisamy.org (no Streamlit page, no header link there)


# The first page is the home page. The header's links are Work, Moments, KOVU and Thoughts (plus About and Contact).
PAGES = {
    "home": Page("Welcome!", "", [
        Title("Welcome to the site of Divya Duraisamy"),
        Text("I want this to be a space for me to display my creative work and thoughts."),
        Photo(title="Afternoon Stroll", date="2021-06-20", place="Genesee Valley Park, Rochester, New York"),
        Heading("I look forward to engaging your mind"),
        Text("Take your time to work through the page and learn more about me."),
        Heading("About", anchor="about"),
        Text("I combine my knowledge of public health and data science to create human centered projects. I want people to regain autonomy over their health. The tools I build turn analysis into something they can actually use. All of my projects have been built to solve problems I have run into personally or noticed while speaking with others through my work. My goal is to improve health equity for all. I also take photos, doodle and write my thoughts, and go hiking with my dog, Kovu, who has inspired some of my projects."),
        Waves(),
    ]),
    "work": Page("Work", "work", [
        Title("Work"),
        Text("Projects I've built are aimed to address specific problems surrounding health equity in locations I've worked.", only="domain"),
        Text("I hope to document the work I’ve done to enhance health equity. I want to document my perspective and reveal how it changes over time. Maybe it will lead me to understand why I think the way I do. I want this to serve as a mix between a collection of memories and life work.", only="streamlit"),
        Waves(),
    ]),
    # Illustrations, photos, stories and cartoons not about KOVU. Header label: Moments.
    "moments": Page("Moments", "moments", [
        Title("Seen & Captured"),
        Gallery("Illustrations", [
            Artwork("Untitled", "2022-12-17", "moments/illustrations/2022-12-17-untitled.webp",
                    alt="A colourful marker and crayon drawing of fish among green seaweed in blue water: "
                        "a pink-faced fish peeks out of a striped shell, a large diamond-shaped fish with "
                        "one big eye faces right, and part of another fish shows at the edge."),
        ]),
        Gallery("Photos"),
        Gallery("Stories & Cartoons"),
        Waves(),
    ], only="domain"),
    "kovu": Page("KOVU", "kovu", [
        Title("projects inspired by my dog kovu"),
        Pet(caption="", still=True),
        Torch(frames="ui-scrapbook/custom-features/assets/kovu-reveal"),
        WalkButton(),
        WalkPlanner(),
        Comic("Smile", "2026-08-27", folder="ui-scrapbook/custom-features/assets/smile", alts=[
            "The word Smile hand-lettered three times, each one bigger.",
            "There once was a dog. A drawing of Kovu sitting and smiling up.",
            "Who loved to roll, with six drawings of Kovu rolling on his back.",
            "He loved to walk, with Kovu on a winding path under trees, looking back.",
            "He loved to snack, with Kovu looking up at treats tossed through the air.",
            "But most of all, he loved to smile. Two drawings of Kovu smiling and a smiley face.",
        ]),
        Waves(),
    ]),
    # Each piece is a text file in thoughts/ (see thoughts/README.md); this page lists them.
    "thoughts": Page("Thoughts", "thoughts", [
        Title("Thoughts"),
        Text("I hope to document the work I’ve done to enhance health equity. I want to document my perspective and reveal how it changes over time. Maybe it will lead me to understand why I think the way I do. I want this to serve as a mix between a collection of memories and life work."),
        ThoughtsList(),
        Waves(),
    ], only="domain"),
}


def shown_on(item, site: str) -> bool:
    """Whether a page or block belongs on this site ("domain" or "streamlit")."""
    only = getattr(item, "only", None)
    return only is None or only == site
