/** Calendar export (.ics) and map links for the events in couple.json. */
type Ev = { id: string; title: string; start: string; end: string; venue: string; address: string; note?: string };

const stamp = (iso: string) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
const esc = (s: string) => s.replace(/[\\;,]/g, (m) => "\\" + m).replace(/\n/g, "\\n");

export function downloadIcs(events: Ev[], who: string) {
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Haba invitation//EN", "CALSCALE:GREGORIAN"];
  for (const e of events) {
    lines.push(
      "BEGIN:VEVENT",
      `UID:${e.id}-${stamp(e.start)}@haba-invite`,
      `DTSTAMP:${stamp(new Date().toISOString())}`,
      `DTSTART:${stamp(e.start)}`,
      `DTEND:${stamp(e.end)}`,
      `SUMMARY:${esc(`${who}: ${e.title}`)}`,
      `LOCATION:${esc(`${e.venue}, ${e.address}`)}`,
      e.note ? `DESCRIPTION:${esc(e.note)}` : "",
      "END:VEVENT",
    );
  }
  lines.push("END:VCALENDAR");
  const blob = new Blob([lines.filter(Boolean).join("\r\n")], { type: "text/calendar" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${who.replace(/\W+/g, "-").toLowerCase()}-wedding.ics`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export const mapUrl = (e: Pick<Ev, "venue" | "address">) =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${e.venue}, ${e.address}`)}`;
