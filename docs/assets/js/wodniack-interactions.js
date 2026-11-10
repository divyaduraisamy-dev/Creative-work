/*!
 * Interactions: wodniack-dev
 * Source: https://wodniack.dev/
 *
 * Adapted from "AW-2025-Portfolio" by Antoine Wodniack
 * https://github.com/AntoineW/AW-2025-Portfolio  (commit c33251d, May 2025)
 * Licensed CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/).
 * Credit is required and commercial use is not allowed. Keep this notice when reusing.
 *
 * Changes from the original: Astro/TypeScript classes became plain object modules; the site's
 * Emitter/Ticker/Noise are inlined; no loader (the "intro" event fires after setup); DrawSVG and
 * SplitText replaced by a stroke-dashoffset draw-in and a manual letter split; a GSAP marquee loop
 * joins the separator flicker; the contrast mask uses a normal blend (original: darken); touch on
 * the waves doesn't block page scrolling; the waves measure their position live so the cursor push
 * stays accurate inside inner scroll containers.
 *
 * HOW TO USE
 *   Nothing runs on load. Start what you need:
 *     WodInteractions.initAll();            // everything (what page-frame.html does)
 *     WodWaves.init("c-hero-waves");        // or one feature by element id (or element)
 *   Every init() starts the shared modules it needs and is safe to call twice.
 *   Needs (load first): gsap 3.13.0 (+ ScrollTrigger for WodWorkScroll / WodReveal,
 *   Lenis 1.3.3 for WodSmoothScroll). The catalog (../feature-catalog.json) lists each feature's
 *   markup contract.
 *
 * Feature modules (default element id):
 *   WodWaves         #c-hero-waves    mouse-reactive Perlin line field
 *   WodHeroIntro     #c-hero          line draw-in, letter roll, star turn
 *   WodMarquee       #c-marquee       GSAP loop + binary flicker (any [data-js~="marquee"])
 *   WodContrast      #c-contrast-toggle  sliding mask + theme flip
 *   WodNavbarIntro   #c-navbar        bar drop + staggered items
 *   WodNavLinks      #c-navbar        menu links smooth-scroll to sections
 *   WodScrollTop     #c-footer-top    smooth scroll to top
 *   WodWorkScroll    #section-2       scrubbed card scale / clip / column drift
 *   WodReveal        #section-1 etc.  rise-in of [data-js~="reveal"] children
 * Shared modules: WodEnv, WodBus, WodLoop, WodIntersect, WodSmoothScroll
 */

/* Shared: environment and helpers ------------------------------------------------------------ */
const WodEnv = {
  source: '[data-source="wodniack-dev"]',
  reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  pluginsRegistered: false,

  get gsap() {
    const g = window.gsap;
    if (g && window.ScrollTrigger && !this.pluginsRegistered) {
      g.registerPlugin(window.ScrollTrigger);
      this.pluginsRegistered = true;
    }
    return g;
  },

  get ScrollTrigger() {
    return this.gsap ? window.ScrollTrigger : undefined;
  },

  resolve(target) {
    return typeof target === "string" ? document.getElementById(target) : target || null;
  },

  all(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  },

  // Marks an element as handled so its component's own fallback script steps aside.
  enhance(el) {
    el.dataset.enhanced = "true";
  },

  warnMissing(name) {
    console.warn(`[wodniack] ${name}: GSAP not found; skipped.`);
  },
};

/* Shared: event bus (the site's Emitter). Events: tick (ms), resize, mousemove (x, y), scroll (y),
 * contrastchange ('contrasted' | 'default'). */
const WodBus = {
  events: {},

  on(name, cb, ctx) {
    const list = (this.events[name] ||= []);
    if (!list.some((o) => o.cb === cb && o.ctx === ctx)) list.push({ cb, ctx });
  },

  off(name, cb, ctx) {
    if (this.events[name]) this.events[name] = this.events[name].filter((o) => !(o.cb === cb && o.ctx === ctx));
  },

  emit(name, ...args) {
    (this.events[name] || []).slice().forEach((o) => o.cb.apply(o.ctx, args));
  },
};

/* Shared: one gsap.ticker loop plus window listeners routed through the bus ---------------------- */
const WodLoop = {
  ready: false,
  resizeTimer: null,

  init() {
    if (this.ready || !WodEnv.gsap) return;
    this.ready = true;
    WodEnv.gsap.ticker.add((time) => WodBus.emit("tick", time * 1000));
    this.bindEvents();
  },

  bindEvents() {
    window.addEventListener("resize", () => {
      clearTimeout(this.resizeTimer);
      this.resizeTimer = setTimeout(() => WodBus.emit("resize"), 200);
    });
    window.addEventListener("mousemove", (e) => WodBus.emit("mousemove", e.clientX, e.clientY), { passive: true });
    window.addEventListener("scroll", () => WodBus.emit("scroll", window.scrollY), { passive: true });
  },
};

/* Shared: visibility observer. Adds is-in-view / is-out-of-view(-top|-bottom) and dispatches an
 * "intersect" event ({ isIntersecting }) so loops can pause off screen. */
const WodIntersect = {
  observer: null,

  init() {
    if (this.observer) return;
    this.observer = new IntersectionObserver((entries) => entries.forEach(this.onEntry), { threshold: 0 });
  },

  onEntry(entry) {
    const el = entry.target;
    el.dispatchEvent(new CustomEvent("intersect", { detail: { isIntersecting: entry.isIntersecting } }));
    if (entry.isIntersecting) {
      el.classList.add("is-in-view");
      el.classList.remove("is-out-of-view", "is-out-of-view-top", "is-out-of-view-bottom");
    } else {
      el.classList.remove("is-in-view");
      el.classList.add("is-out-of-view");
      el.classList.toggle("is-out-of-view-top", entry.boundingClientRect.top < 0);
      el.classList.toggle("is-out-of-view-bottom", entry.boundingClientRect.top > 0);
    }
  },

  observe(el) {
    this.init();
    this.observer.observe(el);
  },

  // Run fn on every tick only while el is on screen.
  tickWhileVisible(el, fn, ctx) {
    this.observe(el);
    el.addEventListener("intersect", (e) => {
      if (e.detail.isIntersecting) WodBus.on("tick", fn, ctx);
      else WodBus.off("tick", fn, ctx);
    }, { passive: true });
  },
};

/* Shared: Lenis smooth scrolling wired to ScrollTrigger and gsap.ticker (as on the site) --------- */
const WodSmoothScroll = {
  ready: false,
  lenis: null,
  duration: 1.5,

  init() {
    if (this.ready) return;
    this.ready = true;
    const g = WodEnv.gsap;
    if (!g || !window.Lenis || WodEnv.reducedMotion) return;
    this.lenis = new window.Lenis(); // site uses defaults: lerp 0.1, smoothWheel true
    if (WodEnv.ScrollTrigger) this.lenis.on("scroll", WodEnv.ScrollTrigger.update);
    g.ticker.add((time) => this.lenis.raf(time * 1000));
    g.ticker.lagSmoothing(0);
    window.lenis = this.lenis;
  },

  easeInOutQuint(t) {
    return t < 0.5 ? 16 * t ** 5 : 1 + 16 * (t - 1) ** 5;
  },

  // Works with or without Lenis.
  scrollTo(target) {
    if (this.lenis) {
      this.lenis.scrollTo(target, { duration: this.duration, easing: this.easeInOutQuint });
      return;
    }
    const behavior = WodEnv.reducedMotion ? "auto" : "smooth";
    if (typeof target === "number") window.scrollTo({ top: target, behavior });
    else { const el = document.querySelector(target); if (el) el.scrollIntoView({ behavior }); }
  },
};

/* Menu links: smooth scroll to their #section ----------------------------------------------------- */
const WodNavLinks = {
  ready: false,

  init(target = "c-navbar") {
    const el = WodEnv.resolve(target);
    if (!el || this.ready) return;
    this.ready = true;
    WodEnv.all('[data-js~="menu-link"]', el).forEach((link) => link.addEventListener("click", this.onClick));
  },

  onClick(e) {
    const href = e.currentTarget.getAttribute("href");
    if (!href || !href.startsWith("#") || href === "#" || !document.querySelector(href)) return;
    e.preventDefault();
    WodSmoothScroll.scrollTo(href);
  },
};

/* Back-to-top link --------------------------------------------------------------------------------- */
const WodScrollTop = {
  ready: false,

  init(target = "c-footer-top") {
    const el = WodEnv.resolve(target);
    if (!el || this.ready) return;
    this.ready = true;
    el.addEventListener("click", (e) => { e.preventDefault(); WodSmoothScroll.scrollTo(0); });
  },
};

/* Contrast: a full-screen mask slides across (1s expo.inOut) and the theme flips.
 * On: the theme switches at once, the mask slides off left (0 -> -100%).
 * Off: the mask slides back (-100% -> 0), then the theme is removed. */
const WodContrast = {
  el: null,
  mask: null,
  isAnimating: false,
  options: {
    maskColor: "#f40c3f",       // original: default theme primary
    maskBorderColor: "#160000", // original: default theme secondary
    maskBorderWidth: "1rem",
    maskBlend: "normal",        // original: "darken"
    duration: 1,
    ease: "expo.inOut",
    scope: '[data-source="wodniack-dev"]', // roots that receive data-theme="contrast"
  },

  init(target = "c-contrast-toggle", options = {}) {
    const el = WodEnv.resolve(target);
    if (!el || this.el) return;
    Object.assign(this.options, options);
    this.el = el;
    this.createMask();
    el.addEventListener("click", this.toggle.bind(this), { passive: true });
    WodEnv.enhance(el);
  },

  createMask() {
    const o = this.options;
    this.mask = document.createElement("div");
    this.mask.setAttribute("aria-hidden", "true");
    this.mask.dataset.js = "contrast-mask";
    Object.assign(this.mask.style, {
      position: "fixed", inset: "0", zIndex: "20", pointerEvents: "none", willChange: "transform",
      background: o.maskColor, borderRight: `${o.maskBorderWidth} solid ${o.maskBorderColor}`, mixBlendMode: o.maskBlend,
      transform: "translateX(-100%)",
    });
    document.body.appendChild(this.mask);
  },

  isOn() {
    return document.documentElement.classList.contains("theme-contrasted");
  },

  setTheme(on) {
    document.documentElement.classList.toggle("theme-contrasted", on);
    WodEnv.all(this.options.scope).forEach((el) => {
      if (on) el.dataset.theme = "contrast";
      else if (el.dataset.theme === "contrast") delete el.dataset.theme;
    });
    this.el.setAttribute("aria-pressed", String(on));
  },

  emit() {
    const state = this.isOn() ? "contrasted" : "default";
    WodBus.emit("contrastchange", state);
    document.dispatchEvent(new CustomEvent("contrastchange", { detail: { state } }));
  },

  toggle() {
    if (this.isAnimating) return;
    const on = this.isOn();
    const g = WodEnv.gsap;
    if (!g || WodEnv.reducedMotion) { this.setTheme(!on); this.emit(); return; }

    this.isAnimating = true;
    g.fromTo(this.mask, { xPercent: on ? -100 : 0 }, {
      xPercent: on ? 0 : -100,
      duration: this.options.duration,
      ease: this.options.ease,
      onComplete: () => {
        g.set(this.mask, { xPercent: -100 });
        if (on) this.setTheme(false);
        this.isAnimating = false;
        this.emit();
      },
    });
    if (!on) this.setTheme(true);
  },
};

/* Navbar intro: bar drops in (1.5s expo.inOut), then items follow (expo.out, stagger 0.1) -------- */
const WodNavbarIntro = {
  el: null,

  init(target = "c-navbar") {
    const el = WodEnv.resolve(target);
    if (!el || this.el) return;
    this.el = el;
    document.addEventListener("intro", () => this.play(), { once: true });
  },

  play() {
    const g = WodEnv.gsap;
    if (!this.el || !g || WodEnv.reducedMotion) return;
    const items = WodEnv.all('[data-js~="navbar-item"]', this.el);
    g.timeline()
      .from(this.el, { yPercent: -100, duration: 1.5, ease: "expo.inOut" }, 0)
      .from(items, { yPercent: -100, opacity: 0, duration: 1.5, ease: "expo.out", stagger: 0.1 }, 0.5);
  },
};

/* Marquee: GSAP loop (xPercent 0 -> -50 over two copies) that pauses off screen and eases to a stop
 * on hover, plus the separator's binary flicker (each digit 10% per frame). Works per instance. */
const WodMarquee = {
  instances: new WeakSet(),

  init(target = "c-marquee") {
    const root = WodEnv.resolve(target);
    if (!root || this.instances.has(root)) return;
    this.instances.add(root);
    const track = root.querySelector('[data-js~="marquee-track"]');
    if (!track) return;

    const chars = this.splitBinary(root);
    const g = WodEnv.gsap;
    if (!g) { WodEnv.warnMissing("WodMarquee"); return; }
    if (WodEnv.reducedMotion) return;
    WodLoop.init();

    track.style.animation = "none"; // take over from the CSS keyframe loop
    const seconds = parseFloat(getComputedStyle(root).getPropertyValue("--motion-duration-marquee")) || 30;
    const reverse = root.classList.contains("c-marquee--reverse");
    const loop = g.fromTo(track,
      { xPercent: reverse ? -50 : 0 },
      { xPercent: reverse ? 0 : -50, duration: seconds, ease: "none", repeat: -1, paused: true });

    root.addEventListener("mouseenter", () => g.to(loop, { timeScale: 0, duration: 0.6, overwrite: true }));
    root.addEventListener("mouseleave", () => g.to(loop, { timeScale: 1, duration: 0.6, overwrite: true }));

    const flicker = () => {
      for (const c of chars) {
        if (Math.random() > 0.1) continue;
        c.textContent = Math.random() > 0.5 ? "0" : "1";
      }
    };

    WodIntersect.observe(root);
    root.addEventListener("intersect", (e) => {
      if (e.detail.isIntersecting) { loop.play(); WodBus.on("tick", flicker); }
      else { loop.pause(); WodBus.off("tick", flicker); }
    }, { passive: true });
  },

  splitBinary(root) {
    const chars = [];
    WodEnv.all('[data-js~="binary"]', root).forEach((run) => {
      const text = run.textContent;
      run.textContent = "";
      for (const ch of text) {
        const span = document.createElement("span");
        span.textContent = ch;
        run.appendChild(span);
        if (ch === "0" || ch === "1") chars.push(span);
      }
    });
    return chars;
  },
};

/* Waves: vertical SVG polylines bent by Perlin noise, pushed by the cursor (velocity push, string
 * tension 0.005, friction 0.925, ±100px clamp) with a dot following the smoothed cursor.
 * Ported from the site's <a-waves>. The cursor push starts after enableCursor() (or "introend"). */
const WodNoise = {
  create(seed = Math.random()) {
    const G = (x, y) => ({ x, y });
    const grad3 = [G(1, 1), G(-1, 1), G(1, -1), G(-1, -1), G(1, 0), G(-1, 0), G(1, 0), G(-1, 0), G(0, 1), G(0, -1), G(0, 1), G(0, -1)];
    const p = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180];
    const perm = new Array(512);
    const gradP = new Array(512);
    if (seed > 0 && seed < 1) seed *= 65536;
    seed = Math.floor(seed);
    if (seed < 256) seed |= seed << 8;
    for (let i = 0; i < 256; i++) {
      const v = i & 1 ? p[i] ^ (seed & 255) : p[i] ^ ((seed >> 8) & 255);
      perm[i] = perm[i + 256] = v;
      gradP[i] = gradP[i + 256] = grad3[v % 12];
    }
    const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);
    const lerp = (a, b, t) => (1 - t) * a + t * b;
    const dot = (g, a, b) => g.x * a + g.y * b;
    return {
      perlin2(x, y) {
        let X = Math.floor(x), Y = Math.floor(y);
        x -= X; y -= Y; X &= 255; Y &= 255;
        const n00 = dot(gradP[X + perm[Y]], x, y);
        const n01 = dot(gradP[X + perm[Y + 1]], x, y - 1);
        const n10 = dot(gradP[X + 1 + perm[Y]], x - 1, y);
        const n11 = dot(gradP[X + 1 + perm[Y + 1]], x - 1, y - 1);
        const u = fade(x);
        return lerp(lerp(n00, n10, u), lerp(n01, n11, u), fade(y));
      },
    };
  },
};

const WodWaves = {
  instances: new Map(),
  options: { xGap: 10, yGap: 32, pushRadius: 175, tension: 0.005, friction: 0.925, clamp: 100 },

  init(target = "c-hero-waves", options = {}) {
    const el = WodEnv.resolve(target);
    if (!el || this.instances.has(el)) return this.instances.get(el) || null;
    if (!WodEnv.gsap) { WodEnv.warnMissing("WodWaves"); return null; }
    WodLoop.init();
    const field = this.createField(el, { ...this.options, ...options });
    this.instances.set(el, field);
    return field;
  },

  get(target) {
    return this.instances.get(WodEnv.resolve(target)) || null;
  },

  enableCursor(target) {
    const field = this.get(target);
    if (field) field.isInteractive = true;
  },

  createField(el, opts) {
    const NS = "http://www.w3.org/2000/svg";
    const field = {
      el, opts,
      svg: document.createElementNS(NS, "svg"),
      dot: document.createElement("span"),
      mouse: { x: -10, y: 0, lx: 0, ly: 0, sx: 0, sy: 0, v: 0, vs: 0, a: 0, set: false },
      lines: [], paths: [], noise: WodNoise.create(), isInteractive: false, bounding: null,
    };

    field.svg.setAttribute("aria-hidden", "true");
    Object.assign(field.svg.style, { position: "absolute", inset: "0", display: "block", width: "100%", height: "100%" });
    Object.assign(field.dot.style, {
      position: "absolute", top: "0", left: "0", width: "0.5rem", height: "0.5rem", borderRadius: "50%",
      background: "currentColor", pointerEvents: "none", willChange: "transform", transform: "translate3d(-1rem, -1rem, 0)",
    });
    el.append(field.svg, field.dot);
    const fallback = el.querySelector('[data-js~="waves-fallback"]');
    if (fallback) fallback.style.display = "none";
    WodEnv.enhance(el);

    this.setSize(field);
    this.setLines(field);

    WodBus.on("mousemove", (x, y) => this.updateMouse(field, x, y));
    WodBus.on("resize", () => { this.setSize(field); this.setLines(field); });
    el.addEventListener("touchmove", (e) => this.updateMouse(field, e.touches[0].clientX, e.touches[0].clientY), { passive: true });
    el.addEventListener("introend", () => { field.isInteractive = true; });

    if (WodEnv.reducedMotion) {
      this.movePoints(field, 0);
      this.draw(field);
    } else {
      WodIntersect.tickWhileVisible(el, (time) => this.tick(field, time));
    }
    return field;
  },

  // Measured live, so it stays right inside inner scroll containers (e.g. Streamlit's main panel).
  updateMouse(field, x, y) {
    const m = field.mouse;
    const r = field.el.getBoundingClientRect();
    m.x = x - r.left;
    m.y = y - r.top;
    if (!m.set) { m.sx = m.lx = m.x; m.sy = m.ly = m.y; m.set = true; }
  },

  setSize(field) {
    const r = field.el.getBoundingClientRect();
    field.bounding = { left: r.left, top: r.top + window.scrollY, width: field.el.clientWidth, height: field.el.clientHeight };
    field.svg.setAttribute("viewBox", `0 0 ${field.bounding.width} ${field.bounding.height}`);
  },

  setLines(field) {
    const { width, height } = field.bounding;
    const { xGap, yGap } = field.opts;
    field.paths.forEach((p) => p.remove());
    field.lines = [];
    field.paths = [];
    const totalLines = Math.ceil((width + 200) / xGap);
    const totalPoints = Math.ceil((height + 30) / yGap);
    const xStart = (width - xGap * totalLines) / 2;
    const yStart = (height - yGap * totalPoints) / 2;
    for (let i = 0; i <= totalLines; i++) {
      const points = [];
      for (let j = 0; j <= totalPoints; j++) {
        points.push({ x: xStart + xGap * i, y: yStart + yGap * j, wave: { x: 0, y: 0 }, cursor: { x: 0, y: 0, vx: 0, vy: 0 } });
      }
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "currentColor");
      path.setAttribute("stroke-width", "1");
      path.setAttribute("pathLength", "1");
      path.setAttribute("vector-effect", "non-scaling-stroke");
      field.svg.appendChild(path);
      field.paths.push(path);
      field.lines.push(points);
    }
    this.draw(field);
  },

  movePoints(field, time) {
    const { mouse, noise, opts } = field;
    field.lines.forEach((points) => points.forEach((p) => {
      const move = noise.perlin2((p.x + time * 0.0125) * 0.002, (p.y + time * 0.005) * 0.0015) * 12;
      p.wave.x = Math.cos(move) * 32;
      p.wave.y = Math.sin(move) * 16;
      if (!field.isInteractive) return;
      const d = Math.hypot(p.x - mouse.sx, p.y - mouse.sy);
      const l = Math.max(opts.pushRadius, mouse.vs);
      if (d < l) {
        const f = Math.cos(d * 0.001) * (1 - d / l);
        p.cursor.vx += Math.cos(mouse.a) * f * l * mouse.vs * 0.00065;
        p.cursor.vy += Math.sin(mouse.a) * f * l * mouse.vs * 0.00065;
      }
      p.cursor.vx += (0 - p.cursor.x) * opts.tension;
      p.cursor.vy += (0 - p.cursor.y) * opts.tension;
      p.cursor.vx *= opts.friction;
      p.cursor.vy *= opts.friction;
      p.cursor.x = Math.min(opts.clamp, Math.max(-opts.clamp, p.cursor.x + p.cursor.vx * 2));
      p.cursor.y = Math.min(opts.clamp, Math.max(-opts.clamp, p.cursor.y + p.cursor.vy * 2));
    }));
  },

  draw(field) {
    const moved = (pt, withCursor) => ({
      x: Math.round((pt.x + pt.wave.x + (withCursor ? pt.cursor.x : 0)) * 10) / 10,
      y: Math.round((pt.y + pt.wave.y + (withCursor ? pt.cursor.y : 0)) * 10) / 10,
    });
    field.lines.forEach((points, i) => {
      const first = moved(points[0], false);
      let d = `M ${first.x} ${first.y}`;
      points.forEach((p, j) => { const c = moved(p, j !== points.length - 1); d += `L ${c.x} ${c.y}`; });
      field.paths[i].setAttribute("d", d);
    });
  },

  tick(field, time) {
    const m = field.mouse;
    m.sx += (m.x - m.sx) * 0.1;
    m.sy += (m.y - m.sy) * 0.1;
    const dx = m.x - m.lx;
    const dy = m.y - m.ly;
    const d = Math.hypot(dx, dy);
    m.v = d;
    m.vs = Math.min(100, m.vs + (d - m.vs) * 0.1);
    m.lx = m.x;
    m.ly = m.y;
    m.a = Math.atan2(dy, dx);
    field.dot.style.transform = `translate3d(calc(${m.sx}px - 50%), calc(${m.sy}px - 50%), 0)`;
    this.movePoints(field, time);
    this.draw(field);
  },
};

/* Hero intro: wave lines draw in from the edges (3s expo.out), cursor push turns on 1s before
 * the end, headline letters roll up (2s expo.inOut, stagger 0.02), the star turns from 90deg. */
const WodHeroIntro = {
  el: null,
  chars: [],

  init(target = "c-hero") {
    const el = WodEnv.resolve(target);
    if (!el || this.el) return;
    this.el = el;
    const waves = el.querySelector('[data-js~="waves"]');
    if (waves) WodWaves.init(waves);
    const title = el.querySelector('[data-js~="hero-title"]');
    this.chars = title ? this.splitChars(title) : [];
    document.addEventListener("intro", () => this.play(), { once: true });
  },

  splitChars(title) {
    const label = title.textContent.replace(/\s+/g, " ").trim();
    const chars = [];
    WodEnv.all(":scope > span", title).forEach((word) => {
      if (word.matches('[data-js~="hero-star"]')) return;
      const text = word.textContent;
      word.textContent = "";
      word.setAttribute("aria-hidden", "true");
      for (const ch of text) {
        const outer = document.createElement("span");
        outer.style.cssText = "display:inline-block;overflow:hidden;vertical-align:top;";
        const inner = document.createElement("span");
        inner.style.cssText = "display:inline-block;";
        inner.textContent = ch;
        outer.appendChild(inner);
        word.appendChild(outer);
        chars.push(inner);
      }
    });
    title.setAttribute("aria-label", label);
    return chars;
  },

  play() {
    if (!this.el) return;
    const g = WodEnv.gsap;
    const wavesEl = this.el.querySelector('[data-js~="waves"]');
    const field = wavesEl ? WodWaves.get(wavesEl) : null;
    if (!g || WodEnv.reducedMotion) { if (field) field.isInteractive = true; return; }

    const tl = g.timeline();
    if (field) {
      tl.fromTo(field.paths, { strokeDasharray: 1, strokeDashoffset: 1 }, {
        strokeDashoffset: 0, duration: 3, ease: "expo.out",
        stagger: { amount: 0.5, from: "edges", ease: "power3.inOut" },
        onComplete: () => field.paths.forEach((p) => { p.style.strokeDasharray = ""; p.style.strokeDashoffset = ""; }),
      }, 0.5);
      tl.call(() => wavesEl.dispatchEvent(new CustomEvent("introend")), null, "-=1");
    }
    if (this.chars.length) tl.fromTo(this.chars, { yPercent: 100 }, { yPercent: 0, duration: 2, ease: "expo.inOut", stagger: 0.02 }, 1);
    const star = this.el.querySelector('[data-js~="hero-star"]');
    if (star) tl.from(star, { rotate: 90, duration: 2, ease: "expo.out" }, 1.5);
  },
};

/* Work: one scrubbed timeline from "top 25%" to "bottom 75%" (scrub 1): card 0.75 -> 1, section
 * inset(0 1rem) -> 0, letter columns drift at different speeds. Needs ScrollTrigger. */
const WodWorkScroll = {
  el: null,
  speeds: [1, 2.2, 1.5, 2.8],

  init(target = "section-2") {
    const el = WodEnv.resolve(target);
    if (!el || this.el) return;
    this.el = el;
    const g = WodEnv.gsap;
    if (!g || !WodEnv.ScrollTrigger || WodEnv.reducedMotion) return;
    const card = el.querySelector('[data-js~="work-card"]');
    const columns = WodEnv.all('[data-js~="work-column"]', el);
    const tl = g.timeline({ scrollTrigger: { trigger: el, start: "top 25%", end: "bottom 75%", scrub: 1 } });
    if (card) tl.fromTo(card, { scale: 0.75 }, { scale: 1, duration: 0.75, ease: "power3.in" }, 0);
    tl.fromTo(el, { clipPath: "inset(0 1rem)" }, { clipPath: "inset(0 0rem)", duration: 0.75, ease: "power3.in" }, 0);
    columns.forEach((col, i) => {
      const s = this.speeds[i % this.speeds.length];
      tl.fromTo(col, { yPercent: 10 * s }, { yPercent: -10 * s, duration: 1, ease: "none" }, 0);
    });
  },
};

/* Reveal: children of [data-js~="reveal"] inside the target rise in at "top 80%" and reverse when
 * scrolled back. Call once per section. Needs ScrollTrigger. */
const WodReveal = {
  done: new WeakSet(),

  init(target) {
    const el = WodEnv.resolve(target);
    if (!el || this.done.has(el)) return;
    this.done.add(el);
    const g = WodEnv.gsap;
    if (!g || !WodEnv.ScrollTrigger || WodEnv.reducedMotion) return;
    const groups = el.matches('[data-js~="reveal"]') ? [el] : WodEnv.all('[data-js~="reveal"]', el);
    groups.forEach((group) => g.from(group.children, {
      y: 40, opacity: 0, duration: 1, ease: "expo.out", stagger: 0.08,
      scrollTrigger: { trigger: group, start: "top 80%", toggleActions: "play none none reverse" },
    }));
  },
};

/* Everything at once (what page-frame.html calls) ------------------------------------------------ */
const WodInteractions = {
  initAll() {
    if (!WodEnv.gsap) {
      console.warn("[wodniack] GSAP not found; components keep their CSS-only fallbacks.");
      return;
    }
    WodLoop.init();
    WodSmoothScroll.init();
    WodNavLinks.init("c-navbar");
    WodScrollTop.init("c-footer-top");
    WodContrast.init("c-contrast-toggle");
    WodNavbarIntro.init("c-navbar");
    WodEnv.all('[data-js~="marquee"]').forEach((el) => WodMarquee.init(el));
    WodHeroIntro.init("c-hero");
    WodWorkScroll.init("section-2");
    ["section-1", "section-3", "c-cta"].forEach((id) => WodReveal.init(id));
    WodEnv.all("[data-intersect]").forEach((el) => WodIntersect.observe(el));

    if (WodEnv.ScrollTrigger && document.fonts) document.fonts.ready.then(() => WodEnv.ScrollTrigger.refresh());
    requestAnimationFrame(() => document.dispatchEvent(new CustomEvent("intro")));
  },
};

// Kept for older pages: window.WodInteractions also exposes the shared helpers.
Object.assign(WodInteractions, { bus: WodBus, scrollTo: (t) => WodSmoothScroll.scrollTo(t), toggleContrast: () => WodContrast.toggle() });
window.WodInteractions = WodInteractions;
