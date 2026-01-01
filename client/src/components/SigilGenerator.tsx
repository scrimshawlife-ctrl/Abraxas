import { useState } from "react";
import { Wand2, Copy, Download, Sparkles } from "lucide-react";
import {
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

interface Sigil {
  path: string;
  nodes: Array<{ x: number; y: number }>;
  seed: string;
  core: string;
}

export default function SigilGenerator() {
  const [phrase, setPhrase] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [sigil, setSigil] = useState<Sigil | null>(null);
  const [history, setHistory] = useState<Array<{ phrase: string; sigil: Sigil }>>([]);

  const handleGenerate = async () => {
    if (!phrase.trim()) return;

    setIsGenerating(true);
    console.log('Generating sigil for:', phrase);

    setTimeout(() => {
      // Mock sigil generation using simplified logic
      const core = phrase.toUpperCase().replace(/[AEIOU\s]/g, "").replace(/(.)/g, '$1').slice(0, 8) || "SIGIL";
      const seed = Math.random().toString(16).slice(2, 18);

      // Generate a mystical-looking SVG path
      const points = [];
      for (let i = 0; i < core.length; i++) {
        const angle = (i / core.length) * 2 * Math.PI;
        const radius = 30 + Math.sin(i) * 15;
        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);
        points.push({ x, y });
      }

      let path = `M ${points[0]?.x || 50} ${points[0]?.y || 50}`;
      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        const controlX = (prev.x + curr.x) / 2 + Math.sin(i) * 8;
        const controlY = (prev.y + curr.y) / 2 + Math.cos(i) * 8;
        path += ` Q ${controlX} ${controlY}, ${curr.x} ${curr.y}`;
      }

      // Add a binding circle at the end
      const lastPoint = points[points.length - 1] || { x: 50, y: 50 };
      const radius = 3 + Math.random() * 4;
      path += ` M ${lastPoint.x} ${lastPoint.y} m -${radius} 0 a ${radius} ${radius} 0 1 0 ${radius * 2} 0 a ${radius} ${radius} 0 1 0 -${radius * 2} 0`;

      const newSigil: Sigil = {
        path,
        nodes: points,
        seed,
        core
      };

      setSigil(newSigil);
      setHistory(prev => [{ phrase, sigil: newSigil }, ...prev.slice(0, 9)]); // Keep last 10
      setIsGenerating(false);
    }, 1500);
  };

  const handleCopySVG = () => {
    if (sigil) {
      const svgString = `<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="${sigil.path}" fill="none" stroke="#FF3EF6" stroke-width="2" />
</svg>`;
      navigator.clipboard.writeText(svgString);
      console.log('SVG copied to clipboard');
    }
  };

  const handleDownload = () => {
    if (sigil) {
      const svgString = `<svg width="400" height="400" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" fill="#0a0a0a" />
  <path d="${sigil.path}" fill="none" stroke="#FF3EF6" stroke-width="1.5" filter="drop-shadow(0 0 3px #FF3EF6)" />
</svg>`;
      const blob = new Blob([svgString], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sigil-${sigil.core.toLowerCase()}.svg`;
      a.click();
      URL.revokeObjectURL(url);
      console.log('Sigil downloaded');
    }
  };

  return (
    <div className="aal-stack-lg">
      <AalCard>
        <div className="aal-stack-md">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AalSigilFrame tone="magenta" size={40}>
              <Wand2 size={20} />
            </AalSigilFrame>
            <div>
              <h2 className="aal-heading-md">Sigil Forge</h2>
              <p className="aal-body" style={{ fontSize: "13px", marginTop: "4px" }}>
                Transform intention into symbolic form
              </p>
            </div>
          </div>

          <AalDivider />

          <div style={{ display: "flex", gap: "12px" }}>
            <input
              type="text"
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              placeholder="Enter your intention or phrase..."
              className="aal-input"
              style={{
                flex: 1,
                padding: "10px 14px",
                background: "var(--aal-color-surface)",
                border: "1px solid var(--aal-color-border)",
                borderRadius: "8px",
                color: "var(--aal-color-text)",
                fontSize: "14px",
              }}
              data-testid="input-sigil-phrase"
              onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
            />
            <AalButton
              onClick={handleGenerate}
              disabled={isGenerating || !phrase.trim()}
              variant="primary"
              leftIcon={isGenerating ? <Sparkles size={16} className="animate-spin" /> : <Wand2 size={16} />}
              data-testid="button-generate-sigil"
            >
              {isGenerating ? "Forging..." : "Generate"}
            </AalButton>
          </div>

          {sigil && (
            <>
              <AalDivider />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                <div className="aal-stack-md">
                  <h3 className="aal-heading-md" style={{ fontSize: "14px" }}>Generated Sigil</h3>
                  <AalCard
                    variant="ghost"
                    style={{
                      aspectRatio: "1",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "rgba(0, 0, 0, 0.3)"
                    }}
                  >
                    <svg
                      width="200"
                      height="200"
                      viewBox="0 0 100 100"
                      style={{ filter: 'drop-shadow(0 0 8px rgba(255, 62, 246, 0.5))' }}
                    >
                      <path
                        d={sigil.path}
                        fill="none"
                        stroke="#FF3EF6"
                        strokeWidth="1.5"
                      />
                    </svg>
                  </AalCard>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <AalButton
                      onClick={handleCopySVG}
                      variant="secondary"
                      leftIcon={<Copy size={14} />}
                      style={{ flex: 1 }}
                      data-testid="button-copy-svg"
                    >
                      Copy SVG
                    </AalButton>
                    <AalButton
                      onClick={handleDownload}
                      variant="secondary"
                      leftIcon={<Download size={14} />}
                      style={{ flex: 1 }}
                      data-testid="button-download-sigil"
                    >
                      Download
                    </AalButton>
                  </div>
                </div>

                <div className="aal-stack-md">
                  <h3 className="aal-heading-md" style={{ fontSize: "14px" }}>Properties</h3>
                  <div className="aal-stack-md">
                    <div>
                      <span className="aal-body" style={{ fontSize: "12px" }}>Core Symbol</span>
                      <div
                        className="aal-heading-md"
                        style={{ fontFamily: "monospace", color: "var(--aal-color-magenta)", marginTop: "4px" }}
                      >
                        {sigil.core}
                      </div>
                    </div>

                    <div>
                      <span className="aal-body" style={{ fontSize: "12px" }}>Seed</span>
                      <div
                        className="aal-body"
                        style={{ fontFamily: "monospace", fontSize: "11px", color: "var(--aal-color-yellow)", wordBreak: "break-all", marginTop: "4px" }}
                      >
                        {sigil.seed}
                      </div>
                    </div>

                    <div>
                      <span className="aal-body" style={{ fontSize: "12px" }}>Method</span>
                      <div style={{ marginTop: "4px" }}>
                        <AalTag>Traditional Strip + Seeded Quadratic</AalTag>
                      </div>
                    </div>

                    <div>
                      <span className="aal-body" style={{ fontSize: "12px" }}>Nodes</span>
                      <div className="aal-body" style={{ marginTop: "4px" }}>
                        {sigil.nodes.length} anchor points
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </AalCard>

      {history.length > 0 && (
        <AalCard>
          <div className="aal-stack-md">
            <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>Grimoire • Recent Sigils</h3>
            <AalDivider />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "16px" }}>
              {history.map((entry, idx) => (
                <AalCard
                  key={idx}
                  variant="ghost"
                  padding="12px"
                  onClick={() => setSigil(entry.sigil)}
                  style={{ cursor: "pointer" }}
                  data-testid={`sigil-history-${idx}`}
                >
                  <div
                    style={{
                      aspectRatio: "1",
                      background: "rgba(0, 0, 0, 0.3)",
                      borderRadius: "6px",
                      marginBottom: "8px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center"
                    }}
                  >
                    <svg
                      width="60"
                      height="60"
                      viewBox="0 0 100 100"
                      style={{ opacity: 0.8 }}
                    >
                      <path
                        d={entry.sigil.path}
                        fill="none"
                        stroke="#FF3EF6"
                        strokeWidth="2"
                      />
                    </svg>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div
                      className="aal-heading-md"
                      style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--aal-color-magenta)" }}
                    >
                      {entry.sigil.core}
                    </div>
                    <div
                      className="aal-body"
                      style={{ fontSize: "10px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    >
                      {entry.phrase}
                    </div>
                  </div>
                </AalCard>
              ))}
            </div>
          </div>
        </AalCard>
      )}
    </div>
  );
}
