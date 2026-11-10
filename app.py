import streamlit as st

import site_effects as fx

st.set_page_config(page_title="Placeholder site name", layout="wide")

# 1. Logo draw-in cover (first load of a session only; click or Escape skips it)
fx.logo_loader()

# 2. Intro
st.title("Placeholder headline")
st.write("Placeholder introduction: one or two sentences about the site.")

# 3. KOVU: hover to tilt, grab and drag to squash, let go to watch him wobble back
fx.pet_head(caption="Placeholder caption: grab me")

# 4. Placeholder content
st.header("Placeholder section")
st.write("Placeholder paragraph for the main content of the page.")

# 5. Wave lines at the bottom (move the cursor over them)
fx.wave_field()
