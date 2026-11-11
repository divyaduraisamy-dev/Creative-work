"""The walk planner on the KOVU page (Streamlit): city in, next 12 hours of dog heat risk out.

It stays hidden until someone pulls "What time should we go on a walk?" (CustomWalkPlanner in
interactions.js opens it). The model and forecast live in heat_model.py.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import heat_model as hm

# Which recovery time the headline answer uses ("15", "30" or "60" minutes after exercise).
# All three are shown for every hour; this one decides "best times to walk".
HEADLINE_RECOVERY = "60"

# The example dog from the notebook's live forecast (cell 101): 30 kg, 55 cm long, obedience work.
DEFAULT_WEIGHT_KG = 30.0
DEFAULT_LENGTH_CM = 55.0
DEFAULT_ACTIVITY = "OB"
LB_PER_KG = 2.20462
DISCLAIMER = (
    "Guidance only, not veterinary advice. The model is from my IST707 project: it learned from a "
    "small study of working dogs in three months of the year, and doesn't know your dog's coat, "
    "hydration, shade or pavement temperature. When in doubt, go shorter and bring water."
)


@st.cache_resource(show_spinner="Getting the dog heat model ready...")
def _model() -> hm.HeatModel:
    return hm.train()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _places(query: str) -> list[dict]:
    return hm.find_places(query)


@st.cache_data(ttl=15 * 60, show_spinner=False)
def _weather(lat: float, lon: float) -> pd.DataFrame:
    return hm.hourly_weather(lat, lon, hours=12)


def _temp(c: float, unit: str) -> str:
    return f"{c * 9 / 5 + 32:.0f}°F" if unit == "°F" else f"{c:.0f}°C"


def _hour(t: pd.Timestamp) -> str:
    return t.strftime("%-I %p")


def _pill(risk: str) -> str:
    return f'<span class="c-walkplan__pill" style="--risk:{hm.RISK_COLORS[risk]}">{risk}</span>'


def _results_html(table: pd.DataFrame, unit: str) -> str:
    key = f"risk_{HEADLINE_RECOVERY}"
    lows = hm.best_windows(table.assign(risk=table[key]), "Low")
    if lows:
        spans = [f"{_hour(a)} – {_hour(b)}" for a, b in lows]
        answer = "Best times for a walk: " + ", ".join(spans)
    else:
        mods = hm.best_windows(table.assign(risk=table[key]), "Moderate")
        answer = ("No low-risk hours in the next 12. Lower risk: " + ", ".join(f"{_hour(a)} – {_hour(b)}" for a, b in mods)
                  if mods else "High heat risk for the next 12 hours. Keep walks short and shaded, or skip.")
    rows = "".join(
        f"<tr><th scope='row'>{_hour(r.time)}</th><td>{_temp(r.temp_c, unit)}</td><td>{r.rh:.0f}%</td>"
        f"<td>{_pill(r.risk_15)}</td><td>{_pill(r.risk_30)}</td><td>{_pill(r.risk_60)}</td></tr>"
        for r in table.itertuples()
    )
    return f"""
<style>
  .c-walkplan {{ font-family: "Rubik", sans-serif; }}
  .c-walkplan__answer {{ font: 400 1.6rem/1.25 "Londrina Solid", sans-serif; margin: 0 0 0.75rem; }}
  .c-walkplan__scroll {{ overflow-x: auto; }}
  .c-walkplan table {{ border-collapse: collapse; width: 100%; font-size: 0.95rem; }}
  .c-walkplan th, .c-walkplan td {{ padding: 0.45rem 0.6rem; text-align: left; white-space: nowrap;
    border-bottom: 1px solid color-mix(in srgb, currentColor 18%, transparent); }}
  .c-walkplan thead th {{ font-weight: 500; font-size: 0.8rem; letter-spacing: 0.04em; opacity: 0.7; }}
  .c-walkplan__pill {{ display: inline-block; min-width: 5.5em; padding: 0.15em 0.7em; border-radius: 999px;
    background: var(--risk); color: #f2ead3; font-size: 0.85rem; text-align: center; }}
</style>
<div class="c-walkplan">
  <p class="c-walkplan__answer">{html.escape(answer)}</p>
  <div class="c-walkplan__scroll">
  <table>
    <thead><tr><th scope="col">Hour (local time)</th><th scope="col">Temp</th><th scope="col">Humidity</th>
      <th scope="col">15 min after</th><th scope="col">30 min after</th><th scope="col">60 min after</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
  {_key_html(unit)}
</div>"""


def _key_html(unit: str) -> str:
    """What Low / Moderate / High mean, with the CTM thresholds in the chosen unit."""
    lo, hi = hm.MODERATE_AT, hm.HIGH_ABOVE

    def t(c):
        return f"{c * 9 / 5 + 32:.1f}°F" if unit == "°F" else f"{c:.1f}°C"

    items = [
        ("Low", f"Predicted core temperature below {t(lo)}.",
         "Your dog should cool down normally. Fine for a walk with the usual water and breaks."),
        ("Moderate", f"Predicted core temperature {t(lo)} – {t(hi)}.",
         "Your dog stays warm for longer after exercise. Keep it shorter and slower, stick to shade, "
         "bring water and watch for heavy panting."),
        ("High", f"Predicted core temperature above {t(hi)}.",
         "Heat stress is likely. Skip the walk or keep it to a quick, shaded potty break."),
    ]
    rows = "".join(
        f"<li>{_pill(name)}<span><strong>{html.escape(rule)}</strong> {html.escape(advice)}</span></li>"
        for name, rule, advice in items
    )
    return f"""
  <div class="c-walkplan__key">
    <p class="c-walkplan__keytitle">How to read this</p>
    <ul>{rows}</ul>
    <p>Each column shows how warm your dog is likely to be 15, 30 and 60 minutes after about
    15 minutes of hard exercise. Longer exercise can warm your dog more. Dogs are always warm right after exercise, so Moderate at
    15 minutes is common. What matters most is whether it drops to Low by 60 minutes; the best
    times above use the {HEADLINE_RECOVERY}-minute column.</p>
    <p class="c-walkplan__caution"><strong>Use caution if you see High in the 15 or 30 minute
    column.</strong> It means that after 15 or 30 minutes of recovery, your dog is experiencing
    heat stress.</p>
  </div>
  <style>
    .c-walkplan__key {{ margin-top: 1.25rem; font-size: 0.9rem; line-height: 1.5; }}
    .c-walkplan__keytitle {{ font-weight: 500; margin: 0 0 0.5rem; }}
    .c-walkplan__key ul {{ list-style: none; margin: 0 0 0.75rem; padding: 0; display: grid; gap: 0.6rem; }}
    .c-walkplan__key li {{ display: grid; grid-template-columns: auto 1fr; gap: 0.75rem; align-items: start; }}
    .c-walkplan__key strong {{ font-weight: 500; }}
    .c-walkplan__key p {{ margin: 0; opacity: 0.85; }}
    .c-walkplan__key .c-walkplan__caution {{ margin-top: 0.6rem; opacity: 1;
      padding-left: 0.75rem; border-left: 3px solid {hm.RISK_COLORS["High"]}; }}
  </style>"""


def render() -> None:
    with st.container(key="walk-planner"):
        st.subheader("Is it too hot for a walk?")
        st.write("Enter your city to see a dog's heat risk for the next 12 hours. Each hour shows the risk "
                 "at 15, 30 and 60 minutes after finishing about 15 minutes of hard exercise.")
        city = st.text_input("Your city", placeholder="Syracuse, NY", key="walk-city")
        c1, c2, c3 = st.columns([2, 1, 1])
        weight_unit = c2.radio("Weight in", ["kg", "lb"], horizontal=True, key="walk-weight-unit")
        if weight_unit == "lb":
            # Its own key, so switching units starts from the notebook dog's weight in that unit.
            weight_lb = c1.number_input("Your dog's weight (lb)", min_value=4.0, max_value=200.0,
                                        value=round(DEFAULT_WEIGHT_KG * LB_PER_KG, 1), step=1.0,
                                        key="walk-weight-lb")
            weight_kg = weight_lb / LB_PER_KG
        else:
            weight_kg = c1.number_input("Your dog's weight (kg)", min_value=2.0, max_value=90.0,
                                        value=DEFAULT_WEIGHT_KG, step=0.5, key="walk-weight")
        unit = c3.radio("Temperature", ["°F", "°C"], horizontal=True, key="walk-unit")

        if not city.strip():
            st.caption(DISCLAIMER)
            return
        try:
            places = _places(city.strip())
        except Exception:
            st.error("Couldn't reach the place search just now. Try again in a minute.")
            return
        if not places:
            st.warning(f"No place called “{city.strip()}” found. Try just the city name, or add the state or country.")
            return
        labels = [hm.place_label(p) for p in places]
        choice = st.selectbox("Which one?", labels, key="walk-place") if len(places) > 1 else labels[0]
        place = places[labels.index(choice)]

        try:
            weather = _weather(place["latitude"], place["longitude"])
        except Exception:
            st.error("Couldn't get the weather forecast just now. Try again in a minute.")
            return
        table = hm.forecast(_model(), weather, weight_kg=weight_kg, length_cm=DEFAULT_LENGTH_CM,
                            activity=DEFAULT_ACTIVITY)
        st.html(_results_html(table, unit))
        st.caption(f"Forecast for {choice}. Hours are shown in local time there. Weather data by [Open-Meteo.com](https://open-meteo.com/). {DISCLAIMER}")
