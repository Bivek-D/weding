import gsap from "gsap";

/** Butterfly flight: each element wanders around where it starts on a smooth, never-repeating path,
 *  banks into its turns, bobs with each wingbeat, and every few seconds settles to rest (wings slow,
 *  via the `resting` class) before flying on. Returns a stop function. */
export function wander(els: HTMLElement[], { ampX = 60, ampY = 40, restingClass = "", scale = 1 } = {}) {
  const rand = (a: number, b: number) => a + Math.random() * (b - a);
  const birds = els.map((el) => ({
    el,
    cx: Number(gsap.getProperty(el, "x")) || 0,
    cy: Number(gsap.getProperty(el, "y")) || 0,
    p: [rand(0, 6.3), rand(0, 6.3), rand(0, 6.3), rand(0, 6.3)],
    f: [rand(.7, 1.1), rand(1.6, 2.3), rand(.8, 1.3), rand(1.4, 2)],
    t: rand(0, 20),
    speed: 1,
    flying: true,
    until: performance.now() + rand(3000, 7000),
    lastX: Number(gsap.getProperty(el, "x")) || 0,
    rot: 0,
    setX: gsap.quickSetter(el, "x", "px"),
    setY: gsap.quickSetter(el, "y", "px"),
    setR: gsap.quickSetter(el, "rotation", "deg"),
  }));
  els.forEach((el) => gsap.set(el, { scale }));

  const tick = (time: number, dt: number) => {
    const now = performance.now();
    for (const b of birds) {
      if (now > b.until) {                      // switch between flying and resting
        b.flying = !b.flying;
        b.until = now + (b.flying ? rand(4000, 8000) : rand(1400, 2800));
        if (restingClass) b.el.classList.toggle(restingClass, !b.flying);
      }
      b.speed += ((b.flying ? 1 : 0.06) - b.speed) * 0.04;
      b.t += (dt / 1000) * b.speed * 0.9;
      const x = b.cx + ampX * (0.62 * Math.sin(b.t * b.f[0] + b.p[0]) + 0.38 * Math.sin(b.t * b.f[1] + b.p[1]));
      const flutter = Math.sin(time * 15 + b.p[2]) * 3 * b.speed;
      const y = b.cy + ampY * (0.6 * Math.sin(b.t * b.f[2] + b.p[2]) + 0.4 * Math.sin(b.t * b.f[3] + b.p[3])) + flutter;
      const vx = (x - b.lastX) / Math.max(dt, 1) * 16;
      b.lastX = x;
      b.rot += (gsap.utils.clamp(-28, 28, vx * 9) - b.rot) * 0.08;
      b.setX(x);
      b.setY(y);
      b.setR(b.rot);
    }
  };
  gsap.ticker.add(tick);
  return () => gsap.ticker.remove(tick);
}
