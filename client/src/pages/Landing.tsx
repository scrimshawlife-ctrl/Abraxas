import { Eye, TrendingUp, Zap, Shield } from "lucide-react";
import {
  AalShell,
  AalCard,
  AalButton,
  AalTag,
  AalDivider,
  AalSigilFrame,
} from "../../../aal-ui-kit/src";

export default function Landing() {
  return (
    <AalShell
      title="ABRAXAS"
      subtitle="Mystical Trading Oracle • Sources & methods sealed • Not financial advice"
    >
      {/* Hero Description */}
      <div className="aal-body" style={{ textAlign: "center", maxWidth: "800px", margin: "0 auto" }}>
        Combine ancient wisdom with modern market analysis through our mystical
        trading algorithms and dynamic watchlist system.
      </div>

      <AalDivider />

      {/* Features Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "20px",
          marginTop: "32px",
        }}
      >
        <AalCard>
          <div className="aal-stack-md">
            <AalSigilFrame tone="cyan" size={48}>
              <TrendingUp />
            </AalSigilFrame>
            <h3 className="aal-heading-md">Dynamic Watchlists</h3>
            <p className="aal-body">
              AI-powered market analysis for growth opportunities and short
              candidates
            </p>
          </div>
        </AalCard>

        <AalCard>
          <div className="aal-stack-md">
            <AalSigilFrame tone="yellow" size={48}>
              <Zap />
            </AalSigilFrame>
            <h3 className="aal-heading-md">Mystical Indicators</h3>
            <p className="aal-body">
              Proprietary algorithms that blend traditional analysis with
              esoteric insights
            </p>
          </div>
        </AalCard>

        <AalCard>
          <div className="aal-stack-md">
            <AalSigilFrame tone="magenta" size={48}>
              <Shield />
            </AalSigilFrame>
            <h3 className="aal-heading-md">Secure Analysis</h3>
            <p className="aal-body">
              Personal watchlists and trading insights protected by modern
              authentication
            </p>
          </div>
        </AalCard>
      </div>

      <AalDivider />

      {/* Call to Action */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "16px",
          marginTop: "24px",
        }}
      >
        <div className="aal-row-md">
          <AalButton
            variant="primary"
            onClick={() => (window.location.href = "/api/login")}
            data-testid="button-login"
          >
            Enter the Oracle
          </AalButton>

          <AalTag icon={<Eye size={12} />}>Mystical • Analytical • Secure</AalTag>
        </div>

        <p
          className="aal-body"
          style={{
            fontSize: "13px",
            maxWidth: "500px",
            textAlign: "center",
            opacity: 0.6,
          }}
        >
          By entering, you acknowledge this is not financial advice. Past
          mystical insights do not guarantee future results.
        </p>
      </div>
    </AalShell>
  );
}
