import { useEffect, useState } from "react";
import { Slider } from "./Controls";
import { getConfig, setConfig, previewConfig } from "../api";
import { SimpleTooltip } from "@/components/ui/tooltip";
import { Settings, RotateCcw, Eye, Save } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

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
  "nightlights_z", "port_dwell_delta", "sam_mod_scope_delta", "ptab_ipr_burst", "fr_waiver_absence", "jobs_clearance_burst", "hs_code_volume_z", "fx_basis_z",
  "numerology_reduced", "numerology_master", "gematria_alignment", "astro_rul_align", "astro_waxing"
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

export default function Config() {
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [defaults, setDefaults] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [currentPreset, setCurrentPreset] = useState<string>("Custom");

  useEffect(() => {
    (async () => {
      try {
        const cfg = await getConfig();
        console.log('Config loaded:', cfg);
        setWeights(cfg.weights || {});
        setDefaults(cfg.defaults || {});
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    })();
  }, []);

  async function save() {
    setSaving(true);
    const out = await setConfig(weights);
    setWeights(out.weights || weights);
    setSaving(false);
  }

  function reset() {
    const w = { ...weights };
    for (const k of Object.keys(defaults)) w[k] = defaults[k];
    setWeights(w);
  }

  async function runPreview() {
    const out = await previewConfig(weights);
    setPreview(out);
  }

  function applyPreset(presetName: string) {
    if (presetName === "Custom") return;
    setWeights(PRESETS[presetName as keyof typeof PRESETS]);
    setCurrentPreset(presetName);
    setPreview(null);
  }

  function onSliderChange(key: string, value: number) {
    setWeights(w => ({ ...w, [key]: value / 100 }));
    setCurrentPreset("Custom");
  }

  function getPresetDescription(preset: string): string {
    const descriptions: Record<string, string> = {
      Conservative: "Lower risk weights emphasizing stability and traditional indicators",
      Aggressive: "High weights across all features for maximum market impact sensitivity",
      Mystical: "Emphasizes esoteric features: numerology, gematria, and astrological influences",
      Technical: "Focuses on data-driven indicators with minimal mystical influence",
      Balanced: "Moderate weights providing equilibrium between all feature types"
    };
    return descriptions[preset] || "";
  }

  return (
    <div className="aal-stack-lg">
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AalSigilFrame tone="cyan" size={40}>
              <Settings size={20} />
            </AalSigilFrame>
            <div>
              <h2 className="aal-heading-md">Config - Model Weights</h2>
              <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }}>
                Tune Abraxas' feature weights. Preview effects before saving.
              </p>
            </div>
          </div>

          <AalDivider />

          {/* Presets */}
          <div className="aal-stack-md">
            <h4 className="aal-heading-md" style={{ fontSize: "14px" }}>Presets</h4>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {Object.keys(PRESETS).map(preset => (
                <SimpleTooltip key={preset} content={getPresetDescription(preset)} side="bottom">
                  <div>
                    <AalButton
                      onClick={() => applyPreset(preset)}
                      variant={currentPreset === preset ? "primary" : "secondary"}
                      data-testid={`preset-${preset.toLowerCase()}`}
                    >
                      {preset}
                    </AalButton>
                  </div>
                </SimpleTooltip>
              ))}
              <AalButton
                variant={currentPreset === "Custom" ? "primary" : "ghost"}
                data-testid="preset-custom"
              >
                Custom
              </AalButton>
            </div>
            <div className="aal-body" style={{ fontSize: "12px" }}>
              Current: <AalTag>{currentPreset}</AalTag>
            </div>
          </div>

          <AalDivider />

          {/* Sliders */}
          <div className="aal-stack-md">
            {ORDER.map(key => (
              <div key={key} style={{ marginBottom: "12px" }}>
                <Slider
                  label={key}
                  min={-200}
                  max={200}
                  step={1}
                  value={Math.round(((weights[key] ?? 0) * 100))}
                  onChange={(v: number) => onSliderChange(key, v)}
                />
                <SimpleTooltip content={FEATURE_EXPLANATIONS[key]} side="right">
                  <div
                    className="aal-body"
                    style={{
                      fontSize: "11px",
                      marginTop: "2px",
                      marginLeft: "4px",
                      fontStyle: "italic",
                      cursor: "help"
                    }}
                  >
                    {FEATURE_EXPLANATIONS[key]}
                  </div>
                </SimpleTooltip>
              </div>
            ))}
          </div>

          <AalDivider />

          {/* Actions */}
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <SimpleTooltip content="Save current weights to persistent storage" side="top">
              <div>
                <AalButton
                  onClick={save}
                  disabled={saving}
                  variant="primary"
                  leftIcon={<Save size={16} />}
                >
                  {saving ? "Saving..." : "Save Weights"}
                </AalButton>
              </div>
            </SimpleTooltip>
            <SimpleTooltip content="Reset all weights to default values" side="top">
              <div>
                <AalButton
                  onClick={reset}
                  variant="secondary"
                  leftIcon={<RotateCcw size={16} />}
                  style={{ background: "linear-gradient(90deg, rgba(255,62,246,0.2), rgba(255,62,246,0.1))" }}
                >
                  Reset
                </AalButton>
              </div>
            </SimpleTooltip>
            <SimpleTooltip content="Test current weights against sample data without saving" side="top">
              <div>
                <AalButton
                  onClick={runPreview}
                  variant="secondary"
                  leftIcon={<Eye size={16} />}
                  style={{ background: "linear-gradient(90deg, rgba(0,212,255,0.2), rgba(0,212,255,0.1))" }}
                >
                  Preview Impact
                </AalButton>
              </div>
            </SimpleTooltip>
          </div>

          {preview && (
            <AalCard variant="ghost" padding="16px">
              <h4 className="aal-heading-md" style={{ fontSize: "14px", marginBottom: "8px" }}>
                Preview Results (not saved)
              </h4>
              <pre
                style={{
                  whiteSpace: "pre-wrap",
                  fontSize: "12px",
                  fontFamily: "monospace",
                  color: "var(--aal-color-muted)"
                }}
              >
                {JSON.stringify(preview.results, null, 2)}
              </pre>
            </AalCard>
          )}

          <p className="aal-body" style={{ fontSize: "11px", fontStyle: "italic" }}>
            Range: -2.00 to +2.00 (internally clamped to [-5, +5]). Esoteric weights are modest by design; push carefully.
          </p>
        </div>
      </AalCard>
    </div>
  );
}
