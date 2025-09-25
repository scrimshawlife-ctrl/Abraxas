import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import http from "http";
import passport from "passport";
import { runRitual, getTodayRunes } from "./runes.js";
import { scoreWatchlists, getWeights, setWeights, DEFAULT_FEATURE_WEIGHTS } from "./abraxas.js";
import metrics, { persistAllSnapshots } from "./metrics.js";
import { seal, fingerprint } from "./crypto.js";
import { installRealtime } from "./realtime.js";
import db, { q } from "./db.js";
import { sessionMiddleware, googlePassport, ensureAuthed } from "./auth.js";
import { v4 as uuidv4 } from "uuid";
import { runSocialScan, getSocialTrends } from "./social_scan.js";
import { forgeSigil } from "./sigil.js";
import { analyzeVC, VC_PERSONA } from "./vc_oracle.js";
import { healthRouter } from "./health.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const rt = installRealtime(server);

app.use(express.json());

// Health + readiness (before auth)
healthRouter(app);

// Sessions + Google SSO
app.use(sessionMiddleware());
app.use(googlePassport().initialize());
app.use(googlePassport().session());

// Public login portal
app.get("/login", (req,res)=> res.sendFile(path.join(__dirname, "..", "client", "dist", "login.html")));
app.get("/auth/google", passport.authenticate("google", { scope: ["profile","email"] }));
app.get("/auth/google/callback", passport.authenticate("google", { failureRedirect: "/login" }), (req,res)=> res.redirect("/"));
app.get("/logout", (req,res)=>{ req.logout(()=>res.redirect("/login")); });

// Guard everything else
app.use(ensureAuthed);

// ---- Config API (weights, persisted)
app.get("/api/config", (req,res)=>{
  const row = q.getConfig.get("feature_weights");
  let weights = { ...DEFAULT_FEATURE_WEIGHTS }; // Start with defaults
  if (row?.value) {
    try { 
      const parsed = JSON.parse(row.value); 
      weights = { ...weights, ...parsed }; // Merge saved weights with defaults
    } catch {}
  }
  res.json({ weights, defaults: DEFAULT_FEATURE_WEIGHTS });
});
app.post("/api/config", (req,res)=>{
  const { weights } = req.body || {};
  if (!weights || typeof weights !== "object") return res.status(400).json({ error:"invalid_payload" });
  const applied = setWeights(weights);
  try {
    q.setConfig.run({ key:"feature_weights", value: JSON.stringify(applied), updated_at: Date.now() });
  } catch {}
  res.json({ ok:true, weights: applied });
});

// Self/user endpoints
app.get("/api/me", (req,res)=>{
  const u = db.prepare("SELECT id,email,name,picture,created_at FROM users WHERE id=?").get(req.user?.id);
  res.json(u || {});
});
app.get("/api/history", (req,res)=>{
  const rows = db.prepare("SELECT id,date,seed,created_at FROM ritual_runs WHERE user_id=? ORDER BY created_at DESC LIMIT 20").all(req.user?.id);
  res.json(rows);
});
app.get("/api/history/:id", (req,res)=>{
  const row = db.prepare("SELECT * FROM ritual_runs WHERE id=? AND user_id=?").get(req.params.id, req.user?.id);
  if(!row) return res.status(404).json({error:"not found"});
  res.json({ ...row, runes: JSON.parse(row.runes_json), results: JSON.parse(row.results_json) });
});
app.get("/api/grimoire", (req,res)=>{
  const rows = db.prepare("SELECT id,core,seed,method,created_at FROM sigils WHERE owner_id=? ORDER BY created_at DESC LIMIT 100").all(req.user?.id);
  res.json(rows);
});

// Ritual core
app.get("/api/runes", (req,res)=> res.json(getTodayRunes()));
app.get("/api/stats", (req,res)=> res.json(metrics.snapshot()));
app.get("/api/daily-oracle", (req,res)=>{
  const s = metrics.snapshot();
  const conf = s.lifetime.accuracy.acc===null ? 0.5 : s.lifetime.accuracy.acc;
  const tone = conf>0.6 ? "ascending" : conf>0.52 ? "tempered" : "probing";
  const b = Buffer.from(JSON.stringify({ day:new Date().toISOString().slice(0,10), tone }), "utf8").toString("base64").replace(/=/g,"");
  const glyph = b.match(/.{1,8}/g)?.join("·") || b;
  res.json({ ciphergram: `⟟Σ ${glyph} Σ⟟`, note:`Litany (${tone}): "Vectors converge; witnesses veiled."` });
});

app.post("/api/ritual", async (req, res) => {
  const { equities = [], fx = [] } = req.body || {};
  const ritual = runRitual();
  const results = scoreWatchlists({ equities, fx }, ritual);

  ["federal_register:DFARS:2025-2191","sam.gov:notice:W91:modP00043","uspto:ptab:IPR-2025-1234"].forEach(s=>metrics.addSource(fingerprint(s)));
  ["rule:dfars:display","mod:sam:scope","ipr:ptab:oled"].forEach(s=>metrics.addSignal(fingerprint(s)));

  [...(results.equities.conservative||[]), ...(results.equities.risky||[])]
    .forEach((x,i)=>metrics.addPrediction({ kind:"equity", id:`eq-${Date.now()}-${i}`, tickerOrPair:x.ticker, edge:x.edge }));
  [...(results.fx.conservative||[]), ...(results.fx.risky||[])]
    .forEach((x,i)=>{ metrics.addPrediction({ kind:"fx", id:`fx-${Date.now()}-${i}`, tickerOrPair:x.pair, edge:x.edge }); metrics.addFxShiftMagnitude(Math.abs(x.edge)); });

  rt.broadcast("results", { results });

  const runId = uuidv4();
  q.insertRun.run({ id: runId, user_id: req.user?.id || null, date: ritual.date, seed: String(ritual.seed),
    runes_json: JSON.stringify(ritual.runes), results_json: JSON.stringify(results), created_at: Date.now() });
  q.insertRecs.run({ id: uuidv4(), user_id: req.user?.id || null, payload_json: JSON.stringify(results), created_at: Date.now() });

  const persistFor = (phrase)=>{ const s=forgeSigil(phrase); q.insertSigil.run({ id: uuidv4(), owner_id: req.user?.id || null, core: s.core, seed: s.seed, method:"traditional_strip+grid3x3+seeded_quadratic", created_at: Date.now() }); };
  (results.equities.conservative||[]).forEach(x=>persistFor(x.ticker));
  (results.equities.risky||[]).forEach(x=>persistFor(x.ticker));
  (results.fx.conservative||[]).forEach(x=>persistFor(x.pair));
  (results.fx.risky||[]).forEach(x=>persistFor(x.pair));

  const sealed = seal({ ritual, results });
  res.json({ ritual, results, sealed, disclaimer:"Abraxas persona is fictional; sources & methods sealed. Not financial advice." });
});

// Social trends
app.get("/api/social-trends", (req,res)=> res.json(getSocialTrends()));
app.post("/api/social-trends/scan", async (req,res)=>{
  const out=await runSocialScan(); rt.broadcast("social_trends", out);
  try { q.insertTrends.run({ id: uuidv4(), payload_json: JSON.stringify(out), created_at: Date.now() }); } catch {}
  res.json(out);
});

// VC Oracle (Athena)
app.post("/api/vc/analyze", async (req, res)=>{
  const { industry="Technology", region="US", horizonDays=90 } = req.body || {};
  try { const out = await analyzeVC({ industry, region, horizonDays }); res.json(out); }
  catch(e){ res.status(500).json({ error:"vc_oracle_failed", details:String(e) }); }
});
app.get("/api/vc/persona", (req,res)=> res.json(VC_PERSONA));

// Serve client
const clientDir = path.join(__dirname, "..", "client");
const distDir = path.join(clientDir, "dist");
app.use(express.static(distDir));
app.get("*", (req,res)=> res.sendFile(path.join(distDir, "index.html")));

const PORT = process.env.PORT || 5000;
server.listen(PORT, ()=> console.log(`Abraxas listening on http://localhost:${PORT}`));

// Schedulers
(async()=>{ try { await runSocialScan(); rt.broadcast("social_trends", getSocialTrends()); } catch{} })();
setInterval(async()=>{ try { const out=await runSocialScan(); rt.broadcast("social_trends", out);} catch{} }, 12*60*60*1000);
setInterval(()=>{ try { persistAllSnapshots(); } catch{} }, 3*60*60*1000);

// Load weights on boot (if present)
try {
  const row = q.getConfig.get("feature_weights");
  if (row?.value) {
    const parsed = JSON.parse(row.value);
    setWeights(parsed);
    console.log("[config] loaded feature_weights from DB");
  }
} catch (e) {
  console.log("[config] no persisted weights yet");
}