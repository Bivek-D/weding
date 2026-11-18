// Renders jobs from scene.js in headless Chromium (SwiftShader WebGL) and writes PNGs to out/.
// Usage: node render.mjs [job ...]      (no jobs = all)
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, "out");
fs.mkdirSync(OUT, { recursive: true });
// playwright-core: installed next to this script (npm i playwright-core), or the copy on the original laptop
let chromium;
try { ({ chromium } = await import("playwright-core")); }
catch { ({ chromium } = await import(path.join(process.env.HOME, ".npm/_npx/9b9809298fe40d2c/node_modules/playwright-core/index.mjs"))); }

const types = { ".html": "text/html", ".js": "text/javascript", ".png": "image/png" };
const server = http.createServer((req, res) => {
  const f = path.join(HERE, decodeURIComponent(req.url.split("?")[0]));
  if (!f.startsWith(HERE) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": types[path.extname(f)] || "application/octet-stream" });
  fs.createReadStream(f).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({
  // CHROME_PATH overrides; otherwise Playwright's own Chromium (npx playwright install chromium)
  executablePath: process.env.CHROME_PATH || undefined,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const page = await browser.newPage();
page.on("console", (m) => { if (m.type() === "error" && !m.text().includes("404")) console.error("page:", m.text()); });
page.on("requestfailed", (r) => console.error("failed:", r.url()));
page.on("response", (r) => { if (r.status() >= 400) console.error("http", r.status(), r.url()); });
page.on("pageerror", (e) => console.error("page error:", e.message));
await page.goto(`http://127.0.0.1:${port}/index.html`);
await page.waitForFunction(() => window.ready === true, null, { timeout: 20000 });
const jobs = process.argv.slice(2).length ? process.argv.slice(2) : await page.evaluate(() => window.JOBS);
for (const job of jobs) {
  const t = Date.now();
  const url = await page.evaluate((j) => window.renderJob(j), job);
  fs.writeFileSync(path.join(OUT, `${job}.png`), Buffer.from(url.split(",")[1], "base64"));
  console.log(`${job}  ${((Date.now() - t) / 1000).toFixed(1)}s`);
}
await browser.close();
server.close();
