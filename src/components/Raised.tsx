"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

/**
 * Raised embroidery: a piece of art lifted off the paper.
 * Two copies of its silhouette lie on the paper as shadows: a tight contact shadow and a soft cast one.
 * As the phone tilts (--lx/--ly, set once for the whole card by useLift) and as the piece scrolls through
 * the screen (--sy, set here), the art and its shadows slide apart by different amounts, so the gap between
 * them reads as real height. `lift` is how high it stands, in px.
 */
export default function Raised({
  src, alt = "", width, lift = 8, className, style,
}: { src: string; alt?: string; width: number | string; lift?: number; className?: string; style?: React.CSSProperties }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    // the light is above the page: low on the screen the shadow falls further below the piece
    const tw = gsap.fromTo(el, { "--sy": -1 }, {
      "--sy": 1, ease: "none",
      scrollTrigger: { trigger: el, start: "top bottom", end: "bottom top", scrub: true },
    });
    return () => { tw.scrollTrigger?.kill(); tw.kill(); };
  }, []);
  const s = `/art/relief/${src}.webp`;
  return (
    <div ref={ref} className={`raised ${className ?? ""}`} style={{ width, "--lift": lift, ...style } as React.CSSProperties}>
      <img className="raised-cast" src={s} alt="" aria-hidden />
      <img className="raised-contact" src={s} alt="" aria-hidden />
      <img className="raised-art" src={s} alt={alt} />
    </div>
  );
}

/** Feeds the phone's tilt (or the pointer on a computer) into --lx/--ly on the card, -1..1, smoothed.
 *  Only writes when the value changes, so a still phone costs nothing. */
export function useLift(target: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = target.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const tgt = { x: 0, y: 0 }, cur = { x: 0, y: 0 }, shown = { x: "", y: "" };
    let base: { b: number; g: number } | null = null;
    const onTilt = (e: DeviceOrientationEvent) => {
      if (e.beta == null || e.gamma == null) return;
      base ??= { b: e.beta, g: e.gamma };
      tgt.x = gsap.utils.clamp(-1, 1, (e.gamma - base.g) / 20);
      tgt.y = gsap.utils.clamp(-1, 1, (e.beta - base.b) / 20);
    };
    const onPointer = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      tgt.x = gsap.utils.clamp(-1, 1, (e.clientX / window.innerWidth - .5) * 2);
      tgt.y = gsap.utils.clamp(-1, 1, (e.clientY / window.innerHeight - .5) * 2);
    };
    const tick = () => {
      cur.x += (tgt.x - cur.x) * .08;
      cur.y += (tgt.y - cur.y) * .08;
      const x = cur.x.toFixed(2), y = cur.y.toFixed(2);
      if (x !== shown.x || y !== shown.y) {
        shown.x = x; shown.y = y;
        el.style.setProperty("--lx", x);
        el.style.setProperty("--ly", y);
      }
    };
    gsap.ticker.add(tick);
    window.addEventListener("deviceorientation", onTilt);
    window.addEventListener("pointermove", onPointer);
    return () => {
      gsap.ticker.remove(tick);
      window.removeEventListener("deviceorientation", onTilt);
      window.removeEventListener("pointermove", onPointer);
    };
  }, [target]);
}
