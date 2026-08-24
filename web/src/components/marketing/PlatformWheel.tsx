"use client";

import { useMemo, useState, type CSSProperties } from "react";
import type { Audience, ToolId } from "./audienceContent";
import { TOOLS } from "./audienceContent";

const HOTSPOTS: Array<{ id: ToolId; style: CSSProperties }> = [
  { id: "research", style: { top: "6%", left: "50%", transform: "translate(-50%, 0)" } },
  { id: "plan", style: { top: "28%", right: "2%" } },
  { id: "execute", style: { bottom: "22%", right: "6%" } },
  { id: "automate", style: { bottom: "4%", left: "50%", transform: "translate(-50%, 0)" } },
  { id: "mentor", style: { bottom: "22%", left: "6%" } },
  { id: "brand", style: { top: "28%", left: "2%" } },
];

export function PlatformWheel({ audience }: { audience: Audience }) {
  const [active, setActive] = useState<ToolId>("research");
  const tool = useMemo(() => TOOLS.find((t) => t.id === active) || TOOLS[0], [active]);
  const copy = tool[audience];

  return (
    <div className="mkt-wheel">
      <div className="mkt-section-head mkt-wheel-head">
        <span className="mkt-label">Platform</span>
        <h2 className="mkt-h2">1 platform. 6 tools.</h2>
        <p className="mkt-sub">
          Click a tool on the wheel to see what it means for{" "}
          {audience === "founder" ? "founders" : "established B2B companies"} — and how it works inside IIDATECH.
        </p>
      </div>

      <div className="mkt-wheel-tools" role="tablist" aria-label="IIDATECH platform tools">
        {TOOLS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={active === t.id}
            className={`mkt-wheel-chip${active === t.id ? " is-active" : ""}`}
            onClick={() => setActive(t.id)}
          >
            {t.short}
          </button>
        ))}
      </div>

      <div className="mkt-wheel-stage">
        <div className="mkt-wheel-canvas">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/marketing/platform-wheel.png"
            alt="IIDATECH platform wheel showing six connected business tools"
            className="mkt-wheel-img"
          />
          {HOTSPOTS.map((h) => {
            const label = TOOLS.find((t) => t.id === h.id)?.short || h.id;
            return (
              <button
                key={h.id}
                type="button"
                className={`mkt-wheel-hotspot${active === h.id ? " is-active" : ""}`}
                style={h.style}
                aria-label={`Show ${label}`}
                onClick={() => setActive(h.id)}
              >
                {label}
              </button>
            );
          })}
        </div>

        <article className="mkt-wheel-panel" aria-live="polite">
          <span className="mkt-tag">{tool.label.toUpperCase()}</span>
          <h3 className="mkt-feature-title">{copy.title}</h3>
          <p className="mkt-feature-body">{copy.body}</p>
          <p className="mkt-wheel-inapp">
            <strong>In the app:</strong> {copy.inApp}
          </p>
          {tool.videoId ? (
            <div className="mkt-wheel-video">
              <iframe
                title={`${tool.label} walkthrough`}
                src={`https://www.youtube.com/embed/${tool.videoId}?rel=0`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          ) : null}
        </article>
      </div>
    </div>
  );
}