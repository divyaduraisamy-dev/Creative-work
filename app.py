import streamlit as st

import site_effects as fx

st.set_page_config(layout="wide")

LINKEDIN = "https://www.linkedin.com/in/divya-duraisamy-936b94260/"
# Your email, stored scrambled so bots reading the code don't see it.
# Make a new code with fx.encode_email("you@example.com").
EMAIL_CODE = "bW9jLmxpYW1nQGtyb3d5bWFzaWFydWRheXZpZA=="


def header(page: str) -> None:
    """Header on every page: logo (home) | About · Work · Contact | LinkedIn | colour toggle."""
    # transition_logo="outline" would show the logo as thin drawing lines during page changes
    fx.site_header(linkedin=LINKEDIN, email_code=EMAIL_CODE, page=page, pages={"home": home, "work": work})


def home_page() -> None:
    header("home")

    # Intro
    st.title("Welcome to the site of Divya Duraisamy")
    st.write("I wanted a space to display my creative work and thoughts.")

    # KOVU: grab him. Hold and drag around him to light up the hidden picture.
    # The picture is a pattern of your logo for now; later: fx.torch_reveal(image="your-picture.png")
    fx.pet_head(caption="Grab here")
    fx.torch_reveal()

    # Placeholder content
    st.header("I look forward to engaging your mind")
    st.write("Take your time to work through the page and learn more about me.")

    # About: the header's About link scrolls here
    st.header("About", anchor="about")
    st.write("Placeholder: a few sentences about you.")

    # Wave lines at the bottom (move the cursor over them)
    fx.wave_field()


def work_page() -> None:
    header("work")

    st.title("Work")
    st.write("Placeholder: your projects or creative work.")

    fx.wave_field()


# Pages. The header switches between them (Work opens Work, the logo goes home);
# Streamlit's own page menu stays hidden. Work lives at /work.
home = st.Page(home_page, title="Welcome!", default=True)
work = st.Page(work_page, title="Work", url_path="work")
nav = st.navigation([home, work], position="hidden")

# Logo draw-in cover (first load of a session only; click or Escape skips it)
fx.logo_loader()

nav.run()
