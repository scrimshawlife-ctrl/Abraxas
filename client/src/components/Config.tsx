import { useEffect, useState } from "react";
import { Slider } from "./Controls";
import { getConfig, setConfig, previewConfig } from "../api";

const FEATURE_EXPLANATIONS: Record<string, string> = {
  nightlights_z: "Satellite nighttime illumination patterns - economic activity correlation",
  port_dwell_delta: "Shipping container dwell time changes - supply chain efficiency indicator", 
  sam_mod_scope_delta: "Strategic market scope modulation - breadth vs depth trading focus",
  ptab_ipr_burst: "Patent Trial & Appeal Board activity bursts - innovation cycle timing",
  fr_waiver_absence: "Federal Register waiver absence patterns - regulatory environment shifts",
  jobs_clearance_burst: "Employment clearance processing spikes - economic momentum signals",
  hs_code_volume_z: "Harmonized System trade code volume anomalies - sector rotation hints",
  fx_basis_z: "Foreign exchange basis point deviations - currency flow irregularities",
  numerology_reduced: "Pythagorean number reduction of ticker symbols - mystical resonance",
  numerology_master: "Master number detection (11, 22, 33) - amplified mystical influence",
  gematria_alignment: "Hebrew/Greek letter-number correspondences - ancient wisdom encoding",
  astro_rul_align: "Planetary ruler alignments with market sectors - celestial governance",
  astro_waxing: "Lunar phase influence on market psychology - emotional tide patterns"
};

const ORDER = [
  "nightlights_z","port_dwell_delta","sam_mod_scope_delta","ptab_ipr_burst","fr_waiver_absence","jobs_clearance_burst","hs_code_volume_z","fx_basis_z",
  "numerology_reduced","numerology_master","gematria_alignment","astro_rul_align","astro_waxing"
];

const PRESETS = {
  Conservative: {
    nightlights_z: 0.3, port_dwell_delta: 0.4, sam_mod_scope_delta: 0.2, ptab_ipr_burst: 0.1, fr_waiver_absence: 0.3,
    jobs_clearance_burst: 0.2, hs_code_volume_z: 0.3, fx_basis_z: 0.4, numerology_reduced: 0.1, numerology_master: 0.0,
    gematria_alignment: 0.1, astro_rul_align: 0.1, astro_waxing: 0.1
  },
  Aggressive: {
    nightlights_z: 0.8, port_dwell_delta: 0.7, sam_mod_scope_delta: 0.9, ptab_ipr_burst: 1.2, fr_waiver_absence: 0.6,
    jobs_clearance_burst: 1.1, hs_code_volume_z: 0.8, fx_basis_z: 0.9, numerology_reduced: 0.4, numerology_master: 0.3,
    gematria_alignment: 0.5, astro_rul_align: 0.4, astro_waxing: 0.6
  },
  Mystical: {
    nightlights_z: 0.2, port_dwell_delta: 0.1, sam_mod_scope_delta: 0.1, ptab_ipr_burst: 0.2, fr_waiver_absence: 0.1,
    jobs_clearance_burst: 0.1, hs_code_volume_z: 0.2, fx_basis_z: 0.1, numerology_reduced: 1.1, numerology_master: 0.8,
    gematria_alignment: 1.3, astro_rul_align: 1.0, astro_waxing: 0.9
  },
  Technical: {
    nightlights_z: 0.9, port_dwell_delta: 1.1, sam_mod_scope_delta: 0.8, ptab_ipr_burst: 1.0, fr_waiver_absence: 0.7,
    jobs_clearance_burst: 0.9, hs_code_volume_z: 1.2, fx_basis_z: 1.0, numerology_reduced: 0.1, numerology_master: 0.0,
    gematria_alignment: 0.1, astro_rul_align: 0.1, astro_waxing: 0.1
  },
  Balanced: {
    nightlights_z: 0.5, port_dwell_delta: 0.5, sam_mod_scope_delta: 0.5, ptab_ipr_burst: 0.5, fr_waiver_absence: 0.5,
    jobs_clearance_burst: 0.5, hs_code_volume_z: 0.5, fx_basis_z: 0.5, numerology_reduced: 0.5, numerology_master: 0.3,
    gematria_alignment: 0.5, astro_rul_align: 0.5, astro_waxing: 0.5
  }
};

export default function Config(){
  const [weights,setWeights]=useState<Record<string,number>>({});
  const [defaults,setDefaults]=useState<Record<string,number>>({});
  const [saving,setSaving]=useState(false);
  const [preview,setPreview]=useState<any>(null);
  const [currentPreset,setCurrentPreset]=useState<string>("Custom");

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
  
  function applyPreset(presetName: string){
    if(presetName === "Custom") return;
    setWeights(PRESETS[presetName as keyof typeof PRESETS]);
    setCurrentPreset(presetName);
    setPreview(null); // Clear any existing preview
  }
  
  function onSliderChange(key: string, value: number){
    setWeights(w=>({ ...w, [key]: value/100 }));
    setCurrentPreset("Custom"); // Switch to custom when manually adjusting
  }
  
  function getPresetDescription(preset: string): string {
    const descriptions = {
      Conservative: "Lower risk weights emphasizing stability and traditional indicators",
      Aggressive: "High weights across all features for maximum market impact sensitivity", 
      Mystical: "Emphasizes esoteric features: numerology, gematria, and astrological influences",
      Technical: "Focuses on data-driven indicators with minimal mystical influence",
      Balanced: "Moderate weights providing equilibrium between all feature types"
    };
    return descriptions[preset as keyof typeof descriptions] || "";
  }

  return (
    <section className="panel">
      <h3>Config — Model Weights</h3>
      <div className="mono" style={{color:"#9aa1b2", marginBottom:8}}>Tune Abraxas' feature weights. You can preview effects before saving.</div>
      
      <div style={{marginBottom:16}}>
        <h4 style={{marginBottom:8}}>Presets</h4>
        <div style={{display:"flex", gap:6, flexWrap:"wrap", marginBottom:8}}>
          {Object.keys(PRESETS).map(preset => (
            <button 
              key={preset} 
              className="btn" 
              onClick={() => applyPreset(preset)}
              style={{
                fontSize:"0.85em",
                background: currentPreset === preset ? "linear-gradient(90deg,#4a90e2,#357abd)" : undefined
              }}
              data-testid={`preset-${preset.toLowerCase()}`}
              title={getPresetDescription(preset)}
            >
              {preset}
            </button>
          ))}
          <button 
            className="btn" 
            style={{
              fontSize:"0.85em",
              background: currentPreset === "Custom" ? "linear-gradient(90deg,#4a90e2,#357abd)" : undefined
            }}
            data-testid="preset-custom"
          >
            Custom
          </button>
        </div>
        <div className="mono" style={{fontSize:"0.75em", color:"#7a8394"}}>
          Current: {currentPreset}
        </div>
      </div>
      {ORDER.map(key=>(
        <div key={key} style={{marginBottom:8}}>
          <Slider label={key} min={-200} max={200} step={1}
            value={Math.round(((weights[key]??0)*100))}
            onChange={(v: number)=> onSliderChange(key, v)}
          />
          <div 
            className="mono" 
            style={{
              fontSize:"0.75em", 
              color:"#7a8394", 
              marginTop:2, 
              marginLeft:4,
              fontStyle:"italic"
            }}
            title={FEATURE_EXPLANATIONS[key]}
          >
            {FEATURE_EXPLANATIONS[key]}
          </div>
        </div>
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