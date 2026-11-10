/*
 * Interactions: custom features (your own site pieces)
 * Written from scratch; no outside libraries (Web Animations API + a small spring simulation).
 *
 * HOW TO USE
 *   Nothing runs on load. Start what you need:
 *     CustomLogoLoader.init("c-logo-loader");   // full-screen logo draw-in, once per session
 *     CustomPetHead.init("c-pet-head");          // grabbable, tilting dog drawing
 *   init() accepts an element id or an element and is safe to call twice.
 *
 * Feature modules (default element id):
 *   CustomLogoLoader  #c-logo-loader   outline draw-in, fill, frame lines, lift-off reveal
 *   CustomPetHead     #c-pet-head      hover tilt + swell, grab squash/stretch, spring wobble
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
 *   2.6s  the logo shrinks slightly, the cover lifts upward (0.8s), then the element is hidden
 * Click / tap / Escape skips. Plays once per browser session (sessionStorage) unless
 * options.oncePerSession is false. Fires document "logoloader:done" at the end.
 */
const CustomLogoLoader = {
  el: null,
  options: {
    oncePerSession: true,
    storageKey: "custom-logo-loader-seen",
    speed: 1,          // 2 = twice as fast
    strokeWidth: 1.5,  // outline thickness in screen pixels
  },
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
      if (svg) svg.animate([{ transform: "scale(1)", opacity: 1 }, { transform: "scale(0.9)", opacity: 0 }],
        { duration: this.t(0.6), easing: easeIn, fill: "forwards" });
      this.el.animate([{ clipPath: "inset(0 0 0 0)" }, { clipPath: "inset(0 0 100% 0)" }],
        { duration: this.t(0.8), delay: this.t(0.25), easing: inOut, fill: "forwards" })
        .finished.then(() => this.finish());
    });
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
    if (!silent) document.dispatchEvent(new CustomEvent("logoloader:done"));
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

window.CustomLogoLoader = CustomLogoLoader;
window.CustomPetHead = CustomPetHead;
