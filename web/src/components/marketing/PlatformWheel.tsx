"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Audience, ToolId } from "./audienceContent";
import { TOOLS } from "./audienceContent";

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
          Click a tool below to see what it means for{" "}
          {audience === "founder" ? "founders" : "established B2B companies"} — and how it works inside
          IIDATECH.
        </p>
      </div>

      <div className="mkt-wheel-tools" role="tablist" aria-label="IIDATECH platform tools">
        {TOOLS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={active === t.id}
            aria-controls={`tool-panel-${t.id}`}
            id={`tool-tab-${t.id}`}
            className={`mkt-wheel-chip${active === t.id ? " is-active" : ""}`}
            onClick={() => setActive(t.id)}
          >
            {t.short}
          </button>
        ))}
      </div>

      <article
        className="mkt-wheel-panel mkt-wheel-panel-full"
        id={`tool-panel-${tool.id}`}
        role="tabpanel"
        aria-labelledby={`tool-tab-${tool.id}`}
        aria-live="polite"
      >
        <span className="mkt-tag">{tool.label.toUpperCase()}</span>
        <h3 className="mkt-feature-title">{copy.title}</h3>
        <p className="mkt-feature-body">{copy.body}</p>
        <p className="mkt-wheel-inapp">
          <strong>In the app:</strong> {copy.inApp}
        </p>
        {tool.videoSrc ? (
          <div className="mkt-wheel-video">
            <video
              key={tool.videoSrc}
              controls
              playsInline
              preload="metadata"
              poster={/marketing/frames/.png}
            >
              <source src={tool.videoSrc} type="video/mp4" />
            </video>
          </div>
        ) : tool.videoId ? (
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

      <div className="mkt-wheel-cta">
        <Link href="/#pricing" className="iid-btn iid-btn-primary">
          Check pricing
        </Link>
      </div>
    </div>
  );
}
