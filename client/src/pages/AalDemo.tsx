/**
 * AAL UI Kit Demo Page
 * Showcases all AAL components and design patterns
 */

import { Sparkles, TrendingUp, Music, Cpu, Zap, Eye } from "lucide-react";
import {
  AalShell,
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

export default function AalDemo() {
  return (
    <AalShell
      title="Applied Alchemy Labs"
      subtitle="Myth-tech systems for music, meaning, and foresight"
    >
      {/* Introduction */}
      <AalCard>
        <div className="aal-stack-md">
          <div className="aal-row-sm">
            <AalTag icon={<Sparkles size={12} />}>Featured</AalTag>
            <AalTag>AAL UI Kit v1.0</AalTag>
          </div>

          <h2 className="aal-heading-md">Abraxas Oracle System</h2>

          <p className="aal-body">
            Mystical trading insights powered by symbolic computation. The
            Abraxas system combines ancient archetypal wisdom with modern
            market analysis to generate deterministic forecasts and trading
            signals.
          </p>

          <div className="aal-row-md">
            <AalButton variant="primary" leftIcon={<Eye size={16} />}>
              Open Console
            </AalButton>
            <AalButton variant="secondary">View Documentation</AalButton>
            <AalButton variant="ghost">Learn More</AalButton>
          </div>
        </div>
      </AalCard>

      <AalDivider />

      {/* Sigil Frame Showcase */}
      <div>
        <h2 className="aal-heading-md" style={{ marginBottom: "16px" }}>
          Sigil Frames
        </h2>
        <p className="aal-body" style={{ marginBottom: "20px" }}>
          Circular icon containers with tone-specific glows for categorizing
          features and modules.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
          }}
        >
          <AalCard variant="ghost">
            <div className="aal-stack-md" style={{ alignItems: "center" }}>
              <AalSigilFrame tone="cyan" size={56}>
                <Cpu />
              </AalSigilFrame>
              <div style={{ textAlign: "center" }}>
                <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>
                  Cyan
                </h3>
                <p className="aal-body" style={{ fontSize: "13px" }}>
                  System / General
                </p>
              </div>
            </div>
          </AalCard>

          <AalCard variant="ghost">
            <div className="aal-stack-md" style={{ alignItems: "center" }}>
              <AalSigilFrame tone="yellow" size={56}>
                <TrendingUp />
              </AalSigilFrame>
              <div style={{ textAlign: "center" }}>
                <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>
                  Yellow
                </h3>
                <p className="aal-body" style={{ fontSize: "13px" }}>
                  Analytics / Forecasting
                </p>
              </div>
            </div>
          </AalCard>

          <AalCard variant="ghost">
            <div className="aal-stack-md" style={{ alignItems: "center" }}>
              <AalSigilFrame tone="magenta" size={56}>
                <Music />
              </AalSigilFrame>
              <div style={{ textAlign: "center" }}>
                <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>
                  Magenta
                </h3>
                <p className="aal-body" style={{ fontSize: "13px" }}>
                  Creative / Music
                </p>
              </div>
            </div>
          </AalCard>
        </div>
      </div>

      <AalDivider />

      {/* Button Variants */}
      <div>
        <h2 className="aal-heading-md" style={{ marginBottom: "16px" }}>
          Button Variants
        </h2>
        <p className="aal-body" style={{ marginBottom: "20px" }}>
          Three button variants for different interaction hierarchies.
        </p>

        <AalCard variant="ghost">
          <div className="aal-stack-md">
            <div className="aal-row-md">
              <AalButton variant="primary">Primary Action</AalButton>
              <AalButton variant="primary" leftIcon={<Sparkles size={16} />}>
                With Icon
              </AalButton>
              <AalButton variant="primary" disabled>
                Disabled
              </AalButton>
            </div>

            <div className="aal-row-md">
              <AalButton variant="secondary">Secondary Action</AalButton>
              <AalButton variant="secondary" rightIcon={<Zap size={16} />}>
                With Icon
              </AalButton>
              <AalButton variant="secondary" disabled>
                Disabled
              </AalButton>
            </div>

            <div className="aal-row-md">
              <AalButton variant="ghost">Ghost Action</AalButton>
              <AalButton variant="ghost" leftIcon={<Eye size={16} />}>
                With Icon
              </AalButton>
              <AalButton variant="ghost" disabled>
                Disabled
              </AalButton>
            </div>
          </div>
        </AalCard>
      </div>

      <AalDivider />

      {/* Card Variants */}
      <div>
        <h2 className="aal-heading-md" style={{ marginBottom: "16px" }}>
          Card Variants
        </h2>

        <div style={{ display: "grid", gap: "16px" }}>
          <AalCard>
            <div className="aal-stack-md">
              <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>
                Default Card
              </h3>
              <p className="aal-body">
                Standard card with subtle cyan glow and shadow. Best for
                primary content containers.
              </p>
            </div>
          </AalCard>

          <AalCard variant="ghost">
            <div className="aal-stack-md">
              <h3 className="aal-heading-md" style={{ fontSize: "16px" }}>
                Ghost Card
              </h3>
              <p className="aal-body">
                Transparent variant with minimal styling. Best for nested
                content or less emphasis.
              </p>
            </div>
          </AalCard>
        </div>
      </div>

      <AalDivider />

      {/* Tags */}
      <div>
        <h2 className="aal-heading-md" style={{ marginBottom: "16px" }}>
          Tags & Badges
        </h2>
        <p className="aal-body" style={{ marginBottom: "20px" }}>
          Small pills for labels, categories, and status indicators.
        </p>

        <AalCard variant="ghost">
          <div className="aal-row-sm">
            <AalTag>Default</AalTag>
            <AalTag icon={<Sparkles size={12} />}>With Icon</AalTag>
            <AalTag icon={<TrendingUp size={12} />}>Forecasting</AalTag>
            <AalTag icon={<Music size={12} />}>Creative</AalTag>
            <AalTag icon={<Cpu size={12} />}>System</AalTag>
          </div>
        </AalCard>
      </div>

      <AalDivider />

      {/* Typography */}
      <div>
        <h2 className="aal-heading-md" style={{ marginBottom: "16px" }}>
          Typography
        </h2>

        <AalCard variant="ghost">
          <div className="aal-stack-lg">
            <div className="aal-stack-md">
              <h1 className="aal-heading-xl">Heading XL</h1>
              <p className="aal-body" style={{ fontSize: "13px" }}>
                Large page titles: 32-40px, uppercase, wide tracking
              </p>
            </div>

            <div className="aal-stack-md">
              <h2 className="aal-heading-md">Heading MD</h2>
              <p className="aal-body" style={{ fontSize: "13px" }}>
                Section headings: ~20px, uppercase, wider tracking
              </p>
            </div>

            <div className="aal-stack-md">
              <p className="aal-body">
                Body text: ~15px, muted color, comfortable line-height for
                reading longer content. This is the standard text style for
                descriptions, explanations, and informational content.
              </p>
            </div>
          </div>
        </AalCard>
      </div>

      {/* Footer */}
      <div
        className="aal-body"
        style={{
          textAlign: "center",
          fontSize: "12px",
          opacity: 0.5,
          marginTop: "40px",
        }}
      >
        AAL UI Kit v1.0 • Applied Alchemy Labs © 2025
      </div>
    </AalShell>
  );
}
