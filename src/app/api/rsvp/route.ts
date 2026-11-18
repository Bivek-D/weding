import { NextResponse } from "next/server";
import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";
import couple from "@/content/couple.json";

/** RSVP: stored in Supabase (table `rsvps`) when SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set,
 *  otherwise appended to data/rsvps.jsonl for local testing. A Resend email goes to the couple when
 *  RESEND_API_KEY and RSVP_NOTIFY_EMAIL are set. See .env.example. */
export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Please try again" }, { status: 400 });
  }
  const name = String(body.name ?? "").trim().slice(0, 120);
  const attending = body.attending === "yes" ? true : body.attending === "no" ? false : null;
  const guests = Math.min(Math.max(parseInt(String(body.guests ?? "0"), 10) || 0, 0), 6);
  const message = String(body.message ?? "").trim().slice(0, 1000);
  if (!name) return NextResponse.json({ error: "Please add your name" }, { status: 400 });
  if (attending === null) return NextResponse.json({ error: "Please tell us if you can come" }, { status: 400 });

  const row = { name, attending, guests, message, created_at: new Date().toISOString() };

  try {
    const { SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY } = process.env;
    if (SUPABASE_URL && SUPABASE_SERVICE_ROLE_KEY) {
      const r = await fetch(`${SUPABASE_URL}/rest/v1/rsvps`, {
        method: "POST",
        headers: {
          apikey: SUPABASE_SERVICE_ROLE_KEY,
          Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify(row),
      });
      if (!r.ok) throw new Error(`supabase ${r.status}`);
    } else {
      const dir = path.join(process.cwd(), "data");
      await mkdir(dir, { recursive: true });
      await appendFile(path.join(dir, "rsvps.jsonl"), JSON.stringify(row) + "\n");
    }
  } catch (e) {
    console.error("rsvp store failed", e);
    return NextResponse.json({ error: "We could not save your reply. Please try again." }, { status: 500 });
  }

  const { RESEND_API_KEY, RSVP_NOTIFY_EMAIL, RSVP_FROM_EMAIL } = process.env;
  if (RESEND_API_KEY && RSVP_NOTIFY_EMAIL) {
    const who = `${couple.groom.name} & ${couple.bride.name}`;
    fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${RESEND_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: RSVP_FROM_EMAIL || "Invitation <onboarding@resend.dev>",
        to: [RSVP_NOTIFY_EMAIL],
        subject: `RSVP for ${who}: ${name} ${attending ? "is coming" : "cannot come"}`,
        text: `${name} ${attending ? `is coming with ${guests} guest(s)` : "cannot come"}.\n\n${message}`,
      }),
    }).catch((e) => console.error("resend failed", e));
  }

  return NextResponse.json({ ok: true });
}
