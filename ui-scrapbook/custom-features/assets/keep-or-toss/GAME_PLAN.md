# Find the Three: game plan and drawing list

A plan for the next Keep, Toss, Refrigerate, or Freeze game. Nothing here is built yet.
Working name: **Find the Three** (change it in one place, like the app's name).

Choices marked **Decided** are yours. Choices marked **Proposed** are my suggestions; change any of
them before we build.

---

## 1. How it plays

1. **Pick a place.** The player taps the **fridge door handle**, the **produce basket**, or the
   **pantry cupboard**. The fridge swings open onto its shelves, the basket tips out onto the
   counter, and the cupboard doors open onto shelves of cans, jars and bread.
2. **Look at the foods.** A small group of foods appears, each in one version: unripe, ripe, very
   ripe, moldy, dented, past a date, left out, and so on. Each food has its clues: the drawing
   itself, plus a small tag when the problem can't be seen (see section 3).
3. **Find the three to toss.** Exactly three foods in every set need to be thrown out. The player
   taps the ones they think should go.
4. **After each tap:**
   - **Right (it should be tossed):** the food goes in the trash with a short reason.
     *"Shredded cheese can carry mold all through the bag. Throw it out, even if the spot is small."*
   - **Wrong (it's still fine):** the food stays, and a card explains why it's OK, then lists its
     storage options (the plans from that food's page: counter, pantry, fridge or freezer, and how
     long it lasts). *"Brown spots mean it's very ripe, not spoiled. Bake with it, or peel and freeze it."*
5. **Set done.** When all three are found, a short summary shows the three tosses and any foods
   tapped by mistake.
6. **Bonus round.** One of the foods that stayed comes back with the question "Where should this go?"
   and four buttons: Counter, Pantry, Fridge, Freezer (see section 2b). Then **Next set**, which is harder.
7. **End.** After the last level in that place, the player can try another place or start over.

**Decided:**
- **No penalty for wrong taps.** No points lost, no lives, no losing. A wrong tap only shows why the
  food is fine and how to store it.
- **The quiz moves inside the game.** The current 10 question game becomes a button on the game's
  start screen: **Test your food storage knowledge**. It works the way it does now.

**Proposed:**
- With no penalty there's no score to lose. The game remembers the furthest level reached in each
  place, in the browser only, and still works if the browser blocks storage.
- A **Hint** button outlines one of the remaining tosses after two wrong taps. It never costs anything.

## 2. Levels

Each place (fridge, basket, pantry) has three levels. Every set always has exactly 3 tosses; the
rest are keeps.

| Level | Foods in a set | What makes it harder |
|---|---|---|
| 1. Easy to spot | 6 (3 toss, 3 keep) | Big, obvious signs: fuzzy mold, a bulging can, slimy lettuce. Keeps are clearly fine. |
| 2. Look closer | 8 (3 toss, 5 keep) | Small signs: one spot of mold on shredded cheese, green under a potato's skin. Trick keeps: brown spotted bananas, a carrot with one mold spot (cut it off), stale bread. |
| 3. Can't see it | 9 (3 toss, 6 keep) | The problem is time or temperature, shown with a tag: chili left out all night, milk left out 3 hours, rice left in the cooker. Trick keeps: a can past its "Best if Used By" date with no damage, ground beef that's gray inside. |

**Proposed:** each new set is picked at random, so replaying gives a different mix. The three
tosses come from that level. The keeps can come from that level or an easier one, since the harder
levels need more of them. The build checks that every place and level has at least 3 tosses
and enough keeps to fill a set.

"Foods in a set" is how many foods are on the screen at once. More foods means more to look through
to find the same three. **Proposed:** 6, 8 and 9 (waiting on your OK).

Level 3 matters most for safety. The app's first rule is that the germs that cause food poisoning
usually don't change how food looks or smells. If every toss in the game were something you can
see, it would teach the opposite.

## 2b. Bonus round: where does it go?

**Decided:** after each set, one food that stayed (a keep) comes back with the question
"Where should this go?" and four buttons: **Counter, Pantry, Fridge, Freezer**.

- The right answers come from that food's plans on its page, so there's nothing new to write. Many
  foods have more than one right answer (bananas: counter or freezer), and every one of them counts.
- After answering, the card shows each right place with how to store it there and how long it lasts,
  in the same words as the food page.
- A wrong answer gets a short reason from the food's facts, like "The fridge takes away a tomato's
  flavor", and no penalty, like the rest of the game.
- The bonus round leans on foods where the place matters most: bananas, tomatoes and avocados
  (counter, then maybe the fridge), potatoes and onions (pantry, not the fridge), raw meat and fish
  (fridge or freezer), and opened cans (out of the can and into the fridge).
- Kids mode asks the same question with simpler words.

## 3. Clues the drawings can't show

Some reasons to toss (or keep) can't be drawn on the food. These show as small tags next to it, and
screen readers read them too:

| Tag | Example | Drawing name |
|---|---|---|
| Clock | "Left out 3 hours" / "Left on the stove overnight" | `tag-clock` |
| Date label | "Best if Used By (last month)" / "Use By (yesterday)" on infant formula | `tag-date` |
| Note | "Cooked 6 days ago" / "Opened 4 days ago" | `tag-note` |
| Nose | "Smells sour, like ammonia" (fish) | `tag-smell` |
| Thermometer | "Fridge reads 50°F" (a level 3 idea for later) | `tag-thermometer` |

## 4. Kids mode

**Decided:** a **Kids** button on the same game, not a separate game. Same places and drawings,
with these differences:

- Simpler words. Every food version gets a second, shorter reason written for kids.
  *Grown up:* "Shredded cheese can carry mold all through the bag from the tools that cut it."
  *Kids:* "Mold can hide in the whole bag of cheese. Toss it."
- Bigger pictures and fewer foods (**Proposed:** 5 per set, with 3 to toss).
- Levels 1 and 2 as they are. Level 3 (time and temperature) uses just one rule, said simply:
  "Food that should be cold can't stay out longer than 2 hours."
- No score, just stars for each set cleared.
- A line on every screen: "Ask a grown up before you throw food away." Kids are never told to touch
  raw meat or moldy food, or to smell anything moldy (USDA says not to sniff moldy food).
- Kids text gets the same source check as the grown up text.

## 5. How it connects to what's built

- Each **food version** is one new entry in `keep_or_toss_content.py`, next to its food:
  the version name, drawing name, place (fridge, basket or pantry), level, verdict (toss or keep),
  any tag, the reason, the kids reason, and its source key.
- A wrong tap shows the food's **existing plans** (where, how, how long), so storage advice stays in
  one place.
- The build checks every version: it needs a source, a reason and a kids reason, and a drawing
  (yours or a stand-in). It prints which versions still use stand-ins, like it does now.
- **Accessibility:** every food is a real button you can reach with the keyboard. Each drawing's
  description names the clue ("Shredded cheese with a small fuzzy green spot"), since mold can't be
  heard. Right and wrong always show an icon and words, never just a color. The fridge door
  animation is skipped when the device asks for less motion.
- Spanish later: all the words stay in the content file, like the rest of the app.

## 6. Decisions

| Question | Answer |
|---|---|
| Kids version | **Decided:** a Kids button on the same game |
| Wrong taps | **Decided:** no penalty |
| The current quiz | **Decided:** a button inside the game, "Test your food storage knowledge" |
| Cans and bread | **Decided:** a third place, the pantry cupboard |
| Where does it go? | **Decided:** a bonus round after each set |
| Foods on screen per set | **Open:** proposed 6, 8 and 9 for Levels 1, 2 and 3 (Kids: 5) |

---

## 7. Drawing list

Name each drawing after the food and version, with the two layers like the rest of the app:
`bananas-spotted-color.webp` and `bananas-spotted-ink.webp` (or a single `.png`). Save them in this
folder. Until a drawing exists, the build uses a stand-in.

**Toss** or **Keep** is the answer in the game. *Cut* means keep it after cutting off the bad part.
The source column is the key in `keep_or_toss_content.py` (SOURCES).

### Scenes

| Drawing | What it shows |
|---|---|
| `scene-fridge-closed` | The fridge, door shut, with a big handle to tap |
| `scene-fridge-open` | The open fridge: two or three shelves and a door with shelves |
| `scene-basket` | A produce basket on a counter |
| `scene-pantry-closed` | The pantry cupboard, doors shut, with handles to tap |
| `scene-pantry-open` | The open cupboard: shelves for cans, jars and bread |
| `scene-counter` | The counter the basket's foods are laid out on |
| `trash-can` | Where tossed foods go |
| `tag-clock`, `tag-date`, `tag-note`, `tag-smell`, `tag-thermometer` | The clue tags (section 3) |

### Fridge

| Food | Version (drawing name) | What to draw | Answer | Level | Source |
|---|---|---|---|---|---|
| Milk | `milk-fine` | A carton, nothing wrong | Keep | 1 | foodkeeper |
| Eggs | `eggs-carton` | A carton of eggs on a shelf | Keep | 1 | fsis_eggs |
| Eggs | `eggs-floating` | An egg floating in a glass of water | Keep | 2 | fsis_eggs |
| Hard cheese | `hard-cheese-spot` | A block with one small mold spot on a corner | Keep (cut) | 2 | fsis_mold |
| Shredded cheese | `shredded-cheese-moldy` | An open bag with a small fuzzy spot | Toss | 2 | fsis_mold |
| Shredded cheese | `shredded-cheese-fine` | A sealed bag | Keep | 1 | foodkeeper |
| Soft cheese | `soft-cheese-moldy` | Cream cheese with a spot of mold | Toss | 1 | fsis_mold |
| Yogurt | `yogurt-moldy` | A cup with mold on top | Toss | 1 | fsis_mold |
| Yogurt | `yogurt-fine` | A sealed cup | Keep | 1 | foodkeeper |
| Deli meat | `deli-meat-moldy` | Slices with a fuzzy spot | Toss | 1 | fsis_mold |
| Deli meat | `deli-meat-sealed` | A sealed package | Keep | 1 | foodkeeper |
| Deli meat | `deli-meat-opened-week` + note "opened 7 days ago" | An open package | Toss | 3 | foodkeeper |
| Raw chicken | `raw-chicken-slimy` | Shiny, slimy chicken in its tray | Toss | 2 | fsis_color |
| Raw chicken | `raw-chicken-dark-bone` | Chicken with darker meat near the bone | Keep | 3 | fsis_chicken |
| Ground beef | `ground-beef-gray-inside` | Red on top, grayish brown where it's cut open | Keep | 3 | fsis_color |
| Ground beef | `ground-beef-slimy` | Sticky, slimy meat | Toss | 2 | fsis_color |
| Raw fish | `fish-smell` + smell tag | A fillet; the tag says it smells sour | Toss | 3 | fda_seafood |
| Leftovers | `leftovers-3-days` + note "cooked 3 days ago" | A container of soup | Keep | 3 | fsis_leftovers |
| Leftovers | `leftovers-6-days` + note "cooked 6 days ago" | A container of soup | Toss | 3 | fsis_leftovers |
| Leftovers | `leftovers-moldy` | A casserole with mold on the edge | Toss | 1 | fsis_mold |
| Leftovers | `leftovers-frozen` + note "frozen 8 months ago" | A frosty container | Keep | 3 | fsis_leftovers |
| Jam | `jam-moldy` | An open jar with mold on top | Toss | 1 | fsis_mold |
| Jam | `jam-open` | An open jar, nothing wrong | Keep | 1 | foodkeeper |
| Berries | `berries-moldy` | A box with fuzzy berries | Toss | 1 | fsis_mold |
| Berries | `berries-fine` | A box of fresh berries | Keep | 1 | foodkeeper |
| Leafy greens | `leafy-greens-slimy` | Lettuce with slime and black spots | Toss | 1 | illinois_lettuce |
| Leafy greens | `leafy-greens-wilted` | Lettuce with a few wilted outer leaves | Keep | 2 | umaine_storing |
| Carrots | `carrots-spot` | A carrot with one small mold spot | Keep (cut) | 2 | fsis_mold |
| Broccoli | `broccoli-yellowing` | Broccoli with some yellow buds | Keep (use soon) | 2 | ndsu_vegetables |
| Butter | `butter-stick` | A stick of butter | Keep | 1 | foodkeeper |

### Basket and counter

| Food | Version (drawing name) | What to draw | Answer | Level | Source |
|---|---|---|---|---|---|
| Bananas | `bananas-green` | A green bunch | Keep | 1 | usu_bananas |
| Bananas | `bananas-ripe` | A yellow bunch | Keep | 1 | unl_bananas |
| Bananas | `bananas-spotted` | Covered in brown spots | Keep | 2 | msu_bananas |
| Bananas | `bananas-moldy` | Moldy at the stem | Toss | 2 | fsis_mold |
| Apples | `apples-bruised` | An apple with a small bruise | Keep (cut) | 2 | fda_produce |
| Apples | `apples-rotten` | A rotten apple | Toss | 1 | fda_produce |
| Avocados | `avocados-unripe` | A hard green avocado | Keep | 1 | illinois_avocados |
| Avocados | `avocados-rotten` | A rotten avocado | Toss | 2 | fda_produce |
| Tomatoes | `tomatoes-ripe` | A red tomato | Keep | 1 | foodkeeper |
| Tomatoes | `tomatoes-moldy` | A tomato with a fuzzy patch | Toss | 1 | fsis_mold |
| Citrus | `citrus-fine` | An orange and a lemon | Keep | 1 | foodkeeper |
| Citrus | `citrus-moldy` | An orange with mold | Toss | 1 | fsis_mold |
| Grapes | `grapes-moldy` | A bunch with a few fuzzy grapes | Toss | 2 | fsis_mold |
| Potatoes | `potatoes-sprouts` | A firm potato with a few small sprouts | Keep (cut) | 2 | isu_potatoes |
| Potatoes | `potatoes-green` | A potato that's green under the skin | Toss | 2 | ndsu_potatoes |
| Potatoes | `potatoes-shriveled` | Shriveled, lots of sprouts, green | Toss | 1 | isu_potatoes |
| Onions | `onions-fine` | A dry onion | Keep | 1 | unh_produce |
| Onions | `onions-damp-neck` | An onion soft and damp at the top | Toss | 2 | ndsu_vegetables |
| Chili (counter) | `chili-overnight` + clock tag "all night" | A pot on the stove | Toss | 3 | fsis_leftovers |
| Milk (counter) | `milk-left-out` + clock tag "3 hours" | A carton sitting on the counter | Toss | 3 | fda_storing |
| Cooked rice (counter) | `cooked-rice-overnight` + clock tag "overnight" | Rice in a rice cooker that's been turned off | Toss | 3 | usu_rice |

### Pantry

| Food | Version (drawing name) | What to draw | Answer | Level | Source |
|---|---|---|---|---|---|
| Canned vegetables | `canned-vegetables-fine` | A good can | Keep | 1 | foodkeeper |
| Canned vegetables | `canned-vegetables-bulging` | A swollen can | Toss | 1 | fsis_shelf |
| Canned vegetables | `canned-vegetables-leaking` | A sticky, leaking can | Toss | 1 | fsis_shelf |
| Bread | `bread-fine` | A fresh loaf | Keep | 1 | foodkeeper |
| Bread | `bread-moldy` | A loaf with fuzzy green dots | Toss | 1 | fsis_mold |
| Jam | `jam-sealed` | A sealed jar | Keep | 1 | foodkeeper |
| Tortillas | `tortillas-sealed` | A sealed package of flour tortillas | Keep | 1 | foodkeeper |
| Canned vegetables | `canned-vegetables-small-dent` | A can with a small dent on the side | Keep | 2 | fsis_shelf |
| Canned vegetables | `canned-vegetables-rust-wipes` | A little surface rust that rubs off | Keep | 2 | fsis_shelf |
| Canned vegetables | `canned-vegetables-seam-dent` | A deep dent on the seam | Toss | 2 | fsis_shelf |
| Canned vegetables | `canned-vegetables-heavy-rust` | A can covered in rust | Toss | 2 | fsis_shelf |
| Canned vegetables | `canned-vegetables-milky` | An open can with milky liquid around vegetables that should be in clear liquid | Toss | 2 | fsis_shelf |
| Bread | `bread-stale` | A dry, stale loaf | Keep | 2 | ucanr_bread |
| Canned vegetables | `canned-vegetables-past-date` + date tag | A good can, past its "Best if Used By" date | Keep | 3 | foodkeeper |
| Canned vegetables | `canned-vegetables-spurted` + note "spurted when opened" | An open can with splashes around it | Toss | 3 | fsis_shelf |
| Opened canned food | `opened-canned-food-in-cupboard` + note "opened yesterday" | An open can left on the shelf | Toss | 3 | fsis_shelf |
| Infant formula | `formula-use-by` + date tag "Use By: yesterday" | A formula container | Toss | 3 | fda_formula |
| Infant formula | `formula-in-date` + date tag "Use By: next month" | A formula container | Keep | 3 | fda_formula |

That's 30 fridge versions, 21 basket and counter versions, and 18 pantry versions, plus the scenes
and tags. Every place has at least 3 tosses at every level. You don't need all of them to start:
Level 1 alone needs 3 tosses and 3 keeps per place.

### Versions left out until there's a source

- A cracked egg at home: USDA only says not to buy cracked eggs.
- Limp carrots, sprouted onions, soft or wrinkled berries and grapes: no source says whether they're fine.
- Moldy butter: the USDA mold chart has no row for butter.
