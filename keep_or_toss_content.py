"""Keep or Toss: every word in the app, in one place.

build_static.py reads this file (through keep_or_toss.py) and makes the app's pages on
divyaduraisamy.org. Nothing here is code you need to change; it is all text and lists.

    APP_NAME, APP_SLUG     the app's name and web address (change them here only)
    MEMBERS_ONLY           True: friends only (password page) while you review it; False: public
    TEXT                   the words on the buttons, headings and messages
    SOURCES                the pages the facts come from (foods, rules and scenarios point to these)
    CATEGORIES             the food groups, in the order they are shown
    FOODS                  one entry per food (see "Adding a food" below)
    BASICS                 the rules on the Basics page
    SCENARIOS              the "Keep or Toss?" game rounds (see "Adding a game round" below)
    WORK_ENTRY             the Keep or Toss section on the Work page

Adding a food
    Copy one Food(...) entry in FOODS, change it, and rebuild (uv run python build_static.py).
    - slug: the food's web address and drawing name, lowercase with no spaces ("bananas")
    - plans: two or three Plan(...) choices. Each says where it goes (COUNTER, PANTRY, FRIDGE or
      FREEZER), how to store it, and how long it lasts. Take the time from USDA FoodKeeper with
      FK(product number, "field"), e.g. FK(251, "Refrigerate"): the build reads the number from
      data/foodkeeper.json and writes "About 3 days". The fields are Pantry, DOP_Pantry,
      Pantry_After_Opening, Refrigerate, DOP_Refrigerate, Refrigerate_After_Opening,
      Refrigerate_After_Thawing, Freeze and DOP_Freeze ("DOP" = from the day you buy it).
      Only when FoodKeeper has no time, write it yourself with Hand("3 to 4 days", "source key").
    - every fact list item is Fact("words", "source key", ...): the build lists those sources
      under the food. FoodKeeper is added for you when a plan uses FK(...).
    - review: notes for you to check. The build prints them in the "needs review" list.
    The build stops and tells you what is missing if a food has no plans, no sources, a source
    key that isn't in SOURCES, or a FoodKeeper number or field that doesn't exist.

Drawings
    Put your drawing for a food in ui-scrapbook/custom-features/assets/keep-or-toss/, named after
    its slug: bananas-color.webp and bananas-ink.webp (two layers, like the Recipe Finder art: the
    ink turns cream on the dark page), or a single bananas.webp or bananas.png. Yours are used
    automatically; until then the stand-in in stand-ins/ is used. The build prints which foods
    still use stand-ins.

Adding a game round
    Copy one Scenario(...) in SCENARIOS: the food's slug, the situation, the answer (KEEP, CUT or
    TOSS), a one or two sentence reason, and its source key. Each game picks 10 at random.

Later: a sorting game (counter, pantry, fridge, freezer) can use each plan's place; nothing else
needs adding for it.

Words: plain, friendly, short sentences, no jargon, no dashes or hyphens. The build warns you
about dashes and hyphens it finds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

APP_NAME = "Keep, Toss, Refrigerate, or Freeze"
APP_SLUG = "keep-or-toss"   # divyaduraisamy.org/keep-or-toss/ (changing APP_NAME doesn't change this,
                            # so links people have saved keep working)
MEMBERS_ONLY = True         # friends only for now; set to False to release it to everyone

# Where food goes. A plan's place is one of these.
COUNTER, PANTRY, FRIDGE, FREEZER = "counter", "pantry", "fridge", "freezer"
# Game answers (and mold advice).
KEEP, CUT, TOSS = "keep", "cut", "toss"


@dataclass
class Fact:
    text: str
    sources: list[str] | str = field(default_factory=list)  # one source key or a list of them

    def __init__(self, text: str, *sources: str):
        self.text = text
        self.sources = list(sources)


@dataclass
class FK:
    """A storage time from USDA FoodKeeper: product number and field (see the top of this file)."""
    product: int
    field: str
    when: str = ""   # words after the time, e.g. "once it's ripe"


@dataclass
class Hand:
    """A storage time FoodKeeper doesn't have, written by hand, with its source key."""
    text: str
    source: str
    when: str = ""


@dataclass
class Plan:
    choice: str             # "Eat it in the next few days"
    place: str              # COUNTER, PANTRY, FRIDGE or FREEZER
    time: FK | Hand
    how: list[Fact] = field(default_factory=list)


@dataclass
class Mold:
    action: str             # CUT or TOSS
    text: list[Fact] = field(default_factory=list)


@dataclass
class Food:
    slug: str
    name: str
    category: str           # a key in CATEGORIES
    also_called: list[str] = field(default_factory=list)   # other names people search for
    intro: str = ""         # one short line under the name (optional)
    plans: list[Plan] = field(default_factory=list)
    use_soon: list[Fact] = field(default_factory=list)      # still fine, just use it soon
    toss: list[Fact] = field(default_factory=list)          # red flags
    mold: Mold | None = None
    mold_needed: bool = True    # False for foods where mold advice doesn't apply (sealed cans)
    ideas: list[Fact] = field(default_factory=list)         # ways to use it up in time
    safety: list[Fact] = field(default_factory=list)        # anything else to know (optional)
    alt: str = ""           # what the drawing shows, for screen readers
    review: list[str] = field(default_factory=list)         # notes for you (printed by the build)


@dataclass
class Rule:
    title: str
    text: list[Fact]


@dataclass
class Scenario:
    food: str               # the food's slug
    situation: str          # "Shredded cheese with a small fuzzy spot"
    answer: str             # KEEP, CUT or TOSS
    reason: str             # one or two sentences
    source: str             # a source key


@dataclass
class Source:
    title: str
    publisher: str
    url: str


# ---------------------------------------------------------------------------------------------
# Words on the page
# ---------------------------------------------------------------------------------------------
TEXT = {
    "tagline": "How to store food so it lasts, and how to tell when it's time to toss it.",
    "why_title": "Why I made this",
    "why": ("Placeholder, rewrite me: I kept seeing good food get thrown out, and food that should "
            "have been thrown out get eaten. I wanted one friendly place to check before you decide."),
    "search_label": "Find a food",
    "search_placeholder": "Try bananas, eggs or rice",
    "groups_label": "Food groups",
    "all_foods": "All foods",
    "count_one": "1 food",
    "count_many": "{n} foods",
    "no_results": "No foods match that. Try another word, or pick a group.",
    "basics_card_title": "The basics",
    "basics_card_text": "A few simple rules that keep you safe.",
    "game_card_title": "Play Keep or Toss?",
    "game_card_text": "Ten quick rounds. Can you tell what to keep?",
    "back_home": "All foods",
    "also_called": "Also called",
    "plan_title": "What's your plan?",
    "plan_help": "Pick one to see where to keep it and how long it lasts.",
    "where": "Where",
    "lasts": "How long",
    "how": "How",
    "places": {COUNTER: "Counter", PANTRY: "Pantry", FRIDGE: "Fridge", FREEZER: "Freezer"},
    "signs_title": "Signs it's turning",
    "use_soon_title": "Still fine, just use it soon",
    "toss_title": "Toss it",
    "mold_title": "If it gets moldy",
    "ideas_title": "Use it up in time",
    "safety_title": "Good to know",
    "sources_title": "Sources",
    "nothing_yet": "We're still checking this part.",
    # Storage times ({min}, {max} and {unit} are filled in by the build)
    "time_one": "About {min} {unit}",
    "time_range": "About {min} to {max} {unit}",
    "time_units": {"Days": ("day", "days"), "Weeks": ("week", "weeks"),
                   "Months": ("month", "months"), "Years": ("year", "years")},
    "time_when_ripe": "Until it's ripe",
    "time_indefinitely": "As long as it stays frozen",
    "time_not_recommended": "Not recommended",
    "time_package": "Until the date on the package",
    # The game
    "game_title": "Keep or Toss?",
    "game_intro": "Each round shows a food and what's going on with it. Pick what you'd do.",
    "game_start": "Start",
    "game_round": "Round {n} of {total}",
    "game_question": "What would you do?",
    "answers": {KEEP: "Keep it", CUT: "Cut it off and use it", TOSS: "Toss it"},
    "game_right": "That's right!",
    "game_wrong": "Not quite.",
    "game_answer_is": "The answer:",
    "game_learn_more": "More about {food}",
    "game_source": "Source:",
    "game_next": "Next",
    "game_finish": "See my score",
    "game_score": "You got {score} out of {total}.",
    "game_best": "Your best so far: {best} out of {total}.",
    "game_best_new": "That's your best score yet!",
    "game_again": "Play again",
    "game_needs_js": "The game needs JavaScript turned on. The food pages work without it.",
    # Basics page
    "basics_title": "The basics",
    "basics_intro": "Keep these in mind for every food.",
    # The note at the bottom of every page ({links} becomes the source links)
    "note": ("This is general guidance based on USDA and FDA information. It's not a medical guide. "
             "When in doubt, throw it out."),
    "note_links_intro": "Learn more:",
}

# Links in the note at the bottom of each page (source keys).
NOTE_LINKS = ["foodkeeper_app", "foodsafety_charts", "fsis_mold", "fda_storing"]

# ---------------------------------------------------------------------------------------------
# Sources. Facts point to these by key. Add a new one here before using it.
# ---------------------------------------------------------------------------------------------
SOURCES = {
    # USDA FoodKeeper (storage times)
    "foodkeeper": Source("FoodKeeper data", "USDA Food Safety and Inspection Service",
                         "https://catalog.data.gov/dataset/fsis-foodkeeper-data"),
    "foodkeeper_app": Source("FoodKeeper app", "FoodSafety.gov",
                             "https://www.foodsafety.gov/keep-food-safe/foodkeeper-app"),
    # USDA Food Safety and Inspection Service
    "fsis_mold": Source("Molds on Food: Are They Dangerous?", "USDA Food Safety and Inspection Service",
                        "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/molds-food-are-they-dangerous"),
    "fsis_shelf": Source("Shelf-Stable Food Safety", "USDA Food Safety and Inspection Service",
                         "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/shelf-stable-food"),
    "fsis_leftovers": Source("Leftovers and Food Safety", "USDA Food Safety and Inspection Service",
                             "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/leftovers-and-food-safety"),
    "fsis_dating": Source("Food Product Dating", "USDA Food Safety and Inspection Service",
                          "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/food-product-dating"),
    "fsis_refrigeration": Source("Refrigeration and Food Safety", "USDA Food Safety and Inspection Service",
                                 "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/refrigeration"),
    "fsis_freezing": Source("Freezing and Food Safety", "USDA Food Safety and Inspection Service",
                            "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/freezing-and-food-safety"),
    "fsis_thaw": Source("The Big Thaw: Safe Defrosting Methods", "USDA Food Safety and Inspection Service",
                        "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/big-thaw-safe-defrosting-methods"),
    "fsis_color": Source("The Color of Meat and Poultry", "USDA Food Safety and Inspection Service",
                         "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/color-meat-and-poultry"),
    "fsis_washing": Source("Washing Food: Does It Promote Food Safety?", "USDA Food Safety and Inspection Service",
                           "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/washing-food-does-it-promote-food"),
    "fsis_chicken": Source("Chicken from Farm to Table", "USDA Food Safety and Inspection Service",
                           "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/poultry/chicken-farm-table"),
    "fsis_eggs": Source("Shell Eggs from Farm to Table", "USDA Food Safety and Inspection Service",
                        "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/eggs/shell-eggs-farm-table"),
    "fsis_emergencies": Source("Keep Your Food Safe During Emergencies", "USDA Food Safety and Inspection Service",
                               "https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/emergencies/keep-your-food-safe-during-emergencies"),
    # FoodSafety.gov
    "foodsafety_charts": Source("Cold Food Storage Chart", "FoodSafety.gov",
                                "https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts"),
    "foodsafety_4steps": Source("4 Steps to Food Safety", "FoodSafety.gov",
                                "https://www.foodsafety.gov/keep-food-safe/4-steps-to-food-safety"),
    # FDA
    "fda_storing": Source("Are You Storing Food Safely?", "U.S. Food and Drug Administration",
                          "https://www.fda.gov/consumers/consumer-updates/are-you-storing-food-safely"),
    "fda_produce": Source("Selecting and Serving Produce Safely", "U.S. Food and Drug Administration",
                          "https://www.fda.gov/food/buy-store-serve-safe-food/selecting-and-serving-produce-safely"),
    "fda_seafood": Source("Selecting and Serving Fresh and Frozen Seafood Safely", "U.S. Food and Drug Administration",
                          "https://www.fda.gov/food/buy-store-serve-safe-food/selecting-and-serving-fresh-and-frozen-seafood-safely"),
    "fda_food_waste": Source("How to Cut Food Waste and Maintain Food Safety", "U.S. Food and Drug Administration",
                             "https://www.fda.gov/food/consumers/how-cut-food-waste-and-maintain-food-safety"),
    "fda_formula": Source("Handling Infant Formula Safely: What You Need to Know", "U.S. Food and Drug Administration",
                          "https://www.fda.gov/food/buy-store-serve-safe-food/handling-infant-formula-safely-what-you-need-know"),
    "fda_thermometers": Source("Refrigerator Thermometers: Cold Facts about Food Safety", "U.S. Food and Drug Administration",
                               "https://www.fda.gov/food/buy-store-serve-safe-food/refrigerator-thermometers-cold-facts-about-food-safety"),
    "fda_date_rfi": Source("USDA, FDA Seek Information About Food Date Labeling (December 2024)", "U.S. Food and Drug Administration",
                           "https://www.fda.gov/news-events/press-announcements/usda-fda-seek-information-about-food-date-labeling-aim-provide-further-clarity-transparency-and-cost"),
    # CDC
    "cdc_deli": Source("Listeria Outbreak Linked to Meats Sliced at Delis", "Centers for Disease Control and Prevention",
                       "https://www.cdc.gov/listeria/outbreaks/delimeats-7-24/index.html"),
    # California
    "ca_82001": Source("California Food and Agricultural Code, section 82001 (food date labels)", "California Legislature",
                       "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=FAC&sectionNum=82001"),
    # Divya's food pantry training slides (no web page; shown without a link)
    "pantry_training": Source("Kitchen Safety (food safety training for food pantry volunteers)", "Training slides, 2024", ""),
    # University extension programs
    "unl_bananas": Source("Prolonging the Life of Bananas", "Nebraska Extension", "https://food.unl.edu/article/prolonging-life-bananas/"),
    "msu_bananas": Source("HappyHealthy Fact Sheet: Bananas", "Mississippi State University Extension",
                          "https://extension.msstate.edu/publications/happyhealthy-fact-sheet-bananas"),
    "usu_bananas": Source("Fruit and Vegetable Guide Series: Bananas", "Utah State University Extension",
                          "https://extension.usu.edu/nutrition/research/bananas"),
    "pnw612": Source("Storing Food for Safety and Quality (PNW 612)", "Pacific Northwest Extension",
                     "https://extension.oregonstate.edu/sites/extd8/files/2023-08/pnw612.pdf"),
    "wsu_storing": Source("Storing Vegetables and Fruits at Home (EB1326E)", "Washington State University Extension",
                          "https://ucanr.edu/sites/default/files/2020-11/338856.pdf"),
    "isu_ripening": Source("Ripening and Storing Fruit", "Iowa State University Extension and Outreach",
                           "https://blogs.extension.iastate.edu/answerline/2026/04/28/which-fruit-will-ripen-after-picking/"),
    "illinois_avocados": Source("Green as Avocado, Smooth as a Smoothie!", "University of Illinois Extension",
                                "https://extension.illinois.edu/blogs/simply-nutritious-quick-and-delicious/2021-09-03-green-avocado-smooth-smoothie"),
    "nchfp_avocados": Source("Freezing Avocados", "National Center for Home Food Preservation",
                             "https://nchfp.uga.edu/how/freeze/fruits/freezing-avocados/"),
    "umaine_storing": Source("Storing and Washing Fresh Fruits and Vegetables", "University of Maine Cooperative Extension",
                             "https://extension.umaine.edu/food-health/2025/05/29/storing-and-washing-fresh-fruits-and-vegetables/"),
    "csu_tomatoes": Source("Colorado Tomatoes", "Colorado State University Extension",
                           "https://extension.colostate.edu/resource/colorado-tomatoes-2/"),
    "usu_berries": Source("How to Preserve Berries", "Utah State University Extension",
                          "https://extension.usu.edu/preserve-the-harvest/dev/berries-1"),
    "illinois_berries": Source("Small Fruits: Handling Care", "University of Illinois Extension",
                               "https://extension.illinois.edu/small-fruits/handling-care"),
    "nchfp_freezing": Source("Freezing", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze"),
    "nchfp_blanching": Source("Blanching Vegetables", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/freeze-general-information/blanching-vegetables/"),
    "nchfp_not_well": Source("Foods That Do Not Freeze Well", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/freeze-general-information/foods-that-do-not-freeze-well/"),
    "nchfp_how_long": Source("How Long Can I Store Frozen Foods?", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/freeze-general-information/how-long-can-i-store-frozen-foods/"),
    "nchfp_fresh_not_frozen": Source("Fresh, Not Frozen", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/blog/fresh-not-frozen"),
    "nchfp_labeling": Source("Packaging and Labeling Foods", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/freeze-general-information/packaging-and-labeling-foods/"),
    "nchfp_thawing": Source("Thawing and Preparing Foods for Serving", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/freeze-general-information/thawing-and-preparing-foods-for-serving/"),
    "nchfp_apples": Source("Freezing Apples", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/fruits/freezing-apples/"),
    "nchfp_peaches": Source("Freezing Peaches or Nectarines", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/fruits/freezing-peaches-or-nectarines/"),
    "nchfp_plums": Source("Freezing Plums", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/fruits/freezing-plums/"),
    "nchfp_mangos": Source("Freezing Mangos", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/fruits/freezing-mangos/"),
    "nchfp_onions": Source("Freezing Onions", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/vegetable/freezing-onions/"),
    "nchfp_peppers": Source("Freezing Bell or Sweet Peppers", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/vegetable/freezing-bell-or-sweet-peppers/"),
    "nchfp_tomatoes": Source("Freezing Tomatoes", "National Center for Home Food Preservation",
                     "https://nchfp.uga.edu/how/freeze/vegetable/freezing-tomatoes/"),
    "usu_freezing_fruit": Source("Fruit Freezing", "Utah State University Extension",
                     "https://extension.usu.edu/preserve-the-harvest/research/fruit-freezing"),
    "montana_freezing": Source("Freezing Fruits (MontGuide)", "Montana State University Extension",
                     "https://ccfruitandnuts.ucanr.edu/sites/default/files/2020-12/340873.pdf"),
    "ucdavis_storing": Source("Storing Fresh Fruits and Vegetables for Better Taste", "University of California, Davis",
                     "https://homeorchard.ucanr.edu/files/115275.pdf"),
    "nchfp_tray": Source("Dry or Tray Packing for Fruits", "National Center for Home Food Preservation",
                         "https://nchfp.uga.edu/how/freeze/freeze-general-information/dry-or-tray-packing-for-fruits/"),
    "umn_freezing_fruit": Source("How to Freeze Fruit Safely", "University of Minnesota Extension",
                                 "https://extension.umn.edu/food/preparing/cooking-at-home/food-preservation/freezing/freezing-fruit"),
    "nchfp_grapes": Source("Freezing Grapes", "National Center for Home Food Preservation",
                           "https://nchfp.uga.edu/how/freeze/fruits/freezing-grapes/"),
    "csu_salad": Source("Health Benefits and Safe Handling of Salad Greens", "Colorado State University Extension",
                        "https://extension.colostate.edu/resource/health-benefits-and-safe-handling-of-salad-greens/"),
    "unh_produce": Source("Simple Tips for Longer Lasting Produce", "University of New Hampshire Extension",
                          "https://extension.unh.edu/blog/2020/08/simple-tips-longer-lasting-produce"),
    "illinois_lettuce": Source("Lettuce", "University of Illinois Extension", "https://extension.illinois.edu/gardening/lettuce"),
    "nchfp_greens": Source("Freezing Greens (Including Spinach)", "National Center for Home Food Preservation",
                           "https://nchfp.uga.edu/how/freeze/vegetable/freezing-greens-including-spinach/"),
    "ndsu_vegetables": Source("Vary Your Veggies: How to Select and Store Vegetables", "North Dakota State University Extension",
                              "https://www.ndsu.edu/agriculture/extension/publications/vary-your-veggies-how-select-and-store-vegetables"),
    "nchfp_carrots": Source("Freezing Carrots", "National Center for Home Food Preservation",
                            "https://nchfp.uga.edu/how/freeze/vegetable/freezing-carrots/"),
    "isu_potatoes": Source("Sprouting or Greening Potatoes: Keep or Toss?", "Iowa State University Extension and Outreach",
                           "https://blogs.extension.iastate.edu/answerline/tag/greening"),
    "ndsu_potatoes": Source("My Potatoes Turned Green, Now What?", "North Dakota State University Extension",
                            "https://www.ndsu.edu/agriculture/extension/publications/garden-table-my-potatoes-turned-green-now-what"),
    "ucanr_onions": Source("Harvesting and Storing Onions from the Garden", "University of California Agriculture and Natural Resources",
                           "https://ucanr.edu/blog/backyard-gardener/article/harvesting-and-storing-onions-garden"),
    "umaine_onions": Source("What's the Best Way to Store Onions?", "University of Maine Cooperative Extension",
                            "https://extension.umaine.edu/gardening/2021/11/15/storing-onions/"),
    "csu_broccoli": Source("How to Use Broccoli", "Colorado State University Extension",
                           "https://extension.colostate.edu/resource/how-to-use-broccoli/"),
    "nchfp_broccoli": Source("Freezing Broccoli", "National Center for Home Food Preservation",
                             "https://nchfp.uga.edu/how/freeze/vegetable/freezing-broccoli/"),
    "unl_freezing_dairy": Source("Freezing Milk and Cheese", "Nebraska Extension", "https://food.unl.edu/article/freezing-milk-and-cheese/"),
    "ucanr_bread": Source("Best Ways to Use Stale Bread", "University of California Agriculture and Natural Resources",
                          "https://ucanr.edu/sites/default/files/2020-07/Shop_Smart_Eat_Well85778.pdf"),
    "usu_bread": Source("How to Use Extra Bread", "Utah State University Extension",
                        "https://extension.usu.edu/fscreate/files/2023-26-staff/Extra-Bread-plus-Recipe-Half-Sheet.pdf"),
    "usu_rice": Source("How Long Can Cooked Rice Sit Out?", "Utah State University Extension",
                       "https://extension.usu.edu/answers/articles/how-long-can-cooked-rice-sit-out"),
    "umaine_rice": Source("Is Your Leftover Rice Safe?", "University of Maine Cooperative Extension",
                          "https://extension.umaine.edu/food-health/2026/03/05/rice/"),
    "wisc_rice": Source("Safe Handling of Cooked Rice", "University of Wisconsin Madison Extension",
                        "https://winnebago.extension.wisc.edu/2019/04/05/safe-handling-of-cooked-rice-by-barb-ingham/"),
    "nchfp_jam": Source("Storing Home Canned Jams and Jellies", "National Center for Home Food Preservation",
                        "https://nchfp.uga.edu/how/make-jam-jelly/jams-jellies-general-information/storing-home-canned-jams-and-jellies/"),
}

CATEGORIES = {
    "fruits": "Fruits",
    "vegetables": "Vegetables",
    "dairy": "Dairy and eggs",
    "meat": "Meat, poultry and fish",
    "bread": "Bread and tortillas",
    "cans": "Cans and jars",
    "leftovers": "Cooked food and leftovers",
}

# ---------------------------------------------------------------------------------------------
# Foods
# ---------------------------------------------------------------------------------------------
FOODS: list[Food] = [
    # ----------------------------------------------------------------------------------- Fruits
    Food(
        "bananas", "Bananas", "fruits", also_called=["banana", "plantains"],
        alt="A yellow banana with a few brown spots",
        intro="Bananas keep ripening after you buy them. Let them ripen on the counter.",
        plans=[
            Plan("Eat them in the next few days", COUNTER, FK(251, "Pantry"), how=[
                Fact("Keep them on the counter, out of a plastic bag. A bag traps moisture and makes them ripen faster.", "unl_bananas"),
                Fact("Hang them by the stems, or lay them upside down, so they don't bruise.", "msu_bananas"),
                Fact("Keep them away from apples and avocados, which make them ripen faster.", "unl_bananas"),
                Fact("Wrap the stems in plastic wrap or foil to slow ripening a little.", "unl_bananas"),
                Fact("Don't put green bananas in the fridge. They won't ripen the right way.", "usu_bananas", "msu_bananas"),
                Fact("In the fridge, banana skins turn black and the bananas don't get sweet.", "ucdavis_storing"),
            ]),
            Plan("Bake or blend with them later", FREEZER, FK(251, "Freeze"), how=[
                Fact("Peel ripe bananas first. Slice them and lay the slices on a lined baking sheet.", "unl_bananas"),
                Fact("Freeze for a couple of hours until solid, then move them to a freezer bag.", "unl_bananas"),
                Fact("Frozen bananas are good for smoothies and baking.", "msu_bananas", "unl_bananas"),
            ]),
        ],
        use_soon=[
            Fact("Brown spots on the peel mean it's very ripe. Soft bananas with brown spots are great for baking.", "msu_bananas"),
        ],
        toss=[Fact("If it looks rotten, throw it out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name bananas. Soft fruit with mold should be thrown out, so play it safe.", "fsis_mold"),
            Fact("Mold spreads quickly in fruit. Check anything the moldy banana touched.", "fsis_mold"),
        ]),
        ideas=[
            Fact("Mash very ripe bananas and use them for baking, like banana bread.", "msu_bananas"),
            Fact("Freeze slices for smoothies.", "unl_bananas"),
        ],
        review=["FoodKeeper (3 days) and extension pages say ripe bananas can go in the fridge (the peel turns dark, "
                "the inside stays light). Left out as you asked; add a fridge plan if you change your mind.",
                "Mold: bananas aren't named on the FSIS chart. I used \"toss\" to be safe."],
    ),
    Food(
        "apples", "Apples", "fruits", also_called=["apple"],
        alt="A red apple with a green leaf",
        plans=[
            Plan("Eat them soon", COUNTER, FK(248, "DOP_Pantry"), how=[
                Fact("Apples ripen at room temperature.", "pnw612"),
                Fact("Keep them away from potatoes and carrots. Apples give off a gas that makes potatoes sprout and carrots taste bitter.", "wsu_storing"),
            ]),
            Plan("Make them last longer", FRIDGE, FK(248, "DOP_Refrigerate"), how=[
                Fact("Once they're ripe, keep them unwashed in a plastic bag in the crisper drawer.", "pnw612"),
                Fact("Wash them under running water right before you eat them.", "fda_produce"),
            ]),
            Plan("Freeze slices for baking", FREEZER, Hand("About 8 to 12 months", "nchfp_how_long"), how=[
                Fact("Wash, peel and core them, then slice.", "nchfp_apples"),
                Fact("Add a little ascorbic acid (vitamin C) so the slices don't turn brown.", "nchfp_apples"),
                Fact("Freeze the slices in one layer on a tray, then bag them as soon as they're frozen.", "nchfp_tray"),
                Fact("Label the bag with what's inside and the date.", "nchfp_labeling"),
            ]),
        ],
        use_soon=[Fact("A bruise or damaged spot: cut it away before you eat or cook the apple.", "fda_produce")],
        toss=[Fact("If it looks rotten, throw it out.", "fda_produce")],
        ideas=[Fact("Freeze apple slices for pies and baking.", "nchfp_apples")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name apples. It says some firm produce can be trimmed, but apples aren't on the list, so play it safe.", "fsis_mold"),
            Fact("Mold spreads quickly in fruit. Check anything the moldy apple touched.", "fsis_mold"),
        ]),
        review=["Counter time: FoodKeeper says about 3 weeks; Pacific Northwest Extension says 1 to 2 days at room temperature. Shown: FoodKeeper.",
                "Mold: apples aren't named on the FSIS chart (firm produce can be trimmed). I used \"toss\" to be safe; switch to CUT if you decide apples count as firm.",
                "Freezer time for apple slices (8 to 12 months) is the National Center for Home Food Preservation's general "
                "fruit time; FoodKeeper's 8 months is for cooked apples."],
    ),
    Food(
        "avocados", "Avocados", "fruits", also_called=["avocado", "guacamole"],
        alt="An avocado cut in half with its pit",
        intro="Avocados ripen on the counter. The fridge is for once they're ripe.",
        plans=[
            Plan("Eat it in a few days", COUNTER, FK(250, "Pantry"), how=[
                Fact("Let it ripen on the counter in a paper bag or a bowl, out of the sun.", "illinois_avocados"),
                Fact("It's ripe when it gives a little when you press it gently.", "nchfp_avocados"),
                Fact("To ripen it faster, put an apple or a banana in the bag with it.", "pnw612"),
            ]),
            Plan("Make a ripe one last a few more days", FRIDGE, FK(250, "Refrigerate", when="once it's ripe"), how=[
                Fact("Let it ripen at room temperature first, then move it to the fridge.", "isu_ripening"),
            ]),
            Plan("Save half for later", FRIDGE, Hand("About 1 to 2 days", "illinois_avocados"), how=[
                Fact("Splash lemon juice, lime juice or white vinegar on the cut side.", "illinois_avocados"),
                Fact("Put it in an airtight container in the fridge.", "illinois_avocados"),
            ]),
        ],
        use_soon=[Fact("Avocados can go from ripe to too ripe quickly, so check them every day.", "illinois_avocados")],
        toss=[Fact("If it looks rotten, throw it out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name avocados. Soft fruit with mold should be thrown out, so play it safe.", "fsis_mold"),
        ]),
        ideas=[Fact("Mash a ripe avocado with a fork for a dip or a spread.", "illinois_avocados")],
        safety=[Fact("Wash the outside before you cut it, even though you don't eat the skin.", "fda_produce")],
        review=["Mold: avocados aren't named on the FSIS chart. I used \"toss\" to be safe.",
                "Cut avocado time (1 to 2 days) is from Illinois Extension, not FoodKeeper."],
    ),
    Food(
        "tomatoes", "Tomatoes", "fruits", also_called=["tomato", "cherry tomatoes"],
        alt="A red tomato with a green top",
        intro="Tomatoes taste best kept on the counter.",
        plans=[
            Plan("Eat them soon", COUNTER, FK(306, "Pantry"), how=[
                Fact("Once a tomato is ripe, it keeps about 7 more days on the counter.", "foodkeeper"),
                Fact("Keep them at room temperature, out of the sun. Wash them just before eating.", "umaine_storing"),
                Fact("The fridge takes away flavor. Only put very ripe tomatoes in the fridge, to stop them from ripening more.", "csu_tomatoes", "umaine_storing", "ucdavis_storing"),
                Fact("Cover and refrigerate cut tomatoes.", "csu_tomatoes"),
            ]),
            Plan("Cook with them later", FREEZER, FK(306, "DOP_Freeze"), how=[
                Fact("Core and peel them, then freeze them whole or in pieces.", "nchfp_tomatoes"),
                Fact("Use them only for cooking: they won't be firm when they thaw.", "nchfp_tomatoes"),
            ]),
        ],
        toss=[Fact("If it looks rotten, throw it out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("Tomatoes are soft and juicy, so mold can spread under the skin where you can't see it. USDA says to throw them out.", "fsis_mold"),
        ]),
        safety=[Fact("Keep tomatoes away from cucumbers.", "umaine_storing")],
        review=["Ripe tomatoes on the counter: FoodKeeper says about 7 days; Colorado State Extension says 2 to 3 days for the best eating.",],
    ),
    Food(
        "berries", "Berries", "fruits",
        also_called=["strawberries", "strawberry", "raspberries", "raspberry", "blueberries", "blueberry", "blackberries"],
        alt="A strawberry and three blueberries",
        intro="Berries don't ripen after they're picked, so keep them cold.",
        plans=[
            Plan("Strawberries or raspberries this week", FRIDGE, FK(481, "DOP_Refrigerate"), how=[
                Fact("Before you put them away, take out any berries that are crushed or spoiled.", "umaine_storing"),
                Fact("Store them unwashed. Wash gently under running water just before eating, and don't soak them.", "usu_berries"),
                Fact("Leave the green tops on strawberries until you eat them.", "umaine_storing"),
                Fact("Don't leave berries out at room temperature for more than a few hours.", "illinois_berries"),
            ]),
            Plan("Blueberries", FRIDGE, FK(254, "DOP_Refrigerate"), how=[
                Fact("Store them unwashed, and wash them just before eating.", "usu_berries"),
            ]),
            Plan("Freeze for smoothies or baking", FREEZER, FK(481, "Freeze"), how=[
                Fact("Wash them and let them dry completely.", "umn_freezing_fruit"),
                Fact("Spread them in one layer on a tray and freeze.", "nchfp_tray"),
                Fact("Once they're frozen, pack them in a bag or container right away so they don't get freezer burn.", "nchfp_tray"),
            ]),
        ],
        toss=[Fact("If they look rotten, throw them out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name berries. Soft fruit with mold should be thrown out, so toss the moldy ones.", "fsis_mold"),
            Fact("Mold spreads quickly in fruit. Check the berries that were touching the moldy ones.", "fsis_mold"),
        ]),
        ideas=[Fact("Freeze extra berries on a tray, then use them in smoothies.", "nchfp_tray", "umn_freezing_fruit")],
        review=["Mold: berries aren't named on the FSIS chart. Whole container or just the moldy ones and their neighbors? "
                "No USDA or extension page settles it (Illinois Extension says spores spread through the package). Your call."],
    ),
    Food(
        "grapes", "Grapes", "fruits", also_called=["grape"],
        alt="A bunch of purple grapes with a leaf",
        intro="Grapes don't ripen after they're picked, so keep them cold.",
        plans=[
            Plan("Eat them this week", FRIDGE, FK(261, "DOP_Refrigerate"), how=[
                Fact("Put them in the fridge soon after you buy them.", "isu_ripening"),
                Fact("Wash them under running water right before eating.", "fda_produce"),
            ]),
            Plan("Freeze them for a cold snack", FREEZER, FK(261, "Freeze"), how=[
                Fact("Leave seedless grapes whole.", "nchfp_grapes"),
            ]),
        ],
        toss=[Fact("If they look rotten, throw them out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name grapes. Soft fruit with mold should be thrown out, so toss the moldy ones.", "fsis_mold"),
            Fact("Mold spreads quickly in fruit. Check the grapes that were touching them.", "fsis_mold"),
        ]),
        ideas=[Fact("Freeze whole seedless grapes.", "nchfp_grapes")],
        review=["Mold: grapes aren't named on the FSIS chart. Whole bunch or just the moldy ones? Your call.",],
    ),
    Food(
        "citrus", "Citrus", "fruits",
        also_called=["oranges", "orange", "lemons", "lemon", "limes", "lime", "grapefruit", "clementines", "tangerines"],
        alt="An orange with a leaf, and a lemon",
        plans=[
            Plan("Eat it within a week or so", COUNTER, FK(256, "DOP_Pantry"), how=[
                Fact("A cool spot in the room is best.", "pnw612"),
            ]),
            Plan("Make it last longer", FRIDGE, FK(256, "DOP_Refrigerate"), how=[
                Fact("Wrap the cut side of a cut lemon or orange so it keeps its vitamin C.", "pnw612"),
            ]),
        ],
        toss=[Fact("If it looks rotten, throw it out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name citrus. Play it safe and throw moldy citrus out.", "fsis_mold"),
            Fact("Mold spreads quickly in fruit. Check anything it touched.", "fsis_mold"),
        ]),
        safety=[Fact("Wash the outside before you cut or peel it.", "fda_produce")],
        review=["Mold: citrus isn't named on the FSIS chart. I used \"toss\" to be safe.",
                "Iowa State says refrigerate citrus; Pacific Northwest Extension says a cool room is best. Both shown as choices.",],
    ),
    # ------------------------------------------------------------------------------- Vegetables
    Food(
        "leafy-greens", "Leafy greens", "vegetables",
        also_called=["lettuce", "spinach", "salad", "salad mix", "romaine", "kale", "greens", "bagged salad"],
        alt="A head of green lettuce",
        plans=[
            Plan("A head of lettuce", FRIDGE, FK(290, "DOP_Refrigerate"), how=[
                Fact("Put it in the fridge within two hours of buying it, in a plastic bag or a lettuce keeper.", "csu_salad"),
                Fact("Wash it right before eating. Washing it before you store it makes it spoil faster.", "unh_produce"),
                Fact("Keep it away from apples, pears and bananas.", "illinois_lettuce"),
            ]),
            Plan("Leaf lettuce or spinach", FRIDGE, FK(291, "DOP_Refrigerate"), how=[
                Fact("Store it in a plastic bag in the crisper drawer. Wash just before using.", "umaine_storing"),
            ]),
            Plan("An open bag of salad", FRIDGE, FK(415, "Refrigerate_After_Opening"), how=[
                Fact("If the bag says it's washed and ready to eat, you don't need to wash it again.", "fda_produce"),
                Fact("Keep bagged salad in the fridge.", "fda_produce"),
            ]),
        ],
        use_soon=[Fact("Wilted outer leaves: take them off and use the rest soon.", "umaine_storing")],
        toss=[Fact("Slimy leaves or black spots: toss it. The slime comes from bacteria, and the black spots are usually mold.", "illinois_lettuce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name leafy greens. Soft, high moisture produce with mold should be thrown out.", "fsis_mold"),
        ]),
        ideas=[
            Fact("Cooking greens like spinach can be blanched for 2 minutes, cooled and frozen.", "nchfp_greens"),
            Fact("Lettuce doesn't freeze well. It comes out limp and soggy, so plan to eat it fresh.", "foodkeeper", "nchfp_not_well"),
        ],
        review=["Paper towel: UNH Extension says a damp towel; another extension page reportedly says dry. Left out until it's settled.",
                "Colorado State Extension says to rinse bagged salad; FDA says washed, ready to eat greens don't need it. Shown: FDA.",
                "Mold: greens aren't named on the FSIS chart. I used \"toss\"."],
    ),
    Food(
        "carrots", "Carrots", "vegetables", also_called=["carrot", "baby carrots"],
        alt="Two orange carrots with green tops",
        plans=[
            Plan("Eat them in the next few weeks", FRIDGE, FK(279, "DOP_Refrigerate"), how=[
                Fact("Cut off the green tops and store the carrots in a plastic bag.", "umaine_storing"),
                Fact("Keep them in the crisper drawer, where it's cold and a little damp.", "ndsu_vegetables"),
                Fact("If you wash them first, drain them well.", "ndsu_vegetables"),
            ]),
            Plan("Cook with them later", FREEZER, FK(279, "DOP_Freeze"), how=[
                Fact("Remove the tops, wash and peel.", "nchfp_carrots"),
                Fact("Boil them briefly first: 2 minutes for slices, 5 minutes for small whole carrots. Then cool and freeze.", "nchfp_carrots"),
            ]),
        ],
        toss=[
            Fact("Soft spots of decay: sort those carrots out and throw them away.", "ndsu_vegetables"),
            Fact("If it looks rotten, throw it out.", "fda_produce"),
        ],
        mold=Mold(CUT, [
            Fact("Carrots are firm, so mold can't get in deep. Cut off at least 1 inch around and below the spot.", "fsis_mold"),
            Fact("Keep the knife out of the mold so you don't spread it.", "fsis_mold"),
        ]),
        ideas=[Fact("Don't toss the tops: they're good in homemade pesto.", "unh_produce")],
        safety=[Fact("Wash carrots under running water before you eat them, even if you peel them. A small vegetable brush helps.", "fda_produce", "pantry_training")],
        review=["Limp or bendy carrots: no source says whether they're fine. Left out."],
    ),
    Food(
        "potatoes", "Potatoes", "vegetables", also_called=["potato", "sweet potatoes", "spuds"],
        alt="A brown potato",
        plans=[
            Plan("Everyday cooking", PANTRY, FK(297, "DOP_Pantry"), how=[
                Fact("Keep them somewhere cool, dark, dry and airy.", "isu_potatoes"),
                Fact("A paper bag works well.", "unh_produce"),
                Fact("Keep them in the dark so they don't turn green.", "ndsu_potatoes"),
                Fact("Keep them away from onions. Stored together, both spoil sooner.", "isu_potatoes"),
                Fact("Don't put raw potatoes in the fridge. The cold turns their starch into sugar.", "ndsu_vegetables", "foodkeeper"),
            ]),
            Plan("Cooked or mashed, for later", FREEZER, FK(297, "Freeze", when="(cooked or mashed)")),
        ],
        use_soon=[
            Fact("A few small sprouts on a firm potato: cut away the sprouts and any green parts, then use it.", "isu_potatoes", "ndsu_potatoes"),
        ],
        toss=[
            Fact("Green under the skin, or green in a lot of places: throw it out.", "ndsu_potatoes", "isu_potatoes"),
            Fact("Lots of sprouts, shriveled, and green inside: throw it out.", "isu_potatoes"),
        ],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name potatoes. Play it safe and throw moldy potatoes out.", "fsis_mold"),
        ]),
        safety=[
            Fact("The green part has a natural toxin that can upset your stomach. Cooking doesn't get rid of it.", "ndsu_potatoes", "isu_potatoes"),
        ],
        review=["Cooking temperatures: your training slides list food service numbers (ground beef 158°F, eggs 145°F). "
                "The app uses USDA's home cooking numbers (160°F for ground meat; eggs until firm).",
                "Solanine facts come from two extension pages (Iowa State, North Dakota State); no USDA or FDA page found.",
                "Mold: potatoes aren't named on the FSIS chart. I used \"toss\"; switch to CUT if you decide potatoes count as firm.",
                "Pantry time: FoodKeeper 1 to 2 months; Iowa State says up to 3 months in a cool place.",],
    ),
    Food(
        "onions", "Onions", "vegetables", also_called=["onion", "yellow onion", "red onion", "white onion"],
        alt="A golden onion",
        plans=[
            Plan("Everyday cooking", PANTRY, FK(294, "DOP_Pantry"), how=[
                Fact("Keep them somewhere dry, dark and cool. Not in plastic, and not near potatoes.", "unh_produce"),
                Fact("A mesh bag lets air move around them.", "ucanr_onions"),
                Fact("Check them every few weeks and take out any bad ones.", "umaine_onions"),
            ]),
            Plan("Chop extras and freeze them", FREEZER, FK(294, "DOP_Freeze"), how=[
                Fact("Extra onions can be frozen.", "umaine_onions"),
                Fact("Peel and dice them. No need to blanch.", "nchfp_onions"),
            ]),
        ],
        use_soon=[Fact("Sweet onions don't keep as long. Use them first.", "umaine_onions")],
        toss=[
            Fact("Damp at the top (the neck) means it's starting to rot.", "ndsu_vegetables"),
            Fact("If it looks rotten, throw it out.", "fda_produce"),
        ],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name onions. Play it safe and throw moldy onions out.", "fsis_mold"),
        ]),
        ideas=[Fact("Covered in the fridge, cut onions keep 7 to 10 days, so chop extra for the week.", "unh_produce")],
        review=["Fridge for whole onions: FoodKeeper (2 months) and North Dakota State allow it if they stay dry; UC ANR says don't. Left out.",
                "Sprouted onions: no source on whether they're fine. Left out.",
                "Mold: onions aren't named on the FSIS chart. I used \"toss\"."],
    ),
    Food(
        "broccoli", "Broccoli", "vegetables", also_called=["broccoli crowns"],
        alt="A head of green broccoli",
        plans=[
            Plan("Eat it this week", FRIDGE, FK(276, "DOP_Refrigerate"), how=[
                Fact("Keep it in a loose plastic bag with holes, in the fridge.", "csu_broccoli"),
                Fact("Wait to wash it until right before you use it.", "csu_broccoli"),
            ]),
            Plan("Cook with it later", FREEZER, FK(276, "DOP_Freeze"), how=[
                Fact("Boil it for 3 minutes first, then cool it quickly, drain and freeze.", "nchfp_broccoli"),
                Fact("Time it. Blanching too briefly is worse than not blanching at all.", "nchfp_blanching"),
            ]),
        ],
        use_soon=[Fact("Yellow buds mean it's getting old. Use it soon.", "ndsu_vegetables")],
        toss=[Fact("If it looks rotten, throw it out.", "fda_produce")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name broccoli. Play it safe and throw moldy broccoli out.", "fsis_mold"),
        ]),
        ideas=[Fact("Blanch and freeze it before it turns yellow.", "nchfp_broccoli")],
        review=["Yellowing broccoli: North Dakota State calls it a sign of age, not safety. Shown as \"use soon\".",
                "Mold: broccoli isn't named on the FSIS chart. I used \"toss\"."],
    ),
    # ---------------------------------------------------------------------------- Dairy and eggs
    Food(
        "milk", "Milk", "dairy", also_called=["dairy milk", "whole milk", "skim milk", "2 percent"],
        alt="A milk carton with a blue wave",
        plans=[
            Plan("Drink it", FRIDGE, FK(27, "Refrigerate"), how=[
                Fact("Keep it on a shelf, not in the door. The door gets warmer every time you open it.", "fsis_refrigeration"),
                Fact("Your fridge should be 40°F or colder.", "fsis_refrigeration"),
            ]),
            Plan("Save some for cooking", FREEZER, FK(27, "DOP_Freeze"), how=[
                Fact("Freeze it in small containers, with some space at the top. Milk grows as it freezes.", "unl_freezing_dairy"),
                Fact("Thaw it in the fridge, then shake or stir it well.", "unl_freezing_dairy"),
            ]),
        ],
        use_soon=[Fact("Thawed milk can look separated or a little grainy. It's still fine, and it works best for cooking.", "unl_freezing_dairy")],
        toss=[
            Fact("Anything that looks or smells suspicious should be thrown out.", "fda_storing"),
            Fact("Left out of the fridge more than 2 hours (1 hour when it's above 90°F): throw it out.", "fda_storing"),
        ],
        mold=Mold(TOSS, [Fact("Moldy milk goes in the trash. Anything that looks or smells suspicious should be thrown out.", "fda_storing")]),
        ideas=[Fact("Freeze milk you won't finish in time, and use it in cooking.", "unl_freezing_dairy")],
        review=["Fridge time: FoodKeeper only says \"until the date on the package\". Nebraska Extension says 7 days. Shown: FoodKeeper.",
                "\"Not in the door\" is FSIS's rule for all perishable food; no page names milk itself.",
                "Sour smell or lumps: no USDA or FDA page names them for milk. Used FDA's general \"looks or smells suspicious\"."],
    ),
    Food(
        "eggs", "Eggs", "dairy", also_called=["egg", "eggs in the shell", "hard boiled eggs"],
        alt="Two eggs",
        plans=[
            Plan("Eggs in the shell", FRIDGE, FK(21, "DOP_Refrigerate"), how=[
                Fact("Keep them in their carton in the coldest part of the fridge, not in the door.", "fsis_eggs"),
                Fact("Once eggs have been in the fridge, keep them cold. A cold egg left out can sweat, which helps bacteria get in.", "fsis_eggs"),
                Fact("You don't need to wash eggs at home.", "fsis_eggs"),
            ]),
            Plan("Hard boiled eggs for the week", FRIDGE, FK(23, "Refrigerate"), how=[
                Fact("Put hard boiled eggs in the fridge within 2 hours of cooking.", "fsis_eggs"),
            ]),
            Plan("Freeze extra eggs", FREEZER, FK(22, "Freeze"), how=[
                Fact("Don't freeze eggs in the shell. Crack them, beat the yolks and whites together, then freeze.", "foodsafety_charts"),
            ]),
        ],
        use_soon=[Fact("An egg that floats in water is older and lower quality, but it may still be safe. Crack it into a bowl and check for an odd look or smell before you use it.", "fsis_eggs")],
        toss=[
            Fact("Cracked eggs: bacteria can get in through cracks. Don't buy them.", "fsis_eggs"),
            Fact("Left out more than 2 hours: throw them out.", "fsis_eggs"),
            Fact("An egg that froze and cracked: throw it out.", "fsis_freezing"),
            Fact("An unpleasant smell when you crack it open means it's spoiled.", "fsis_eggs"),
        ],
        mold_needed=False,
        safety=[Fact("Cook eggs until the yolk and white are firm.", "fda_thermometers")],
        review=["No mold section: the FSIS chart has no row for eggs.",
                "Egg dates: FSIS gives 3 to 5 weeks in the fridge but no \"from the pack date\" wording was found."],
    ),
    Food(
        "hard-cheese", "Hard cheese", "dairy", also_called=["cheddar", "swiss", "parmesan", "block cheese", "cheese"],
        alt="A wedge of yellow cheese with holes",
        plans=[
            Plan("Unopened", FRIDGE, FK(3, "DOP_Refrigerate")),
            Plan("Opened", FRIDGE, FK(3, "Refrigerate_After_Opening")),
            Plan("Freeze some for cooking", FREEZER, FK(3, "DOP_Freeze"), how=[
                Fact("Cut it into blocks of half a pound to 1 pound. Wrap in plastic wrap, then put it in a freezer bag.", "unl_freezing_dairy"),
                Fact("Frozen cheese can get crumbly, but it keeps its flavor. It works best for cooking.", "unl_freezing_dairy"),
            ]),
        ],
        use_soon=[Fact("Crumbly after freezing: it's fine. Use it in cooking.", "unl_freezing_dairy")],
        mold=Mold(CUT, [
            Fact("Mold can't get deep into hard cheese. Cut off at least 1 inch around and below the spot.", "fsis_mold"),
            Fact("Keep the knife out of the mold, then wrap the cheese in fresh wrap.", "fsis_mold"),
            Fact("This is only for a block. Shredded, sliced or crumbled cheese with mold should be thrown out.", "fsis_mold"),
        ]),
        review=["How to wrap hard cheese in the fridge: no source found."],
    ),
    Food(
        "soft-cheese", "Soft cheese", "dairy",
        also_called=["cream cheese", "cottage cheese", "brie", "goat cheese", "ricotta", "camembert"],
        alt="A round of soft white cheese with a wedge cut out",
        plans=[
            Plan("Cream cheese", FRIDGE, FK(10, "DOP_Refrigerate"), how=[
                Fact("Cream cheese doesn't freeze well.", "unl_freezing_dairy"),
            ]),
            Plan("Cottage cheese, once it's open", FRIDGE, FK(9, "Refrigerate_After_Opening"), how=[
                Fact("Cottage cheese doesn't freeze well.", "unl_freezing_dairy"),
            ]),
            Plan("Brie or goat cheese", FRIDGE, FK(7, "DOP_Refrigerate")),
        ],
        mold=Mold(TOSS, [
            Fact("Soft cheese is moist, so mold can spread below what you see, and bacteria can grow with it. Throw it out.", "fsis_mold"),
            Fact("Brie and camembert are made with mold. Throw them out if other mold shows up.", "fsis_mold"),
        ]),
    ),
    Food(
        "shredded-cheese", "Shredded cheese", "dairy", also_called=["grated cheese", "mozzarella", "sliced cheese", "crumbled cheese"],
        alt="A bag of shredded orange cheese",
        plans=[
            Plan("Use it in the next few weeks", FRIDGE, FK(5, "DOP_Refrigerate")),
            Plan("Freeze it for later", FREEZER, FK(5, "DOP_Freeze"), how=[
                Fact("Freeze it in its original bag.", "unl_freezing_dairy"),
                Fact("Thaw it in the fridge for 24 to 48 hours, then use it soon.", "unl_freezing_dairy"),
            ]),
        ],
        mold=Mold(TOSS, [
            Fact("Throw it out, even if the spot is small. Mold can spread through shredded cheese from the tools that cut it.", "fsis_mold"),
            Fact("This goes for sliced and crumbled cheese too.", "fsis_mold"),
        ]),
    ),
    Food(
        "yogurt", "Yogurt", "dairy", also_called=["yoghurt", "greek yogurt", "sour cream"],
        alt="A cup of yogurt with a pink band",
        plans=[
            Plan("Eat it soon", FRIDGE, FK(33, "DOP_Refrigerate")),
            Plan("Freeze it for smoothies", FREEZER, FK(33, "Freeze")),
        ],
        toss=[Fact("Anything that looks or smells suspicious should be thrown out.", "fda_storing")],
        mold=Mold(TOSS, [
            Fact("Throw it out. Don't scoop the mold off: it can spread below the surface, and bacteria can grow with it.", "fsis_mold"),
        ]),
        review=["Liquid on top of yogurt: no source found."],
    ),
    Food(
        "butter", "Butter", "dairy", also_called=["margarine", "stick of butter"],
        alt="A stick of yellow butter",
        plans=[
            Plan("Soft butter for spreading", COUNTER, Hand("About 1 to 2 days", "foodkeeper")),
            Plan("Everyday", FRIDGE, FK(1, "DOP_Refrigerate")),
            Plan("Stock up for later", FREEZER, FK(1, "DOP_Freeze")),
        ],
        review=["The counter time (1 to 2 days) is FoodKeeper's note, typed by hand because it isn't in a time field.",
                "No mold advice: the FSIS chart has no row for butter.",],
    ),
    # -------------------------------------------------------------------- Meat, poultry and fish
    Food(
        "raw-chicken", "Raw chicken", "meat", also_called=["chicken", "chicken breast", "chicken thighs", "drumsticks", "poultry", "turkey"],
        alt="A raw chicken drumstick",
        plans=[
            Plan("Cook it in a day or two", FRIDGE, FK(117, "DOP_Refrigerate"), how=[
                Fact("Put it in the fridge as soon as you get home.", "fsis_chicken"),
                Fact("Keep it in a sealed container or wrapped well, on a tray or plate, so juices don't drip on other food.", "fsis_refrigeration", "pnw612"),
                Fact("Keep raw meat on the bottom shelf.", "pantry_training"),
                Fact("Store it apart from cheese and ready to eat foods like deli meat.", "pnw612"),
            ]),
            Plan("Freeze it for later", FREEZER, FK(117, "DOP_Freeze"), how=[
                Fact("You can freeze it in the store package.", "fsis_freezing"),
                Fact("For more than 2 months, wrap the package again so it keeps its quality.", "fsis_chicken"),
            ]),
        ],
        use_soon=[Fact("Dark color near the bones is normal, and it's safe.", "fsis_chicken")],
        toss=[Fact("An off smell, a sticky or tacky feel, or a slimy surface: don't use it.", "fsis_color")],
        mold=Mold(TOSS, [
            Fact("Fresh poultry is usually mold free. If you do see mold, throw it out.", "fsis_mold"),
        ]),
        safety=[
            Fact("Don't wash raw chicken. Rinsing doesn't kill germs, and the splashes can spread them to other food. Only cooking kills them.", "fsis_chicken", "fsis_washing"),
            Fact("Thaw it in the fridge, in cold water, or in the microwave. Never on the counter.", "fsis_thaw"),
            Fact("Cook it to 165°F. Use a food thermometer: the color doesn't tell you it's done.", "fsis_chicken", "fsis_washing"),
        ],
        review=["\"Bottom shelf\" comes from your pantry training slides (no USDA page found that says it).",
                "Times are FoodKeeper's boneless breast row (whole chicken freezes for 12 months).",
                "Mold: raw poultry isn't on the FSIS chart. \"Toss\" is my wording."],
    ),
    Food(
        "ground-beef", "Ground beef", "meat", also_called=["hamburger", "ground meat", "ground turkey", "ground pork", "mince"],
        alt="Ground beef on a tray",
        plans=[
            Plan("Cook it in a day or two", FRIDGE, FK(43, "DOP_Refrigerate"), how=[
                Fact("Keep it wrapped well, on a tray or plate, so juices don't drip on other food.", "fsis_refrigeration", "pnw612"),
                Fact("Keep raw meat on the bottom shelf.", "pantry_training"),
            ]),
            Plan("Freeze it for later", FREEZER, FK(43, "DOP_Freeze"), how=[
                Fact("You can freeze it in the store package. For longer storage, wrap it again.", "fsis_freezing"),
            ]),
        ],
        use_soon=[
            Fact("Red on the outside and grayish brown inside is normal. The inside just doesn't get air.", "fsis_color"),
            Fact("A color change alone doesn't mean it's spoiled.", "fsis_color"),
        ],
        toss=[Fact("An off smell, a sticky or tacky feel, or a slimy surface: don't use it.", "fsis_color")],
        mold=Mold(TOSS, [Fact("Fresh meat is usually mold free. If you do see mold, throw it out.", "fsis_mold")]),
        safety=[
            Fact("Thaw it in the fridge, in cold water, or in the microwave. Never on the counter.", "fsis_thaw"),
            Fact("Cook ground meat to 160°F.", "fsis_washing"),
        ],
        review=["FSIS \"Ground Beef and Food Safety\" couldn't be read; facts come from the FSIS color page.",
                "Mold: raw meat isn't on the FSIS chart. \"Toss\" is my wording."],
    ),
    Food(
        "fish", "Raw fish", "meat", also_called=["fish", "salmon", "cod", "tilapia", "tuna steak", "seafood"],
        alt="A pink fish fillet",
        plans=[
            Plan("Cook it in a day or two", FRIDGE, FK(144, "DOP_Refrigerate"), how=[
                Fact("If you'll cook it within 2 days, keep it in a clean fridge at 40°F or colder.", "fda_seafood"),
                Fact("Keep it sealed, on the bottom shelf, so juices don't drip on other food.", "pantry_training", "fsis_refrigeration"),
            ]),
            Plan("Freeze cod, haddock or other lean fish", FREEZER, FK(144, "DOP_Freeze"), how=[
                Fact("Wrap it tightly in plastic, foil or freezer paper.", "fda_seafood"),
                Fact("Thaw it in the fridge overnight.", "fda_seafood"),
            ]),
            Plan("Freeze salmon, tuna or other fatty fish", FREEZER, FK(146, "DOP_Freeze"), how=[
                Fact("Wrap it tightly in plastic, foil or freezer paper.", "fda_seafood"),
            ]),
        ],
        use_soon=[Fact("Fish that was frozen may not look quite like fresh, but it should still smell fresh and mild.", "fda_seafood")],
        toss=[Fact("A sour, rancid, fishy or ammonia smell: don't eat it.", "fda_seafood")],
        mold=Mold(TOSS, [Fact("Fresh fish is rarely moldy. If you see mold, throw it out.", "fsis_mold")]),
        safety=[Fact("Cook fish to 145°F, or until it's opaque and flakes easily.", "fsis_washing")],
        review=["Mold: raw fish isn't on the FSIS chart, and the FSIS page says fresh meat and poultry are usually mold free. \"Toss\" is my wording.",
                "Slimy fish: no source found (FDA lists smells only)."],
    ),
    Food(
        "deli-meat", "Deli meat", "meat", also_called=["lunch meat", "cold cuts", "ham", "turkey slices", "bologna", "salami"],
        alt="Folded slices of pink deli meat",
        plans=[
            Plan("Sliced at the deli counter", FRIDGE, FK(184, "DOP_Refrigerate"), how=[
                Fact("Keep it apart from raw meat.", "pnw612"),
            ]),
            Plan("A sealed package", FRIDGE, FK(192, "DOP_Refrigerate")),
            Plan("A package you've opened", FRIDGE, FK(192, "Refrigerate_After_Opening")),
        ],
        toss=[Fact("Anything that looks or smells suspicious should be thrown out.", "fda_storing")],
        mold=Mold(TOSS, [
            Fact("Deli meat is moist, so mold can spread below the surface. Throw it out.", "fsis_mold"),
        ]),
        safety=[
            Fact("If you're pregnant, 65 or older, or have a weak immune system, heat deli meat until steaming hot (165°F) before eating. You can let it cool first.", "cdc_deli"),
            Fact("Listeria, the germ to worry about, can grow in the fridge.", "cdc_deli"),
        ],
        review=["Slimy deli meat: no source names it. Used FDA's general \"looks or smells suspicious\".",],
    ),
    # ------------------------------------------------------------------------ Bread and tortillas
    Food(
        "bread", "Bread", "bread", also_called=["loaf", "sliced bread", "rolls", "buns", "bagels"],
        alt="A loaf of bread",
        plans=[
            Plan("Eat it this week", COUNTER, FK(195, "DOP_Pantry"), how=[
                Fact("The fridge slows mold, but bread goes stale faster there than on the counter.", "pnw612", "ucanr_bread"),
            ]),
            Plan("Keep it fresh longer", FREEZER, FK(195, "DOP_Freeze"), how=[
                Fact("Freezing keeps bread from going stale so fast.", "ucanr_bread"),
            ]),
        ],
        use_soon=[Fact("Stale but not moldy: it's fine. Toast it or use it in recipes.", "ucanr_bread")],
        mold=Mold(TOSS, [
            Fact("Bread is full of tiny holes, so mold spreads below the surface. Throw it out.", "fsis_mold"),
            Fact("Don't sniff moldy food. It can cause breathing trouble.", "fsis_mold"),
        ]),
        ideas=[
            Fact("Make croutons or bread crumbs: cut or tear the bread into small pieces and bake at 350°F until dry.", "ucanr_bread"),
            Fact("Make bread pudding with dry bread cubes, eggs, milk, sugar and vanilla.", "usu_bread"),
            Fact("French toast or grilled cheese are good ways to use bread up.", "ucanr_bread"),
        ],
        review=["FoodKeeper's store bought bread row says 14 to 18 days on the counter, but its store bought whole wheat row says 3 to 5 days. Shown: 14 to 18."],
    ),
    Food(
        "tortillas", "Tortillas", "bread", also_called=["tortilla", "wraps", "flour tortillas", "corn tortillas"],
        alt="A stack of tortillas",
        plans=[
            Plan("Flour tortillas, still sealed", PANTRY, FK(196, "DOP_Pantry")),
            Plan("Flour tortillas, once opened", FRIDGE, FK(196, "Refrigerate_After_Opening"), how=[
                Fact("Put them in the fridge or freezer after you open the package.", "pnw612"),
            ]),
            Plan("Corn tortillas", FRIDGE, FK(553, "DOP_Refrigerate")),
        ],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't name tortillas. Bread and baked goods with mold get thrown out, so play it safe.", "fsis_mold"),
        ]),
        review=["Mold: tortillas aren't named on the FSIS chart. Treated like bread (toss).",
                "Pacific Northwest Extension says 2 to 4 days in the cupboard; FoodKeeper says 3 months unopened. Shown: FoodKeeper.",],
    ),
    # ------------------------------------------------------------------------------ Cans and jars
    Food(
        "canned-vegetables", "Canned vegetables", "cans",
        also_called=["cans", "canned food", "canned beans", "canned corn", "canned soup", "canned goods"],
        alt="A can with a green label and yellow corn",
        intro="Sealed cans keep a long time. The can itself tells you when to worry.",
        plans=[
            Plan("Sealed, on the shelf", PANTRY, FK(372, "DOP_Pantry"), how=[
                Fact("Keep cans somewhere cool and dry. Below 85°F is best.", "fsis_shelf"),
                Fact("Not above or next to the stove, under the sink, or in a damp garage or basement.", "fsis_shelf"),
                Fact("Keep food away from cleaning products and chemicals.", "fda_storing"),
                Fact("Check your pantry every few weeks and use the older cans first.", "fsis_shelf"),
            ]),
            Plan("Leftovers from an opened can", FRIDGE, FK(372, "Refrigerate_After_Opening"), how=[
                Fact("Move what's left into a glass or plastic container for the best flavor.", "fsis_shelf"),
            ]),
        ],
        use_soon=[
            Fact("A small dent on a can that's otherwise in good shape is fine.", "fsis_shelf"),
            Fact("Surface rust you can rub off with your finger or a paper towel isn't serious.", "fsis_shelf"),
            Fact("Past the date on the can? Cans are safe well past it if there are no dents, rust or swelling.", "foodkeeper"),
            Fact("A little hiss when you open it is normal. Many cans are vacuum packed.", "fsis_shelf"),
        ],
        toss=[
            Fact("Bulging or swollen cans.", "fsis_shelf"),
            Fact("Leaking cans, or a sticky outside.", "fsis_shelf", "fda_storing"),
            Fact("A deep dent (one you can lay your finger in), or any dent on a seam.", "fsis_shelf"),
            Fact("Heavy rust, or any rust inside when you open it.", "fsis_shelf"),
            Fact("Liquid that spurts out when you open it, or a loud hiss.", "fsis_shelf"),
            Fact("A bad smell, or milky liquid around vegetables that should be clear.", "fsis_shelf"),
            Fact("Never taste food from a can like this, not even a little.", "fsis_shelf"),
        ],
        mold_needed=False,
        safety=[
            Fact("Damaged cans can carry botulism, a rare but very dangerous food poisoning.", "fsis_shelf"),
            Fact("Throw bad cans out in two plastic bags tied tight.", "fsis_shelf"),
        ],
        review=["Times are FoodKeeper's low acid canned goods row (vegetables, beans, soup, meat)."],
    ),
    Food(
        "opened-canned-food", "Opened canned food", "cans",
        also_called=["open can", "leftover canned food", "canned beans", "canned tomatoes", "canned fruit"],
        alt="An open can and a small container",
        plans=[
            Plan("Beans, vegetables, soup or meat", FRIDGE, FK(372, "Refrigerate_After_Opening"), how=[
                Fact("Put what's left in the fridge. You can keep it in the can, but a glass or plastic container keeps the flavor better.", "fsis_shelf"),
            ]),
            Plan("Fruit, tomatoes, pickles or sauerkraut", FRIDGE, FK(373, "Refrigerate_After_Opening"), how=[
                Fact("Move it into a clean glass or plastic container and refrigerate it right away.", "fsis_shelf", "fsis_mold"),
            ]),
        ],
        toss=[Fact("Anything that looks or smells suspicious should be thrown out.", "fda_storing")],
        mold=Mold(TOSS, [
            Fact("USDA's mold chart doesn't list opened canned food. When in doubt, throw it out.", "fsis_mold", "fsis_emergencies"),
        ]),
        review=["Mold: opened canned food isn't named on the FSIS chart. \"Toss\" is my wording.",],
    ),
    Food(
        "jam", "Jam and jelly", "cans", also_called=["jam", "jelly", "preserves", "fruit spread", "marmalade"],
        alt="A purple jar of jam with a red lid",
        plans=[
            Plan("Sealed jar", PANTRY, FK(347, "DOP_Pantry")),
            Plan("Once it's open", FRIDGE, FK(347, "Refrigerate_After_Opening"), how=[
                Fact("Keep an open jar in the fridge until it's gone.", "nchfp_jam"),
                Fact("Spoon out what you need and put the jar back. Leaving it open or out a long time makes it go bad sooner.", "nchfp_jam"),
            ]),
        ],
        toss=[Fact("A fermented, yeasty or alcohol smell, or anything growing in it: throw out the whole jar.", "nchfp_jam")],
        mold=Mold(TOSS, [
            Fact("Throw out the whole jar. Don't scoop out the mold: it may be making toxins in the rest.", "fsis_mold", "nchfp_jam"),
        ]),
        review=["The National Center for Home Food Preservation page is about home canned jam; store bought times come from FoodKeeper.",],
    ),
    # --------------------------------------------------------------------- Cooked food and leftovers
    Food(
        "cooked-rice", "Cooked rice", "leftovers", also_called=["rice", "leftover rice", "fried rice"],
        alt="A blue bowl of rice with chopsticks",
        intro="Cooked rice needs to get cold fast.",
        plans=[
            Plan("Eat it in the next few days", FRIDGE, Hand("About 3 to 4 days", "fsis_leftovers"), how=[
                Fact("Put it in the fridge within 2 hours of cooking, or within 1 hour if it's above 90°F.", "usu_rice"),
                Fact("Split big batches into small, shallow containers so they cool faster.", "usu_rice"),
            ]),
            Plan("Freeze it for later", FREEZER, FK(178, "Freeze")),
        ],
        toss=[
            Fact("Rice left out too long: throw it out. It can look and smell normal even when it has germs or toxins.", "usu_rice"),
            Fact("Reheating doesn't fix it. Heat can kill the germs but won't remove the toxins they made.", "umaine_rice"),
            Fact("Past 3 to 4 days in the fridge: throw it out.", "usu_rice"),
        ],
        mold=Mold(TOSS, [Fact("Cooked grains are moist, so mold can spread below the surface. Throw it out.", "fsis_mold")]),
        ideas=[Fact("Use leftover rice in a rice salad.", "wisc_rice")],
        safety=[Fact("Reheat rice until it reaches 165°F.", "umaine_rice")],
        review=["Fridge time: FoodKeeper says 4 to 6 days, but USDA's leftovers rule and two extension pages say 3 to 4. Shown: 3 to 4 (typed by hand). Your call."],
    ),
    Food(
        "leftovers", "Leftovers", "leftovers",
        also_called=["leftover", "cooked food", "casserole", "soup", "chili", "stew", "pizza", "takeout"],
        alt="A food container with a lid",
        plans=[
            Plan("Eat them in the next few days", FRIDGE, FK(173, "Refrigerate"), how=[
                Fact("Refrigerate leftovers within 2 hours of cooking.", "fsis_leftovers"),
                Fact("Split big amounts into shallow containers so they cool fast.", "fsis_leftovers"),
                Fact("Cover them, wrap them airtight, or seal them in containers.", "fsis_leftovers"),
            ]),
            Plan("Freeze dishes with meat, fish, poultry or egg", FREEZER, FK(173, "Freeze"), how=[
                Fact("Frozen leftovers stay safe, but they can dry out and lose flavor over time.", "fsis_leftovers"),
            ]),
            Plan("Freeze vegetables, rice or potatoes", FREEZER, FK(174, "Freeze")),
        ],
        toss=[
            Fact("Left out more than 2 hours (1 hour when it's above 90°F): throw it out.", "fsis_leftovers"),
            Fact("More than 3 to 4 days in the fridge: throw it out.", "fsis_leftovers"),
        ],
        mold=Mold(TOSS, [Fact("Cooked food is moist, so mold can spread below the surface, and bacteria can grow with it. Throw it out.", "fsis_mold")]),
        safety=[
            Fact("Reheat leftovers to 165°F. Bring soups, sauces and gravies to a rolling boil.", "fsis_leftovers"),
            Fact("Thaw frozen leftovers in the fridge, in cold water, or in the microwave.", "fsis_leftovers"),
        ],
        review=["Freezer times: FoodKeeper says 2 to 3 months (with meat) and 1 to 2 months (without); the FSIS leftovers page says 3 to 4 months. Shown: FoodKeeper.",],
    ),
]

# ---------------------------------------------------------------------------------------------
# The Basics page
# ---------------------------------------------------------------------------------------------
BASICS: list[Rule] = [
    Rule("Looks and smell can fool you", [
        Fact("The germs that cause food poisoning usually don't change how food looks, smells or tastes. Food can look fine and still make you sick.",
             "fsis_refrigeration", "fda_storing"),
        Fact("A bad smell or slime means food has spoiled, so toss it. But a normal look and smell doesn't prove it's safe. Time and temperature come first.",
             "fsis_dating", "fsis_refrigeration"),
        Fact("Never taste food to check if it's safe.", "fsis_emergencies"),
    ]),
    Rule("When in doubt, throw it out", [
        Fact("If you're not sure, or the food looks questionable, throw it out.", "fda_storing", "fsis_emergencies"),
    ]),
    Rule("Keep it cold", [
        Fact("Keep your fridge at 40°F or colder, and your freezer at 0°F.", "fda_storing", "foodsafety_4steps"),
        Fact("An appliance thermometer is the best way to know.", "fda_storing"),
        Fact("Keep perishable food on the shelves, not in the door. The door gets warmer.", "fsis_refrigeration"),
        Fact("Don't pack the fridge too full. Cold air needs room to move around the food.", "pantry_training"),
    ]),
    Rule("Two hours, or one hour when it's hot", [
        Fact("Don't leave food that needs the fridge out for more than 2 hours. If it's above 90°F, make that 1 hour.", "fda_storing", "fsis_leftovers"),
        Fact("That goes for meat, poultry, seafood, eggs, produce and anything else that needs the fridge.", "fda_storing"),
        Fact("On hot days, bring a cooler or ice packs for food that needs to stay cold.", "pantry_training"),
    ]),
    Rule("Most leftovers last 3 to 4 days", [
        Fact("Cooked leftovers keep 3 to 4 days in the fridge.", "fsis_leftovers", "foodsafety_charts"),
        Fact("Reheat them to 165°F, and bring soups and sauces to a rolling boil.", "fsis_leftovers"),
    ]),
    Rule("The freezer keeps food safe", [
        Fact("Food kept frozen at 0°F stays safe. Freezer times are only about taste and texture.", "foodsafety_charts", "fsis_freezing"),
        Fact("Freezer burn makes food dry in spots, but it doesn't make it unsafe.", "fsis_freezing"),
        Fact("Thaw food in the fridge, in cold water, or in the microwave. Never on the counter.", "fsis_thaw"),
    ]),
    Rule("Freezing fruits and vegetables", [
        Fact("Most fruits and vegetables can be frozen, but some need a step first. Peel bananas. Peel, core and slice apples. "
             "Pit and cut fruits with a big pit, like peaches, nectarines, plums and mangoes.",
             "nchfp_freezing", "unl_bananas", "nchfp_apples", "nchfp_peaches", "nchfp_plums", "nchfp_mangos"),
        Fact("Wash produce before you freeze it. Freezing doesn't kill germs. It only pauses them, and they can grow again once the food thaws.",
             "umn_freezing_fruit", "fsis_freezing"),
        Fact("Spread cut pieces in one layer on a tray and freeze them, then bag them as soon as they're frozen. "
             "They stay loose, so you can pour out just what you need, and bagging them right away helps prevent freezer burn.",
             "nchfp_tray"),
        Fact("Apples and peaches turn brown once they're cut. A little ascorbic acid (vitamin C) helps them keep their color. "
             "Lemon juice works too, but not as well, and it can make the fruit taste tart.",
             "nchfp_apples", "nchfp_peaches", "usu_freezing_fruit", "montana_freezing"),
        Fact("Most vegetables need blanching first: a short dip in boiling water, then right into cold water. "
             "It stops natural enzymes that would keep breaking down flavor, color and texture, even in the freezer.",
             "nchfp_blanching"),
        Fact("Follow the blanching time for each vegetable. Blanching too briefly is worse than not blanching at all.", "nchfp_blanching"),
        Fact("Diced onions and raw bell peppers can go in the freezer without blanching.", "nchfp_onions", "nchfp_peppers"),
        Fact("Label each bag with what's inside and the date.", "nchfp_labeling"),
        Fact("At 0°F, most fruits and vegetables are at their best for 8 to 12 months. After that they're still safe, just lower in quality.",
             "nchfp_how_long"),
    ]),
    Rule("What to expect after freezing", [
        Fact("Watery, crunchy produce like lettuce, cucumbers, celery and radishes comes out limp and soggy, so it won't work in a salad.",
             "nchfp_not_well", "nchfp_fresh_not_frozen"),
        Fact("Tomatoes won't be firm after freezing, but they're fine for cooking.", "nchfp_tomatoes"),
        Fact("Starchy vegetables like corn and peas hold up especially well.", "nchfp_fresh_not_frozen"),
        Fact("Thawed fruit is softer than fresh, so it's best eaten with a few ice crystals still in it.", "nchfp_thawing"),
        Fact("Handle anything you've thawed like fresh food.", "fsis_freezing"),
    ]),
    Rule("Colder isn't always better", [
        Fact("Some produce does best on the counter. In the fridge, banana skins turn black and the bananas don't get sweet, "
             "and tomatoes lose their flavor.", "ucdavis_storing"),
        Fact("Other produce can ripen on the counter first, then move to the fridge.", "ucdavis_storing"),
    ]),
    Rule("What the dates mean", [
        Fact("Under federal rules, dates on food are about quality, not safety. Infant formula is the one exception.", "fsis_dating"),
        Fact("\"Best if Used By\" means when the food will taste best. It's not a safety date. A \"Sell By\" date is for the store.", "fsis_dating"),
        Fact("Never use infant formula after its \"Use By\" date.", "fda_formula", "fsis_dating"),
        Fact("If a date passes at home, food that has been stored the right way should still be safe until you see signs it has spoiled.", "fsis_dating"),
        Fact("USDA and FDA asked the public about date labels in December 2024. For now they recommend \"Best if Used By\" for quality dates.", "fda_date_rfi"),
        Fact("In California, food made on or after July 1, 2026 uses standard words: \"BEST if Used by\" is a quality date, and \"USE by\" is a safety date. "
             "\"Sell by\" can't be shown to shoppers. Infant formula and eggs are left out of this law, and older food on the shelf may still have the old labels.",
             "ca_82001"),
    ]),
    Rule("Mold: a few foods can be trimmed, most can't", [
        Fact("Hard cheese and firm produce like cabbage, bell peppers and carrots: cut off at least 1 inch around and below the spot. Keep the knife out of the mold.",
             "fsis_mold"),
        Fact("Throw out moldy soft fruits and vegetables, bread, soft cheese, shredded or sliced cheese, yogurt, jam, deli meat and leftovers.", "fsis_mold"),
        Fact("If food is covered with mold, throw it out. Don't sniff it, and check anything it touched.", "fsis_mold"),
    ]),
    Rule("Bad cans go in the trash", [
        Fact("Throw out cans that bulge, leak, are badly rusted or deeply dented, or spurt liquid when you open them.", "fsis_shelf"),
        Fact("Never taste what's inside a can like that.", "fsis_shelf"),
    ]),
]

# ---------------------------------------------------------------------------------------------
# The game
# ---------------------------------------------------------------------------------------------
GAME_ROUNDS = 10
SCENARIOS: list[Scenario] = [
    Scenario("shredded-cheese", "Shredded cheese with a small fuzzy spot", TOSS,
             "Shredded cheese can carry mold all through the bag from the tools that cut it. Throw it out, even if the spot is small.", "fsis_mold"),
    Scenario("hard-cheese", "A block of cheddar with a small mold spot on one corner", CUT,
             "Mold can't get deep into hard cheese. Cut off at least 1 inch around and below the spot, then wrap it fresh.", "fsis_mold"),
    Scenario("soft-cheese", "Cream cheese with a spot of mold on top", TOSS,
             "Soft cheese is moist, so mold spreads below what you see. Throw it out.", "fsis_mold"),
    Scenario("bread", "A loaf with a few fuzzy green dots on one slice", TOSS,
             "Bread is full of tiny holes, so mold spreads below the surface. Toss the loaf.", "fsis_mold"),
    Scenario("bread", "Bread that's dry and stale, with no mold", KEEP,
             "Stale isn't unsafe. Toast it, or turn it into croutons or bread crumbs.", "ucanr_bread"),
    Scenario("jam", "A jar of jam with a little mold on top", TOSS,
             "Don't scoop it out. The mold may be making toxins in the rest of the jar.", "fsis_mold"),
    Scenario("carrots", "A carrot with one small mold spot", CUT,
             "Carrots are firm, so mold can't get in deep. Cut off at least 1 inch around and below the spot.", "fsis_mold"),
    Scenario("tomatoes", "A tomato with a fuzzy moldy patch", TOSS,
             "Tomatoes are soft and juicy, so mold can spread inside where you can't see it.", "fsis_mold"),
    Scenario("yogurt", "Yogurt with a spot of mold on top", TOSS,
             "Mold can spread below the surface of yogurt. Don't scoop it off: throw it out.", "fsis_mold"),
    Scenario("leftovers", "A leftover casserole with mold on one edge", TOSS,
             "Cooked food is moist, so mold spreads below the surface and bacteria can grow with it.", "fsis_mold"),
    Scenario("leftovers", "A pot of chili left on the stove all night", TOSS,
             "Cooked food shouldn't sit out more than 2 hours. Throw it out.", "fsis_leftovers"),
    Scenario("leftovers", "Soup you made 3 days ago, kept in the fridge", KEEP,
             "Leftovers keep 3 to 4 days in the fridge. Bring it to a rolling boil when you reheat it.", "fsis_leftovers"),
    Scenario("leftovers", "Leftovers frozen 8 months ago that stayed frozen the whole time", KEEP,
             "Food kept frozen at 0°F stays safe. It may be a little dry, but it's safe to eat.", "fsis_leftovers"),
    Scenario("canned-vegetables", "A can of green beans with a bulging lid", TOSS,
             "A bulging can is a warning sign for botulism. Throw it out and never taste it.", "fsis_shelf"),
    Scenario("canned-vegetables", "A can of corn with a small dent on the side, otherwise fine", KEEP,
             "A small dent is OK. A deep dent you can lay your finger in, or any dent on a seam, means toss it.", "fsis_shelf"),
    Scenario("canned-vegetables", "A can that spurts liquid when you open it", TOSS,
             "Liquid that spurts out can mean the food is unsafe. Don't taste it.", "fsis_shelf"),
    Scenario("canned-vegetables", "A can a few months past its date, with no dents, rust or swelling", KEEP,
             "Cans are safe well past the date as long as the can is in good shape.", "foodkeeper"),
    Scenario("bananas", "Bananas covered in brown spots", KEEP,
             "Brown spots mean they're very ripe, not spoiled. They're great for baking.", "msu_bananas"),
    Scenario("ground-beef", "Ground beef you bought yesterday, red on top and grayish brown inside", KEEP,
             "That's normal. The inside just didn't get air. Color alone doesn't mean it's spoiled.", "fsis_color"),
    Scenario("raw-chicken", "Raw chicken that feels slimy and sticky", TOSS,
             "A slimy or sticky feel, or an off smell, means it has spoiled. Don't use it.", "fsis_color"),
    Scenario("eggs", "An egg that floats in water, but looks and smells normal when you crack it", KEEP,
             "A floating egg is older and lower quality, but it may still be safe. Checking it in a bowl first, like you did, is the right move.", "fsis_eggs"),
    Scenario("potatoes", "A firm potato with a few small sprouts", CUT,
             "Cut away the sprouts and any green parts, then use it.", "isu_potatoes"),
    Scenario("potatoes", "A potato that's green under the skin", TOSS,
             "The green part has a natural toxin, and cooking doesn't remove it.", "ndsu_potatoes"),
    Scenario("leafy-greens", "Lettuce that's slimy with black spots", TOSS,
             "The slime comes from bacteria, and the black spots are usually mold.", "illinois_lettuce"),
    Scenario("milk", "A carton of milk left on the counter for 3 hours", TOSS,
             "Food that needs the fridge shouldn't sit out more than 2 hours.", "fda_storing"),
    Scenario("deli-meat", "Deli turkey with a fuzzy spot of mold", TOSS,
             "Deli meat is moist, so mold spreads below the surface. Throw it out.", "fsis_mold"),
    Scenario("cooked-rice", "Rice left in the rice cooker overnight after it was turned off", TOSS,
             "Rice should go in the fridge within 2 hours. It can look and smell normal and still make you sick.", "usu_rice"),
    Scenario("fish", "Raw fish with a sour, ammonia smell", TOSS,
             "A sour, rancid, fishy or ammonia smell means it has spoiled.", "fda_seafood"),
]

# ---------------------------------------------------------------------------------------------
# The Work page entry (after Recipe Finder). "drawing" is a drawing name like a food's slug.
# ---------------------------------------------------------------------------------------------
WORK_ENTRY = {
    "drawing": "keep-or-toss",
    "alt": "A fridge with its door open, a banana and a milk carton on the shelves",
    "link_text": "Open the app",
    "points": [
        "Look up a food and see where to store it and how long it lasts.",
        "Learn the signs that it's time to use it soon, or toss it.",
        "Play a quick game to test what you know.",
    ],
    "why": ("Placeholder, rewrite me: I built this because a lot of the people I worked with weren't "
            "sure what was still safe to eat, and nobody wants to waste food."),
    "note": ("Anyone can use this, but it was made with food pantry clients in mind. It's general "
             "guidance based on USDA and FDA information, not a medical guide."),
}
