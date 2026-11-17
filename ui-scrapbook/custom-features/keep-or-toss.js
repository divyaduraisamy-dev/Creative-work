/*
 * Keep or Toss: search and food groups (home), plan choices (food pages), and the game.
 * Plain JavaScript, no libraries. Every visible word comes from the page (keep_or_toss_content.py,
 * passed in <script type="application/json" id="k-data">), so nothing here needs translating.
 * Without this script the pages still work: every food is listed, every plan is shown, and the
 * game page says it needs JavaScript.
 *
 * Hooks: #k-data (words and game rounds), #k-finder (home), .k-choices + .k-plan (food pages),
 *        #k-game (game page).
 */
const KeepOrToss = {
  data: {},

  init() {
    const el = document.getElementById("k-data");
    try { this.data = el ? JSON.parse(el.textContent) : {}; } catch (e) { this.data = {}; }
    const finder = document.getElementById("k-finder");
    if (finder) KeepOrTossFinder.init(finder, this.data.text || {});
    document.querySelectorAll(".k-choices").forEach((group) => KeepOrTossPlans.init(group));
    const game = document.getElementById("k-game");
    if (game && this.data.rounds) KeepOrTossGame.init(game, this.data);
  },

  /* "Round {n} of {total}" with the numbers filled in. */
  fill(text, values) {
    return String(text).replace(/\{(\w+)\}/g, (m, k) => (k in values ? values[k] : m));
  },

  escape(text) {
    const d = document.createElement("div");
    d.textContent = String(text);
    return d.innerHTML;
  },
};

/* Home: search box plus food group buttons. */
const KeepOrTossFinder = {
  init(root, text) {
    const form = root.querySelector(".k-search");
    const input = root.querySelector("#k-search-input");
    const chips = root.querySelector(".k-chips");
    const count = root.querySelector(".k-count");
    const none = root.querySelector(".k-none");
    const cards = Array.from(root.querySelectorAll(".k-card"));
    const groups = Array.from(root.querySelectorAll(".k-group"));
    form.hidden = false;
    chips.hidden = false;
    cards.forEach((card) => { card.words = this.words(card.dataset.search || ""); });
    let group = "";

    const update = (announce) => {
      const query = this.words(input.value);
      let shown = 0;
      groups.forEach((g) => {
        const inGroup = !group || g.dataset.group === group;
        let visible = 0;
        g.querySelectorAll(".k-card").forEach((card) => {
          const ok = inGroup && query.every((q) => card.words.some((w) => w.startsWith(q)));
          card.hidden = !ok;
          if (ok) visible += 1;
        });
        g.hidden = visible === 0;
        shown += visible;
      });
      none.hidden = shown > 0;
      if (announce) count.textContent = shown === 1 ? text.count_one : KeepOrToss.fill(text.count_many, { n: shown });
    };

    input.addEventListener("input", () => update(true));
    chips.querySelectorAll("[data-filter]").forEach((chip) => chip.addEventListener("click", () => {
      group = chip.dataset.filter;
      chips.querySelectorAll("[data-filter]").forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      update(true);
    }));
    update(false);
  },

  /* Lowercase words without accents or punctuation, with plurals trimmed (berries = berry). */
  words(text) {
    return String(text).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, " ").trim().split(" ").filter(Boolean)
      .map((w) => (w.length > 4 && w.endsWith("ies") ? w.slice(0, -3) + "y"
        : w.length > 4 && w.endsWith("oes") ? w.slice(0, -2)
        : w.length > 3 && w.endsWith("s") && !w.endsWith("ss") ? w.slice(0, -1) : w));
  },
};

/* Food pages: "What's your plan?" buttons show one plan at a time. */
const KeepOrTossPlans = {
  init(group) {
    const section = group.closest(".k-section");
    const buttons = Array.from(group.querySelectorAll("[aria-controls]"));
    const panels = buttons.map((b) => document.getElementById(b.getAttribute("aria-controls")));
    if (buttons.length < 2) return;
    group.hidden = false;
    const help = section && section.querySelector(".k-help");
    if (help) help.hidden = false;
    const show = (i) => {
      buttons.forEach((b, j) => b.setAttribute("aria-pressed", String(i === j)));
      panels.forEach((p, j) => { if (p) p.hidden = i !== j; });
    };
    buttons.forEach((b, i) => b.addEventListener("click", () => show(i)));
    show(0);
  },
};

/* The "Keep or Toss?" game: 10 random rounds, a reason after each, a score at the end. */
const KeepOrTossGame = {
  init(root, data) {
    const g = {
      root, data, text: data.text, rounds: [], index: 0, score: 0,
      start: root.querySelector("[data-start]"),
      best: root.querySelector("[data-best]"),
      area: document.createElement("div"),
    };
    root.appendChild(g.area);
    g.start.parentElement.hidden = false;
    g.start.addEventListener("click", () => this.begin(g));
    this.showBest(g);
  },

  /* Best score lives in this browser only; if storage is blocked the game still works. */
  readBest(g) {
    try { const v = parseInt(window.localStorage.getItem(g.data.storageKey), 10); return Number.isFinite(v) ? v : null; }
    catch (e) { return null; }
  },

  saveBest(g, score) {
    try { window.localStorage.setItem(g.data.storageKey, String(score)); } catch (e) { /* blocked: fine */ }
  },

  showBest(g) {
    const best = g.bestInMemory ?? this.readBest(g);
    g.best.hidden = best === null;
    if (best !== null) g.best.textContent = KeepOrToss.fill(g.text.game_best, { best, total: this.total(g) });
  },

  total(g) {
    return Math.min(g.data.count, g.data.rounds.length);
  },

  shuffle(list) {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  },

  begin(g) {
    g.rounds = this.shuffle(g.data.rounds).slice(0, this.total(g));
    g.index = 0;
    g.score = 0;
    g.start.parentElement.hidden = true;
    g.best.hidden = true;
    this.round(g);
  },

  round(g) {
    const r = g.rounds[g.index];
    const t = g.text;
    const esc = KeepOrToss.escape;
    const buttons = ["keep", "cut", "toss"].map((a) =>
      `<li><button type="button" class="k-btn" data-answer="${a}">${g.data.icons[a]}<span>${esc(t.answers[a])}</span></button></li>`).join("");
    g.area.innerHTML =
      `<p class="k-round__count">${esc(KeepOrToss.fill(t.game_round, { n: g.index + 1, total: g.rounds.length }))}</p>` +
      `<div class="k-round__card">${r.art}<p class="k-round__food">${esc(r.name)}</p>` +
      `<p class="k-round__situation" tabindex="-1">${esc(r.situation)}</p></div>` +
      `<h2 class="k-round__question">${esc(t.game_question)}</h2>` +
      `<ul class="k-answers">${buttons}</ul><div class="k-feedback-slot"></div>`;
    g.area.querySelectorAll("[data-answer]").forEach((b) => b.addEventListener("click", () => this.answer(g, b)));
    const focus = g.area.querySelector(".k-round__situation");
    if (g.index > 0 || g.focusOnStart !== false) focus.focus({ preventScroll: false });
  },

  answer(g, button) {
    const r = g.rounds[g.index];
    const t = g.text;
    const esc = KeepOrToss.escape;
    const right = button.dataset.answer === r.answer;
    if (right) g.score += 1;
    g.area.querySelectorAll("[data-answer]").forEach((b) => {
      b.disabled = true;
      if (b === button) b.classList.add("is-chosen");
      if (b.dataset.answer === r.answer) b.classList.add("is-right");
    });
    const last = g.index + 1 >= g.rounds.length;
    const slot = g.area.querySelector(".k-feedback-slot");
    slot.innerHTML =
      `<div class="k-feedback"><h3 tabindex="-1">${esc(right ? t.game_right : t.game_wrong)}</h3>` +
      `<p>${esc(t.game_answer_is)}</p>` +
      `<p class="k-verdict k-verdict--${r.answer}">${g.data.icons[r.answer]}<strong>${esc(t.answers[r.answer])}</strong></p>` +
      `<p>${esc(r.reason)}</p>` +
      `<p class="k-feedback__source">${esc(t.game_source)} <a href="${esc(r.source.url)}" rel="noopener">${esc(r.source.title)}</a></p>` +
      `<p class="k-feedback__actions"><button type="button" class="k-btn k-btn--main" data-next>${esc(last ? t.game_finish : t.game_next)}</button>` +
      `<a href="${esc(r.url)}">${esc(KeepOrToss.fill(t.game_learn_more, { food: r.name }))}</a></p></div>`;
    slot.querySelector("h3").focus();
    slot.querySelector("[data-next]").addEventListener("click", () => {
      g.index += 1;
      if (last) this.finish(g); else this.round(g);
    });
  },

  finish(g) {
    const t = g.text;
    const esc = KeepOrToss.escape;
    const total = g.rounds.length;
    const old = g.bestInMemory ?? this.readBest(g);
    const isBest = old === null || g.score > old;
    if (isBest) { g.bestInMemory = g.score; this.saveBest(g, g.score); }
    const best = isBest ? g.score : old;
    g.area.innerHTML =
      `<div class="k-score"><h2 class="k-score__number" tabindex="-1">${esc(KeepOrToss.fill(t.game_score, { score: g.score, total }))}</h2>` +
      `<p>${esc(isBest && old !== null ? t.game_best_new : KeepOrToss.fill(t.game_best, { best, total }))}</p>` +
      `<p><button type="button" class="k-btn k-btn--main" data-again>${esc(t.game_again)}</button></p></div>`;
    g.area.querySelector("h2").focus();
    g.area.querySelector("[data-again]").addEventListener("click", () => this.begin(g));
  },
};

window.KeepOrToss = KeepOrToss;
