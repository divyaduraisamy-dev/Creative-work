"""The Streamlit version of the site. Your pages and text live in site_content.py."""

import streamlit as st

import site_content as content
import site_effects as fx
from site_content import Heading, Pet, Photo, Text, Title, Torch, Waves

st.set_page_config(layout="wide")


def render(block) -> None:
    """Show one block from site_content.py."""
    if isinstance(block, Title):
        st.title(block.text)
    elif isinstance(block, Text):
        st.write(block.text)
    elif isinstance(block, Heading):
        st.header(block.text, anchor=block.anchor)
    elif isinstance(block, Photo):
        fx.home_photo(image=block.image, alt=block.alt)
    elif isinstance(block, Pet):
        fx.pet_head(caption=block.caption)
    elif isinstance(block, Torch):
        fx.torch_reveal(hint=block.hint, image=block.image)
    elif isinstance(block, Waves):
        fx.wave_field()


def make_page(name: str):
    def page() -> None:
        # Header on every page: logo (home) | About · Work · KOVU · Contact | LinkedIn | colour toggle
        fx.site_header(linkedin=content.LINKEDIN, email_code=content.EMAIL_CODE, page=name, pages=st_pages)
        for block in content.PAGES[name].blocks:
            render(block)

    page.__name__ = f"{name}_page"
    return page


# Pages. The header switches between them with the logo transition; Streamlit's own page menu
# stays hidden. Work lives at /work, KOVU at /kovu.
st_pages = {}
for index, (name, page) in enumerate(content.PAGES.items()):
    st_pages[name] = st.Page(make_page(name), title=page.title, url_path=page.path or None, default=index == 0)
nav = st.navigation(list(st_pages.values()), position="hidden")

# Logo draw-in cover (first load of a session only; click or Escape skips it)
fx.logo_loader()

nav.run()
