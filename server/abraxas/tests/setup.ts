/**
 * Vitest Setup - Mock external dependencies
 */

import { vi } from "vitest";

// Mock the indicators module to avoid db/storage dependencies
vi.mock("../../indicators", () => ({
  evalDynamicIndicators: vi.fn().mockResolvedValue({
    nightlights_z: 0.5,
    port_dwell_delta: -0.2,
    sam_mod_scope_delta: 0.3,
    ptab_ipr_burst: 0.1,
    fr_waiver_absence: 0.4,
    cbp_hold_rate: 0.25,
    tariff_exposure_pct: 0.15,
    competitor_velocity: 0.6,
    insider_sentiment_ratio: 0.7,
    patent_citation_accel: 0.35,
  }),
  getCachedIndicatorValue: vi.fn().mockResolvedValue(null),
  setCachedIndicatorValue: vi.fn().mockResolvedValue(undefined),
}));
