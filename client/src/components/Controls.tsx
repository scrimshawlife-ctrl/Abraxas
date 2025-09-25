interface SliderProps {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
}

export function Slider({ label, min, max, step, value, onChange }: SliderProps) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <label style={{ fontSize: 13, color: "#9aa1b2" }}>{label}</label>
        <span style={{ fontSize: 11, color: "#66ffe6" }}>{(value / 100).toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          width: "100%",
          height: 6,
          background: "linear-gradient(90deg, #4c1d95, #7c3aed)",
          borderRadius: 3,
          outline: "none",
          cursor: "pointer"
        }}
      />
    </div>
  );
}