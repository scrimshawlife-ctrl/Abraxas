export async function fetchRunes(){ const r=await fetch("/api/runes"); return r.json(); }
export async function postRitual(payload:{equities:string[];fx:string[]}){ const r=await fetch("/api/ritual",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); return r.json(); }
export async function fetchStats(){ const r=await fetch("/api/stats"); return r.json(); }
export async function fetchDailyOracle(){ const r=await fetch("/api/daily-oracle"); return r.json(); }
export async function fetchSocialTrends(){ const r=await fetch("/api/social-trends"); return r.json(); }

export async function getConfig(){ const r=await fetch("/api/config"); return r.json(); }
export async function setConfig(weights:Record<string,number>){ const r=await fetch("/api/config",{ method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify({ weights }) }); return r.json(); }
export async function previewConfig(weights:Record<string,number>){ const r=await fetch("/api/config/preview",{ method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify({ weights }) }); return r.json(); }