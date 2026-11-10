import streamlit as st

import site_effects as fx

st.set_page_config(page_title="Welcome!", layout="wide")

# 1. Logo draw-in cover (first load of a session only; click or Escape skips it)
fx.logo_loader()

# 1b. Header: logo (back to top) | About · Work · Contact | LinkedIn | colour toggle.
# Contact inverts the page and shows your email. The email is stored scrambled so bots
# reading the code don't see it; make a new code with fx.encode_email("you@example.com").
fx.site_header(
    linkedin="https://www.linkedin.com/in/divya-duraisamy-936b94260/",
    email_code="bW9jLmxpYW1nQGtyb3d5bWFzaWFydWRheXZpZA==",
)

# 2. Intro
st.title("Welcome to the site of Divya Duraisamy")
st.write("I wanted a space to display my creative work and thoughts.")

# 3. KOVU: hover to tilt, grab and drag to squash, let go to watch him wobble back
fx.pet_head(caption="Grab here")

# 4. Placeholder content
st.header("I look forward to engaging your mind")
st.write("Take your time to work through the page and learn more about me.")

# About and Work: the header links scroll to these anchors
st.header("About", anchor="about")
st.write("Placeholder: a few sentences about you.")

st.header("Work", anchor="work")
st.write("Placeholder: your projects or creative work.")

# 5. Wave lines at the bottom (move the cursor over them)
fx.wave_field()
