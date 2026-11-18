"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const LenisContext = createContext<Lenis | null>(null);
export const useLenis = () => useContext(LenisContext);

/** Lenis smooth scroll driven by GSAP's ticker, so ScrollTrigger and Lenis share one clock.
 *  Also runs the scroll-wide effects: band parallax ([data-band]) and drifting layers ([data-speed]). */
export default function SmoothScroll({ children }: { children: React.ReactNode }) {
  const [lenis, setLenis] = useState<Lenis | null>(null);
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // every visit starts at the cover: on a refresh the browser would otherwise put the page back where it
    // was scrolled to, while the opening locks scrolling, leaving the guest stuck mid-page
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    window.scrollTo(0, 0);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const l = new Lenis({ duration: 1.15, smoothWheel: !reduce, syncTouch: false });
    l.scrollTo(0, { immediate: true, force: true });
    l.on("scroll", ScrollTrigger.update);
    const tick = (t: number) => l.raf(t * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);
    l.stop(); // the opening unlocks it
    setLenis(l);
    return () => {
      gsap.ticker.remove(tick);
      l.destroy();
    };
  }, []);

  useEffect(() => {
    if (!lenis || !root.current) return;
    const ctx = gsap.context(() => {
      // aronai bands slide sideways against the scroll
      gsap.utils.toArray<HTMLElement>("[data-band]").forEach((b, i) => {
        gsap.fromTo(b, { backgroundPositionX: 0 }, {
          backgroundPositionX: (i % 2 ? 1 : -1) * 160,
          ease: "none",
          scrollTrigger: { trigger: b, start: "top bottom", end: "bottom top", scrub: true },
        });
      });
      // layers that drift at their own speed ([data-speed] = fraction of the scroll)
      gsap.utils.toArray<HTMLElement>("[data-speed]").forEach((el) => {
        const s = parseFloat(el.dataset.speed || "0");
        gsap.to(el, {
          yPercent: s * 100,
          ease: "none",
          scrollTrigger: { trigger: el.closest("section") || el, start: "top top", end: "bottom top", scrub: true },
        });
      });
    }, root);
    return () => ctx.revert();
  }, [lenis]);

  return (
    <LenisContext.Provider value={lenis}>
      <div ref={root}>{children}</div>
    </LenisContext.Provider>
  );
}
