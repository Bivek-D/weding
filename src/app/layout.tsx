import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import couple from "@/content/couple.json";
import "./globals.css";

// SIL Open Font License fonts, bundled locally
const serif = localFont({ src: "../fonts/CormorantGaramond-VF.ttf", variable: "--font-serif", weight: "300 700" });
const caps = localFont({ src: "../fonts/Cinzel-VF.ttf", variable: "--font-caps", weight: "400 900" });

export const metadata: Metadata = {
  title: `${couple.groom.name} & ${couple.bride.name} · Haba`,
  description: `${couple.groom.full} and ${couple.bride.full} invite you to their wedding, ${couple.dateLabel}, ${couple.place}.`,
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0F7A4A",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        {/* before anything is drawn: never put the page back where it was scrolled to on a refresh */}
        <script dangerouslySetInnerHTML={{ __html: `if("scrollRestoration"in history)history.scrollRestoration="manual";scrollTo(0,0)` }} />
      </head>
      {/* the page arrives locked to one screen (the cover), so a refresh can't land mid-page;
          the opening unlocks it once it has played */}
      <body className={`${serif.variable} ${caps.variable} is-locked`}>{children}</body>
    </html>
  );
}
