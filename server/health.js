import db from "./db.js";

export function healthRouter(app){
  app.get("/healthz", (req,res)=> res.status(200).json({ ok:true, ts: Date.now() }));
  app.get("/readyz", (req,res)=>{
    try {
      db.prepare("SELECT 1").get();
      res.status(200).json({ ready:true, ts: Date.now() });
    } catch (e) {
      res.status(503).json({ ready:false, error: String(e) });
    }
  });
}