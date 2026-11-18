"use client";

import { motion, useReducedMotion } from "motion/react";

/** Soft fade with a small rise as a block scrolls into view (Motion). */
export default function Reveal({
  children, delay = 0, className, as = "div",
}: { children: React.ReactNode; delay?: number; className?: string; as?: "div" | "li" | "p" }) {
  const reduce = useReducedMotion();
  const M = motion[as];
  return (
    <M
      className={className}
      initial={reduce ? false : { opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -12% 0px" }}
      transition={{ duration: 1.3, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </M>
  );
}
