/*
 * Interactions: custom features (your own site pieces)
 * Written from scratch; no outside libraries (Web Animations API + a small spring simulation).
 *
 * HOW TO USE
 *   Nothing runs on load. Start what you need:
 *     CustomLogoLoader.init("c-logo-loader");   // full-screen logo draw-in, once per session
 *     CustomPetHead.init("c-pet-head");          // grabbable, tilting dog drawing
 *     CustomCornerLogo.init("c-corner-logo");    // pinned top-left logo
 *     CustomSiteHeader.init("c-site-header");    // header (also starts CustomSiteTheme)
 *     CustomTorchReveal.init("c-pet-head");      // hold-and-drag light that shows a hidden picture
 *     CustomWalkPlanner.init("c-walk-button");   // pulling the walk button opens the walk planner
 *   init() accepts an element id or an element and is safe to call twice.
 *   CustomPageTransition (logo takes over the screen between pages) is started by the header.
 *
 * Feature modules (default element id):
 *   CustomLogoLoader  #c-logo-loader   outline draw-in, fill, frame lines, lift-off reveal
 *   CustomPetHead     #c-pet-head      hover tilt + swell, grab squash/stretch, spring wobble
 *   CustomCornerLogo  #c-corner-logo   pinned logo: hover colour swap, spring tilt, back to top
 *   CustomSiteHeader  #c-site-header   hairline header: lines bend from the cursor, menu, LinkedIn,
 *                                      Contact email reveal, page colour toggle (CustomSiteTheme)
 */

/* Shared helpers ----------------------------------------------------------------------------- */
const CustomEnv = {
  reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,

  resolve(target) {
    return typeof target === "string" ? document.getElementById(target) : target || null;
  },

  // Marks an element as handled so a second init (e.g. a Streamlit rerun) does nothing.
  claim(el) {
    if (!el || el.dataset.enhanced) return false;
    el.dataset.enhanced = "true";
    return true;
  },

  session: {
    get(key) { try { return window.sessionStorage.getItem(key); } catch (e) { return null; } },
    set(key, value) { try { window.sessionStorage.setItem(key, value); } catch (e) { /* blocked */ } },
  },

  // Scroll the window and any scrolled inner panel (e.g. Streamlit's main section) to the top.
  scrollToTop(instant = false) {
    const behavior = instant || CustomEnv.reducedMotion ? "auto" : "smooth";
    const scrolled = [document.scrollingElement || document.documentElement];
    document.querySelectorAll("body *").forEach((node) => { if (node.scrollTop > 0) scrolled.push(node); });
    scrolled.forEach((node) => node.scrollTo({ top: 0, behavior }));
  },

  ease: {
    inOut: "cubic-bezier(0.65, 0, 0.35, 1)",
    out: "cubic-bezier(0.16, 1, 0.3, 1)",
    in: "cubic-bezier(0.7, 0, 0.84, 0)",
  },
};

/* Logo loader -------------------------------------------------------------------------------------
 * Timeline (default speed 1):
 *   0.0s  each logo piece's outline draws (1.2s each, pieces staggered over ~0.9s)
 *   1.5s  the solid logo fades in while the outlines fade out (0.6s)
 *   1.2s  frame lines grow from their centres (1s)
 *   2.6s  the cover lifts upward (0.8s), then the element is hidden. If the corner logo
 *         (options.dockTo) is on the page, the logo glides into its spot and takes its colour;
 *         otherwise it shrinks slightly and fades.
 * Click / tap / Escape skips. Plays once per browser session (sessionStorage) unless
 * options.oncePerSession is false. Always fires document "logoloader:done" when it is out of the
 * way, also when skipped or already seen (detail: { played, docked }). While it plays,
 * <html data-logo-loader="playing">; afterwards "done".
 */
const CustomLogoLoader = {
  el: null,
  options: {
    oncePerSession: true,
    storageKey: "custom-logo-loader-seen",
    speed: 1,          // 2 = twice as fast
    strokeWidth: 1.5,  // outline thickness in screen pixels
    dockTo: "c-site-header",  // element id whose [data-logo] the logo glides into (false: no glide)
  },
  docked: false,
  timers: [],
  isDone: false,

  init(target = "c-logo-loader", options = {}) {
    const el = CustomEnv.resolve(target);
    if (!CustomEnv.claim(el)) return;
    this.el = el;
    Object.assign(this.options, options);

    if (this.options.oncePerSession && CustomEnv.session.get(this.options.storageKey)) {
      this.finish(true);
      return;
    }
    CustomEnv.session.set(this.options.storageKey, "true");
    document.documentElement.dataset.logoLoader = "playing";
    this.lockScroll(true);
    this.bindEvents();
    if (CustomEnv.reducedMotion) this.playReduced();
    else this.play();
  },

  bindEvents() {
    this.onSkip = () => this.skip();
    this.onKey = (e) => { if (e.key === "Escape") this.skip(); };
    this.el.addEventListener("click", this.onSkip);
    document.addEventListener("keydown", this.onKey);
  },

  lockScroll(lock) {
    document.documentElement.style.overflow = lock ? "hidden" : "";
  },

  t(seconds) {
    return (seconds * 1000) / this.options.speed;
  },

  later(seconds, fn) {
    this.timers.push(setTimeout(fn, this.t(seconds)));
  },

  // Turn every filled <path> into stroked outline copies, one per subpath, so each piece draws.
  buildOutlines(svg) {
    const NS = "http://www.w3.org/2000/svg";
    const outlines = [];
    const fills = Array.from(svg.querySelectorAll("path"));
    fills.forEach((path) => {
      const isFilled = (path.getAttribute("fill") || "currentColor") !== "none";
      const pieces = path.getAttribute("d").split(/(?=[Mm])/).map((s) => s.trim()).filter(Boolean);
      pieces.forEach((d, i) => {
        // A relative "m" only works after the first piece in its original path; keep those whole.
        const piece = document.createElementNS(NS, "path");
        piece.setAttribute("d", i > 0 && d[0] === "m" ? path.getAttribute("d") : d);
        piece.setAttribute("fill", "none");
        piece.setAttribute("stroke", "currentColor");
        piece.setAttribute("stroke-width", String(this.options.strokeWidth));
        piece.setAttribute("vector-effect", "non-scaling-stroke");
        piece.setAttribute("stroke-linecap", "round");
        piece.setAttribute("stroke-linejoin", "round");
        piece.setAttribute("pathLength", "1");
        piece.style.strokeDasharray = "1";
        piece.style.strokeDashoffset = "1";
        svg.appendChild(piece);
        outlines.push(piece);
      });
      if (isFilled) path.style.opacity = "0";
    });
    return { outlines, fills };
  },

  play() {
    const svg = this.el.querySelector("[data-logo]");
    const frames = Array.from(this.el.querySelectorAll("[data-frame]"));
    const { inOut, out, in: easeIn } = CustomEnv.ease;
    const { outlines, fills } = svg ? this.buildOutlines(svg) : { outlines: [], fills: [] };
    const spread = 0.9 / Math.max(1, outlines.length - 1);

    outlines.forEach((p, i) => p.animate(
      [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }],
      { duration: this.t(1.2), delay: this.t(i * spread), easing: inOut, fill: "forwards" }
    ));

    frames.forEach((f) => {
      const axis = f.dataset.frame === "y" ? "scaleY" : "scaleX";
      f.style.transform = axis === "scaleY" ? "scaleX(1) scaleY(0)" : "scaleX(0) scaleY(1)";
      f.animate(
        [{ transform: axis === "scaleY" ? "scaleY(0)" : "scaleX(0)" }, { transform: "scale(1)" }],
        { duration: this.t(1), delay: this.t(1.2), easing: inOut, fill: "forwards" }
      );
    });

    this.later(1.5, () => {
      fills.forEach((p) => p.animate([{ opacity: 0 }, { opacity: 1 }], { duration: this.t(0.6), easing: out, fill: "forwards" }));
      outlines.forEach((p) => p.animate([{ opacity: 1 }, { opacity: 0 }], { duration: this.t(0.6), easing: out, fill: "forwards" }));
    });

    this.later(2.6, () => {
      const docked = svg && this.glideToDock(svg);
      if (svg && !docked) svg.animate([{ transform: "scale(1)", opacity: 1 }, { transform: "scale(0.9)", opacity: 0 }],
        { duration: this.t(0.6), easing: easeIn, fill: "forwards" });
      this.el.animate([{ clipPath: "inset(0 0 0 0)" }, { clipPath: "inset(0 0 100% 0)" }],
        { duration: this.t(0.8), delay: this.t(docked ? 0.35 : 0.25), easing: inOut, fill: "forwards" })
        .finished.then(() => this.finish());
    });
  },

  // Move the logo onto the corner logo (same size, place and colour). Returns true if it glided.
  glideToDock(svg) {
    const dockEl = this.options.dockTo && document.getElementById(this.options.dockTo);
    const dock = dockEl && (dockEl.querySelector("[data-logo]") || dockEl);
    if (!dock) return false;
    const from = svg.getBoundingClientRect();
    const to = dock.getBoundingClientRect();
    if (!from.width || !to.width) return false;
    const dx = to.left + to.width / 2 - (from.left + from.width / 2);
    const dy = to.top + to.height / 2 - (from.top + from.height / 2);
    const scale = to.width / from.width;
    svg.style.transformOrigin = "50% 50%";
    svg.animate([
      { transform: "translate(0, 0) scale(1)", color: getComputedStyle(svg).color },
      { transform: `translate(${dx}px, ${dy}px) scale(${scale})`, color: getComputedStyle(dock).color },
    ], { duration: this.t(0.9), easing: CustomEnv.ease.inOut, fill: "forwards" });
    this.docked = true;
    return true;
  },

  playReduced() {
    this.later(0.8, () => {
      this.el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300, fill: "forwards" })
        .finished.then(() => this.finish());
    });
  },

  skip() {
    if (this.isDone) return;
    this.timers.forEach(clearTimeout);
    this.timers = [];
    this.el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300, easing: CustomEnv.ease.out, fill: "forwards" })
      .finished.then(() => this.finish());
  },

  finish(silent = false) {
    if (this.isDone) return;
    this.isDone = true;
    this.timers.forEach(clearTimeout);
    this.el.hidden = true;
    this.lockScroll(false);
    if (this.onSkip) this.el.removeEventListener("click", this.onSkip);
    if (this.onKey) document.removeEventListener("keydown", this.onKey);
    document.documentElement.dataset.logoLoader = "done";
    document.dispatchEvent(new CustomEvent("logoloader:done", { detail: { played: !silent, docked: this.docked } }));
  },
};

/* Pet head ----------------------------------------------------------------------------------------
 * Every frame, each value (tilt, swell, offset, stretch) moves toward its target on a spring:
 *   velocity += (target - value) * stiffness;  velocity *= damping;  value += velocity
 * Hover: tilt up to options.maxTilt degrees toward the pointer, swell to options.hoverScale.
 * Grab:  follow the pointer by options.follow (clamped to options.maxPull px) and stretch along
 *        the drag direction; on release a looser spring makes it wobble back.
 * Ears (optional layers) lag behind horizontal motion.
 */
const CustomPetHead = {
  instances: new Map(),
  options: {
    maxTilt: 14,          // degrees
    hoverScale: 1.04,
    follow: 0.35,         // share of the drag distance the head follows
    maxPull: 90,          // px
    maxStretch: 0.22,     // 22% longer along the drag at full pull
    spring: { stiffness: 0.14, damping: 0.74 },
    releaseSpring: { stiffness: 0.12, damping: 0.86 }, // looser: wobbles on release
    earLag: 0.6,          // degrees of ear swing per px/frame of movement
    titles: null,         // e.g. { idle: "Kovu :D", hover: "Kovu :o", grab: "Kovu x/" }
  },

  init(target = "c-pet-head", options = {}) {
    const root = CustomEnv.resolve(target);
    if (!CustomEnv.claim(root)) return this.instances.get(root) || null;
    const opts = { ...this.options, ...options };
    const rig = root.querySelector(".c-pet__rig");
    if (!rig) return null;
    const pet = {
      root, rig, opts,
      mover: rig.querySelector('[data-layer="head"]') || rig,
      ears: Array.from(rig.querySelectorAll('[data-layer^="ear"]')),
      value: { rx: 0, ry: 0, s: 1, x: 0, y: 0, stretch: 0, angle: 0, ear: 0 },
      vel: { rx: 0, ry: 0, s: 0, x: 0, y: 0, stretch: 0, ear: 0 },
      target: { rx: 0, ry: 0, s: 1, x: 0, y: 0, stretch: 0, ear: 0 },
      spring: opts.spring,
      mood: "idle",
      dragStart: null,
      frame: null,
      lastX: 0,
    };
    this.instances.set(root, pet);
    this.bindEvents(pet);
    this.setMood(pet, "idle");
    return pet;
  },

  bindEvents(pet) {
    const { rig } = pet;
    rig.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse" && !pet.dragStart) this.setMood(pet, "hover"); this.wake(pet); });
    rig.addEventListener("pointermove", (e) => this.onMove(pet, e));
    rig.addEventListener("pointerleave", () => { if (!pet.dragStart) this.rest(pet); });
    rig.addEventListener("pointerdown", (e) => this.onDown(pet, e));
    window.addEventListener("pointermove", (e) => { if (pet.dragStart) this.onDrag(pet, e); });
    window.addEventListener("pointerup", () => this.onUp(pet));
    window.addEventListener("pointercancel", () => this.onUp(pet));
  },

  setMood(pet, mood) {
    pet.mood = mood;
    pet.root.dataset.mood = mood;
    if (pet.opts.titles && pet.opts.titles[mood]) document.title = pet.opts.titles[mood];
  },

  onMove(pet, e) {
    if (pet.dragStart || CustomEnv.reducedMotion) return;
    const r = pet.rig.getBoundingClientRect();
    const dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);   // -1 .. 1
    const dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
    pet.target.ry = Math.max(-1, Math.min(1, dx)) * pet.opts.maxTilt;
    pet.target.rx = -Math.max(-1, Math.min(1, dy)) * pet.opts.maxTilt;
    pet.target.s = pet.opts.hoverScale;
    pet.spring = pet.opts.spring;
    this.wake(pet);
  },

  onDown(pet, e) {
    if (e.button !== 0) return;
    pet.dragStart = { x: e.clientX, y: e.clientY };
    try { pet.rig.setPointerCapture(e.pointerId); } catch (err) { /* pointer already gone */ }
    this.setMood(pet, "grab");
    pet.target.rx = 0;
    pet.target.ry = 0;
    pet.target.s = 1;
    pet.spring = pet.opts.spring;
    this.wake(pet);
  },

  onDrag(pet, e) {
    if (CustomEnv.reducedMotion) return;
    const dx = e.clientX - pet.dragStart.x;
    const dy = e.clientY - pet.dragStart.y;
    const dist = Math.hypot(dx, dy);
    const pull = Math.min(pet.opts.maxPull, dist * pet.opts.follow);
    const scale = dist ? pull / dist : 0;
    pet.target.x = dx * scale;
    pet.target.y = dy * scale;
    pet.target.stretch = (pull / pet.opts.maxPull) * pet.opts.maxStretch;
    if (dist > 2) pet.value.angle = Math.atan2(dy, dx);
    this.wake(pet);
  },

  onUp(pet) {
    if (!pet.dragStart) return;
    pet.dragStart = null;
    pet.target.x = 0;
    pet.target.y = 0;
    pet.target.stretch = 0;
    pet.spring = pet.opts.releaseSpring;
    // Give the release a kick toward the centre so it overshoots and wobbles.
    pet.vel.x -= pet.value.x * 0.25;
    pet.vel.y -= pet.value.y * 0.25;
    pet.vel.stretch -= pet.value.stretch * 0.5;
    const pull = Math.min(1, Math.hypot(pet.value.x, pet.value.y) / pet.opts.maxPull);
    pet.root.dispatchEvent(new CustomEvent("pet:release", { bubbles: true, detail: { pull } }));
    this.setMood(pet, pet.rig.matches(":hover") ? "hover" : "idle");
    this.wake(pet);
  },

  rest(pet) {
    pet.target.rx = 0;
    pet.target.ry = 0;
    pet.target.s = 1;
    pet.spring = pet.opts.spring;
    this.setMood(pet, "idle");
    this.wake(pet);
  },

  wake(pet) {
    if (!pet.frame) pet.frame = requestAnimationFrame(() => this.step(pet));
  },

  step(pet) {
    pet.frame = null;
    const { value: v, vel, target: t, spring } = pet;
    let moving = false;
    for (const key of ["rx", "ry", "s", "x", "y", "stretch", "ear"]) {
      vel[key] += (t[key] - v[key]) * spring.stiffness;
      vel[key] *= spring.damping;
      v[key] += vel[key];
      if (Math.abs(vel[key]) > 0.0005 || Math.abs(t[key] - v[key]) > 0.0005) moving = true;
    }
    // Ears swing against horizontal movement, then settle.
    const dxFrame = v.x - pet.lastX;
    pet.lastX = v.x;
    t.ear = Math.max(-18, Math.min(18, -dxFrame * pet.opts.earLag * 10));
    this.render(pet);
    if (moving) this.wake(pet);
  },

  render(pet) {
    const v = pet.value;
    const deg = (v.angle * 180) / Math.PI;
    const sx = 1 + v.stretch;
    const sy = 1 - v.stretch * 0.6;
    pet.mover.style.transform =
      `translate3d(${v.x.toFixed(2)}px, ${v.y.toFixed(2)}px, 0) ` +
      `rotateX(${v.rx.toFixed(2)}deg) rotateY(${v.ry.toFixed(2)}deg) ` +
      `rotate(${deg.toFixed(2)}deg) scale(${(sx * v.s).toFixed(4)}, ${(sy * v.s).toFixed(4)}) rotate(${(-deg).toFixed(2)}deg)`;
    pet.ears.forEach((ear, i) => {
      ear.style.transformOrigin = "50% 10%";
      ear.style.transform = `rotate(${(v.ear * (i % 2 ? -1 : 1)).toFixed(2)}deg)`;
    });
  },
};

/* Corner logo -------------------------------------------------------------------------------------
 * The hover colour swap is CSS (works without this file). This module adds:
 *   - a spring tilt toward the cursor (up to options.maxTilt degrees) and a small swell on hover
 *   - tap feedback on touch screens (data-active for options.tapMs)
 *   - click scrolls back to the top, including pages that scroll an inner panel (Streamlit)
 *   - waiting for the logo loader: hidden while it plays, shown when it ends ("logoloader:done");
 *     CustomLogoLoader glides its logo into this element's spot first.
 */
const CustomCornerLogo = {
  el: null,
  options: {
    maxTilt: 18,        // degrees
    hoverScale: 1.06,
    spring: { stiffness: 0.16, damping: 0.72 },
    tapMs: 600,
    waitForLoader: "c-logo-loader",  // id, or false to show immediately
    maxWaitMs: 8000,    // show anyway if the loader never reports back
  },
  value: { rx: 0, ry: 0, s: 1 },
  vel: { rx: 0, ry: 0, s: 0 },
  target: { rx: 0, ry: 0, s: 1 },
  frame: null,

  init(target = "c-corner-logo", options = {}) {
    const el = CustomEnv.resolve(target);
    if (!CustomEnv.claim(el)) return;
    this.el = el;
    this.options = { ...this.options, ...options };
    this.mark = el.querySelector(".c-corner-logo__mark") || el;
    this.bindEvents();
    this.waitForLoader();
  },

  bindEvents() {
    const el = this.el;
    el.addEventListener("pointermove", (e) => this.onMove(e));
    el.addEventListener("pointerleave", () => this.rest());
    el.addEventListener("pointerdown", (e) => { if (e.pointerType !== "mouse") this.flash(); });
    el.addEventListener("click", (e) => { e.preventDefault(); CustomEnv.scrollToTop(); });
  },

  // Hidden while the loader plays; the loader's "logoloader:done" (or a timeout) reveals it.
  waitForLoader() {
    const id = this.options.waitForLoader;
    const loader = id && document.getElementById(id);
    const playing = loader && !loader.hidden && document.documentElement.dataset.logoLoader !== "done";
    if (!playing) return;
    this.el.dataset.waiting = "";
    const show = () => {
      clearTimeout(timer);
      document.removeEventListener("logoloader:done", show);
      delete this.el.dataset.waiting;
    };
    const timer = setTimeout(show, this.options.maxWaitMs);
    document.addEventListener("logoloader:done", show);
  },

  onMove(e) {
    if (CustomEnv.reducedMotion || e.pointerType !== "mouse") return;
    const r = this.el.getBoundingClientRect();
    const dx = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / (r.width / 2)));
    const dy = Math.max(-1, Math.min(1, (e.clientY - (r.top + r.height / 2)) / (r.height / 2)));
    this.target.ry = dx * this.options.maxTilt;
    this.target.rx = -dy * this.options.maxTilt;
    this.target.s = this.options.hoverScale;
    this.wake();
  },

  rest() {
    this.target.rx = 0;
    this.target.ry = 0;
    this.target.s = 1;
    this.wake();
  },

  flash() {
    this.el.dataset.active = "";
    clearTimeout(this.flashTimer);
    this.flashTimer = setTimeout(() => { delete this.el.dataset.active; }, this.options.tapMs);
  },

  wake() {
    if (!this.frame) this.frame = requestAnimationFrame(() => this.step());
  },

  step() {
    this.frame = null;
    const { value: v, vel, target: t } = this;
    const { stiffness, damping } = this.options.spring;
    let moving = false;
    for (const key of ["rx", "ry", "s"]) {
      vel[key] += (t[key] - v[key]) * stiffness;
      vel[key] *= damping;
      v[key] += vel[key];
      if (Math.abs(vel[key]) > 0.0005 || Math.abs(t[key] - v[key]) > 0.0005) moving = true;
    }
    this.mark.style.transform =
      `rotateX(${v.rx.toFixed(2)}deg) rotateY(${v.ry.toFixed(2)}deg) scale(${v.s.toFixed(4)})`;
    if (moving) this.wake();
  },
};

/* Site theme --------------------------------------------------------------------------------------
 * Page-wide colour switch: <html data-site-theme="dark|light">. Components read it in their CSS.
 * set(theme, { animate, save }) runs a wipe (a cover in the new background colour slides down,
 * the theme switches, the cover slides off) and remembers the choice in localStorage unless
 * save is false. Fires document "sitetheme:change" (detail: { theme }).
 * Wipe concept from wodniack.dev's contrast toggle; written from scratch.
 */
const CustomSiteTheme = {
  options: {
    storageKey: "site-theme",
    themes: ["dark", "light"],
    colors: { dark: "#000000", light: "#f2ead3" },  // wipe colour per theme
    wipeSeconds: 0.38,
  },
  ready: false,
  busy: null,

  init(options = {}) {
    if (this.ready) return this;
    this.ready = true;
    this.options = { ...this.options, ...options };
    let saved = null;
    try { saved = window.localStorage.getItem(this.options.storageKey); } catch (e) { /* blocked */ }
    this.apply(this.options.themes.includes(saved) ? saved : this.options.themes[0]);
    return this;
  },

  get() {
    return document.documentElement.dataset.siteTheme || this.options.themes[0];
  },

  saved() {
    try { return window.localStorage.getItem(this.options.storageKey) || this.options.themes[0]; }
    catch (e) { return this.options.themes[0]; }
  },

  other(theme = this.get()) {
    const t = this.options.themes;
    return t[(t.indexOf(theme) + 1) % t.length];
  },

  apply(theme) {
    document.documentElement.dataset.siteTheme = theme;
    document.dispatchEvent(new CustomEvent("sitetheme:change", { detail: { theme } }));
  },

  // Resolves once the new colours are on screen (before the cover finishes sliding off).
  set(theme, { animate = true, save = true } = {}) {
    if (save) { try { window.localStorage.setItem(this.options.storageKey, theme); } catch (e) { /* blocked */ } }
    if (theme === this.get()) return Promise.resolve();
    if (!animate || CustomEnv.reducedMotion) { this.apply(theme); return Promise.resolve(); }
    if (this.busy) this.busy.cancel();
    const cover = document.createElement("div");
    cover.setAttribute("aria-hidden", "true");
    Object.assign(cover.style, {
      position: "fixed", inset: "0", zIndex: "2147482000", pointerEvents: "none",
      background: this.options.colors[theme] || "#000",
    });
    document.body.appendChild(cover);
    const ms = this.options.wipeSeconds * 1000;
    const ease = CustomEnv.ease.inOut;
    const grow = cover.animate([{ clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0 0)" }],
      { duration: ms, easing: ease, fill: "forwards" });
    let cancelled = false;
    this.busy = { cancel: () => { cancelled = true; cover.remove(); } };
    return grow.finished.then(() => {
      if (cancelled) return;
      this.apply(theme);
      cover.animate([{ clipPath: "inset(0 0 0 0)" }, { clipPath: "inset(100% 0 0 0)" }],
        { duration: ms, easing: ease, fill: "forwards" })
        .finished.then(() => { cover.remove(); this.busy = null; });
    }).catch(() => cover.remove());
  },

  toggle(opts) {
    return this.set(this.other(), opts);
  },
};

/* Site header -------------------------------------------------------------------------------------
 * Hairlines: the cell dividers and the bottom line are drawn as SVG paths over the header (the CSS
 * borders turn transparent). Each point springs toward an offset that pushes it away from the
 * cursor: offset = (1 - distance / radius)^2 * push, along the line's normal.
 * Hover fills: the logo, LinkedIn and toggle cells invert on hover. The fill is an SVG shape
 * (behind the cell contents) whose edges are the same moving dividers and bottom line, so it
 * stays solid while they bend. Without JS the cells use a plain CSS background instead.
 * Logo cell: spring tilt; goes home. Work / KOVU open their pages (CustomPageTransition); About
 * scrolls to id="about". The toggle switches the page colours (CustomSiteTheme). Contact slides
 * open the inverted email strip without touching the page colours (email decoded from
 * data-email: base64 of the reversed address).
 */
const CustomSiteHeader = {
  instances: new Map(),
  options: {
    radius: 120,          // px around the cursor that the lines react to
    push: 22,             // px a line moves at the cursor
    segment: 18,          // px between points along a line
    spring: { stiffness: 0.12, damping: 0.78 },
    logoTilt: 16,         // degrees
    logoScale: 1.06,
    tapMs: 600,
    waitForLoader: "c-logo-loader",  // hide the logo while the loader plays (it glides in)
    maxWaitMs: 8000,
    linkedin: null,       // URL; otherwise the href in the markup is kept
    email: null,          // encoded email (see Notes); otherwise data-email in the markup
    theme: {},            // options for CustomSiteTheme
    page: null,           // this page's name ("home", "work"); else data-page or "home"
    home: "home",         // the page the logo returns to
    pages: { home: "./", work: "work", kovu: "kovu" },  // addresses for a full reload when no in-app link exists
    navKey: "site-nav",   // Streamlit: hidden st.page_link per page in st.container(key=navKey-<page>)
    transition: {},       // options for CustomPageTransition
  },

  init(target = "c-site-header", options = {}) {
    const root = CustomEnv.resolve(target);
    if (!CustomEnv.claim(root)) return this.instances.get(root) || null;
    const opts = { ...this.options, ...options };
    CustomSiteTheme.init(opts.theme);
    const h = {
      root, opts,
      row: root.querySelector(".c-site-header__row"),
      cells: Array.from(root.querySelectorAll(".c-site-header__row > .c-site-header__cell")),
      logo: root.querySelector(".c-site-header__logo"),
      mark: root.querySelector(".c-site-header__mark"),
      contact: root.querySelector(".c-site-header__contact"),
      contactBtn: root.querySelector("[data-contact-toggle]"),
      themeBtn: root.querySelector("[data-theme-toggle]"),
      lines: [], svg: null, fillSvg: null, fills: [], mouse: null, frame: null,
      tilt: { v: { rx: 0, ry: 0, s: 1 }, vel: { rx: 0, ry: 0, s: 0 }, t: { rx: 0, ry: 0, s: 1 } },
    };
    if (opts.linkedin) root.querySelectorAll("[data-linkedin]").forEach((a) => { a.href = opts.linkedin; });
    if (opts.email && h.contact) h.contact.dataset.email = opts.email;
    h.page = opts.page || root.dataset.page || opts.home;
    root.dataset.page = h.page;
    Object.assign(CustomPageTransition.options, opts.transition);
    root.querySelectorAll("[data-go]").forEach((a) => { if (opts.pages[a.dataset.go]) a.href = opts.pages[a.dataset.go]; });
    this.instances.set(root, h);
    this.buildSvg(h);
    this.bindEvents(h);
    this.syncThemeButton(h);
    this.waitForLoader(h);
    // Arrived by a full page reload in the middle of a transition (static sites).
    CustomPageTransition.arrive({ to: () => root.querySelector("[data-logo]"), after: (note) => this.afterArrive(note) });
    return h;
  },

  /* Pages: Work opens its own page, the logo goes back home; both with CustomPageTransition. */
  goTo(h, page, note = {}) {
    if (page === h.page) {
      if (note.scrollTo) this.afterArrive(note);
      else CustomEnv.scrollToTop();
      return;
    }
    if (this.isContactOpen(h)) this.closeContact(h);
    const svg = h.root.querySelector("[data-logo]");
    const next = () => document.querySelector(`#c-site-header[data-page="${page}"][data-enhanced]`);
    CustomPageTransition.play({
      from: svg,
      navigate: () => this.navigate(h, page, note),
      ready: () => { const n = next(); return Boolean(n && n !== h.root && n.isConnected); },
      to: () => { const n = next(); return n && n.querySelector("[data-logo]"); },
      after: () => this.afterArrive(note),
    });
  },

  navigate(h, page, note) {
    const link = document.querySelector(`.st-key-${h.opts.navKey}-${page} a`);
    if (link) { link.click(); return; }
    CustomPageTransition.leave(note);
    window.location.assign(h.opts.pages[page] || "./");
  },

  afterArrive(note = {}) {
    if (!note.scrollTo) return;
    const dest = document.getElementById(note.scrollTo);
    if (dest) dest.scrollIntoView({ behavior: CustomEnv.reducedMotion ? "auto" : "smooth", block: "start" });
  },

  bindEvents(h) {
    const { root } = h;
    root.addEventListener("pointermove", (e) => {
      if (e.pointerType === "touch") return;
      const r = root.getBoundingClientRect();
      h.mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
      this.wake(h);
    });
    root.addEventListener("pointerleave", () => { h.mouse = null; this.wake(h); });

    if (h.logo) {
      h.logo.addEventListener("pointermove", (e) => this.tiltLogo(h, e));
      h.logo.addEventListener("pointerleave", () => this.tiltLogo(h, null));
      h.logo.addEventListener("click", (e) => { e.preventDefault(); this.goTo(h, h.opts.home); });
    }
    root.querySelectorAll("[data-go]").forEach((a) => a.addEventListener("click", (e) => {
      e.preventDefault();
      this.goTo(h, a.dataset.go);
    }));
    // Section links; a section that lives on another page (data-on-page) goes there first.
    root.querySelectorAll("[data-scroll-to]").forEach((a) => a.addEventListener("click", (e) => {
      const page = a.dataset.onPage;
      const dest = document.getElementById(a.dataset.scrollTo);
      if (page && page !== h.page) { e.preventDefault(); this.goTo(h, page, { scrollTo: a.dataset.scrollTo }); return; }
      if (!dest) return;
      e.preventDefault();
      dest.scrollIntoView({ behavior: CustomEnv.reducedMotion ? "auto" : "smooth", block: "start" });
    }));
    if (h.themeBtn) h.themeBtn.addEventListener("click", () => CustomSiteTheme.toggle());
    if (h.contactBtn) h.contactBtn.addEventListener("click", () => {
      if (this.isContactOpen(h)) this.closeContact(h);
      else this.openContact(h);
    });
    const copy = root.querySelector("[data-email-copy]");
    if (copy) copy.addEventListener("click", () => this.copyEmail(h, copy));
    document.addEventListener("sitetheme:change", () => this.syncThemeButton(h));
    if (window.ResizeObserver) new ResizeObserver(() => this.layout(h)).observe(root);
    else window.addEventListener("resize", () => this.layout(h));
  },

  /* Hairlines */
  buildSvg(h) {
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("aria-hidden", "true");
    Object.assign(svg.style, { position: "absolute", inset: "0", width: "100%", height: "100%", overflow: "visible", pointerEvents: "none" });
    h.root.appendChild(svg);
    h.svg = svg;

    // Fill layer sits behind the row (the row is position: relative, so it paints on top).
    const fillSvg = svg.cloneNode(false);
    h.root.insertBefore(fillSvg, h.root.firstChild);
    h.fillSvg = fillSvg;
    h.cells.forEach((cell, index) => {
      if (!cell.matches(".c-site-header__logo, .c-site-header__icon")) return;
      const path = document.createElementNS(NS, "path");
      path.setAttribute("class", "c-site-header__fill");
      path.setAttribute("fill", "currentColor");
      fillSvg.appendChild(path);
      const fill = { cell, index, path };
      h.fills.push(fill);
      const on = () => { path.dataset.on = ""; };
      const off = () => { if (!cell.matches(":focus-visible") && !("active" in cell.dataset)) delete path.dataset.on; };
      cell.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") on(); });
      cell.addEventListener("pointerleave", off);
      cell.addEventListener("focus", () => { if (cell.matches(":focus-visible")) on(); });
      cell.addEventListener("blur", () => { delete path.dataset.on; });
      cell.addEventListener("pointerdown", (e) => {
        if (e.pointerType === "mouse") return;
        on();
        this.flash(cell, h.opts.tapMs, () => delete path.dataset.on);
      });
    });
    this.layout(h);
  },

  // Offset of a line at a position along it (linear between its points).
  offAt(line, along) {
    if (!line || !line.off) return 0;
    const t = Math.max(0, Math.min(1, (along - line.from) / (line.to - line.from))) * line.count;
    const i = Math.min(line.count - 1, Math.floor(t));
    return line.off[i] + (line.off[i + 1] - line.off[i]) * (t - i);
  },

  renderFills(h) {
    if (!h.fills.length) return;
    const width = h.root.getBoundingClientRect().width;
    const dividers = h.lines.filter((l) => l.axis === "v");
    const bottom = h.lines.find((l) => l.axis === "h" && Math.abs(l.at - (h.rowH - 0.5)) < 1);
    const rowH = h.rowH;
    const steps = Math.max(4, Math.round(rowH / h.opts.segment));
    h.fills.forEach(({ index, path }) => {
      const left = index > 0 ? dividers[index - 1] : null;
      const right = dividers[index] || null;
      const xl = (y) => (left ? left.at + this.offAt(left, y) : 0);
      const xr = (y) => (right ? right.at + this.offAt(right, y) : width);
      const yb = (x) => (bottom ? bottom.at + this.offAt(bottom, x) + 0.5 : rowH);
      const pts = [[xl(0), 0]];
      for (let i = 0; i <= steps; i++) { const y = (rowH * i) / steps; pts.push([xr(y), Math.min(y, yb(xr(y)))]); }
      const x0 = xr(rowH), x1 = xl(rowH);
      const across = Math.max(2, Math.round(Math.abs(x0 - x1) / h.opts.segment));
      for (let i = 0; i <= across; i++) { const x = x0 + ((x1 - x0) * i) / across; pts.push([x, yb(x)]); }
      for (let i = steps; i >= 0; i--) { const y = (rowH * i) / steps; pts.push([xl(y), Math.min(y, yb(xl(y)))]); }
      path.setAttribute("d", "M" + pts.map((p) => p[0].toFixed(2) + " " + p[1].toFixed(2)).join(" L") + " Z");
    });
  },

  layout(h) {
    const NS = "http://www.w3.org/2000/svg";
    const hr = h.root.getBoundingClientRect();
    if (!hr.width) return;
    const rowH = h.row.getBoundingClientRect().height;
    h.rowH = rowH;
    const defs = [];
    h.cells.slice(0, -1).forEach((c) => {
      defs.push({ axis: "v", at: c.getBoundingClientRect().right - hr.left - 0.5, from: 0, to: rowH });
    });
    if (hr.height - rowH > 1) defs.push({ axis: "h", at: rowH - 0.5, from: 0, to: hr.width });
    defs.push({ axis: "h", at: hr.height - 0.5, from: 0, to: hr.width });

    while (h.lines.length > defs.length) h.lines.pop().path.remove();
    defs.forEach((d, i) => {
      let line = h.lines[i];
      if (!line) {
        const path = document.createElementNS(NS, "path");
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", "currentColor");
        path.setAttribute("stroke-width", "1");
        path.setAttribute("vector-effect", "non-scaling-stroke");
        h.svg.appendChild(path);
        line = h.lines[i] = { path };
      }
      const count = Math.max(4, Math.round((d.to - d.from) / h.opts.segment));
      if (line.count !== count) {
        line.off = new Float32Array(count + 1);
        line.vel = new Float32Array(count + 1);
        line.count = count;
      }
      Object.assign(line, d);
    });
    this.wake(h, true);
  },

  wake(h, force = false) {
    if (force) this.render(h);
    if (!h.frame) h.frame = requestAnimationFrame(() => this.step(h));
  },

  step(h) {
    h.frame = null;
    const { radius, push, spring } = h.opts;
    const m = CustomEnv.reducedMotion ? null : h.mouse;
    let moving = false;
    h.lines.forEach((line) => {
      for (let i = 0; i <= line.count; i++) {
        const along = line.from + ((line.to - line.from) * i) / line.count;
        let target = 0;
        if (m) {
          const px = line.axis === "v" ? line.at : along;
          const py = line.axis === "v" ? along : line.at;
          const dist = Math.hypot(px - m.x, py - m.y);
          if (dist < radius) {
            const away = line.axis === "v" ? px - m.x : py - m.y;
            const f = 1 - dist / radius;
            target = f * f * push * (away < 0 ? -1 : 1);
          }
        }
        line.vel[i] += (target - line.off[i]) * spring.stiffness;
        line.vel[i] *= spring.damping;
        line.off[i] += line.vel[i];
        if (Math.abs(line.vel[i]) > 0.01 || Math.abs(target - line.off[i]) > 0.01) moving = true;
      }
    });
    this.tiltStep(h) && (moving = true);
    this.render(h);
    if (moving) h.frame = requestAnimationFrame(() => this.step(h));
  },

  render(h) {
    h.lines.forEach((line) => {
      const pts = [];
      for (let i = 0; i <= line.count; i++) {
        const along = line.from + ((line.to - line.from) * i) / line.count;
        const o = line.off ? line.off[i] : 0;
        pts.push(line.axis === "v" ? [line.at + o, along] : [along, line.at + o]);
      }
      // Smooth curve through the points (quadratic segments between midpoints).
      let d = `M${pts[0][0].toFixed(2)} ${pts[0][1].toFixed(2)}`;
      for (let i = 1; i < pts.length - 1; i++) {
        const mx = (pts[i][0] + pts[i + 1][0]) / 2;
        const my = (pts[i][1] + pts[i + 1][1]) / 2;
        d += ` Q${pts[i][0].toFixed(2)} ${pts[i][1].toFixed(2)} ${mx.toFixed(2)} ${my.toFixed(2)}`;
      }
      const last = pts[pts.length - 1];
      d += ` L${last[0].toFixed(2)} ${last[1].toFixed(2)}`;
      line.path.setAttribute("d", d);
    });
    this.renderFills(h);
  },

  /* Logo cell */
  tiltLogo(h, e) {
    const t = h.tilt.t;
    if (!e || CustomEnv.reducedMotion || e.pointerType !== "mouse") {
      t.rx = 0; t.ry = 0; t.s = 1;
    } else {
      const r = h.logo.getBoundingClientRect();
      const dx = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / (r.width / 2)));
      const dy = Math.max(-1, Math.min(1, (e.clientY - (r.top + r.height / 2)) / (r.height / 2)));
      t.ry = dx * h.opts.logoTilt;
      t.rx = -dy * h.opts.logoTilt;
      t.s = h.opts.logoScale;
    }
    this.wake(h);
  },

  tiltStep(h) {
    if (!h.mark) return false;
    const { v, vel, t } = h.tilt;
    const { stiffness, damping } = h.opts.spring;
    let moving = false;
    for (const key of ["rx", "ry", "s"]) {
      vel[key] += (t[key] - v[key]) * (stiffness + 0.04);
      vel[key] *= damping - 0.06;
      v[key] += vel[key];
      if (Math.abs(vel[key]) > 0.0005 || Math.abs(t[key] - v[key]) > 0.0005) moving = true;
    }
    h.mark.style.transform = `rotateX(${v.rx.toFixed(2)}deg) rotateY(${v.ry.toFixed(2)}deg) scale(${v.s.toFixed(4)})`;
    return moving;
  },

  flash(el, ms, after) {
    el.dataset.active = "";
    clearTimeout(el.__flash);
    el.__flash = setTimeout(() => { delete el.dataset.active; if (after) after(); }, ms);
  },

  waitForLoader(h) {
    const id = h.opts.waitForLoader;
    const loader = id && document.getElementById(id);
    if (!loader || loader.hidden || document.documentElement.dataset.logoLoader === "done") return;
    h.root.dataset.waiting = "";
    const show = () => {
      clearTimeout(timer);
      document.removeEventListener("logoloader:done", show);
      delete h.root.dataset.waiting;
    };
    const timer = setTimeout(show, h.opts.maxWaitMs);
    document.addEventListener("logoloader:done", show);
  },

  /* Theme + contact */
  syncThemeButton(h) {
    if (h.themeBtn) h.themeBtn.setAttribute("aria-pressed", String(CustomSiteTheme.get() !== CustomSiteTheme.options.themes[0]));
  },

  isContactOpen(h) {
    return h.root.dataset.contact === "open";
  },

  decodeEmail(h) {
    try { return atob(h.contact.dataset.email || "").split("").reverse().join(""); }
    catch (e) { return ""; }
  },

  openContact(h) {
    if (!h.contact) return;
    const email = this.decodeEmail(h);
    const link = h.root.querySelector("[data-email-link]");
    if (link && email) {
      link.textContent = email;
      link.href = "mailto:" + email;
    }
    h.root.querySelectorAll("[data-email-link], [data-email-copy]").forEach((el) => el.removeAttribute("tabindex"));
    h.contactBtn.setAttribute("aria-expanded", "true");
    h.root.dataset.contact = "open";
  },

  closeContact(h) {
    h.root.dataset.contact = "closed";
    h.contactBtn.setAttribute("aria-expanded", "false");
    h.root.querySelectorAll("[data-email-link], [data-email-copy]").forEach((el) => el.setAttribute("tabindex", "-1"));
  },

  copyEmail(h, button) {
    const email = this.decodeEmail(h);
    const done = () => {
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = "Copy"; }, 1500);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(email).then(done, () => this.copyFallback(email, done));
    } else this.copyFallback(email, done);
  },

  copyFallback(text, done) {
    const area = document.createElement("textarea");
    area.value = text;
    Object.assign(area.style, { position: "fixed", opacity: "0" });
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); done(); } catch (e) { /* not allowed */ }
    area.remove();
  },
};

/* Torch reveal ------------------------------------------------------------------------------------
 * Three canvases: "art" holds the hidden picture, "mask" holds where the light has been, and the
 * visible canvas draws art only where the mask is (source-in). Holding the pointer down stamps a
 * soft round light into the mask along the path (one stamp every quarter radius, so fast moves
 * stay smooth). options.fadeDelayMs after letting go, the mask fades a little every frame
 * (destination-out) and is cleared outright once it is nearly gone (avoids 8-bit leftovers).
 * The art is options.frames (a list of pictures played in order, once per press, options.frameMs
 * each, then resting on the last), options.image (one picture), or a brick pattern of the logo
 * (options.logoPath) in the element's text colour, redrawn when the page colours change
 * ("sitetheme:change"). Pictures are cover-fit: they fill the element and the overflow is cropped.
 * Frames are loaded and decoded up front, so playing them only copies a ready picture per step.
 * Concept from adrienlamy.fr's drag trail; written from scratch.
 */
const CustomTorchReveal = {
  instances: new Map(),
  options: {
    radius: 90,            // px, mouse
    touchRadius: 70,       // px, finger
    strength: 0.6,         // how much one stamp lights (0-1); overlapping stamps add up
    fadeDelayMs: 500,      // wait after letting go before the light fades
    fade: 0.05,            // share of the light removed per frame while fading
    fadeFrames: 110,       // frames until the light is cleared completely
    frames: null,          // list of picture URLs / data URIs, played in order on each press
    frameMs: 410,          // time from one frame to the next (18 frames: about 7 seconds)
    crossfade: true,       // each frame fades into the next instead of switching
    alignTo: null,         // element inside the host to line the picture up with (see placement)
    alignBox: null,        // [left, top, right, bottom] share of the picture where that element sits
    extendEdges: false,    // fill space around a lined-up picture by stretching its edge colours
    edgeInset: 0.01,       // how far inside the edge (share of the picture) the stretched strip is
    image: null,           // picture URL / data URI; otherwise the logo pattern
    logoPath: null,        // SVG path data of the logo (pattern)
    logoViewBox: [1037, 1157],
    tile: 118,             // px between logos in the pattern
    logoSize: 52,          // px width of each logo in the pattern
    tilt: 12,              // degrees, alternating
    ignore: ".c-pet__rig", // parts that keep their own behaviour (no light there)
    busyWhen: '[data-mood="grab"]',  // element state that pauses the torch (KOVU being dragged)
    hint: null,            // small text added at the end of the element
    bleed: false,          // run the surface edge to edge
    over: false,           // light paints on top of the element's contents (hint stays above)
    ring: false,           // true: faint ring under the mouse while hovering
    waitMs: 5000,          // how long to wait for the element to appear
  },

  init(target = "c-pet-head", options = {}) {
    const host = CustomEnv.resolve(target);
    if (!host) {
      if (typeof target === "string") this.waitFor(target, options);
      return null;
    }
    if (host.dataset.torch) return this.instances.get(host) || null;
    host.dataset.torch = "on";
    const opts = { ...this.options, ...options };
    const canvas = document.createElement("canvas");
    canvas.className = "c-torch__canvas";
    canvas.setAttribute("aria-hidden", "true");
    host.classList.add("c-torch");
    if (opts.bleed) host.classList.add("c-torch--bleed");
    if (opts.over) host.classList.add("c-torch--over");
    host.insertBefore(canvas, host.firstChild);
    if (opts.hint) {
      const p = document.createElement("p");
      p.className = "c-torch__hint";
      p.textContent = opts.hint;
      host.appendChild(p);
    }
    const t = {
      host, opts, canvas, ctx: canvas.getContext("2d"),
      mask: document.createElement("canvas"), art: document.createElement("canvas"),
      w: 0, h: 0, dpr: 1, down: false, last: null, hover: null, radius: opts.radius,
      lit: false, upAt: 0, faded: 0, frame: null, sprite: null, spriteR: 0, artToken: 0,
      pics: [], shown: -1, playAt: 0, playing: false,
    };
    t.mctx = t.mask.getContext("2d");
    t.actx = t.art.getContext("2d");
    if (opts.frames && opts.frames.length) this.loadFrames(t);
    this.instances.set(host, t);
    this.bindEvents(t);
    this.resize(t);
    return t;
  },

  // The element may render a moment after this script (Streamlit); wait for it.
  waitFor(id, options) {
    const obs = new MutationObserver(() => {
      if (document.getElementById(id)) { obs.disconnect(); clearTimeout(timer); this.init(id, options); }
    });
    const timer = setTimeout(() => obs.disconnect(), this.options.waitMs);
    obs.observe(document.body, { childList: true, subtree: true });
  },

  bindEvents(t) {
    const { host } = t;
    host.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || this.blocked(t, e)) return;
      t.down = true;
      t.radius = e.pointerType === "mouse" ? t.opts.radius : t.opts.touchRadius;
      try { host.setPointerCapture(e.pointerId); } catch (err) { /* pointer already gone */ }
      const p = this.point(t, e);
      this.stamp(t, p, p);
      t.last = p;
      t.hover = null;
      host.dataset.torchActive = "";
      if (t.pics.length) { t.playing = true; t.playAt = performance.now(); this.showFrame(t, 0); }
      this.wake(t);
    });
    host.addEventListener("pointermove", (e) => {
      const p = this.point(t, e);
      if (t.down) { this.stamp(t, t.last, p); t.last = p; }
      else t.hover = e.pointerType === "mouse" && !this.blocked(t, e) ? p : null;
      this.wake(t);
    });
    const up = () => {
      if (!t.down) return;
      t.down = false;
      t.last = null;
      t.upAt = performance.now();
      delete host.dataset.torchActive;
      this.wake(t);
    };
    host.addEventListener("pointerup", up);
    host.addEventListener("pointercancel", up);
    host.addEventListener("pointerleave", () => { t.hover = null; this.wake(t); });
    if (window.ResizeObserver) new ResizeObserver(() => this.resize(t)).observe(host);
    else window.addEventListener("resize", () => this.resize(t));
    document.addEventListener("sitetheme:change", () => requestAnimationFrame(() => this.drawArt(t)));
  },

  blocked(t, e) {
    const inIgnored = t.opts.ignore && e.target && e.target.closest && e.target.closest(t.opts.ignore);
    return Boolean(inIgnored || (t.opts.busyWhen && t.host.matches(t.opts.busyWhen)));
  },

  point(t, e) {
    const r = t.host.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  },

  resize(t) {
    const r = t.host.getBoundingClientRect();
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = Math.round(r.width), h = Math.round(r.height);
    if (!w || !h || (w === t.w && h === t.h && dpr === t.dpr)) return;
    Object.assign(t, { w, h, dpr });
    [t.canvas, t.mask, t.art].forEach((c) => { c.width = w * dpr; c.height = h * dpr; });
    t.lit = false;
    this.drawArt(t);
  },

  // A soft round light, drawn once per radius and stamped with drawImage.
  spriteFor(t) {
    const r = t.radius;
    if (t.sprite && t.spriteR === r) return t.sprite;
    const s = document.createElement("canvas");
    s.width = s.height = r * 2 * t.dpr;
    const c = s.getContext("2d");
    const g = c.createRadialGradient(s.width / 2, s.height / 2, 0, s.width / 2, s.height / 2, s.width / 2);
    const a = t.opts.strength;
    g.addColorStop(0, `rgba(0,0,0,${a})`);
    g.addColorStop(0.45, `rgba(0,0,0,${a * 0.7})`);
    g.addColorStop(1, "rgba(0,0,0,0)");
    c.fillStyle = g;
    c.fillRect(0, 0, s.width, s.height);
    t.sprite = s;
    t.spriteR = r;
    return s;
  },

  stamp(t, a, b) {
    const sprite = this.spriteFor(t);
    const r = t.radius, d = t.dpr;
    const dist = Math.hypot(b.x - a.x, b.y - a.y);
    const steps = Math.max(1, Math.ceil(dist / (r * 0.25)));
    t.mctx.globalCompositeOperation = "source-over";
    for (let i = 1; i <= steps; i++) {
      const x = a.x + ((b.x - a.x) * i) / steps;
      const y = a.y + ((b.y - a.y) * i) / steps;
      t.mctx.drawImage(sprite, (x - r) * d, (y - r) * d);
    }
    t.lit = true;
    t.faded = 0;
  },

  // Load every frame and decode it now, so playback never waits on the network or the decoder.
  // Each frame is also drawn once, off screen, while the page is idle: the browser's first real draw
  // of a big picture is slow, and doing it early keeps the first press from stuttering.
  loadFrames(t) {
    const scratch = document.createElement("canvas").getContext("2d");
    const later = window.requestIdleCallback || ((fn) => setTimeout(fn, 50));
    t.pics = t.opts.frames.map((src) => {
      const img = new Image();
      img.decoding = "async";
      img.src = src;
      const ready = () => {
        if (img.ready) return;
        img.ready = true;
        later(() => scratch.drawImage(img, 0, 0, 1, 1));
      };
      (img.decode ? img.decode() : Promise.reject()).then(ready, () => { img.onload = ready; if (img.complete) ready(); });
      return img;
    });
  },

  // Put the frames at position pos on the art canvas: pos 3.4 is frame 3 with 40% of frame 4
  // faded over it. A frame that isn't loaded yet falls back to the nearest earlier ready one.
  showFrame(t, pos) {
    const last = t.pics.length - 1;
    pos = Math.max(0, Math.min(pos, last));
    let k = Math.floor(pos);
    while (k >= 0 && !t.pics[k].ready) k--;
    if (k < 0 || !t.w) return;
    const next = t.pics[k + 1];
    const mix = next && next.ready && k === Math.floor(pos) && t.opts.crossfade ? pos - k : 0;
    const key = k + mix;
    if (key === t.shown) return;
    t.shown = key;
    this.clearArt(t);
    this.placePic(t, t.pics[k], 1);
    if (mix > 0) this.placePic(t, next, mix);
  },

  clearArt(t) {
    t.actx.setTransform(1, 0, 0, 1, 0, 0);
    t.actx.globalAlpha = 1;
    t.actx.clearRect(0, 0, t.art.width, t.art.height);
  },

  // Where a picture goes, in canvas pixels. With options.alignTo, the picture is scaled and moved
  // so that options.alignBox (the share of the picture where that element's drawing sits:
  // [left, top, right, bottom], 0-1) lands exactly on the element, e.g. a painting under its own
  // line drawing. Otherwise it is cover-fit (fills the element, overflow cropped).
  placement(t, img) {
    const W = t.art.width, H = t.art.height, d = t.dpr;
    const el = t.opts.alignTo && [...t.host.querySelectorAll(t.opts.alignTo)].find((e) => e.offsetWidth);
    if (el && t.opts.alignBox) {
      const [x0, y0, x1, y1] = t.opts.alignBox;
      const box = this.boxIn(t.host, el);
      const w = (box.w / (x1 - x0)) * d;
      const h = (box.h / (y1 - y0)) * d;
      return { x: box.x * d - x0 * w, y: box.y * d - y0 * h, w, h };
    }
    const s = Math.max(W / img.naturalWidth, H / img.naturalHeight);
    const w = img.naturalWidth * s, h = img.naturalHeight * s;
    return { x: (W - w) / 2, y: (H - h) / 2, w, h };
  },

  // An element's untransformed box inside host (so KOVU's tilt and stretch don't move the painting).
  boxIn(host, el) {
    let x = 0, y = 0, n = el;
    while (n && n !== host) {
      x += n.offsetLeft; y += n.offsetTop;
      const parent = n.offsetParent;
      if (parent && parent !== host && !host.contains(parent)) break;
      n = parent;
    }
    if (n !== host) {
      const a = host.getBoundingClientRect(), b = el.getBoundingClientRect();
      return { x: b.left - a.left, y: b.top - a.top, w: b.width, h: b.height };
    }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight };
  },

  // Draw a picture at its placement. With options.extendEdges, any space left around it is filled
  // by stretching a thin strip from just inside each edge outwards (so the colour carries on).
  placePic(t, img, alpha) {
    const c = t.actx, W = t.art.width, H = t.art.height;
    const p = this.placement(t, img);
    const iw = img.naturalWidth, ih = img.naturalHeight;
    c.globalAlpha = alpha;
    c.drawImage(img, p.x, p.y, p.w, p.h);
    if (t.opts.extendEdges) {
      const inset = t.opts.edgeInset, sx = (iw * inset) | 0, sy = (ih * inset) | 0;
      const left = Math.max(0, p.x), right = Math.min(W, p.x + p.w);
      const top = Math.max(0, p.y), bottom = Math.min(H, p.y + p.h);
      // the visible part of the picture, as source rows/columns
      const srcY = ((top - p.y) / p.h) * ih, srcH = ((bottom - top) / p.h) * ih;
      const srcX = ((left - p.x) / p.w) * iw, srcW = ((right - left) / p.w) * iw;
      if (left > 0) c.drawImage(img, sx, srcY, 1, srcH, 0, top, left, bottom - top);
      if (right < W) c.drawImage(img, iw - sx - 1, srcY, 1, srcH, right, top, W - right, bottom - top);
      if (top > 0) c.drawImage(img, srcX, sy, srcW, 1, left, 0, right - left, top);
      if (bottom < H) c.drawImage(img, srcX, ih - sy - 1, srcW, 1, left, bottom, right - left, H - bottom);
      // corners: the corner colour
      if (left > 0 && top > 0) c.drawImage(img, sx, sy, 1, 1, 0, 0, left, top);
      if (right < W && top > 0) c.drawImage(img, iw - sx - 1, sy, 1, 1, right, 0, W - right, top);
      if (left > 0 && bottom < H) c.drawImage(img, sx, ih - sy - 1, 1, 1, 0, bottom, left, H - bottom);
      if (right < W && bottom < H) c.drawImage(img, iw - sx - 1, ih - sy - 1, 1, 1, right, bottom, W - right, H - bottom);
    }
    c.globalAlpha = 1;
  },

  coverFit(t, img) {
    this.clearArt(t);
    this.placePic(t, img, 1);
  },

  drawArt(t) {
    if (!t.w) return;
    if (t.pics.length) {
      const i = t.shown < 0 ? t.pics.length - 1 : t.shown;
      t.shown = -1;
      this.showFrame(t, i);
      this.render(t);
      return;
    }
    const token = ++t.artToken;
    const img = new Image();
    img.onload = () => {
      if (token !== t.artToken) return;
      const c = t.actx, d = t.dpr;
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, t.art.width, t.art.height);
      if (t.opts.image) this.coverFit(t, img);
      else this.drawPattern(t, img, c, d);
      this.render(t);
    };
    if (t.opts.image) img.src = t.opts.image;
    else if (t.opts.logoPath) {
      const [vw, vh] = t.opts.logoViewBox;
      const color = getComputedStyle(t.host).color || "#f2ead3";
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${vw} ${vh}"><path fill="${color}" fill-rule="evenodd" d="${t.opts.logoPath}"/></svg>`;
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    }
  },

  // Brick layout: every other row shifted half a tile, logos tilted left and right in turn.
  drawPattern(t, img, c, d) {
    const { tile, logoSize, tilt, logoViewBox } = t.opts;
    const lw = logoSize, lh = (logoSize * logoViewBox[1]) / logoViewBox[0];
    const rowH = tile * 0.8;
    for (let row = 0, y = rowH / 2; y - rowH / 2 < t.h; row++, y += rowH) {
      const shift = row % 2 ? tile / 2 : 0;
      for (let col = 0, x = shift - tile / 2; x - tile / 2 < t.w; col++, x += tile) {
        c.setTransform(d, 0, 0, d, x * d, y * d);
        c.rotate((((row + col) % 2 ? 1 : -1) * tilt * Math.PI) / 180);
        c.drawImage(img, -lw / 2, -lh / 2, lw, lh);
      }
    }
    c.setTransform(1, 0, 0, 1, 0, 0);
  },

  wake(t) {
    if (!t.frame) t.frame = requestAnimationFrame(() => this.step(t));
  },

  step(t) {
    t.frame = null;
    let again = false;
    if (t.playing) {
      const pos = (performance.now() - t.playAt) / t.opts.frameMs;
      this.showFrame(t, pos);
      if (pos >= t.pics.length - 1 && t.shown === t.pics.length - 1) t.playing = false;
      else again = true;
    }
    if (t.lit && !t.down) {
      if (performance.now() - t.upAt > t.opts.fadeDelayMs) {
        t.faded++;
        if (t.faded >= t.opts.fadeFrames) {
          t.mctx.clearRect(0, 0, t.mask.width, t.mask.height);
          t.lit = false;
        } else {
          t.mctx.globalCompositeOperation = "destination-out";
          t.mctx.fillStyle = `rgba(0,0,0,${t.opts.fade})`;
          t.mctx.fillRect(0, 0, t.mask.width, t.mask.height);
          t.mctx.globalCompositeOperation = "source-over";
        }
      }
      again = t.lit;
    }
    this.render(t);
    if (again) this.wake(t);
  },

  render(t) {
    const c = t.ctx, d = t.dpr;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, t.canvas.width, t.canvas.height);
    if (t.lit) {
      c.globalCompositeOperation = "source-over";
      c.drawImage(t.mask, 0, 0);
      c.globalCompositeOperation = "source-in";
      c.drawImage(t.art, 0, 0);
      c.globalCompositeOperation = "source-over";
    }
    if (t.opts.ring && t.hover && !t.down) {
      c.setTransform(d, 0, 0, d, 0, 0);
      c.strokeStyle = getComputedStyle(t.host).color;
      c.globalAlpha = 0.4;
      c.lineWidth = 1;
      c.beginPath();
      c.arc(t.hover.x, t.hover.y, t.opts.radius * 0.45, 0, Math.PI * 2);
      c.stroke();
      c.globalAlpha = 1;
      c.setTransform(1, 0, 0, 1, 0, 0);
    }
  },
};

/* Walk planner opener ------------------------------------------------------------------------------
 * Pulling (or clicking / pressing Enter on) the walk button opens the walk planner: it sets
 * <html data-walk-open> (page CSS shows the planner only then), scrolls to it and focuses its
 * first field. Where there is no planner on the page (the plain web version), it goes to
 * options.href instead. A page address with ?walk opens it straight away.
 */
const CustomWalkPlanner = {
  options: {
    panel: ".st-key-walk-planner",  // the planner (Streamlit container key="walk-planner")
    href: null,                     // where to go when the page has no planner
    waitMs: 6000,
  },

  init(target = "c-walk-button", options = {}) {
    const root = CustomEnv.resolve(target);
    if (!root || root.dataset.walkPlanner) return;
    root.dataset.walkPlanner = "on";
    const opts = { ...this.options, ...options };
    const open = () => this.open(opts);
    root.addEventListener("pet:release", open);
    root.addEventListener("click", open);
    if (/[?&]walk\b/.test(window.location.search)) this.open(opts, true);
  },

  open(opts, fromAddress = false) {
    const started = performance.now();
    const go = () => {
      const panel = document.querySelector(opts.panel);
      if (!panel) {
        if (performance.now() - started < (fromAddress ? opts.waitMs : 0)) return void setTimeout(go, 100);
        if (opts.href && !fromAddress) window.location.assign(opts.href);
        return;
      }
      const first = !("walkOpen" in document.documentElement.dataset);
      document.documentElement.dataset.walkOpen = "";
      if (!first && !fromAddress) return;
      requestAnimationFrame(() => {
        panel.scrollIntoView({ behavior: CustomEnv.reducedMotion ? "auto" : "smooth", block: "start" });
        const field = panel.querySelector("input");
        if (field) setTimeout(() => field.focus({ preventScroll: true }), 400);
      });
    };
    go();
  },
};

/* Page transition ---------------------------------------------------------------------------------
 * Your logo takes over the screen while the next page loads:
 *   1. the page frosts over (a blurred, lightly tinted glass layer fades in) while a copy of the
 *      logo moves from the header to the middle of the screen and grows past the edges
 *      (options.zoom x the screen height), bulging like a fish-eye lens (options.lens)
 *   2. navigate() runs (Streamlit: a hidden st.page_link is clicked, no reload); the page changes
 *      under the frost; the transition waits until ready() says the new page is there
 *   3. the logo shrinks back into the new header's logo cell, the bulge relaxes and the frost
 *      clears, then after() runs (e.g. scroll to a section)
 * options.logoStyle: "solid" (the logo as it is), "outline" (thin lines that draw themselves while
 * it grows and fill in as it lands) or "alternate" (switches every time, for comparing).
 * The fish-eye bends the logo's own outline (no image filter), so it stays sharp. With reduced
 * motion the page simply changes. While it plays, <html data-page-transition="playing"> (the header
 * hides its own logo). Full-reload sites: leave(note) / arrive() on the next page play step 3.
 */
const CustomPageTransition = {
  options: {
    growSeconds: 1.2,
    holdSeconds: 0.25,
    returnSeconds: 1.3,
    maxWaitMs: 6000,
    storageKey: "site-page-arrive",
    zoom: 1.6,             // logo height at its biggest, as a multiple of the screen height
    lens: 0.45,            // fish-eye strength, 0 = none (below 0.5 so lines never fold)
    lensRadius: 0.6,       // size of the lens, x the logo's longer side
    logoStyle: "solid",    // "solid" | "outline" | "alternate"
    strokeWidth: 1.5,      // outline thickness in screen pixels
    frostBlur: 18,         // px
    frostTint: 0.35,       // how much of the page colour is laid over the blur (0-1)
  },
  busy: false,

  colors() {
    const theme = CustomSiteTheme.get();
    return { bg: CustomSiteTheme.options.colors[theme], fg: CustomSiteTheme.options.colors[CustomSiteTheme.other(theme)] };
  },

  rgba(hex, alpha) {
    const n = parseInt(String(hex).replace("#", ""), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
  },

  pickStyle() {
    const style = this.options.logoStyle;
    if (style !== "alternate") return style;
    const n = Number(CustomEnv.session.get("site-transition-count") || 0);
    CustomEnv.session.set("site-transition-count", String(n + 1));
    return n % 2 ? "outline" : "solid";
  },

  useLens() {
    return this.options.lens > 0 && !CustomEnv.reducedMotion;
  },

  // Frost layer + a big copy of the logo resting in the middle of the screen.
  makeLayer(svg, style) {
    const { bg, fg } = this.colors();
    const o = this.options;
    const vb = svg.viewBox && svg.viewBox.baseVal;
    const vw = vb && vb.width ? vb.width : 100, vh = vb && vb.height ? vb.height : 100;
    const h = window.innerHeight * o.zoom;
    const w = (h * vw) / vh;
    const frost = document.createElement("div");
    frost.setAttribute("aria-hidden", "true");
    Object.assign(frost.style, {
      position: "fixed", inset: "0", zIndex: "2147482500", pointerEvents: "auto", opacity: "0",
      background: this.rgba(bg, o.frostTint),
      backdropFilter: `blur(${o.frostBlur}px)`, webkitBackdropFilter: `blur(${o.frostBlur}px)`,
    });
    const logo = svg.cloneNode(true);
    logo.removeAttribute("class");
    logo.setAttribute("aria-hidden", "true");
    const left = (window.innerWidth - w) / 2, top = (window.innerHeight - h) / 2;
    Object.assign(logo.style, {
      position: "fixed", left: left + "px", top: top + "px", width: w + "px", height: h + "px",
      zIndex: "2147482501", color: fg, transformOrigin: "0 0", pointerEvents: "none", overflow: "visible",
    });
    const L = { frost, logo, w, left, top, style, lens: null, outlines: [], fills: [] };
    if (style === "outline") {
      const built = CustomLogoLoader.buildOutlines.call({ options: { strokeWidth: o.strokeWidth } }, logo);
      L.outlines = built.outlines;
      L.fills = built.fills;
    }
    if (this.useLens()) L.lens = this.addLens(logo, vw, vh);
    document.body.append(frost, logo);
    return L;
  },

  // Fish-eye: every point of the logo's outline is pushed away from the middle, most near the
  // centre and not at all at the rim (radius options.lensRadius x the logo's longer side):
  //   r' = r * (1 + k * (1 - r^2)), k up to options.lens (kept under 0.5 so lines never fold).
  // It bends the shape itself, so the edges stay sharp at any size and it works in every browser.
  // Logo paths may only use absolute M / C / L / Q / Z commands (every number pair is a point).
  addLens(svg, vw, vh) {
    const paths = Array.from(svg.querySelectorAll("path")).map((path) => {
      const d = path.getAttribute("d") || "";
      if (/[a-yA-BD-KN-PR-Y]/.test(d.replace(/e-?\d/g, ""))) return null;  // other commands: leave alone
      const tokens = d.match(/[A-Za-z]|-?\d*\.?\d+(?:e-?\d+)?/g) || [];
      const nums = [], slots = [];
      tokens.forEach((tok, i) => { if (!/[A-Za-z]/.test(tok)) { slots.push(i); nums.push(parseFloat(tok)); } });
      return nums.length % 2 ? null : { path, tokens, slots, nums: Float64Array.from(nums) };
    }).filter(Boolean);
    if (!paths.length) return null;
    return { paths, cx: vw / 2, cy: vh / 2, radius: Math.max(vw, vh) * this.options.lensRadius, last: -1 };
  },

  setLens(L, amount) {
    const lens = L.lens;
    if (!lens) return;
    const k = this.options.lens * Math.max(0, Math.min(1, amount));
    if (Math.abs(k - lens.last) < 0.0005) return;
    lens.last = k;
    const { cx, cy, radius } = lens;
    lens.paths.forEach(({ path, tokens, slots, nums }) => {
      const out = tokens.slice();
      for (let i = 0; i < nums.length; i += 2) {
        const dx = nums[i] - cx, dy = nums[i + 1] - cy;
        const r = Math.hypot(dx, dy) / radius;
        const f = r < 1 ? 1 + k * (1 - r * r) : 1;
        out[slots[i]] = (cx + dx * f).toFixed(2);
        out[slots[i + 1]] = (cy + dy * f).toFixed(2);
      }
      path.setAttribute("d", out.join(" "));
    });
  },

  // Runs fn(eased progress 0-1) every frame for ms milliseconds.
  tween(ms, fn, delay = 0) {
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    return new Promise((resolve) => {
      const start = performance.now() + delay;
      const frame = (now) => {
        const t = Math.max(0, Math.min(1, (now - start) / ms));
        fn(ease(t));
        if (t < 1) requestAnimationFrame(frame); else resolve();
      };
      requestAnimationFrame(frame);
    });
  },

  // Transform that puts the big centred logo copy exactly over rect r.
  over(L, r) {
    return `translate(${(r.left - L.left).toFixed(2)}px, ${(r.top - L.top).toFixed(2)}px) scale(${(r.width / L.w).toFixed(5)})`;
  },

  waitFor(ready) {
    const start = performance.now();
    return new Promise((resolve) => {
      const check = () => {
        if ((ready && ready()) || performance.now() - start > this.options.maxWaitMs) resolve();
        else setTimeout(check, 50);
      };
      check();
    });
  },

  play({ from, navigate, ready, to, after } = {}) {
    if (this.busy || !from) return;
    this.busy = true;
    const finish = () => { this.busy = false; if (after) after(); };
    if (CustomEnv.reducedMotion) {
      navigate();
      this.waitFor(ready).then(() => { CustomEnv.scrollToTop(true); finish(); });
      return;
    }
    document.documentElement.dataset.pageTransition = "playing";
    const fromRect = from.getBoundingClientRect();
    const L = this.makeLayer(from, this.pickStyle());
    const ms = this.options.growSeconds * 1000, ease = CustomEnv.ease.inOut;
    const grow = [
      L.frost.animate([{ opacity: 0 }, { opacity: 1 }], { duration: ms * 0.7, easing: ease, fill: "forwards" }).finished,
      L.logo.animate([{ transform: this.over(L, fromRect), color: getComputedStyle(from).color }, { transform: "none", color: L.logo.style.color }],
        { duration: ms, easing: ease, fill: "forwards" }).finished,
      this.tween(ms, (p) => this.setLens(L, p)),
    ];
    if (L.style === "outline") {
      const spread = (ms * 0.45) / Math.max(1, L.outlines.length - 1);
      L.outlines.forEach((p, i) => p.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }],
        { duration: ms * 0.75, delay: i * spread, easing: ease, fill: "forwards" }));
    }
    Promise.all(grow)
      .then(() => { navigate(); return this.waitFor(ready); })
      .then(() => new Promise((r) => setTimeout(r, this.options.holdSeconds * 1000)))
      .then(() => this.land(L, to, finish))
      .catch(() => { this.cleanup(L); finish(); });
  },

  // Step 3: the logo shrinks into the header on the new page, the frost clears.
  land(L, to, done) {
    CustomEnv.scrollToTop(true);
    requestAnimationFrame(() => {
      const target = to && to();
      const r = target && target.getBoundingClientRect();
      const ms = this.options.returnSeconds * 1000, ease = CustomEnv.ease.inOut;
      const moves = [
        L.frost.animate([{ opacity: 1 }, { opacity: 0 }], { duration: ms * 0.8, delay: ms * 0.2, easing: ease, fill: "forwards" }).finished,
        this.tween(ms * 0.8, (p) => this.setLens(L, 1 - p)),
      ];
      if (r && r.width) {
        moves.push(L.logo.animate([{ transform: "none", color: L.logo.style.color }, { transform: this.over(L, r), color: getComputedStyle(target).color }],
          { duration: ms, easing: ease, fill: "forwards" }).finished);
      } else {
        moves.push(L.logo.animate([{ opacity: 1 }, { opacity: 0 }], { duration: ms * 0.6, fill: "forwards" }).finished);
      }
      if (L.style === "outline") {
        // The lines fill in as the logo lands, so it matches the header's solid logo.
        const opts = { duration: ms * 0.4, delay: ms * 0.6, easing: ease, fill: "forwards" };
        L.fills.forEach((p) => p.animate([{ opacity: 0 }, { opacity: 1 }], opts));
        L.outlines.forEach((p) => p.animate([{ opacity: 1 }, { opacity: 0 }], opts));
      }
      Promise.all(moves).then(() => { this.cleanup(L); done(); }, () => { this.cleanup(L); done(); });
    });
  },

  cleanup(L) {
    delete document.documentElement.dataset.pageTransition;
    L.frost.remove();
    // The header's own logo fades back in (0.3s) under the copy, then the copy goes.
    setTimeout(() => L.logo.remove(), 320);
  },

  // Full-reload sites: leave a note, then the next page calls arrive().
  leave(note = {}) {
    CustomEnv.session.set(this.options.storageKey, JSON.stringify(note));
  },

  arrive({ to, after } = {}) {
    const raw = CustomEnv.session.get(this.options.storageKey);
    if (!raw) return false;
    try { window.sessionStorage.removeItem(this.options.storageKey); } catch (e) { /* blocked */ }
    let note = {};
    try { note = JSON.parse(raw) || {}; } catch (e) { /* ignore */ }
    const target = to && to();
    // A page can show a plain frost from its first paint (<html data-arriving>, set by an inline
    // script in its <head>) until this takes over.
    const done = () => { delete document.documentElement.dataset.arriving; };
    if (!target || CustomEnv.reducedMotion) { done(); if (after) after(note); return true; }
    this.busy = true;
    document.documentElement.dataset.pageTransition = "playing";
    const L = this.makeLayer(target, this.pickStyle() === "outline" ? "outline" : "solid");
    L.frost.style.opacity = "1";
    done();
    L.outlines.forEach((p) => { p.style.strokeDashoffset = "0"; });
    this.setLens(L, 1);
    this.land(L, to, () => { this.busy = false; if (after) after(note); });
    return true;
  },
};

window.CustomLogoLoader = CustomLogoLoader;
window.CustomPetHead = CustomPetHead;
window.CustomCornerLogo = CustomCornerLogo;
window.CustomSiteTheme = CustomSiteTheme;
window.CustomSiteHeader = CustomSiteHeader;
window.CustomTorchReveal = CustomTorchReveal;
window.CustomPageTransition = CustomPageTransition;
window.CustomWalkPlanner = CustomWalkPlanner;
