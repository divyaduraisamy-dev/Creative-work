"""Precompute the dog heat model into a small answer table for the in-page walk planner.

The plain site (docs/) can't run Python, so this runs the real model from heat_model.py over a
grid of temperatures, humidities, dog weights and seasons and saves the predicted core
temperatures 15, 30 and 60 minutes after exercise. The page's JavaScript (CustomWalkForecast in
interactions.js) looks up each forecast hour in the table, blending the nearest grid points.

The model only splits on temperature, humidity and weight inside the ranges it was trained on,
so outside them its answer doesn't change: the grid covers exactly those ranges, and the page
uses the nearest edge beyond them, which gives the same answer as the model.

Length and activity are fixed at the notebook's example dog (55 cm, obedience work), the same
as the Streamlit planner.

Run it after changing the model or the dataset:
    uv run python build_walk_table.py           # writes the table and checks it
    uv run python build_walk_table.py --check   # only checks the existing table
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import heat_model as hm

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ui-scrapbook" / "custom-features" / "assets" / "walk-table.json"

LENGTH_CM = 55.0
ACTIVITY = "OB"
TEMP_SD, RH_SD = 0.8, 3.0  # the same fixed spreads heat_model.forecast uses
SEASONS = ["MAR", "AUG", "OCT"]


def split_range(model: hm.HeatModel, column: str) -> tuple[float, float]:
    """Lowest and highest split the forests make on one input, in real units."""
    i = model.feature_columns.index(column)
    lo, hi = np.inf, -np.inf
    for forest in (model.rf_15, model.rf_30, model.rf_60):
        for tree in forest.estimators_:
            t = tree.tree_
            v = t.threshold[t.feature == i]
            if v.size:
                lo, hi = min(lo, v.min()), max(hi, v.max())
    return lo * model.scaler.scale_[i] + model.scaler.mean_[i], hi * model.scaler.scale_[i] + model.scaler.mean_[i]


def axis(lo: float, hi: float, step: float) -> np.ndarray:
    """Grid points from just below `lo` to just above `hi`, `step` apart."""
    start, stop = np.floor(lo / step) * step, np.ceil(hi / step) * step
    return np.round(np.arange(start, stop + step / 2, step), 3)


def predict(model: hm.HeatModel, temp, rh, weight, season) -> np.ndarray:
    """Core temperatures (n x 3: 15, 30, 60 min) straight from the model."""
    frame = pd.DataFrame({
        "Weight_kg": weight, "Length_cm": LENGTH_CM,
        "AirTemp_mean": temp, "AirTemp_sd": TEMP_SD,
        "RH_mean": rh, "RH_sd": RH_SD,
        "Activity": ACTIVITY, "Month": season,
    })
    frame = pd.get_dummies(frame).reindex(columns=model.feature_columns, fill_value=0)
    scaled = model.scaler.transform(frame)
    return np.column_stack([m.predict(scaled) for m in (model.rf_15, model.rf_30, model.rf_60)])


# The finest spacing worth adding: Open-Meteo gives temperature to 0.1 C and humidity in whole %.
RESOLUTION = {"temp": 0.1, "rh": 1.0, "weight": 0.5}
AXIS_ORDER = ("temp", "rh", "weight")


def grid_predict(model: hm.HeatModel, axes: dict[str, np.ndarray], season: str) -> np.ndarray:
    """Model answers on the full grid (temp x rh x weight x 3) for one season."""
    t, r, w = np.meshgrid(axes["temp"], axes["rh"], axes["weight"], indexing="ij")
    return predict(model, t.ravel(), r.ravel(), w.ravel(), season).reshape(*t.shape, 3)


def refine(model: hm.HeatModel, axes: dict[str, np.ndarray], name: str, tol: float, passes: int = 8) -> None:
    """Add grid points along one axis where the model jumps between neighbouring points.

    The forests are step functions: in places the answer jumps by half a degree within 0.1 C.
    Blending across a jump gives a value in between, which can flip Moderate/High. So each gap is
    halved (down to RESOLUTION) wherever the model at its middle is more than `tol` from the blend,
    checked across a sample of the other two inputs and all seasons."""
    sample = {k: v for k, v in axes.items()}
    for k in AXIS_ORDER:
        if k != name and len(axes[k]) > 8:
            sample[k] = np.unique(np.concatenate([axes[k][::3], axes[k][-1:]]))
    res = RESOLUTION[name]
    for _ in range(passes):
        g = axes[name]
        a, b = g[:-1], g[1:]
        mid = np.round((a + b) / 2 / res) * res
        ok = (mid > a + 1e-9) & (mid < b - 1e-9)
        if not ok.any():
            break
        i = np.nonzero(ok)[0]
        mids = mid[ok]
        f = (mids - a[ok]) / (b[ok] - a[ok])
        err = np.zeros(len(mids))
        pos = AXIS_ORDER.index(name)
        for season in SEASONS:
            ends = np.moveaxis(grid_predict(model, {**sample, name: g}, season), pos, 0)
            middle = np.moveaxis(grid_predict(model, {**sample, name: mids}, season), pos, 0)
            shape = (-1,) + (1,) * (ends.ndim - 1)
            blend = ends[i] * (1 - f).reshape(shape) + ends[i + 1] * f.reshape(shape)
            err = np.maximum(err, np.abs(middle - blend).reshape(len(mids), -1).max(axis=1))
        split = mids[err > tol]
        if not split.size:
            break
        axes[name] = np.round(np.unique(np.concatenate([g, split])), 3)


def build(model: hm.HeatModel, steps: dict[str, float], tol: float) -> dict:
    axes = {
        "temp": axis(*split_range(model, "AirTemp_mean"), steps["temp"]),
        "rh": axis(*split_range(model, "RH_mean"), steps["rh"]),
        "weight": axis(*split_range(model, "Weight_kg"), steps["weight"]),
    }
    if tol > 0:
        for name in AXIS_ORDER:
            refine(model, axes, name, tol)
    t, r, w = np.meshgrid(axes["temp"], axes["rh"], axes["weight"], indexing="ij")
    values = []
    for season in SEASONS:
        tc = predict(model, t.ravel(), r.ravel(), w.ravel(), season)
        values.append(np.round(tc * 100).astype(int))  # hundredths of a degree C
    # Layout: values[season][((temp * nRH) + rh) * nWeight + weight][recovery 15/30/60]
    return {
        "about": "Dog heat model from IST707, precomputed by build_walk_table.py. Core temperature "
                 "in hundredths of a degree C, 15/30/60 minutes after exercise.",
        "length_cm": LENGTH_CM, "activity": ACTIVITY,
        "moderate_at": hm.MODERATE_AT, "high_above": hm.HIGH_ABOVE,
        "month_season": {str(k): v for k, v in hm.MONTH_MAPPING.items()},
        "seasons": SEASONS,
        "temp": axes["temp"].tolist(), "rh": axes["rh"].tolist(), "weight": axes["weight"].tolist(),
        "values": [v.ravel().tolist() for v in values],
    }


def lookup(table: dict, temp, rh, weight, season) -> np.ndarray:
    """The same blend the page's JavaScript does (clamped trilinear), for checking."""
    grids = [np.array(table[k]) for k in ("temp", "rh", "weight")]
    shape = [len(g) for g in grids]
    vals = np.array(table["values"][table["seasons"].index(season)]).reshape(*shape, 3) / 100
    idx, frac = [], []
    for g, x in zip(grids, (temp, rh, weight)):
        x = np.clip(np.asarray(x, float), g[0], g[-1])
        i = np.clip(np.searchsorted(g, x, side="right") - 1, 0, len(g) - 2)
        idx.append(i)
        frac.append((x - g[i]) / (g[i + 1] - g[i]))
    out = 0
    for dt in (0, 1):
        for dr in (0, 1):
            for dw in (0, 1):
                wgt = ((frac[0] if dt else 1 - frac[0]) * (frac[1] if dr else 1 - frac[1])
                       * (frac[2] if dw else 1 - frac[2]))
                out = out + wgt[:, None] * vals[idx[0] + dt, idx[1] + dr, idx[2] + dw]
    return out


def check(model: hm.HeatModel, table: dict, n: int = 20000, seed: int = 7, weight_kg: float | None = None) -> dict:
    """Compare the table with the model at random hours (wider than the grid, to test the edges).

    With `weight_kg`, every hour uses that dog weight (the planner's default dog is 30 kg)."""
    rng = np.random.default_rng(seed)
    temp = rng.uniform(-10, 42, n)
    rh = rng.uniform(5, 100, n)
    weight = np.full(n, weight_kg) if weight_kg else rng.uniform(5, 70, n)
    season = rng.choice(SEASONS, n)
    direct = np.zeros((n, 3))
    looked = np.zeros((n, 3))
    for s in SEASONS:
        m = season == s
        direct[m] = predict(model, temp[m], rh[m], weight[m], s)
        looked[m] = lookup(table, temp[m], rh[m], weight[m], s)
    gap = np.abs(direct - looked)
    label = np.vectorize(hm.classify_risk)
    differ = label(direct) != label(looked)
    return {"hours checked": n, "largest gap (C)": round(float(gap.max()), 3),
            "typical gap (C)": round(float(np.median(gap)), 3),
            "95% of gaps under (C)": round(float(np.quantile(gap, 0.95)), 3),
            "labels that differ (%)": round(100 * float(differ.mean()), 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only check the existing table")
    parser.add_argument("--temp-step", type=float, default=1.0)
    parser.add_argument("--rh-step", type=float, default=4.0)
    parser.add_argument("--weight-step", type=float, default=3.0)
    parser.add_argument("--tolerance", type=float, default=0.02,
                        help="add grid points where blending is off by more than this (C); 0 = even grid only")
    args = parser.parse_args()

    model = hm.train()
    if args.check:
        table = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        table = build(model, {"temp": args.temp_step, "rh": args.rh_step, "weight": args.weight_step},
                      args.tolerance)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(table, separators=(",", ":")), encoding="utf-8")
        sizes = f"{len(table['temp'])} temps x {len(table['rh'])} humidities x {len(table['weight'])} weights x 3 seasons"
        print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB, {sizes})")
    for title, kwargs in (("any dog, 5-70 kg", {}), ("the 30 kg default dog", {"weight_kg": 30.0})):
        print(f"check against the model ({title}):")
        for k, v in check(model, table, **kwargs).items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
