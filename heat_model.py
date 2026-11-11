"""Dog heat-risk forecast: your IST707 final project model, outside the notebook.

The training steps are the notebook's (Divya_duraisamy_final_project_IST707.ipynb), in order:
  1. read data/MWD_heat_strain_dataset.csv (46 rows from O'Brien & Berglund's military working dog
     study), make the number columns numeric, fill gaps (mean / most frequent)
  2. baseline Random Forests (300 trees) on the real rows, used only to make synthetic rows
  3. 75 synthetic dogs x 7 activities = 525 rows (seed 42), seasonal weather ranges
  4. real + synthetic rows -> one-hot encode -> StandardScaler -> final Random Forests (500 trees)
     for core temperature (Tc) 15, 30 and 60 minutes into recovery
Then the live part: hourly temperature and humidity for a place (Open-Meteo, free, no key) ->
predicted Tc for each hour -> Low / Moderate / High using the CTM thresholds (38.7 / 40.1 C).

Guidance only: the model has seen three months of the year and a small group of dogs.

    uv run python heat_model.py "Syracuse, NY"     # try it from the command line
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parent / "data" / "MWD_heat_strain_dataset.csv"

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# CTM thresholds for core temperature (C)
MODERATE_AT = 38.7
HIGH_ABOVE = 40.1
RISK_ORDER = ["Low", "Moderate", "High"]
RISK_COLORS = {"Low": "#515425", "Moderate": "#bf7362", "High": "#af3f27"}

# The training data only has October, March and August; other months use the closest season.
MONTH_MAPPING = {
    1: "MAR", 2: "MAR", 3: "MAR",
    4: "AUG", 5: "AUG", 6: "AUG",
    7: "AUG", 8: "AUG", 9: "OCT",
    10: "OCT", 11: "OCT", 12: "MAR",
}

ACTIVITIES = ["OB", "BS", "CA", "OC", "SC", "GF", "VS"]
SEASONAL_ENV = {
    "OCT": {"AirTemp_mean": (10, 18), "RH_mean": (40, 70)},
    "MAR": {"AirTemp_mean": (5, 15), "RH_mean": (50, 80)},
    "AUG": {"AirTemp_mean": (22, 32), "RH_mean": (20, 40)},
}
NUMERIC_COLS = [
    "Weight_kg", "Length_cm", "AirTemp_mean", "AirTemp_sd", "RH_mean", "RH_sd",
    "Tc_EndEx", "Tc_Peak", "Tc_5min", "Tc_10min", "Tc_15min", "Tc_30min", "Tc_60min",
    "CTM_5min", "CTM_10min", "CTM_15min", "CTM_30min", "CTM_60min",
    "CTM_diff_30", "CTM_diff_60", "HeatStress",
]
REAL_COLS = [
    "DogID", "Date", "Month", "Activity", "Weight_kg", "Length_cm",
    "AirTemp_mean", "AirTemp_sd", "RH_mean", "RH_sd", "Tc_15min", "Tc_30min", "Tc_60min",
]


@dataclass
class HeatModel:
    rf_15: RandomForestRegressor
    rf_30: RandomForestRegressor
    rf_60: RandomForestRegressor
    scaler: StandardScaler
    feature_columns: list[str]
    mean_weight_kg: float
    mean_length_cm: float


def load_data(path: Path = DATA) -> pd.DataFrame:
    df = pd.read_csv(path)
    df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
    num_cols = df.select_dtypes(include="number").columns
    cat_cols = df.select_dtypes(include=["object", "str"]).columns
    df[num_cols] = SimpleImputer(strategy="mean").fit_transform(df[num_cols])
    df[cat_cols] = SimpleImputer(strategy="most_frequent").fit_transform(df[cat_cols])
    return df


def train(path: Path = DATA) -> HeatModel:
    """Train the three recovery models exactly as the notebook does."""
    df = load_data(path)

    # Real rows only: features, split, baseline models for synthetic generation
    df_model = df.drop(columns=["HeatStress", "Tc_EndEx", "Tc_Peak", "CTM_5min", "CTM_10min",
                                "CTM_15min", "CTM_30min", "CTM_60min", "CTM_diff_30", "CTM_diff_60"])
    df_encoded = pd.get_dummies(df_model, columns=["Activity", "Month", "CTM_accept_30", "CTM_accept_60"],
                                drop_first=True)
    X = df_encoded.drop(columns=["DogID", "Date", "Tc_5min", "Tc_10min", "Tc_15min", "Tc_30min", "Tc_60min"])
    y_15, y_30, y_60 = df_encoded["Tc_15min"], df_encoded["Tc_30min"], df_encoded["Tc_60min"]
    real_features = X.columns.tolist()

    X_train, _, y_train_15, y_test_15 = train_test_split(X, y_15, test_size=0.2, random_state=42)
    y_train_30 = y_30.loc[y_train_15.index]
    y_train_60 = y_60.loc[y_train_15.index]
    X_train_scaled = StandardScaler().fit_transform(X_train)

    baselines = []
    for y in (y_train_15, y_train_30, y_train_60):
        model = RandomForestRegressor(n_estimators=300, random_state=42)
        model.fit(X_train_scaled, y)
        baselines.append(model)

    scaler_synth = StandardScaler().fit(X_train)

    def synth_row(weight, length, env, activity, month):
        row = {"Weight_kg": weight, "Length_cm": length, **env, "Activity": activity, "Month": month,
               "CTM_accept_30": "Accept", "CTM_accept_60": "Accept"}
        frame = pd.get_dummies(pd.DataFrame([row])).reindex(columns=real_features, fill_value=0)
        return scaler_synth.transform(frame)

    # The notebook predicts one row at a time; here the random draws happen in exactly the same
    # order (predicting uses no randomness), and the predictions are made in one batch afterwards.
    np.random.seed(42)
    synthetic, scaled_rows, noises = [], [], []
    for _ in range(75):
        dog_id = f"SYN_Dog_{np.random.randint(1000, 9999)}"
        month = np.random.choice(["OCT", "MAR", "AUG"])
        weight = np.random.normal(df["Weight_kg"].mean(), df["Weight_kg"].std())
        length = np.random.normal(df["Length_cm"].mean(), df["Length_cm"].std())
        for act in ACTIVITIES:
            lo_t, hi_t = SEASONAL_ENV[month]["AirTemp_mean"]
            lo_h, hi_h = SEASONAL_ENV[month]["RH_mean"]
            env = {
                "AirTemp_mean": np.random.uniform(lo_t, hi_t),
                "AirTemp_sd": np.random.uniform(0.3, 1.5),
                "RH_mean": np.random.uniform(lo_h, hi_h),
                "RH_sd": np.random.uniform(1, 8),
            }
            scaled_rows.append(synth_row(weight, length, env, act, month)[0])
            noises.append([np.random.normal(0, 0.15) for _ in baselines])
            synthetic.append({"DogID": dog_id, "Date": "SYN", "Month": month, "Activity": act,
                              "Weight_kg": weight, "Length_cm": length, **env})
    scaled_rows, noises = np.array(scaled_rows), np.array(noises)
    for k, (target, model) in enumerate(zip(("Tc_15min", "Tc_30min", "Tc_60min"), baselines)):
        values = np.round(model.predict(scaled_rows) + noises[:, k], 2)
        for row, value in zip(synthetic, values):
            row[target] = value

    # Real + synthetic -> final models
    df_full = pd.concat([df[REAL_COLS].copy(), pd.DataFrame(synthetic)], ignore_index=True)
    full_encoded = pd.get_dummies(df_full, columns=["Activity", "Month"], drop_first=True)
    X_full = full_encoded.drop(columns=["DogID", "Date", "Tc_15min", "Tc_30min", "Tc_60min"])
    scaler_full = StandardScaler()
    X_full_scaled = scaler_full.fit_transform(X_full)

    train_idx, _ = train_test_split(np.arange(len(X_full_scaled)), test_size=0.2, random_state=42)
    finals = []
    for target in ("Tc_15min", "Tc_30min", "Tc_60min"):
        model = RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1)
        model.fit(X_full_scaled[train_idx], full_encoded[target].iloc[train_idx])
        finals.append(model)

    return HeatModel(*finals, scaler=scaler_full, feature_columns=X_full.columns.tolist(),
                     mean_weight_kg=float(df["Weight_kg"].mean()), mean_length_cm=float(df["Length_cm"].mean()))


def classify_risk(tc: float) -> str:
    if tc < MODERATE_AT:
        return "Low"
    if tc <= HIGH_ABOVE:
        return "Moderate"
    return "High"


# --- Open-Meteo -----------------------------------------------------------------------------------

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
    "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}


def find_places(query: str, count: int = 8) -> list[dict]:
    """Places matching "City" or "City, State/Country" (Open-Meteo geocoding), best first."""
    parts = [p.strip() for p in query.split(",") if p.strip()]
    if not parts:
        return []
    resp = requests.get(GEOCODE_URL, params={"name": parts[0], "count": count, "language": "en", "format": "json"},
                        timeout=10)
    resp.raise_for_status()
    places = resp.json().get("results") or []
    if len(parts) > 1:
        want = " ".join(parts[1:]).lower()
        want_full = US_STATES.get(want.upper(), want).lower()

        def matches(p):
            fields = [p.get("admin1", ""), p.get("country", ""), p.get("country_code", "")]
            return any(want_full in f.lower() or want == f.lower() for f in fields if f)

        filtered = [p for p in places if matches(p)]
        places = filtered or places
    return places


def place_label(p: dict) -> str:
    return ", ".join(x for x in (p.get("name"), p.get("admin1"), p.get("country")) if x)


def hourly_weather(lat: float, lon: float, hours: int = 12) -> pd.DataFrame:
    """The next `hours` hours (local time) of temperature (C) and relative humidity (%)."""
    resp = requests.get(FORECAST_URL, params={
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m",
        "forecast_hours": hours, "timezone": "auto",
    }, timeout=10)
    resp.raise_for_status()
    h = resp.json()["hourly"]
    return pd.DataFrame({"time": pd.to_datetime(h["time"]), "temp_c": h["temperature_2m"],
                         "rh": h["relative_humidity_2m"]})


# --- Forecast -------------------------------------------------------------------------------------

def forecast(model: HeatModel, weather: pd.DataFrame, weight_kg: float | None = None,
             length_cm: float | None = None, activity: str = "OB") -> pd.DataFrame:
    """Predicted recovery core temperature and risk for each hour of `weather`."""
    rows = []
    for t, temp, rh in weather[["time", "temp_c", "rh"]].itertuples(index=False):
        rows.append({
            "Weight_kg": weight_kg or model.mean_weight_kg,
            "Length_cm": length_cm or model.mean_length_cm,
            "AirTemp_mean": temp, "AirTemp_sd": 0.8,
            "RH_mean": rh, "RH_sd": 3.0,
            "Activity": activity,
            "Month": MONTH_MAPPING[t.month],
        })
    frame = pd.get_dummies(pd.DataFrame(rows)).reindex(columns=model.feature_columns, fill_value=0)
    scaled = model.scaler.transform(frame)
    out = weather.copy()
    out["tc_15"] = model.rf_15.predict(scaled)
    out["tc_30"] = model.rf_30.predict(scaled)
    out["tc_60"] = model.rf_60.predict(scaled)
    for k in ("15", "30", "60"):
        out[f"risk_{k}"] = out[f"tc_{k}"].map(classify_risk)
    # The walk answer uses the most cautious of the three recovery times.
    out["risk"] = out[["risk_15", "risk_30", "risk_60"]].apply(
        lambda r: max(r, key=RISK_ORDER.index), axis=1)
    return out


def best_windows(table: pd.DataFrame, level: str = "Low") -> list[tuple[datetime, datetime]]:
    """Runs of consecutive hours at `level`, as (first hour, last hour + 1h)."""
    runs, start = [], None
    times = list(table["time"])
    for i, risk in enumerate(table["risk"]):
        if risk == level and start is None:
            start = times[i]
        if risk != level and start is not None:
            runs.append((start, times[i]))
            start = None
    if start is not None:
        runs.append((start, times[-1] + pd.Timedelta(hours=1)))
    return runs


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "Syracuse, NY"
    places = find_places(query)
    if not places:
        sys.exit(f"No place found for {query!r}")
    place = places[0]
    print("Place:", place_label(place))
    model = train()
    table = forecast(model, hourly_weather(place["latitude"], place["longitude"]))
    print(table[["time", "temp_c", "rh", "tc_15", "tc_30", "tc_60", "risk"]].round(2).to_string(index=False))
