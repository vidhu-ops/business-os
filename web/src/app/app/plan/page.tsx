"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ProjectPicker } from "@/components/ProjectPicker";
import { ExistingCompanyPlanForward } from "@/components/ExistingCompanyPlanForward";
import { ValidationUnderstanding } from "@/components/ValidationUnderstanding";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { useProjects } from "@/hooks/useProjects";

type CompanyMode = "new" | "existing" | null;
type PlanTab = "intake" | "output" | "validation" | "existing" | "gauge-plan";

function PlanContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const [companyMode, setCompanyMode] = useState<CompanyMode>(null);
  const [activeTab, setActiveTab] = useState<PlanTab>("intake");

  const [idea, setIdea] = useState("");
  const [industry, setIndustry] = useState("");
  const [country, setCountry] = useState("Global");
  const [areas, setAreas] = useState("");
  const [pastedResearch, setPastedResearch] = useState("");
  const [useResearch, setUseResearch] = useState(true);
  const [applicationMode, setApplicationMode] = useState(false);
  const [applicationPurpose, setApplicationPurpose] = useState("General market research");

  const [markdown, setMarkdown] = useState("");
  const [gaugeForwardMd, setGaugeForwardMd] = useState("");
  const [hasResearch, setHasResearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    api.me().then((u) => setIsDemo(Boolean(u.is_demo))).catch(() => setIsDemo(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api.getPlan(selectedId).then((data) => {
      setHasResearch(data.has_research);
      setCompanyMode((data.company_mode as CompanyMode) ?? null);
      const intake = data.intake || {};
      setIdea(String(intake.idea || ""));
      setIndustry(String(intake.industry || ""));
      setCountry(String(intake.country || "Global"));
      setAreas(String(intake.areas || ""));
      setPastedResearch(String(intake.pasted_research || ""));
      setUseResearch(Boolean(intake.use_research ?? true));
      setApplicationMode(Boolean(intake.application_mode));
      setApplicationPurpose(String(intake.application_purpose || "General market research"));
      const plan = data.plan || {};
      setMarkdown(String(plan.markdown || plan.report_markdown || ""));
      const gfp = data.gauge_forward_plan || {};
      setGaugeForwardMd(String(gfp.markdown || gfp.report_markdown || ""));
    }).catch(() => {
      setMarkdown("");
    });
  }, [selectedId]);

  async function pickMode(mode: CompanyMode) {
    if (!selectedId) return;
    setError("");
    try {
      await api.setPlanMode(selectedId, mode);
      setCompanyMode(mode);
      setActiveTab(mode === "existing" ? "existing" : "intake");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save company type");
    }
  }

  async function saveIntake() {
    if (!selectedId) return;
    await api.savePlanIntake(selectedId, {
      idea, industry, country, areas, pasted_research: pastedResearch,
      use_research: useResearch, application_mode: applicationMode, application_purpose: applicationPurpose,
    });
  }

  async function generatePlan() {
    if (!selectedId) return;
    setLoading(true);
    setError("");
    try {
      await saveIntake();
      const data = await api.runPlan(selectedId, useResearch);
      setMarkdown(String(data.markdown || data.report_markdown || ""));
      setActiveTab("output");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan generation failed");
    } finally {
      setLoading(false);
    }
  }

  const newTabs = [
    { id: "intake" as PlanTab, label: "Intake" },
    { id: "output" as PlanTab, label: "Plan Output" },
    { id: "validation" as PlanTab, label: "Reference" },
  ];
  const existingTabs = [
    { id: "existing" as PlanTab, label: "GAUGE plan forward" },
    { id: "output" as PlanTab, label: "Plan Output" },
    { id: "validation" as PlanTab, label: "Reference" },
  ];
  const demoTabs = [
    { id: "output" as PlanTab, label: "New company plan" },
    { id: "existing" as PlanTab, label: "GAUGE audit" },
    { id: "gauge-plan" as PlanTab, label: "GAUGE forward plan" },
    { id: "validation" as PlanTab, label: "Reference" },
  ];
  const tabs = isDemo ? demoTabs : companyMode === "existing" ? existingTabs : newTabs;

  useEffect(() => {
    if (isDemo) setActiveTab("output");
  }, [isDemo]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Business Plan Workspace</h1>
        <p className="mt-2 muted">
          {isDemo
            ? "Sample business plan workspace — view the completed GAUGE flow below. Sign up to build plans for your company."
            : "Build from your IIDATECH market research report, uploads, and notes — same flow as Streamlit."}
        </p>
      </div>

      {projects.length === 0 ? (
        <section className="iid-card">
          <p className="muted">{isDemo ? "No sample project available." : "No projects yet."}</p>
          {!isDemo && (
          <Link href="/app/projects" className="iid-btn iid-btn-primary mt-4 inline-flex">Create your first project</Link>
          )}
        </section>
      ) : (
        <>
          <section className="iid-card space-y-4">
            <ProjectPicker projects={projects} selectedId={selectedId} onChange={setSelectedId} />
          </section>

          {!companyMode && !isDemo ? (
            <section className="iid-card space-y-4">
              <h2 className="font-display text-lg font-bold">What are you planning?</h2>
              <p className="text-sm muted">Pick new company for a startup-style plan, or existing company for GAUGE audit and a forward operating plan.</p>
              <div className="flex flex-wrap gap-3">
                <button type="button" className="iid-btn iid-btn-primary" onClick={() => pickMode("new")}>Build plan for new company</button>
                <button type="button" className="iid-btn iid-btn-ghost" onClick={() => pickMode("existing")}>Build plan for existing company</button>
              </div>
            </section>
          ) : companyMode || isDemo ? (
            <>
              {!isDemo && (
              <button type="button" className="text-sm text-[var(--iid-blue)] hover:underline" onClick={() => pickMode(null)}>← Choose a different company type</button>
              )}

              <div className="flex flex-wrap gap-2 border-b border-[var(--iid-line)] pb-2">
                {tabs.map((t) => (
                  <button key={t.id} type="button" className={`px-3 py-1.5 text-xs font-semibold rounded-full ${activeTab === t.id ? "bg-[var(--iid-blue)] text-white" : "border border-[var(--iid-line)] text-[var(--iid-muted)]"}`} onClick={() => setActiveTab(t.id)}>{t.label}</button>
                ))}
              </div>

              {activeTab === "intake" && companyMode === "new" && !isDemo && (
                <section className="iid-card space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-3">
                      <label className="block text-sm font-semibold">Business idea, product, or opportunity</label>
                      <textarea className="iid-input min-h-[120px]" value={idea} onChange={(e) => setIdea(e.target.value)} />
                      <label className="block text-sm font-semibold">Paste research notes</label>
                      <textarea className="iid-input min-h-[140px]" value={pastedResearch} onChange={(e) => setPastedResearch(e.target.value)} />
                    </div>
                    <div className="space-y-3">
                      <label className="block text-sm muted">Business industry</label>
                      <input className="iid-input" value={industry} onChange={(e) => setIndustry(e.target.value)} />
                      <label className="block text-sm muted">Launch geography</label>
                      <input className="iid-input" value={country} onChange={(e) => setCountry(e.target.value)} />
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={useResearch} onChange={(e) => setUseResearch(e.target.checked)} className="accent-[var(--iid-blue)]" />
                        Use latest IIDATECH market research report
                      </label>
                      {!hasResearch && useResearch && (
                        <p className="text-sm text-amber-300">No matching research yet — <Link href="/app/research" className="underline">run Market Research</Link> first.</p>
                      )}
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={applicationMode} onChange={(e) => setApplicationMode(e.target.checked)} className="accent-[var(--iid-blue)]" />
                        This plan is for visa / MSME loan / funding application
                      </label>
                      {applicationMode && (
                        <input className="iid-input" value={applicationPurpose} onChange={(e) => setApplicationPurpose(e.target.value)} placeholder="Business plan purpose" />
                      )}
                    </div>
                  </div>
                  {error && <p className="text-sm text-red-400">{error}</p>}
                  <p className="text-xs muted">Each business plan build uses 5 credits (Growth plan: unlimited).</p>
                  <button type="button" className="iid-btn iid-btn-primary" onClick={generatePlan} disabled={loading}>{loading ? "Building agentic business plan…" : "Build Agentic Business Plan"}</button>
                </section>
              )}

              {activeTab === "output" && (
                <section className="iid-card iid-report-shell">
                  <h2 className="font-display text-xl font-bold">Readable plan</h2>
                  {markdown ? (
                    <div className="mt-4">
                      <ReportMarkdown markdown={markdown} title="IIDATECH business plan" subtitle={country} />
                    </div>
                  ) : (
                    <p className="muted mt-4">No plan yet — complete Intake and build your plan.</p>
                  )}
                </section>
              )}

              {activeTab === "gauge-plan" && isDemo && (
                <section className="iid-card iid-report-shell">
                  <h2 className="font-display text-xl font-bold">GAUGE forward plan</h2>
                  {gaugeForwardMd ? (
                    <div className="mt-4">
                      <ReportMarkdown markdown={gaugeForwardMd} title="GAUGE forward plan" subtitle="Acme CRM Pvt Ltd" />
                    </div>
                  ) : (
                    <p className="muted mt-4">No forward plan in sample.</p>
                  )}
                </section>
              )}

              {activeTab === "existing" && (companyMode === "existing" || isDemo) && selectedId && (
                <ExistingCompanyPlanForward
                  key={selectedId}
                  workspaceId={selectedId}
                  demoMode={isDemo}
                  onPlanReady={(md) => {
                    setMarkdown(md);
                    setActiveTab("output");
                  }}
                />
              )}

              {activeTab === "validation" && <ValidationUnderstanding />}
            </>
          ) : null}
        </>
      )}
    </div>
  );
}

export default function PlanPage() {
  return (
    <Suspense fallback={<p className="muted">Loading...</p>}>
      <PlanContent />
    </Suspense>
  );
}