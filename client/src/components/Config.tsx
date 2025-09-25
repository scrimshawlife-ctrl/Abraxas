import { useEffect, useState } from "react";
import { Slider } from "./Controls";
import { getConfig, setConfig, previewConfig } from "../api";

const ORDER = [
  "nightlights_z","port_dwell_delta","sam_mod_scope_delta","ptab_ipr_burst","fr_waiver_absence","jobs_clearance_burst","hs_code_volume_z","fx_basis_z",
  "numerology_reduced","numerology_master","gematria_alignment","astro_rul_align","astro_waxing"
];

export default function Config(){
  const [weights,setWeights]=useState<Record<string,number>>({});
  const [defaults,setDefaults]=useState<Record<string,number>>({});
  const [saving,setSaving]=useState(false);
  const [preview,setPreview]=useState<any>(null);

  useEffect(()=>{ 
    (async()=>{ 
      try {
        const cfg = await getConfig(); 
        console.log('Config loaded:', cfg);
        setWeights(cfg.weights || {}); 
        setDefaults(cfg.defaults || {});
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    })(); 
  },[]);

  async function save(){
    setSaving(true);
    const out=await setConfig(weights);
    setWeights(out.weights||weights);
    setSaving(false);
  }
  function reset(){ const w={...weights}; for(const k of Object.keys(defaults)) w[k]=defaults[k]; setWeights(w); }
  async function runPreview(){
    const out=await previewConfig(weights);
    setPreview(out);
  }

  return (
    <section className="panel">
      <h3>Config — Model Weights</h3>
      <div className="mono" style={{color:"#9aa1b2", marginBottom:8}}>Tune Abraxas' feature weights. You can preview effects before saving.</div>
      {ORDER.map(key=>(
        <Slider key={key} label={key} min={-200} max={200} step={1}
          value={Math.round(((weights[key]??0)*100))}
          onChange={(v: number)=> setWeights(w=>({ ...w, [key]: v/100 }))}
        />
      ))}
      <div style={{display:"flex", gap:8, marginTop:10, flexWrap:"wrap"}}>
        <button className="btn" onClick={save} disabled={saving}>{saving? "Saving…" : "Save Weights"}</button>
        <button className="btn" onClick={reset} style={{background:"linear-gradient(90deg,#7a1a1a,#7a430a)"}}>Reset</button>
        <button className="btn" onClick={runPreview} style={{background:"linear-gradient(90deg,#0a7a5c,#0a7a2e)"}}>Preview Impact</button>
      </div>
      {preview && (
        <div className="panel" style={{marginTop:12}}>
          <h4>Preview Results (not saved)</h4>
          <pre style={{whiteSpace:"pre-wrap", fontSize:12}}>{JSON.stringify(preview.results,null,2)}</pre>
        </div>
      )}
      <div className="disc" style={{marginTop:8}}>Range: -2.00 to +2.00 (internally clamped to [-5, +5]). Esoteric weights are modest by design; push carefully.</div>
    </section>
  );
}