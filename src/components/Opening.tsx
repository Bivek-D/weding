"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import couple from "@/content/couple.json";
import { useLenis } from "./SmoothScroll";
import { wander } from "@/lib/flight";
import { createCurtain, type Curtain } from "@/lib/curtainGL";
import s from "./opening.module.css";

const FRAMES = 36;
const UNTIE_FRAMES = 30;     // design/blender/render_aronai.py -- untie
const frameSrc = (i: number) => `/art/curtain/${String(i).padStart(2, "0")}.webp`;

/** The cinematic opening: woven doors → curtain sequence (pre-rendered, drawn on a canvas) → swags,
 *  butterflies, five Bathou lamps, names. Scroll stays locked until it has played. */
export default function Opening() {
  const root = useRef<HTMLElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const rig = useRef<HTMLDivElement>(null);
  const stopFlight = useRef<(() => void)[]>([]);
  const frames = useRef<HTMLImageElement[]>([]);
  const frame = useRef({ i: 0 });
  const [opened, setOpened] = useState(false);
  const altarRef = useRef<HTMLDivElement>(null);
  const hangs = useRef<(HTMLImageElement | null)[]>([]);

  // the aronai hung on the walls beside the shrine: each centred in the free wall between the curtain's
  // gathered edge and the shrine's post, sized to it, left out where the curtains leave no wall
  useEffect(() => {
    const fit = () => {
      const al = altarRef.current, st = root.current;
      if (!al || !st) return;
      const Wst = st.clientWidth, Wa = al.offsetWidth;
      const altarLeft = al.offsetLeft - Wa / 2;            // .altar is centred with translateX(-50%)
      const curtain = Wst * 0.13;                          // the gathered curtain's inner edge, roughly
      const gap = altarLeft + Wa * 0.1 - curtain;           // to the shrine's left post
      const w = Math.min(64, gap * 0.7);
      hangs.current.forEach((h, i) => {
        if (!h) return;
        h.style.display = gap < 24 ? "none" : "";
        const cx = curtain + gap * 0.42;                   // a little nearer the curtain than the shrine
        h.style.width = `${w}px`;
        h.style.left = `${(i === 0 ? cx : Wst - cx) - w / 2}px`;
        h.style.top = `${al.offsetTop - w * 0.4}px`;        // the nail a little above the shrine's bar
      });
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  const [ready, setReady] = useState(false);
  const lenis = useLenis();

  // the curtain: drawn live on the GPU (smooth at any frame rate); the 36 pre-rendered frames are only a
  // fallback for phones without WebGL. frame.current.i runs 0 .. FRAMES - 1 either way.
  const gl = useRef<Curtain | null>(null);
  const draw = useCallback(() => {
    if (gl.current) { gl.current.draw(frame.current.i / (FRAMES - 1)); return; }
    const c = canvas.current;
    const i = frame.current.i;
    const i0 = Math.floor(i), i1 = Math.min(i0 + 1, FRAMES - 1), f = i - i0;
    const a = frames.current[i0], b = frames.current[i1];
    if (!c || !a || !a.complete || !a.naturalWidth) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    const { width: w, height: h } = c;
    const k = Math.max(w / a.naturalWidth, h / a.naturalHeight);
    const dw = a.naturalWidth * k, dh = a.naturalHeight * k;
    const x = (w - dw) / 2, y = (h - dh) / 2;
    ctx.clearRect(0, 0, w, h);
    if (f > 0.01 && b && b.complete && b.naturalWidth) {
      // a true linear blend: (1 - f) of one frame plus f of the next, added together ("lighter"),
      // so the soft cast shadows never stack up and flicker between frames
      ctx.globalAlpha = 1 - f;
      ctx.drawImage(a, x, y, dw, dh);
      ctx.globalCompositeOperation = "lighter";
      ctx.globalAlpha = f;
      ctx.drawImage(b, x, y, dw, dh);
      ctx.globalCompositeOperation = "source-over";
    } else {
      ctx.drawImage(a, x, y, dw, dh);
    }
    ctx.globalAlpha = 1;
  }, []);

  // set up the curtain (live WebGL, or the frame sequence as a fallback) and keep the canvas sized to the stage
  useEffect(() => {
    let done = false;
    const go = () => { if (!done) { done = true; setReady(true); } };
    const curtain = canvas.current ? createCurtain(canvas.current) : null;
    gl.current = curtain;
    if (curtain) {
      curtain.ready.then(go, () => { gl.current = null; loadFrames(); });
    } else {
      loadFrames();
    }
    function loadFrames() {
      frames.current = Array.from({ length: FRAMES }, (_, i) => {
        const im = new Image();
        im.src = frameSrc(i);
        if (i === 0) im.onload = draw;
        return im;
      });
      // the tap only opens once every curtain frame is decoded, so the sequence never stutters
      Promise.all(frames.current.map((im) => im.decode().catch(() => {}))).then(go);
    }
    const fallback = window.setTimeout(go, 9000);
    const fit = () => {
      const c = canvas.current;
      if (!c) return;
      const r = c.getBoundingClientRect();
      // 1.5x is plenty for soft cloth and keeps the per-pixel shader cheap on phones
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      c.width = Math.round(r.width * dpr);
      c.height = Math.round(r.height * dpr);
      draw();
    };
    fit();
    window.addEventListener("resize", fit);
    document.body.classList.add("is-locked");   // already there from the server; kept for client navigations
    window.scrollTo(0, 0);
    return () => {
      window.removeEventListener("resize", fit);
      window.clearTimeout(fallback);
      curtain?.dispose();
      gl.current = null;
    };
  }, [draw]);

  // the butterflies on the cover wander about until the tap; their shadows travel with them on the cloth
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const els = gsap.utils.toArray<HTMLElement>(`.${s.coverFly}`, root.current);
    stopFlight.current.push(wander(els, { ampX: 70, ampY: 70, restingClass: s.resting }));
    const stops = stopFlight.current;
    return () => stops.forEach((f) => f());
  }, []);

  // (no cursor, tilt or drift movement on the front page: the cover and the stage stay still)

  const open = useCallback(() => {
    if (opened || !ready) return;
    setOpened(true);
    const q = gsap.utils.selector(root);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tl = gsap.timeline({
      defaults: { ease: "power2.inOut" },
      onComplete: () => {
        document.body.classList.remove("is-locked");
        lenis?.start();
        ScrollTrigger.refresh(); // positions were measured while the page was locked
        q(`.${s.doors}`)[0]?.remove();
        stopFlight.current.shift()?.(); // the cover butterflies are gone with the doors
      },
    });
    if (reduce) tl.timeScale(20);
    // the untie film: frames laid out 6 across, 5 down
    const film = { f: 0 };
    const filmEl = q(`.${s.untie}`)[0] as HTMLElement | undefined;
    const showFrame = (i: number) => {
      if (filmEl) filmEl.style.backgroundPosition = `${(i % 6) * 20}% ${Math.floor(i / 6) * 25}%`;
    };

    // slow and soft: every move eases in and out, and each beat overlaps the next (about 15 s in all)
    tl.to(q(`.${s.hint}`), { autoAlpha: 0, duration: 0.6, ease: "sine.out" })
      // the bow is untied as one continuous motion of cloth (30 rendered frames): the right tail is drawn
      // out and grows as the right loop runs through the knot into it, then the left; the knot opens and
      // the freed ends swing loose and fall. The sharp still bow hands over to the film's first frame,
      // which is the same pose.
      .set(q(`.${s.bowStill}`), { autoAlpha: 0 }, 0.3)
      .set(q(`.${s.untie}`), { autoAlpha: 1 }, 0.3)
      .to(film, { f: UNTIE_FRAMES - 1, duration: 2.4, ease: "none", onUpdate: () => showFrame(Math.round(film.f)) }, 0.3)
      .to(q(`.${s.untie}`), { y: 90, autoAlpha: 0, duration: 0.55, ease: "power2.in" }, 2.3);
    // the untied aronai goes slack: each half is a chain of short pieces hanging from its far end (round the
    // door edge). Its free end sags first, then the whole length swings down, the wave running out to the
    // tip, and it slips off the doors.
    for (const [side, sg] of [[s.ribbonL, 1], [s.ribbonR, -1]] as const) {
      const segs = q(`.${side} .${s.rseg}`);
      tl.to(segs, { rotate: (k: number) => sg * (1 + 0.8 * k), duration: 0.8, ease: "sine.in" }, 1.9)
        .to(segs[0], { rotate: sg * 64, duration: 1.7, ease: "power2.in" }, 2.5)
        .to(segs.slice(1), { rotate: (k: number) => sg * (3 - 0.3 * k), duration: 1.5, ease: "sine.inOut", stagger: 0.07 }, 2.6)
        .to(q(`.${side}`), { y: 280, autoAlpha: 0, duration: 1.2, ease: "power2.in" }, 3.5);
    }
    tl
      // the butterflies resting on the doors take off first
      .to(q(`.${s.flyShadow}`), { autoAlpha: 0, duration: 0.9, ease: "sine.out" }, 0)
      .to(q(`.${s.flyBody}`), {
        y: -window.innerHeight * 0.75, x: (i: number) => [-120, 90, 150][i], rotate: (i: number) => [-25, 18, 30][i],
        scale: 0.7, autoAlpha: 0, duration: 2.4, stagger: 0.2, ease: "sine.in",
      }, 0.1)
      .to(q(`.${s.plaque}`), { scale: 0.97, duration: 0.35, yoyo: true, repeat: 1, ease: "sine.inOut" }, 0.2)
      // the thread seam comes undone stitch by stitch, a spark running down it
      .to(q(`.${s.seam}`), { clipPath: "inset(100% 0 0 0)", duration: 1.7, ease: "sine.inOut" }, 2.5)
      .fromTo(q(`.${s.spark}`), { top: "0%", autoAlpha: 1 }, { top: "100%", duration: 1.7, ease: "sine.inOut" }, 2.5)
      .to(q(`.${s.spark}`), { autoAlpha: 0, duration: 0.4 }, 4.1)
      // the badge parts along its diamond column
      .to(q(`.${s.liftL}`), { x: -7, rotate: -2, duration: 0.9, ease: "power2.out" }, 3.9)
      .to(q(`.${s.liftR}`), { x: 7, rotate: 2, duration: 0.9, ease: "power2.out" }, 3.9)
      // doors swing outward on their hinges while the view eases in
      .to(q(`.${s.leafL}`), { rotateY: -100, duration: 4.2, ease: "sine.inOut" }, 4.5)
      .to(q(`.${s.leafR}`), { rotateY: 100, duration: 4.2, ease: "sine.inOut" }, 4.5)
      .to(q(`.${s.leafShade}`), { opacity: 0.8, duration: 4.2, ease: "sine.inOut" }, 4.5)
      .to(q(`.${s.doorsBack}`), { opacity: 0, duration: 2.6, ease: "sine.inOut" }, 5.0)
      .fromTo(q(`.${s.stage}`), { scale: 1.1 }, { scale: 1, duration: 5.4, ease: "sine.out" }, 4.5)
      // the curtain bow comes undone: the loops pull through the knot, the tails loosen, then it drops
      // to the floor with its tails trailing up behind it, and is gone as the curtains part
      .to(q(`.${s.cbowBody}`), { scaleX: 0.3, scaleY: 0.72, duration: 0.6, ease: "power2.in" }, 6.4)
      .to(q(`.${s.cbowTailL}`), { rotate: 9, duration: 0.5, ease: "sine.out" }, 6.5)
      .to(q(`.${s.cbowTailR}`), { rotate: -9, duration: 0.5, ease: "sine.out" }, 6.5)
      .to(q(`.${s.cbow}`), { y: () => (root.current?.clientHeight ?? 700) * 0.62, rotate: 16, duration: 1.15, ease: "power2.in" }, 6.95)
      .to(q(`.${s.cbowTailL}`), { rotate: 62, duration: 1.15, ease: "power2.in" }, 6.95)
      .to(q(`.${s.cbowTailR}`), { rotate: -48, duration: 1.15, ease: "power2.in" }, 6.95)
      .to(q(`.${s.cbow}`), { autoAlpha: 0, duration: 0.45, ease: "sine.in" }, 7.75)
      // curtains: glide through the pre-rendered sequence
      .to(frame.current, { i: FRAMES - 1, duration: 4.6, ease: "sine.inOut", onUpdate: draw }, 7.3)
      // swags settle in one by one, centre pair first
      .fromTo(q(`.${s.swag}`), { yPercent: -115, autoAlpha: 1 }, {
        yPercent: 0, duration: 1.6, ease: "back.out(1.15)",
        stagger: { each: 0.28, from: "center" },
      }, 10.6)
      .fromTo(q(`.${s.strand}`), { y: -340, autoAlpha: 1 }, { y: 0, duration: 2, ease: "back.out(1.05)", stagger: 0.3 }, 10.9)
      .fromTo(q(`.${s.bush}`), { yPercent: 35, autoAlpha: 0 }, { yPercent: 0, autoAlpha: 1, duration: 2.2, ease: "power2.out", stagger: 0.2 }, 11.1)
      // butterflies lift off the swags
      .fromTo(q(`.${s.fly}`), { autoAlpha: 0, x: 0, y: -40, scale: 0.6 }, {
        autoAlpha: 1, scale: 1, duration: 2.4, stagger: 0.35, ease: "sine.inOut",
        x: (i: number) => [-30, 92, 46][i], y: (i: number) => [210, 22, 64][i],
        onComplete: () => {
          if (!reduce) stopFlight.current.push(wander(q(`.${s.fly}`), { ampX: 42, ampY: 34, restingClass: s.resting }));
        },
      }, 11.4)
      // the five lamps of the Bathou light one after another
      .to(q(`.${s.lampGlow}`), { opacity: 1, duration: 0.9, stagger: 0.45, ease: "sine.out" }, 11.8)
      .to(q(`.${s.lampImg}`), { filter: "brightness(1) saturate(1)", duration: 0.9, stagger: 0.45, ease: "sine.out" }, 11.8)
      // names arrive softly, as if coming into focus
      .fromTo(q(`.${s.names} > *`), { autoAlpha: 0, y: 16, filter: "blur(6px)" }, {
        autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 1.8, stagger: 0.2, ease: "power2.out", clearProps: "filter",
      }, 12.6)      .fromTo(q(`.${s.scroll}`), { autoAlpha: 0 }, { autoAlpha: 1, duration: 1.2, ease: "sine.out" }, ">-0.4");
  }, [opened, ready, lenis, draw]);

  return (
    <section ref={root} className={s.hero} aria-label="Opening">
      <div className={s.stage}>
        <div className={s.backdrop} />
        {/* far to near: palms, banana plants, altar, names, curtains, swags, butterflies, foreground marigolds */}
        <img className={`${s.palm} ${s.palmL} depth`} style={{ "--d": -3 } as React.CSSProperties} src="/art/palm.webp" alt="" />
        <img className={`${s.palm} ${s.palmR} depth`} style={{ "--d": -3 } as React.CSSProperties} src="/art/palm.webp" alt="" />
        <img className={`${s.banana} ${s.bananaL} depth`} style={{ "--d": 4 } as React.CSSProperties} src="/art/banana-l.webp" alt="" />
        <img className={`${s.banana} ${s.bananaR} depth`} style={{ "--d": 4 } as React.CSSProperties} src="/art/banana-r.webp" alt="" />
        {/* names sit in the gap between the curtains */}
        <div className={`${s.names} depth`} style={{ "--d": 2 } as React.CSSProperties}>
          <p className={`caps ${s.blessing}`}>{couple.blessing.replace(" of ", "\n of ").split("\n").map((l) => <span key={l} style={{ display: "block" }}>{l}</span>)}</p>
          <div className={`agor-rule ${s.rule}`}><span /></div>
          <h1 className={`display ${s.name}`}>{couple.groom.name}</h1>
          <p className={s.parents}>{couple.groom.parents}</p>
          <p className={`display ${s.amp}`}>&amp;</p>
          <h1 className={`display ${s.name}`}>{couple.bride.name}</h1>
          <p className={s.parents}>{couple.bride.parents}</p>
          <p className={`caps ${s.date}`}>{couple.dateLabel}</p>
        </div>
        {/* aronai hung on the walls either side of the shrine (placed by the effect above) */}
        {[0, 1].map((i) => (
          <img key={i} ref={(el) => { hangs.current[i] = el; }} className={`${s.hang} ${i ? s.hangR : ""}`}
            src="/art/aronai-hang.webp" alt="" aria-hidden />
        ))}
        <div ref={altarRef} className={`${s.altar} depth`} style={{ "--d": 6 } as React.CSSProperties} data-speed="0.12">
          {/* the shrine's frame is dressed with aronai: two festoons, and an end with its fringe at each post */}
          <img src="/art/altar.webp" alt="The Bathou altar: a sijou plant in its bamboo fence, its frame hung with aronai" width={600} height={621} />
          {/* the two ends of the aronai knotted round the fence, waving in a breeze (a 32-frame loop) */}
          <span className={s.fenceTail} aria-hidden />
          <div className={s.lamps}>
            {Array.from({ length: 5 }, (_, i) => (
              <div className={s.lamp} key={i}>
                <span className={s.lampGlow} />
                <img className={s.lampImg} src="/art/lamp.webp" alt="" width={88} height={120} />
              </div>
            ))}
          </div>
        </div>
        <canvas ref={canvas} className={`${s.curtains} depth`} style={{ "--d": 9 } as React.CSSProperties} aria-hidden />
        {/* an aronai bow tying the closed curtains together; it comes undone and falls as they open */}
        <div className={s.cbow} aria-hidden>
          <img className={s.cbowTailL} src="/art/cbow-tail-l.webp" alt="" />
          <img className={s.cbowTailR} src="/art/cbow-tail-r.webp" alt="" />
          <img className={s.cbowBody} src="/art/cbow-body.webp" alt="" />
        </div>
        <div className={`${s.valance} depth`} style={{ "--d": 11 } as React.CSSProperties} aria-hidden>
          {[25, 75].map((x) => <img key={x} className={s.strand} src="/art/strand.webp" alt="" style={{ left: `${x}%` }} />)}
          {[0, 1, 2, 3].map((i) => <img key={i} className={s.swag} src="/art/swag.webp" alt="" style={{ left: `${i * 25 - 4}%` }} />)}
          <div className={s.header} />
        </div>
        <div className={`${s.flies} depth`} style={{ "--d": 14 } as React.CSSProperties} aria-hidden>
          {[0, 1, 2].map((i) => (
            <div key={i} className={s.fly} style={{ left: `${[26, 47, 70][i]}%` }}>
              <img className={s.wingL} src="/art/wing.webp" alt="" />
              <img className={s.wingR} src="/art/wing.webp" alt="" />
            </div>
          ))}
        </div>
        <img className={`${s.bush} ${s.bushL} depth`} style={{ "--d": 20 } as React.CSSProperties} src="/art/bush-l.webp" alt="" />
        <img className={`${s.bush} ${s.bushR} depth`} style={{ "--d": 20 } as React.CSSProperties} src="/art/bush-r.webp" alt="" />
        <p className={`caps ${s.scroll}`}>Scroll</p>
      </div>

      <div className={s.doors}>
        <div className={s.doorsBack} />
        {/* the cover is built in layers at real depths: cloth, sewn-on strips, the aronai bow, the badge,
            butterflies */}
        <div className={s.rig} ref={rig}>
          <Leaf side="L" />
          <Leaf side="R" />
          <div className={s.seam} />
          <span className={s.spark} aria-hidden />
          {/* one aronai tied round the doors in a bow under the badge (Blender renders: the band, and the
              bow's two loops, knot and two tails on one frame, so it can be untied piece by piece) */}
          <div className={s.bow} aria-hidden>
            <Ribbon side="L" />
            <Ribbon side="R" />
            <img className={s.bowStill} src="/art/cover-bow.webp" alt="" />
            <span className={s.untie} />
          </div>
          {[0, 1, 2].map((i) => (
            <div key={i} className={`${s.coverFly} ${s[`cf${i}`]}`} aria-hidden>
              <div className={s.flyShadow}><Wings /></div>
              <div className={s.flyBody}><Wings /></div>
            </div>
          ))}
        </div>
        <button className={s.tap} onClick={open} aria-label="Open the invitation" aria-busy={!ready}>
          <span className={`caps ${s.hint}`}>{ready ? "Tap to open" : "Weaving your invitation"}</span>
        </button>
      </div>
    </section>
  );
}

/** One half of the ribbon, from the door edge in to the knot: ten short pieces, each nested in the one
 *  before and hinged where they meet, so the ribbon can bend anywhere along its length. */
function Ribbon({ side }: { side: "L" | "R" }) {
  let chain: React.ReactNode = null;
  for (let k = 9; k >= 0; k--) chain = <span className={s.rseg} style={{ "--k": k } as React.CSSProperties}>{chain}</span>;
  return <span className={`${s.ribbon} ${side === "L" ? s.ribbonL : s.ribbonR}`}>{chain}</span>;
}

function Wings() {
  return (
    <>
      <img className={s.wingL} src="/art/wing.webp" alt="" />
      <img className={s.wingR} src="/art/wing.webp" alt="" />
    </>
  );
}

/** One door leaf: woven cloth, the raised aronai column and hem, and its half of the badge. */
function Leaf({ side }: { side: "L" | "R" }) {
  const L = side === "L";
  return (
    <div className={`${s.leaf} ${L ? s.leafL : s.leafR}`}>
      <div className={`${s.leafFace} ${L ? "" : s.mirror}`} />
      <div className={s.hem} />
      <div className={s.column} />
      <div className={`${s.shadowClip} ${L ? s.clipL : s.clipR}`} aria-hidden>
        <div className={s.plaqueShadow} />
      </div>
      <div className={`${s.lift} ${L ? s.liftL : s.liftR}`}>
        <div className={`${s.plaqueHalf} ${L ? s.halfL : s.halfR}`}><Plaque /></div>
        <span className={`${s.edge} ${L ? s.edgeL : s.edgeR}`} aria-hidden />
      </div>
      <div className={s.leafShade} />
    </div>
  );
}

const dateParts = (() => {
  const d = new Date(couple.date);
  return [d.toLocaleDateString("en-GB", { day: "numeric", month: "long", timeZone: "Asia/Kolkata" }), String(d.getUTCFullYear())];
})();

function Plaque() {
  return (
    <div className={s.plaque}>
      <img src="/art/plaque.webp" alt="" width={400} height={460} />
      {/* the groom's name rides the left door, the bride's the right; the badge parts along the diamond column */}
      <div className={s.plaqueText}>
        <span className={`display ${s.pName} ${s.pL}`}>{couple.groom.name}</span>
        <span className={`display ${s.pName} ${s.pR}`}>{couple.bride.name}</span>
        <span className={`caps ${s.pDate} ${s.pL}`}>{dateParts[0]}</span>
        <span className={`caps ${s.pDate} ${s.pR}`}>{dateParts[1]}</span>
      </div>
    </div>
  );
}
