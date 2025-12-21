export interface GoldenCase {
  id: string;
  label: "high" | "low" | "ambiguous";
  text: string;
  notes?: string;
}

export interface GoldenEvalResult {
  case_id: string;
  expected: GoldenCase["label"];
  observed_value: number;
  pass: boolean;
}

export function passRule(expected: GoldenCase["label"], value: number): boolean {
  if (expected === "high") return value >= 0.7;
  if (expected === "low") return value <= 0.3;
  return true;
}
