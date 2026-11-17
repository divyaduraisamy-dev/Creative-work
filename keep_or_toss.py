"""Build the Keep or Toss app pages from keep_or_toss_content.py (run by build_static.py).

    divyaduraisamy.org/keep-or-toss/            home: search, food groups, every food
    divyaduraisamy.org/keep-or-toss/<food>/     one page per food
    divyaduraisamy.org/keep-or-toss/basics/     the rules
    divyaduraisamy.org/keep-or-toss/game/       the "Keep or Toss?" game

Storage times are read from USDA FoodKeeper (data/foodkeeper.json) while the site builds, so no
number is typed twice. Before anything is written, every food, rule and game round is checked:
required parts, sources, FoodKeeper numbers. Problems stop the build with a clear message;
warnings (dashes, stand-in drawings, notes to review) are printed.

The pages share the site's header, colour switch, password page and footer (build_static.py
render_page). The app's own styles and script are ui-scrapbook/custom-features/keep-or-toss.css
and keep-or-toss.js. All visible words come from the content file; the script gets the words it
needs as data in the page.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Callable

import keep_or_toss_content as c

ROOT = Path(__file__).resolve().parent
FOODKEEPER = ROOT / "data" / "foodkeeper.json"
FEATURES = ROOT / "ui-scrapbook" / "custom-features"
ART = FEATURES / "assets" / "keep-or-toss"
STAND_INS = ART / "stand-ins"
CSS_FILE = FEATURES / "keep-or-toss.css"
JS_FILE = FEATURES / "keep-or-toss.js"
RESERVED = {"basics", "game"}  # page names a food can't use


def esc(text: str) -> str:
    return html.escape(text, quote=True)


# ---------------------------------------------------------------------------------------------
# USDA FoodKeeper
# ---------------------------------------------------------------------------------------------
@cache
def foodkeeper() -> tuple[str, dict[int, dict]]:
    """(version line, products by number). Each product is a dict of its columns."""
    if not FOODKEEPER.exists():
        raise SystemExit(f"Keep or Toss: {FOODKEEPER.relative_to(ROOT)} is missing. Download the FSIS "
                         "FoodKeeper JSON (see data/README.md) and save it there.")
    data = json.loads(FOODKEEPER.read_text(encoding="utf-8"))
    sheets = {s["name"]: [{k: v for cell in row for k, v in cell.items()} for row in s["data"]]
              for s in data["sheets"]}
    current = next((v for v in sheets["Version"] if v.get("Current_Version") == "Yes"), sheets["Version"][-1])
    version = f"version {current['Data_Version_Number']:g}, modified {current['Modified_Date']}"
    return version, {int(p["ID"]): p for p in sheets["Product"]}


def fk_name(product: int) -> str:
    p = foodkeeper()[1][product]
    return p["Name"].strip() + (f" ({p['Name_subtitle'].strip()})" if p.get("Name_subtitle") else "")


def number(value) -> str:
    return f"{value:g}"


def time_text(t: c.FK | c.Hand) -> str:
    """The storage time as words, e.g. "About 3 to 5 days once it's ripe"."""
    T = c.TEXT
    if isinstance(t, c.Hand):
        words = t.text
    else:
        p = foodkeeper()[1][t.product]
        low, high, metric = p.get(f"{t.field}_Min"), p.get(f"{t.field}_Max"), p.get(f"{t.field}_Metric")
        special = {"When Ripe": "time_when_ripe", "Indefinitely": "time_indefinitely",
                   "Not Recommended": "time_not_recommended", "Package use-by date": "time_package"}
        if metric in special:
            words = T[special[metric]]
        else:
            one, many = T["time_units"][metric]
            if low == high or high is None:
                words = T["time_one"].format(min=number(low), unit=one if low == 1 else many)
            else:
                words = T["time_range"].format(min=number(low), max=number(high), unit=many)
    return f"{words} {t.when}".strip()


# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------
@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    review: list[str] = field(default_factory=list)
    stand_ins: list[str] = field(default_factory=list)


DASHES = re.compile(r"[‒–—―]|(?<=[A-Za-z])-(?=[A-Za-z])")


def visible_strings(value, where: str):
    """Every piece of visible text in a content value, with where it came from."""
    if isinstance(value, str):
        yield where, value
    elif isinstance(value, dict):
        for k, v in value.items():
            if k != "drawing":  # a file name, not words on the page
                yield from visible_strings(v, f"{where}.{k}")
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            yield from visible_strings(v, f"{where}[{i}]")
    elif isinstance(value, c.Fact):
        yield where, value.text
    elif isinstance(value, (c.Plan, c.Mold, c.Rule, c.Scenario, c.Food)):
        skip = {"slug", "category", "place", "action", "answer", "source", "sources", "food", "review"}
        for k, v in vars(value).items():
            if k not in skip:
                yield from visible_strings(v, f"{where}.{k}")
    elif isinstance(value, c.Hand):
        yield where, value.text
        yield where, value.when
    elif isinstance(value, c.FK):
        yield where, value.when


def fact_sources(facts) -> list[str]:
    out = []
    for f in facts:
        out += f.sources
    return out


def food_sources(food: c.Food) -> list[str]:
    """Source keys for a food, in the order they first appear (FoodKeeper first when used)."""
    keys = []
    if any(isinstance(p.time, c.FK) for p in food.plans):
        keys.append("foodkeeper")
    for p in food.plans:
        if isinstance(p.time, c.Hand):
            keys.append(p.time.source)
        keys += fact_sources(p.how)
    keys += fact_sources(food.use_soon) + fact_sources(food.toss)
    if food.mold:
        keys += fact_sources(food.mold.text)
    keys += fact_sources(food.ideas) + fact_sources(food.safety)
    return list(dict.fromkeys(keys))


def check(report: Report) -> None:
    E, W, R = report.errors.append, report.warnings.append, report.review.append
    _, products = foodkeeper()
    slugs = [f.slug for f in c.FOODS]
    for s in {s for s in slugs if slugs.count(s) > 1}:
        E(f"two foods have the slug '{s}'")
    if not c.FOODS:
        E("FOODS is empty")

    def fact_check(facts, where):
        for i, f in enumerate(facts):
            if not f.sources:
                E(f"{where}[{i}] (\"{f.text[:40]}\") has no source")
            for key in f.sources:
                if key not in c.SOURCES:
                    E(f"{where}[{i}] uses source '{key}', which isn't in SOURCES")

    for food in c.FOODS:
        w = f"food '{food.slug}'"
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", food.slug):
            E(f"{w}: the slug can only have lowercase letters, numbers and single hyphens")
        if food.slug in RESERVED or food.slug == c.WORK_ENTRY["drawing"]:
            E(f"{w}: '{food.slug}' is used by the app itself; pick another slug")
        if not food.name:
            E(f"{w}: add a name")
        if food.category not in c.CATEGORIES:
            E(f"{w}: category '{food.category}' isn't in CATEGORIES ({', '.join(c.CATEGORIES)})")
        if not food.alt:
            E(f"{w}: add alt (what the drawing shows, for screen readers)")
        if not 2 <= len(food.plans) <= 3:
            (E if not food.plans else W)(f"{w}: has {len(food.plans)} plans (2 or 3 is the goal)")
        for i, plan in enumerate(food.plans):
            pw = f"{w} plans[{i}]"
            if plan.place not in c.TEXT["places"]:
                E(f"{pw}: place '{plan.place}' should be COUNTER, PANTRY, FRIDGE or FREEZER")
            if not plan.choice:
                E(f"{pw}: add the choice text")
            if isinstance(plan.time, c.FK):
                p = products.get(plan.time.product)
                if not p:
                    E(f"{pw}: FoodKeeper has no product {plan.time.product}")
                elif f"{plan.time.field}_Metric" not in p:
                    E(f"{pw}: '{plan.time.field}' isn't a FoodKeeper time field")
                elif not p.get(f"{plan.time.field}_Metric"):
                    E(f"{pw}: FoodKeeper {plan.time.product} ({fk_name(plan.time.product)}) has no "
                      f"{plan.time.field} time")
                elif p[f"{plan.time.field}_Metric"] not in c.TEXT["time_units"] and p[f"{plan.time.field}_Metric"] not in (
                        "When Ripe", "Indefinitely", "Not Recommended", "Package use-by date"):
                    E(f"{pw}: FoodKeeper unit '{p[f'{plan.time.field}_Metric']}' has no words in TEXT['time_units']")
            elif isinstance(plan.time, c.Hand):
                if plan.time.source not in c.SOURCES:
                    E(f"{pw}: the time's source '{plan.time.source}' isn't in SOURCES")
                R(f"{food.name}: \"{plan.choice}\" uses a hand written time ({plan.time.text}, "
                  f"{c.SOURCES.get(plan.time.source, c.Source('?', '?', '?')).publisher}), not FoodKeeper")
            else:
                E(f"{pw}: time should be FK(...) or Hand(...)")
            fact_check(plan.how, f"{pw}.how")
        for part in ("use_soon", "toss", "ideas", "safety"):
            fact_check(getattr(food, part), f"{w}.{part}")
        for part, label in (("use_soon", "still fine, use it soon"), ("toss", "toss it"), ("ideas", "use it up")):
            if not getattr(food, part):
                R(f"{food.name}: no sourced \"{label}\" points yet")
        if food.mold:
            if food.mold.action not in (c.CUT, c.TOSS):
                E(f"{w}.mold: action should be CUT or TOSS")
            fact_check(food.mold.text, f"{w}.mold.text")
            if not food.mold.text:
                E(f"{w}.mold: add the advice text")
        elif food.mold_needed:
            R(f"{food.name}: no sourced mold advice yet (the FSIS mold chart has no row for it)")
        if not food_sources(food):
            E(f"{w}: needs at least one source")
        for note in food.review:
            R(f"{food.name}: {note}")

    for i, rule in enumerate(c.BASICS):
        if not rule.text:
            E(f"BASICS[{i}] ('{rule.title}') has no text")
        fact_check(rule.text, f"BASICS[{i}]")
    if not c.BASICS:
        E("BASICS is empty")

    for i, s in enumerate(c.SCENARIOS):
        sw = f"SCENARIOS[{i}]"
        if s.food not in slugs:
            E(f"{sw}: food '{s.food}' isn't in FOODS")
        if s.answer not in (c.KEEP, c.CUT, c.TOSS):
            E(f"{sw}: answer should be KEEP, CUT or TOSS")
        if s.source not in c.SOURCES:
            E(f"{sw}: source '{s.source}' isn't in SOURCES")
        if not s.situation or not s.reason:
            E(f"{sw}: add the situation and the reason")
    if len(c.SCENARIOS) < c.GAME_ROUNDS:
        W(f"only {len(c.SCENARIOS)} game rounds; each game plays {c.GAME_ROUNDS} (or as many as there are)")

    for key in c.NOTE_LINKS:
        if key not in c.SOURCES:
            E(f"NOTE_LINKS: '{key}' isn't in SOURCES")

    content = {"TEXT": c.TEXT, "CATEGORIES": c.CATEGORIES, "FOODS": c.FOODS, "BASICS": c.BASICS,
               "SCENARIOS": c.SCENARIOS, "WORK_ENTRY": c.WORK_ENTRY}
    for name, value in content.items():
        for where, text in visible_strings(value, name):
            if DASHES.search(text):
                W(f"{where}: has a dash or hyphen: \"{text[:70]}\"")


# ---------------------------------------------------------------------------------------------
# Drawings: yours (webp or png) win over the stand-ins (svg)
# ---------------------------------------------------------------------------------------------
@dataclass
class Art:
    color: Path | None      # colour layer (or the whole picture when ink is None)
    ink: Path | None        # line layer, shown in the page's text colour
    mine: bool              # True: your drawing, False: the stand-in


def find_art(name: str) -> Art | None:
    def first(*names):
        return next((p for p in names if p.exists()), None)
    color = first(*(ART / f"{name}-color.{x}" for x in ("webp", "png")))
    ink = first(*(ART / f"{name}-ink.{x}" for x in ("webp", "png")))
    if color or ink:
        return Art(color, ink, True)
    single = first(*(ART / f"{name}.{x}" for x in ("webp", "png")))
    if single:
        return Art(single, None, True)
    color, ink = STAND_INS / f"{name}-color.svg", STAND_INS / f"{name}-ink.svg"
    if color.exists() or ink.exists():
        return Art(color if color.exists() else None, ink if ink.exists() else None, False)
    return None


def svg_size(path: Path) -> tuple[int, int]:
    box = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', path.read_text(encoding="utf-8"))
    return (round(float(box.group(1))), round(float(box.group(2)))) if box else (600, 600)


@dataclass
class Site:
    """What the app borrows from build_static.py."""
    copy_asset: Callable[[Path, str], str]
    image_size: Callable[[Path], tuple[int, int]]


def art_markup(site: Site, name: str, alt: str, prefix: str, cls: str = "") -> str:
    """A drawing: the colour layer as an <img>, the ink as a mask in the text colour. alt="" for
    decorative ones (when the food's name is right next to it)."""
    art = find_art(name)
    role = f' role="img" aria-label="{esc(alt)}"' if alt else ' aria-hidden="true"'
    if art is None:
        return f'<span class="k-art k-art--missing {cls}"{role}></span>'
    size = lambda p: svg_size(p) if p.suffix == ".svg" else site.image_size(p)
    folder = "keep-or-toss/stand-ins" if not art.mine else "keep-or-toss"
    first = art.color or art.ink
    w, h = size(first)
    parts = []
    if art.color:
        src = prefix + site.copy_asset(art.color, folder)
        parts.append(f'<img class="k-art__color" src="{src}" alt="" width="{w}" height="{h}" loading="lazy" decoding="async">')
    if art.ink:
        ink = prefix + site.copy_asset(art.ink, folder)
        # The mask is set right here, not through a CSS variable: a url() inside a variable is read
        # from the stylesheet's folder, which would point to assets/assets/...
        parts.append(f'<span class="k-art__ink" style="-webkit-mask-image: url(\'{ink}\'); mask-image: url(\'{ink}\')"></span>')
    only_ink = "" if art.color else " k-art--ink-only"
    return (f'<span class="k-art{only_ink} {cls}" style="--ratio: {w} / {h}"{role}>' + "".join(parts) + "</span>")


# ---------------------------------------------------------------------------------------------
# Icons (line drawings in the text colour; they always sit next to words)
# ---------------------------------------------------------------------------------------------
def icon(name: str) -> str:
    paths = {
        c.KEEP: '<circle cx="12" cy="12" r="9"/><path d="M7.5 12.5l3 3 6-7"/>',
        c.CUT: '<path d="M3 17l11.5-11.5c1.5-1.5 4-1 5 .5L8 17.5"/><path d="M8 17.5L5.5 20H3v-3"/>',
        c.TOSS: '<path d="M4 7h16"/><path d="M9.5 7V4.5h5V7"/><path d="M6 7l1 13h10l1-13"/><path d="M10 11v6M14 11v6"/>',
        "soon": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4.5l3 2"/><path d="M9.5 2.5h5"/>',
        c.COUNTER: '<path d="M2.5 13h19"/><path d="M4 13v8M20 13v8"/><path d="M7 13c0-3 2.2-5 5-5s5 2 5 5"/>',
        c.PANTRY: '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M4 10h16M4 16h16"/><path d="M8 10V7h3v3M13 16v-4h3v4"/>',
        c.FRIDGE: '<rect x="5" y="2.5" width="14" height="19" rx="2"/><path d="M5 10h14"/><path d="M8.5 5.5v2M8.5 13v3"/>',
        c.FREEZER: '<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/><path d="M9.5 4.5L12 6l2.5-1.5M9.5 19.5L12 18l2.5 1.5"/>',
        "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
        "back": '<path d="M15 5l-7 7 7 7"/>',
        "next": '<path d="M9 5l7 7-7 7"/>',
    }
    return (f'<svg class="k-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" '
            f'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>')


# ---------------------------------------------------------------------------------------------
# Page parts
# ---------------------------------------------------------------------------------------------
def home_url(prefix: str) -> str:
    return f"{prefix}{c.APP_SLUG}/"


def food_url(prefix: str, food: c.Food) -> str:
    return f"{prefix}{c.APP_SLUG}/{food.slug}/"


def facts_list(facts: list[c.Fact], cls: str) -> str:
    if not facts:
        return f'<p class="k-empty">{esc(c.TEXT["nothing_yet"])}</p>'
    return f'<ul class="{cls}">' + "".join(f"<li>{esc(f.text)}</li>" for f in facts) + "</ul>"


def note_markup() -> str:
    links = ", ".join(f'<a href="{esc(c.SOURCES[k].url)}" rel="noopener">{esc(c.SOURCES[k].title)}</a>'
                      for k in c.NOTE_LINKS)
    return (f'<aside class="k-note"><p>{esc(c.TEXT["note"])}</p>'
            f'<p>{esc(c.TEXT["note_links_intro"])} {links}.</p></aside>')


def sources_markup(keys: list[str], products: list[int] = ()) -> str:
    items = []
    for key in keys:
        s = c.SOURCES[key]
        extra = ""
        if key == "foodkeeper" and products:
            extra = f' <span class="k-sources__detail">({esc("; ".join(fk_name(p) for p in dict.fromkeys(products)))})</span>'
        name = f'<a href="{esc(s.url)}" rel="noopener">{esc(s.title)}</a>' if s.url else esc(s.title)
        items.append(f'<li>{name}, {esc(s.publisher)}{extra}</li>')
    return f'<ol class="k-sources">{"".join(items)}</ol>'


def back_link(prefix: str) -> str:
    return (f'<p class="k-back"><a href="{home_url(prefix)}">{icon("back")}<span>{esc(c.TEXT["back_home"])}</span></a></p>')


def page_open(extra_class: str = "") -> str:
    return f'<div class="k-app {extra_class}" data-source="custom">'


def home_body(site: Site, prefix: str) -> tuple[str, dict]:
    T = c.TEXT
    groups = []
    for key, label in c.CATEGORIES.items():
        foods = [f for f in c.FOODS if f.category == key]
        if not foods:
            continue
        cards = "".join(
            f'<li class="k-card" data-search="{esc(" ".join([f.name] + f.also_called).lower())}">'
            f'<a href="{food_url(prefix, f)}">{art_markup(site, f.slug, "", prefix, "k-card__art")}'
            f'<span class="k-card__name">{esc(f.name)}</span></a></li>'
            for f in foods)
        groups.append(f'<section class="k-group" data-group="{esc(key)}" aria-labelledby="k-group-{esc(key)}">'
                      f'<h2 id="k-group-{esc(key)}">{esc(label)}</h2><ul class="k-cards">{cards}</ul></section>')
    buttons = (f'<button type="button" class="k-chip" data-filter="" aria-pressed="true">{esc(T["all_foods"])}</button>'
               + "".join(f'<button type="button" class="k-chip" data-filter="{esc(k)}" aria-pressed="false">{esc(v)}</button>'
                         for k, v in c.CATEGORIES.items() if any(f.category == k for f in c.FOODS)))
    body = (
        page_open("k-home")
        + f'<header class="k-hero"><h1>{esc(c.APP_NAME)}</h1><p class="k-lead">{esc(T["tagline"])}</p></header>'
        + f'<section class="k-why" aria-labelledby="k-why"><h2 id="k-why">{esc(T["why_title"])}</h2><p>{esc(T["why"])}</p></section>'
        + '<div class="k-finder" id="k-finder">'
        + f'<form class="k-search" role="search" hidden onsubmit="return false"><label for="k-search-input">{esc(T["search_label"])}</label>'
        + f'<span class="k-search__box">{icon("search")}<input id="k-search-input" type="search" autocomplete="off" '
        + f'placeholder="{esc(T["search_placeholder"])}" aria-describedby="k-count"></span></form>'
        + f'<div class="k-chips" role="group" aria-label="{esc(T["groups_label"])}" hidden>{buttons}</div>'
        + '<p class="k-count" id="k-count" role="status" aria-live="polite"></p>'
        + f'<p class="k-none" hidden>{esc(T["no_results"])}</p>'
        + "".join(groups) + "</div>"
        + '<ul class="k-links">'
        + f'<li><a href="{prefix}{c.APP_SLUG}/basics/"><span class="k-links__title">{esc(T["basics_card_title"])}</span>'
        + f'<span>{esc(T["basics_card_text"])}</span></a></li>'
        + f'<li><a href="{prefix}{c.APP_SLUG}/game/"><span class="k-links__title">{esc(T["game_card_title"])}</span>'
        + f'<span>{esc(T["game_card_text"])}</span></a></li></ul>'
        + note_markup() + "</div>")
    data = {"text": {k: T[k] for k in ("count_one", "count_many")}}
    return body, data


def food_body(site: Site, prefix: str, food: c.Food) -> str:
    T = c.TEXT
    choices, panels = [], []
    for i, plan in enumerate(food.plans):
        pid = f"k-plan-{i + 1}"
        place = T["places"][plan.place]
        choices.append(f'<button type="button" class="k-chip k-choice" aria-pressed="{"true" if i == 0 else "false"}" '
                       f'aria-controls="{pid}">{esc(plan.choice)}</button>')
        panels.append(
            f'<section class="k-plan" id="{pid}" aria-labelledby="{pid}-title">'
            f'<h3 id="{pid}-title">{esc(plan.choice)}</h3>'
            f'<dl class="k-facts"><div><dt>{esc(T["where"])}</dt><dd class="k-place k-place--{plan.place}">{icon(plan.place)}<span>{esc(place)}</span></dd></div>'
            f'<div><dt>{esc(T["lasts"])}</dt><dd>{esc(time_text(plan.time))}</dd></div></dl>'
            + (f'<h4>{esc(T["how"])}</h4>' + facts_list(plan.how, "k-how") if plan.how else "")
            + "</section>")
    products = [p.time.product for p in food.plans if isinstance(p.time, c.FK)]
    mold = None
    if not food.mold and not food.mold_needed:
        pass
    elif food.mold:
        answer = T["answers"][food.mold.action]
        mold = (f'<p class="k-verdict k-verdict--{food.mold.action}">{icon(food.mold.action)}<strong>{esc(answer)}</strong></p>'
                + "".join(f"<p>{esc(f.text)}</p>" for f in food.mold.text))
    else:
        mold = f'<p class="k-empty">{esc(T["nothing_yet"])}</p>'
    also = (f'<p class="k-also">{esc(T["also_called"])}: {esc(", ".join(food.also_called))}</p>' if food.also_called else "")
    return (
        page_open("k-food")
        + back_link(prefix)
        + f'<header class="k-food__head">{art_markup(site, food.slug, food.alt, prefix, "k-food__art")}'
        + f'<div><p class="k-kicker">{esc(c.CATEGORIES[food.category])}</p><h1>{esc(food.name)}</h1>{also}'
        + (f'<p class="k-lead">{esc(food.intro)}</p>' if food.intro else "") + "</div></header>"
        + f'<section class="k-section" aria-labelledby="k-plan"><h2 id="k-plan">{esc(T["plan_title"])}</h2>'
        + f'<p class="k-help" hidden>{esc(T["plan_help"])}</p>'
        + f'<div class="k-chips k-choices" role="group" aria-label="{esc(T["plan_title"])}" hidden>{"".join(choices)}</div>'
        + f'<div class="k-plans">{"".join(panels)}</div></section>'
        + f'<section class="k-section" aria-labelledby="k-signs"><h2 id="k-signs">{esc(T["signs_title"])}</h2><div class="k-signs">'
        + f'<div class="k-sign k-sign--soon"><h3>{icon("soon")}<span>{esc(T["use_soon_title"])}</span></h3>{facts_list(food.use_soon, "k-list")}</div>'
        + f'<div class="k-sign k-sign--toss"><h3>{icon(c.TOSS)}<span>{esc(T["toss_title"])}</span></h3>{facts_list(food.toss, "k-list")}</div>'
        + "</div></section>"
        + (f'<section class="k-section" aria-labelledby="k-mold"><h2 id="k-mold">{esc(T["mold_title"])}</h2>{mold}</section>'
           if mold is not None else "")
        + f'<section class="k-section" aria-labelledby="k-ideas"><h2 id="k-ideas">{esc(T["ideas_title"])}</h2>{facts_list(food.ideas, "k-list")}</section>'
        + (f'<section class="k-section" aria-labelledby="k-safety"><h2 id="k-safety">{esc(T["safety_title"])}</h2>'
           f'{facts_list(food.safety, "k-list")}</section>' if food.safety else "")
        + f'<section class="k-section" aria-labelledby="k-sources"><h2 id="k-sources">{esc(T["sources_title"])}</h2>'
        + sources_markup(food_sources(food), products) + "</section>"
        + next_links(prefix) + note_markup() + "</div>")


def next_links(prefix: str) -> str:
    T = c.TEXT
    return (f'<ul class="k-links k-links--small">'
            f'<li><a href="{prefix}{c.APP_SLUG}/basics/"><span class="k-links__title">{esc(T["basics_card_title"])}</span></a></li>'
            f'<li><a href="{prefix}{c.APP_SLUG}/game/"><span class="k-links__title">{esc(T["game_card_title"])}</span></a></li></ul>')


def basics_body(prefix: str) -> str:
    T = c.TEXT
    rules = "".join(
        f'<li class="k-rule"><h2>{esc(r.title)}</h2>' + "".join(f"<p>{esc(f.text)}</p>" for f in r.text) + "</li>"
        for r in c.BASICS)
    keys = list(dict.fromkeys(k for r in c.BASICS for k in fact_sources(r.text)))
    return (page_open("k-basics") + back_link(prefix)
            + f'<header class="k-hero"><h1>{esc(T["basics_title"])}</h1><p class="k-lead">{esc(T["basics_intro"])}</p></header>'
            + f'<ol class="k-rules">{rules}</ol>'
            + f'<section class="k-section" aria-labelledby="k-sources"><h2 id="k-sources">{esc(T["sources_title"])}</h2>'
            + sources_markup(keys) + "</section>"
            + f'<ul class="k-links k-links--small"><li><a href="{prefix}{c.APP_SLUG}/game/"><span class="k-links__title">'
            + f'{esc(T["game_card_title"])}</span></a></li></ul>'
            + note_markup() + "</div>")


def game_body(site: Site, prefix: str) -> tuple[str, dict]:
    T = c.TEXT
    foods = {f.slug: f for f in c.FOODS}
    rounds = [{
        "food": s.food, "name": foods[s.food].name, "url": food_url(prefix, foods[s.food]),
        "art": art_markup(site, s.food, "", prefix, "k-round__art"),
        "situation": s.situation, "answer": s.answer, "reason": s.reason,
        "source": {"title": c.SOURCES[s.source].title, "url": c.SOURCES[s.source].url},
    } for s in c.SCENARIOS]
    words = ("game_round", "game_question", "answers", "game_right", "game_wrong", "game_answer_is",
             "game_learn_more", "game_source", "game_next", "game_finish", "game_score", "game_best",
             "game_best_new", "game_again")
    data = {"rounds": rounds, "count": c.GAME_ROUNDS, "text": {k: T[k] for k in words},
            "icons": {k: icon(k) for k in (c.KEEP, c.CUT, c.TOSS)}, "storageKey": f"{c.APP_SLUG}-best"}
    body = (page_open("k-game-page") + back_link(prefix)
            + f'<header class="k-hero"><h1>{esc(T["game_title"])}</h1><p class="k-lead">{esc(T["game_intro"])}</p></header>'
            + '<div class="k-game" id="k-game" aria-live="off">'
            + f'<noscript><p class="k-empty">{esc(T["game_needs_js"])}</p></noscript>'
            + f'<p class="k-game__start" hidden><button type="button" class="k-btn k-btn--main" data-start>{esc(T["game_start"])}</button></p>'
            + '<p class="k-game__best" data-best hidden></p>'
            + '</div>'
            + next_links(prefix).replace(f'<li><a href="{prefix}{c.APP_SLUG}/game/"><span class="k-links__title">{esc(T["game_card_title"])}</span></a></li>', "")
            + note_markup() + "</div>")
    return body, data


def data_script(data: dict) -> str:
    text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="k-data">{text}</script>'


# ---------------------------------------------------------------------------------------------
# Work page entry
# ---------------------------------------------------------------------------------------------
def work_entry(site: Site, prefix: str) -> str:
    W = c.WORK_ENTRY
    url = home_url(prefix)
    points = "".join(f"<li>{esc(p)}</li>" for p in W["points"])
    members = " data-members" if c.MEMBERS_ONLY else ""
    return (f'<section class="s-project k-work"{members} aria-labelledby="k-work-title">'
            f'<h2 class="s-project__title" id="k-work-title"><a href="{url}">{esc(c.APP_NAME)}</a></h2>'
            f'<a class="k-work__link" href="{url}" aria-label="{esc(W["link_text"])}">'
            f'{art_markup(site, W["drawing"], W["alt"], prefix, "k-work__art")}</a>'
            f'<div class="k-work__text"><ul class="k-work__points">{points}</ul>'
            f'<p class="k-work__why">{esc(W["why"])}</p>'
            f'<p class="k-work__open"><a href="{url}">{esc(W["link_text"])} {icon("next")}</a></p>'
            f'<p class="k-work__note">{esc(W["note"])}</p></div></section>')


# ---------------------------------------------------------------------------------------------
# All the pages
# ---------------------------------------------------------------------------------------------
@dataclass
class AppPage:
    name: str           # header page name
    title: str          # browser tab title (before the owner's name)
    path: str           # web address after the domain
    body: str           # what goes in <main> (with {prefix} already filled in)
    description: str    # search engine summary
    data: dict | None = None


def depth_prefix(path: str) -> str:
    return "../" * (path.count("/") + 1)


def check_or_stop() -> Report:
    """Check the content; print the problems and stop the build if there are any. Run before
    docs/ is cleared, so a mistake here never leaves the site half built."""
    report = Report()
    check(report)
    if report.errors:
        print("\nKeep or Toss: please fix these in keep_or_toss_content.py, then build again:")
        for e in report.errors:
            print(f"  - {e}")
        raise SystemExit(1)
    return report


def pages(site: Site, report: Report) -> list[AppPage]:
    """Copy the styles and script and return every page; print what's still to do."""
    site.copy_asset(CSS_FILE, "keep-or-toss")
    site.copy_asset(JS_FILE, "keep-or-toss")
    out: list[AppPage] = []
    home = c.APP_SLUG
    p = depth_prefix(home)
    body, data = home_body(site, p)
    out.append(AppPage("keep-or-toss", c.APP_NAME, home, body, c.TEXT["tagline"], data))
    for food in c.FOODS:
        path = f"{c.APP_SLUG}/{food.slug}"
        out.append(AppPage("keep-or-toss", f"{food.name} · {c.APP_NAME}", path,
                           food_body(site, depth_prefix(path), food),
                           f"How to store {food.name.lower()}, how long it lasts, and when to toss it."))
    path = f"{c.APP_SLUG}/basics"
    out.append(AppPage("keep-or-toss", f"{c.TEXT['basics_title']} · {c.APP_NAME}", path,
                       basics_body(depth_prefix(path)), c.TEXT["basics_intro"]))
    path = f"{c.APP_SLUG}/game"
    body, data = game_body(site, depth_prefix(path))
    out.append(AppPage("keep-or-toss", f"{c.TEXT['game_title']} · {c.APP_NAME}", path, body, c.TEXT["game_intro"], data))

    # What's still to do
    for food in c.FOODS:
        art = find_art(food.slug)
        if art is None:
            report.warnings.append(f"{food.name}: no drawing at all (add {food.slug}-color.webp and {food.slug}-ink.webp)")
        elif not art.mine:
            report.stand_ins.append(food.slug)
    work_art = find_art(c.WORK_ENTRY["drawing"])
    if work_art is not None and not work_art.mine:
        report.stand_ins.append(c.WORK_ENTRY["drawing"])
    print(f"Keep or Toss: {len(c.FOODS)} foods, {len(c.SCENARIOS)} game rounds, FoodKeeper {foodkeeper()[0]}")
    if report.stand_ins:
        print(f"  still using stand-in drawings ({len(report.stand_ins)}): {', '.join(report.stand_ins)}")
    for w in report.warnings:
        print(f"  warning: {w}")
    if report.review:
        print(f"  needs review ({len(report.review)}):")
        for r in report.review:
            print(f"    - {r}")
    return out
