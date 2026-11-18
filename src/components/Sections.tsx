"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import couple from "@/content/couple.json";
import Reveal from "./Reveal";
import Raised from "./Raised";
import { downloadIcs, mapUrl } from "@/lib/calendar";
import s from "./sections.module.css";

const WHO = `${couple.groom.name} & ${couple.bride.name}`;

export function Band({ tone = "scarlet" }: { tone?: "scarlet" | "emerald" | "navy" | "yellow" | "magenta" }) {
  return <div className={`band band--${tone}`} data-band aria-hidden />;
}

/** A rendered object from Bodo life: it acts as the section's emblem and carries the depth. */
function Emblem({ src, alt, width }: { src: string; alt: string; width: number }) {
  return (
    <Reveal className={s.emblem}>
      <img src={`/art/${src}.webp`} alt={alt} style={{ width }} />
    </Reveal>
  );
}

/** Section title in the reference order: big light caps title, a gold agor hairline, a spaced label. */
function Heading({ children, kicker }: { children: React.ReactNode; kicker?: string }) {
  return (
    <Reveal className={s.heading} delay={0.05}>
      <h2 className="display h-section press">{children}</h2>
      <div className="agor-rule"><span /></div>
      {kicker && <p className="caps kicker">{kicker}</p>}
    </Reveal>
  );
}

export function Welcome() {
  return (
    <section className={`section ${s.welcome}`}>
      {/* marigold strands hanging from the woven ribbon above, and vines climbing both edges */}
      <Raised src="garland" width="100%" lift={10} className={s.garland} />
      <Raised src="vine-l" width={40} lift={6} className={`${s.vine} ${s.vineL}`} />
      <Raised src="vine-r" width={40} lift={6} className={`${s.vine} ${s.vineR}`} />
      <div className="stack">
        <Reveal className={s.peacocks}>
          <Raised src="peacocks" width={286} lift={9}
            alt="Two embroidered peacocks facing each other over a peacock-eye medallion, as in the agor of a dokhona" />
        </Reveal>
        <Heading kicker="Haba · our wedding">Welcome</Heading>
        <Reveal as="p" className="lead" delay={0.1}>{couple.welcome}</Reveal>
        <Reveal as="p" className={`caps soft ${s.aside}`} delay={0.15}>Khulumbai · an aronai awaits you</Reveal>
      </div>
    </section>
  );
}

function useCountdown(target: string) {
  const [left, setLeft] = useState<number | null>(null);
  useEffect(() => {
    const t = new Date(target).getTime();
    const tick = () => setLeft(Math.max(0, t - Date.now()));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [target]);
  if (left === null) return null;
  const sec = Math.floor(left / 1000);
  return [
    [Math.floor(sec / 86400), "Days"], [Math.floor(sec / 3600) % 24, "Hours"], [Math.floor(sec / 60) % 60, "Minutes"],
  ] as [number, string][];
}

/** Countdown on a die-cut card with an aronai ribbon threaded through it. */
export function Countdown() {
  const parts = useCountdown(couple.date);
  return (
    <section className={`section ${s.countSection}`}>
      <Reveal className={s.countWrap}>
        <div className={s.ribbon} aria-hidden />
        <Raised src="sprig-tl" width={96} lift={7} className={`${s.corner} ${s.cornerTL}`} />
        <Raised src="sprig-br" width={96} lift={7} className={`${s.corner} ${s.cornerBR}`} />
        <div className={`paper ${s.countCard}`}>
          <span className="paper-face" />
          <h2 className="display h-section press">Countdown</h2>
          <p className="caps kicker">Until {couple.dateLabel.split("·")[1]?.trim()}</p>
          <div className={s.count}>
            {(parts ?? [[0, "Days"], [0, "Hours"], [0, "Minutes"]]).map(([n, label]) => (
              <div className={s.cell} key={label}>
                <span className={`display ${s.num}`}>{String(n).padStart(2, "0")}</span>
                <span className="caps soft">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
      <Reveal className={s.saveDate} delay={0.15}>
        <button className="link" onClick={() => downloadIcs(couple.events, WHO)}>Save the date</button>
      </Reveal>
    </section>
  );
}

export function Events() {
  return (
    <section className="section">
      <div className="stack">
        <Emblem src="lamps3" alt="Three brass lamps, lit" width={230} />
        <Heading kicker="Where and when">The ceremonies</Heading>
        {couple.events.map((e, i) => {
          const d = new Date(e.start);
          const time = d.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata" });
          const day = d.toLocaleDateString("en-GB", { weekday: "long", timeZone: "Asia/Kolkata" });
          return (
            <Reveal className={`arch ${s.event}`} key={e.id} delay={i * 0.1}>
              <Raised src="swag" width={210} lift={8} className={s.archSwag} />
              <img className={s.eventArt} src={`/art/${e.id === "haba" ? "meal" : "instruments"}.webp`} alt={e.id === "haba"
                ? "Rice and ondlakhari served on a banana leaf, with a wooden hatha" : "A kham drum, a siphung flute and jotha cymbals"} />
              <h3 className={`display ${s.eventTitle}`}>{e.title}</h3>
              <p className="caps soft">{e.subtitle}</p>
              <div className={s.block}>
                <p className={`display ${s.blockHead}`}>When</p>
                <p className="caps soft">On {day}</p>
                <p className={`display ${s.big}`}>{couple.dateLabel.split("·")[1]?.trim()}</p>
                <p className={s.mid}>{time}</p>
              </div>
              <div className={s.block}>
                <p className={`display ${s.blockHead}`}>Where</p>
                <p className={s.mid}>{e.venue}</p>
                <p className="soft">{e.address}</p>
              </div>
              <p className={`soft ${s.note}`}>{e.note}</p>
              <div className="links">
                <a className="link" href={mapUrl(e)} target="_blank" rel="noopener noreferrer">Open in maps</a>
                <button className="link" onClick={() => downloadIcs([e], WHO)}>Add to calendar</button>
              </div>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}

/** Dress code: the three folded garments as a still life; Bagurumba butterflies drift across as you scroll. */
export function DressCode() {
  const root = useRef<HTMLElement>(null);
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(`.${s.drift}`).forEach((el, i) => {
        gsap.fromTo(el, { x: i % 2 ? 300 : -60, y: 60 + i * 160 }, {
          x: i % 2 ? -60 : 300, y: i * 130, rotate: i % 2 ? -12 : 10, ease: "none",
          scrollTrigger: { trigger: root.current, start: "top bottom", end: "bottom top", scrub: 1.4 },
        });
      });
    }, root);
    return () => ctx.revert();
  }, []);
  const art = ["fold-dokhona", "fold-gamsa", "fold-aronai"];
  const alt = ["A folded dokhona", "A folded gamsa", "A folded aronai"];
  return (
    <section ref={root} className={`section ${s.clip}`}>
      <div className={s.drifts} aria-hidden>
        {[0, 1].map((i) => (
          <div key={i} className={s.drift}>
            <img className={s.wl} src="/art/wing.webp" alt="" />
            <img className={s.wr} src="/art/wing.webp" alt="" />
          </div>
        ))}
      </div>
      <div className="stack">
        <Heading kicker="Wear your colours">Dress code</Heading>
        <ul className={s.dress}>
          {couple.dressCode.map((d, i) => (
            <Reveal as="li" key={d.who} delay={i * 0.08}>
              <img className={s.garment} src={`/art/${art[i] ?? "fold-aronai"}.webp`} alt={alt[i] ?? ""} />
              <p className={`display ${s.who}`}>{d.who}</p>
              <p className="soft">{d.what}</p>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function Story() {
  return (
    <section className="section">
      <div className="stack">
        <Reveal className={s.storyArt}>
          <Raised src="butterfly-l" width={66} lift={12} className={`${s.fly} ${s.flyL}`}
            alt="An embroidered Bagurumba butterfly" />
          <img className={s.knotArt} src="/art/knot.webp" alt="An emerald aronai and a scarlet aronai tied together" />
          <Raised src="butterfly-r" width={60} lift={12} className={`${s.fly} ${s.flyR}`} />
        </Reveal>
        <Heading kicker="Seven springs">Our story</Heading>
        <Reveal as="p" className="lead" delay={0.1}>{couple.story}</Reveal>
        <Reveal as="p" className={`display ${s.quote}`} delay={0.15}>Two families, one knot</Reveal>
      </div>
    </section>
  );
}

/** The day: times on the left of a gold thread that draws itself as you scroll, the moments on the right. */
export function Timeline() {
  const root = useRef<HTMLElement>(null);
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(`.${s.thread}`, { scaleY: 0 }, {
        scaleY: 1, ease: "none",
        scrollTrigger: { trigger: `.${s.steps}`, start: "top 70%", end: "bottom 60%", scrub: true },
      });
      gsap.utils.toArray<HTMLElement>(`.${s.bead}`).forEach((k) => {
        gsap.fromTo(k, { scale: 0, opacity: 0 }, {
          scale: 1, opacity: 1, duration: 0.6, ease: "sine.out",
          scrollTrigger: { trigger: k, start: "top 66%", toggleActions: "play none none reverse" },
        });
      });
    }, root);
    ScrollTrigger.refresh();
    return () => ctx.revert();
  }, []);
  return (
    <section ref={root} className="section">
      <div className="stack">
        <Emblem src="lamp" alt="A lit brass saki lamp" width={56} />
        <Heading kicker={`On ${couple.dateLabel.split("·")[1]?.trim()}`}>The big day</Heading>
      </div>
      <ol className={s.steps}>
        <span className={s.track} aria-hidden><span className={s.thread} /></span>
        {couple.timeline.map((t) => {
          const w = ("artWidth" in t && t.artWidth) || 50;   // tall objects are shown narrower
          return (
          <li key={t.title} className={s.step}>
            <Raised src={t.art} width={w} lift={5} className={s.bead} style={{ left: 100 - w / 2 }} />
            <Reveal className={s.stepTime}><span className="display">{t.time}</span></Reveal>
            <Reveal className={s.stepBody} delay={0.05}>
              <h3 className={`display ${s.stepTitle}`}>{t.title}</h3>
              <p className="soft">{t.text}</p>
            </Reveal>
          </li>
          );
        })}
      </ol>
    </section>
  );
}

export function Travel() {
  return (
    <section className="section">
      <div className="stack">
        <Heading kicker="Coming to Kokrajhar">Travel &amp; stay</Heading>
        {couple.travel.map((t, i) => (
          <Reveal className={`paper ${s.travel}`} key={t.title} delay={i * 0.08}>
            <span className="paper-face" />
            <p className="caps kicker">{t.title}</p>
            <p className={s.travelText}>{t.text}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

export function Gift() {
  return (
    <section className="section">
      <div className="stack">
        <Emblem src="plate" alt="A brass plate with a folded aronai and marigolds" width={200} />
        <Heading kicker="With blessings">Gifts</Heading>
        <Reveal as="p" className="lead" delay={0.1}>{couple.gift}</Reveal>
      </div>
    </section>
  );
}

export function Rsvp() {
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [error, setError] = useState("");
  async function submit(ev: React.FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const data = Object.fromEntries(new FormData(ev.currentTarget));
    setState("sending");
    try {
      const r = await fetch("/api/rsvp", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || "Something went wrong");
      setState("done");
    } catch (e) {
      setError((e as Error).message);
      setState("error");
    }
  }
  return (
    <section className={`section ${s.withVines}`} id="rsvp">
      <Raised src="vine-l" width={40} lift={6} className={`${s.vine} ${s.vineL}`} />
      <Raised src="vine-r" width={40} lift={6} className={`${s.vine} ${s.vineR}`} />
      <div className="stack">
        <Heading>RSVP</Heading>
        <Reveal className={`paper ${s.rsvpCard}`} delay={0.1}>
          <span className="paper-face" />
          <p className={`caps soft ${s.replyBy}`}>Kindly respond by<br />{couple.rsvpBy}</p>
          {state === "done" ? (
            <div className={s.thanks}>
              <img className={s.thanksArt} src="/art/fold-aronai.webp" alt="" />
              <p className="lead">Thank you. An aronai is waiting for you.</p>
            </div>
          ) : (
            <form className={s.form} onSubmit={submit}>
              <label className={s.field}>
                <span>Full name *</span>
                <input name="name" required autoComplete="name" placeholder="Enter your full name" />
              </label>
              <fieldset className={s.field}>
                <legend>Will you be attending? *</legend>
                <div className={s.choices}>
                  <label className={s.choice}>
                    <input type="radio" name="attending" value="yes" required />
                    <span className={s.dot} aria-hidden />
                    <span>Joyfully accepts</span>
                  </label>
                  <label className={s.choice}>
                    <input type="radio" name="attending" value="no" />
                    <span className={s.dot} aria-hidden />
                    <span>Regretfully declines</span>
                  </label>
                </div>
              </fieldset>
              <label className={s.field}>
                <span>Guests with you</span>
                <select name="guests" defaultValue="0">
                  <option value="0">Just me</option>
                  <option value="1">One more</option>
                  <option value="2">Two more</option>
                  <option value="3">Three more</option>
                </select>
              </label>
              <label className={s.field}>
                <span>A blessing for the couple</span>
                <textarea name="message" rows={3} placeholder="A wish, a memory, anything you would like us to read" />
              </label>
              {state === "error" && <p className={s.error} role="alert">{error}</p>}
              <button className="link" type="submit" disabled={state === "sending"}>
                {state === "sending" ? "Sending" : "Send RSVP"}
              </button>
            </form>
          )}
        </Reveal>
      </div>
    </section>
  );
}

/** A raised marigold divider between sections. */
export function Divider() {
  return (
    <Reveal className={s.divider}>
      <Raised src="divider" width={194} lift={5} />
    </Reveal>
  );
}

export function Footer() {
  return (
    <footer className={`section ${s.footer}`}>
      <Raised src="sprig-bl" width={84} lift={7} className={`${s.corner} ${s.footBL}`} />
      <Raised src="sprig-br" width={84} lift={7} className={`${s.corner} ${s.footBR}`} />
      <div className="stack">
        <img className={s.lamp} src="/art/lamps3.webp" alt="Three brass lamps, lit" />
        <p className="caps kicker">With love</p>
        <p className={`display ${s.sign}`}>{couple.groom.name}<span>&amp;</span>{couple.bride.name}</p>
        <Raised src="divider" width={180} lift={5} />
        <p className="caps soft">{couple.place}</p>
      </div>
    </footer>
  );
}
