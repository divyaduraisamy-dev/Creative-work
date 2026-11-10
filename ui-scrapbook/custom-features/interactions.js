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
 *   init() accepts an element id or an element and is safe to call twice.
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
  scrollToTop() {
    const behavior = CustomEnv.reducedMotion ? "auto" : "smooth";
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
 * Logo cell: spring tilt and back-to-top. About / Work scroll to
 * id="about" / id="work". The toggle and Contact use CustomSiteTheme; Contact also slides open
 * the email strip (email decoded from data-email: base64 of the reversed address).
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
    this.instances.set(root, h);
    this.buildSvg(h);
    this.bindEvents(h);
    this.syncThemeButton(h);
    this.waitForLoader(h);
    return h;
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
      h.logo.addEventListener("click", (e) => { e.preventDefault(); CustomEnv.scrollToTop(); });
    }
    root.querySelectorAll("[data-scroll-to]").forEach((a) => a.addEventListener("click", (e) => {
      const dest = document.getElementById(a.dataset.scrollTo);
      if (!dest) return;
      e.preventDefault();
      dest.scrollIntoView({ behavior: CustomEnv.reducedMotion ? "auto" : "smooth", block: "start" });
    }));
    if (h.themeBtn) h.themeBtn.addEventListener("click", () => {
      if (this.isContactOpen(h)) this.closeContact(h);
      else CustomSiteTheme.toggle();
    });
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
    CustomSiteTheme.set(CustomSiteTheme.other(CustomSiteTheme.saved()), { save: false }).then(() => {
      h.root.dataset.contact = "open";
    });
  },

  closeContact(h) {
    h.root.dataset.contact = "closed";
    h.contactBtn.setAttribute("aria-expanded", "false");
    h.root.querySelectorAll("[data-email-link], [data-email-copy]").forEach((el) => el.setAttribute("tabindex", "-1"));
    CustomSiteTheme.set(CustomSiteTheme.saved(), { save: false });
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

window.CustomLogoLoader = CustomLogoLoader;
window.CustomPetHead = CustomPetHead;
window.CustomCornerLogo = CustomCornerLogo;
window.CustomSiteTheme = CustomSiteTheme;
window.CustomSiteHeader = CustomSiteHeader;
