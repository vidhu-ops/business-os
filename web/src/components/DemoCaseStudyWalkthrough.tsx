"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { IidaMascot } from "@/components/iida/IidaMascot";
import { api } from "@/lib/api";
import {
  DEMO_WALKTHROUGH_STEPS,
  getWalkthroughStepIndex,
  isWalkthroughDone,
  markWalkthroughDone,
  resetWalkthrough,
  saveWalkthroughStepIndex,
} from "@/lib/demo-walkthrough";

function stepRouteMatches(pathname: string, search: string, route: string): boolean {
  const [routePath, routeQuery] = route.split("?");
  if (pathname !== routePath) return false;
  if (!routeQuery) return true;
  const expected = new URLSearchParams(routeQuery);
  const actual = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  for (const [key, value] of expected.entries()) {
    if (actual.get(key) !== value) return false;
  }
  return true;
}

function DemoCaseStudyWalkthroughInner() {
  const router = useRouter();
  const pathname = usePathname() || "";
  const searchParams = useSearchParams();
  const search = searchParams?.toString() ? `?${searchParams.toString()}` : "";

  const [isDemo, setIsDemo] = useState(false);
  const [open, setOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    let timer: number | undefined;
    const restartGuided = searchParams?.get("guided") === "1";
    if (restartGuided) {
      resetWalkthrough();
      router.replace("/app/research?project=demo_readonly");
    }
    api
      .me()
      .then((user) => {
        const demo = Boolean(user.is_demo);
        setIsDemo(demo);
        if (!demo || isWalkthroughDone()) return;
        setStepIndex(restartGuided ? 0 : getWalkthroughStepIndex());
        timer = window.setTimeout(() => setOpen(true), 800);
      })
      .catch(() => setIsDemo(false));
    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [router, searchParams]);

  const step = DEMO_WALKTHROUGH_STEPS[stepIndex];

  const scrollToHighlight = useCallback(() => {
    if (!step?.highlight) return;
    const el = document.querySelector(step.highlight);
    if (!el) return;
    el.classList.add("demo-tour-highlight");
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => el.classList.remove("demo-tour-highlight"), 2400);
  }, [step]);

  useEffect(() => {
    if (!open || !isDemo || !step) return;
    if (!stepRouteMatches(pathname, search, step.route)) {
      router.push(step.route);
      return;
    }
    const timer = window.setTimeout(scrollToHighlight, 450);
    return () => window.clearTimeout(timer);
  }, [open, isDemo, step, pathname, search, router, scrollToHighlight]);

  const closeTour = (done = false) => {
    if (done) markWalkthroughDone();
    setOpen(false);
  };

  const onPrimary = () => {
    if (step.id === "finish") {
      markWalkthroughDone();
      router.push("/login?mode=register");
      setOpen(false);
      return;
    }
    const next = Math.min(stepIndex + 1, DEMO_WALKTHROUGH_STEPS.length - 1);
    setStepIndex(next);
    saveWalkthroughStepIndex(next);
    const nextStep = DEMO_WALKTHROUGH_STEPS[next];
    if (!stepRouteMatches(pathname, search, nextStep.route)) {
      router.push(nextStep.route);
    }
  };

  const onSkip = () => closeTour(true);

  if (!isDemo || !open || !step) return null;

  return (
    <aside className="demo-walkthrough" aria-live="polite">
      <div className="demo-walkthrough-card">
        <div className="demo-walkthrough-head">
          <IidaMascot mood="excited" size={48} className="demo-walkthrough-mascot" />
          <div>
            <p className="demo-walkthrough-kicker">
              Guided demo · {stepIndex + 1}/{DEMO_WALKTHROUGH_STEPS.length}
            </p>
            <h2 className="demo-walkthrough-title">{step.title}</h2>
          </div>
        </div>
        <p className="demo-walkthrough-body">{step.body}</p>
        <div className="demo-walkthrough-actions">
          <button type="button" className="iid-btn iid-btn-primary" onClick={onPrimary}>
            {step.primaryLabel}
          </button>
          <button type="button" className="iid-btn iid-btn-ghost" onClick={onSkip}>
            Skip tour
          </button>
        </div>
      </div>
    </aside>
  );
}

/** Floating guided case study for demo_readonly sessions. */
export function DemoCaseStudyWalkthrough() {
  return (
    <Suspense fallback={null}>
      <DemoCaseStudyWalkthroughInner />
    </Suspense>
  );
}

export function restartDemoWalkthrough() {
  resetWalkthrough();
  window.location.href = "/app/research?project=demo_readonly&guided=1";
}
