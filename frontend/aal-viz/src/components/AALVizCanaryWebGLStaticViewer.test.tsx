import { describe, it, expect } from "vitest";
import { AALVizCanaryWebGLStaticViewer } from "./AALVizCanaryWebGLStaticViewer";

describe("AALVizCanaryWebGLStaticViewer", () => {
  it("exports component", () => {
    expect(AALVizCanaryWebGLStaticViewer).toBeDefined();
  });

  it("does not use animation loops", () => {
    const src = AALVizCanaryWebGLStaticViewer.toString();
    expect(src.includes("requestAnimationFrame")).toBe(false);
    expect(src.includes("setInterval")).toBe(false);
    expect(src.includes("setTimeout")).toBe(false);
  });

  it("contains fallback text", () => {
    const src = AALVizCanaryWebGLStaticViewer.toString();
    expect(src.includes("WebGL not supported")).toBe(true);
  });
});
