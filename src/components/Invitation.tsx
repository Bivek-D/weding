"use client";

import { useRef } from "react";
import SmoothScroll from "./SmoothScroll";
import Opening from "./Opening";
import { useLift } from "./Raised";
import { Band, Countdown, Divider, DressCode, Events, Footer, Gift, Rsvp, Story, Timeline, Travel, Welcome } from "./Sections";

export default function Invitation() {
  const card = useRef<HTMLElement>(null);
  useLift(card);
  return (
    <SmoothScroll>
      <main className="card" ref={card}>
        <Opening />
        {/* one woven ribbon closes the stage; after it the card is a single sheet of paper */}
        <Band tone="scarlet" />
        <Welcome />
        <Countdown />
        <Events />
        <Divider />
        <Story />
        <Timeline />
        <Divider />
        <DressCode />
        <Travel />
        <Gift />
        <Divider />
        <Rsvp />
        <Footer />
      </main>
    </SmoothScroll>
  );
}
