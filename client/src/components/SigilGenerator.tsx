import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Wand2, Copy, Download, Sparkles } from "lucide-react";

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
  <path d="${sigil.path}" fill="none" stroke="#a855f7" stroke-width="2" />
</svg>`;
      navigator.clipboard.writeText(svgString);
      console.log('SVG copied to clipboard');
    }
  };

  const handleDownload = () => {
    if (sigil) {
      const svgString = `<svg width="400" height="400" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" fill="#0a0a0a" />
  <path d="${sigil.path}" fill="none" stroke="#a855f7" stroke-width="1.5" filter="drop-shadow(0 0 3px #a855f7)" />
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
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-primary flex items-center gap-2">
              <Wand2 className="w-5 h-5" />
              Sigil Forge
            </h2>
            <p className="text-sm text-muted-foreground">
              Transform intention into symbolic form
            </p>
          </div>
        </div>

        <div className="flex gap-3 mb-6">
          <Input
            value={phrase}
            onChange={(e) => setPhrase(e.target.value)}
            placeholder="Enter your intention or phrase..."
            className="flex-1"
            data-testid="input-sigil-phrase"
            onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
          />
          <Button 
            onClick={handleGenerate}
            disabled={isGenerating || !phrase.trim()}
            data-testid="button-generate-sigil"
          >
            {isGenerating ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin mr-2" />
                Forging...
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4 mr-2" />
                Generate
              </>
            )}
          </Button>
        </div>

        {sigil && (
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Generated Sigil</h3>
              <Card className="p-6 bg-black/20 flex items-center justify-center aspect-square">
                <svg 
                  width="200" 
                  height="200" 
                  viewBox="0 0 100 100"
                  className="filter drop-shadow-lg"
                  style={{ filter: 'drop-shadow(0 0 8px rgba(168, 85, 247, 0.5))' }}
                >
                  <path 
                    d={sigil.path} 
                    fill="none" 
                    stroke="#a855f7" 
                    strokeWidth="1.5"
                  />
                </svg>
              </Card>
              
              <div className="flex gap-2 mt-4">
                <Button 
                  onClick={handleCopySVG}
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  data-testid="button-copy-svg"
                >
                  <Copy className="w-3 h-3 mr-2" />
                  Copy SVG
                </Button>
                <Button 
                  onClick={handleDownload}
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  data-testid="button-download-sigil"
                >
                  <Download className="w-3 h-3 mr-2" />
                  Download
                </Button>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3">Properties</h3>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-muted-foreground">Core Symbol</span>
                  <div className="font-mono text-primary mt-1">{sigil.core}</div>
                </div>
                
                <div>
                  <span className="text-sm text-muted-foreground">Seed</span>
                  <div className="font-mono text-xs text-accent mt-1 break-all">{sigil.seed}</div>
                </div>
                
                <div>
                  <span className="text-sm text-muted-foreground">Method</span>
                  <Badge variant="outline" className="mt-1">
                    Traditional Strip + Seeded Quadratic
                  </Badge>
                </div>
                
                <div>
                  <span className="text-sm text-muted-foreground">Nodes</span>
                  <div className="text-sm mt-1">{sigil.nodes.length} anchor points</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {history.length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Grimoire • Recent Sigils</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {history.map((entry, idx) => (
              <Card 
                key={idx} 
                className="p-3 cursor-pointer hover-elevate" 
                onClick={() => setSigil(entry.sigil)}
                data-testid={`sigil-history-${idx}`}
              >
                <div className="aspect-square bg-black/20 rounded-md mb-2 flex items-center justify-center">
                  <svg 
                    width="60" 
                    height="60" 
                    viewBox="0 0 100 100"
                    className="opacity-80"
                  >
                    <path 
                      d={entry.sigil.path} 
                      fill="none" 
                      stroke="#a855f7" 
                      strokeWidth="2"
                    />
                  </svg>
                </div>
                <div className="text-center">
                  <div className="text-xs font-mono text-primary mb-1">
                    {entry.sigil.core}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {entry.phrase}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}