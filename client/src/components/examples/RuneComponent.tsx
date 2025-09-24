import RuneComponent from '../RuneComponent';

export default function RuneComponentExample() {
  const sampleRune = {
    id: "aether",
    name: "Aether",
    color: "#FFD166",
    svgPath: "M50 10 L70 60 L30 60 Z",
    feature_map: ["nightlights_z", "hs_code_volume_z"]
  };

  return (
    <div className="p-4">
      <RuneComponent 
        rune={sampleRune} 
        onClick={() => console.log('Rune clicked')}
      />
    </div>
  );
}