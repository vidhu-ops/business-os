type Props = { className?: string };

export function GlowOrb({ className = "" }: Props) {
  return (
    <div className={`mkt-glow-orb ${className}`} aria-hidden="true">
      <span className="mkt-glow-orb-a" />
      <span className="mkt-glow-orb-b" />
    </div>
  );
}

export function HeroVisual() {
  return (
    <div className="mkt-hero-visual" aria-hidden="true">
      <div className="mkt-hero-device">
        <div className="mkt-hero-device-top">
          <span className="dot r" /><span className="dot y" /><span className="dot g" />
          <span className="mkt-device-title">IIDA workspace</span>
        </div>
        <div className="mkt-hero-device-body">
          <div className="mkt-device-sidebar">
            {["Dashboard", "Research", "Plan", "Team"].map((l) => (
              <span key={l} className="mkt-device-nav">{l}</span>
            ))}
          </div>
          <div className="mkt-device-main">
            <div className="mkt-device-kpis">
              <div><strong>40+</strong><span>Report pages</span></div>
              <div><strong>18</strong><span>Topics</span></div>
              <div><strong>6</strong><span>AI agents</span></div>
            </div>
            <div className="mkt-device-chart">
              {[38, 62, 48, 78, 55, 88, 64].map((h, i) => (
                <span key={i} style={{ height: `${h}%` }} />
              ))}
            </div>
            <div className="mkt-device-rows">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>
      <div className="mkt-float-card mkt-float-card-a">
        <span className="mkt-float-label">TAM / SAM</span>
        <strong>₹2,400 Cr</strong>
      </div>
      <div className="mkt-float-card mkt-float-card-b">
        <span className="mkt-float-label">Sources</span>
        <strong>24 verified</strong>
      </div>
    </div>
  );
}

export function DocPreview({ variant = "report" }: { variant?: "report" | "plan" | "exec" }) {
  const accent = variant === "exec" ? "#34d399" : variant === "plan" ? "#a78bfa" : "#60a5fa";
  return (
    <div className="mkt-doc-preview" style={{ ["--doc-accent" as string]: accent }}>
      <div className="mkt-doc-line title" />
      <div className="mkt-doc-line w90" />
      <div className="mkt-doc-line w70" />
      <div className="mkt-doc-chart">
        {[45, 72, 58, 85, 50].map((h, i) => (
          <span key={i} style={{ height: `${h}%` }} />
        ))}
      </div>
      <div className="mkt-doc-line w80 accent" />
      <div className="mkt-doc-line w60 accent" />
    </div>
  );
}

export function AgentBadge({ initials, tone }: { initials: string; tone: string }) {
  return <div className={`mkt-agent-badge tone-${tone}`}>{initials}</div>;
}