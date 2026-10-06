/**
 * InferenceNotice
 *
 * Engines that need an inference callable currently run through the
 * model-agnostic adapter (abraxas.evidence.adapters.model_agnostic), which talks
 * to any OpenAI-compatible endpoint configured via ABX_INFERENCE_* and otherwise
 * falls back to deterministic offline provenance.
 *
 * Engine-specific custom inference is not built yet. This notice says so plainly
 * rather than letting the UI imply a bespoke model is behind every engine.
 */
export function InferenceNotice() {
  return (
    <div
      className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
      role="status"
    >
      <span className="font-medium">Custom inference coming soon.</span>{' '}
      Evidence engines currently run through a model-agnostic adapter. Engine-specific
      custom inference is not yet available; results carry provenance saying which path ran.
    </div>
  );
}
