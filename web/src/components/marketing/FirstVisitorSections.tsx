"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import {
  CASE_STUDIES,
  CHATGPT_COMPARE,
  CREDIT_GUIDE,
  DEMO_CASE_STUDY,
  EVIDENCE_EXAMPLE,
  PRODUCT_STORY,
  PRODUCT_UI_SHOTS,
  TAYLOR_EXAMPLE,
  VISITOR_GOALS,
} from "./audienceContent";

export function VisitorGoalsSection() {
  return (
    <section id="start-here" className="mkt-wrap mkt-section mkt-section-goals">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">Start here</span>
        <h2 className="mkt-h2">What are you trying to do?</h2>
        <p className="mkt-sub">Pick the job that matches you. IIDATECH routes you to the right workflow — not six tools at once.</p>
      </div>
      <div className="mkt-goal-grid">
        {VISITOR_GOALS.map((goal) => {
          const body = (
            <>
              <span className="mkt-goal-emoji" aria-hidden="true">{goal.emoji}</span>
              <h3>{goal.title}</h3>
              <p>{goal.question}</p>
              <span className="mkt-goal-cta">{goal.cta} →</span>
            </>
          );
          if (goal.external) {
            return (
              <a
                key={goal.id}
                href={goal.href}
                className="mkt-goal-card mkt-goal-card-whatsapp"
                target="_blank"
                rel="noopener noreferrer"
              >
                {body}
              </a>
            );
          }
          return (
            <WorkspaceEntryLink key={goal.id} href={goal.href} wrapperClassName="contents" className="mkt-goal-card">
              {body}
            </WorkspaceEntryLink>
          );
        })}
      </div>
    </section>
  );
}

export function DemoCaseStudySection() {
  return (
    <section id="demo-story" className="mkt-band mkt-band-full mkt-band-demo">
      <div className="mkt-wrap mkt-section mkt-band-content">
        <div className="mkt-section-head mkt-section-head-center">
          <span className="mkt-label">Example output</span>
          <h2 className="mkt-h2">{DEMO_CASE_STUDY.title}</h2>
          <p className="mkt-sub mkt-demo-idea">
            Demo business: <strong>{DEMO_CASE_STUDY.idea}</strong>
          </p>
        </div>
        <div className="mkt-demo-board">
          <div className="mkt-demo-panel mkt-demo-panel-input">
            <h3>What you enter</h3>
            <ul className="mkt-demo-input-grid">
              {DEMO_CASE_STUDY.inputs.map((row) => (
                <li key={row.label} className="mkt-demo-tile">
                  <strong>{row.label}</strong>
                  <span>{row.value}</span>
                </li>
              ))}
            </ul>
          </div>
          <p className="mkt-demo-bridge" aria-hidden="true">
            <span className="mkt-demo-bridge-line" />
            IIDATECH produces
            <span className="mkt-demo-bridge-line" />
          </p>
          <div className="mkt-demo-panel mkt-demo-panel-output">
            <ul className="mkt-demo-output-grid">
              {DEMO_CASE_STUDY.outputs.map((row) => (
                <li key={row.label} className="mkt-demo-tile">
                  <strong>{row.label}</strong>
                  <span>{row.value}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="mkt-demo-footer">
          <p className="mkt-demo-dashboard-note">{DEMO_CASE_STUDY.dashboardNote}</p>
          <div className="mkt-demo-cta-row">
          <WorkspaceEntryLink href={DEMO_CASE_STUDY.demoHref} className="iid-btn iid-btn-primary">
            Open the live demo →
          </WorkspaceEntryLink>
          <Link href="/login?mode=register" className="iid-btn iid-btn-ghost">
            Analyze my business
          </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ProductStorySection() {
  return (
    <section id="product-story" className="mkt-wrap mkt-section mkt-section-story-compact">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">The story</span>
        <h2 className="mkt-h2">One idea → complete business intelligence</h2>
        <p className="mkt-sub">From a single input to research, plan, roadmap, and AI employees — in one linked project.</p>
      </div>
      <ol className="mkt-story-flow mkt-story-flow-compact">
        {PRODUCT_STORY.map((item, i) => (
          <li key={item.step} className="mkt-story-step">
            <span className="mkt-story-num">{i + 1}</span>
            <div>
              <strong>{item.step}</strong>
              <p>{item.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function ProductScreensSection() {
  const [expanded, setExpanded] = useState<(typeof PRODUCT_UI_SHOTS)[number] | null>(null);

  const closeLightbox = useCallback(() => setExpanded(null), []);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeLightbox();
    };
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener("keydown", onKey);
    };
  }, [expanded, closeLightbox]);

  return (
    <section id="product" className="mkt-wrap mkt-section">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">Inside IIDATECH</span>
        <h2 className="mkt-h2">Real product screens — not stock photos</h2>
        <p className="mkt-sub">What you see in the demo is what you get in your workspace. Tap any screen to expand.</p>
      </div>
      <div className="mkt-ui-shots">
        {PRODUCT_UI_SHOTS.map((shot) => (
          <figure key={shot.src} className="mkt-ui-shot">
            <button
              type="button"
              className="mkt-ui-shot-expand"
              onClick={() => setExpanded(shot)}
              aria-label={`Expand screenshot: ${shot.caption}`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={shot.src} alt="" loading="lazy" />
              <span className="mkt-ui-shot-zoom" aria-hidden="true">Expand</span>
            </button>
            <figcaption>{shot.caption}</figcaption>
          </figure>
        ))}
      </div>

      {expanded ? (
        <div
          className="mkt-ui-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label={expanded.caption}
          onClick={closeLightbox}
        >
          <div className="mkt-ui-lightbox-panel" onClick={(event) => event.stopPropagation()}>
            <button type="button" className="mkt-ui-lightbox-close" onClick={closeLightbox} aria-label="Close">
              ×
            </button>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="mkt-ui-lightbox-img" src={expanded.src} alt={expanded.alt} />
            <p className="mkt-ui-lightbox-caption">{expanded.caption}</p>
          </div>
        </div>
      ) : null}
    </section>
  );
}

export function ChatGptCompareSection() {
  return (
    <section id="vs-chatgpt" className="mkt-wrap mkt-section">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">Why not just ChatGPT?</span>
        <h2 className="mkt-h2">IIDATECH is a business workflow — not a chat thread</h2>
      </div>
      <div className="mkt-compare-grid">
        <article className="mkt-compare-card">
          <h3>ChatGPT</h3>
          <ul>
            {CHATGPT_COMPARE.chatgpt.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
        <article className="mkt-compare-card mkt-compare-card-highlight">
          <h3>IIDATECH</h3>
          <ul>
            {CHATGPT_COMPARE.iidatech.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}

export function TaylorExampleSection() {
  return (
    <section id="taylor" className="mkt-band mkt-band-full mkt-band-taylor">
      <div className="mkt-wrap mkt-section mkt-band-content">
        <div className="mkt-taylor-grid">
          <div className="mkt-section-head">
            <span className="mkt-label">AI employees</span>
            <h2 className="mkt-h2">What does Taylor actually do?</h2>
            <p className="mkt-sub">
              Give Taylor a concrete goal. Taylor researches, drafts, and queues work — you approve before anything external sends.
            </p>
          </div>
          <div className="mkt-taylor-example">
            <p className="mkt-taylor-goal">
              <strong>Goal:</strong> {TAYLOR_EXAMPLE.goal}
            </p>
            <ol>
              {TAYLOR_EXAMPLE.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <WorkspaceEntryLink href="/app/team" className="iid-btn iid-btn-primary">
              See Taylor in the demo →
            </WorkspaceEntryLink>
          </div>
        </div>
      </div>
    </section>
  );
}

export function EvidenceSection() {
  return (
    <section id="evidence" className="mkt-wrap mkt-section">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">Evidence</span>
        <h2 className="mkt-h2">Source → finding → what it means</h2>
        <p className="mkt-sub">Every serious report should show where conclusions come from — and what to do next.</p>
      </div>
      <article className="mkt-evidence-card">
        <p className="mkt-evidence-finding">{EVIDENCE_EXAMPLE.finding}</p>
        <dl className="mkt-evidence-meta">
          <div>
            <dt>Source</dt>
            <dd>{EVIDENCE_EXAMPLE.source}</dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{EVIDENCE_EXAMPLE.updated}</dd>
          </div>
        </dl>
        <p className="mkt-evidence-implication">
          <strong>What this means:</strong> {EVIDENCE_EXAMPLE.implication}
        </p>
      </article>
    </section>
  );
}

export function CreditsGuideSection({ signupCredits = 30 }: { signupCredits?: number }) {
  return (
    <section id="credits" className="mkt-wrap mkt-section">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">Credits</span>
        <h2 className="mkt-h2">What {signupCredits} free credits actually buy</h2>
        <p className="mkt-sub">No mystery numbers — approximate usage from the live credit catalog.</p>
      </div>
      <div className="mkt-credits-grid">
        {CREDIT_GUIDE.map((row) => (
          <div key={row.action} className="mkt-credit-row">
            <span>{row.action}</span>
            <strong>{row.credits} credits</strong>
          </div>
        ))}
      </div>
      <p className="mkt-credits-footnote mkt-sub">
        {signupCredits} credits ≈ up to {Math.floor(signupCredits / 5)} quick research runs, or a mix of research, plans, Mentor, and Employee OS tasks.
      </p>
    </section>
  );
}

export function CaseStudiesSection() {
  return (
    <section id="results" className="mkt-wrap mkt-section">
      <div className="mkt-section-head mkt-section-head-center">
        <span className="mkt-label">Early results</span>
        <h2 className="mkt-h2">Before → after (representative workflows)</h2>
        <p className="mkt-sub">We are publishing named case studies as customers approve them. These show the decision → action story today.</p>
      </div>
      <div className="mkt-case-grid">
        {CASE_STUDIES.map((study) => (
          <article key={study.title} className="mkt-case-card">
            <h3>{study.title}</h3>
            <p><strong>Before:</strong> {study.before}</p>
            <p><strong>After:</strong> {study.after}</p>
            <p className="mkt-case-note">{study.note}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
