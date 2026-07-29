"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ProjectPicker } from "@/components/ProjectPicker";
import { ExistingCompanyPlanForward } from "@/components/ExistingCompanyPlanForward";
import { ValidationUnderstanding } from "@/components/ValidationUnderstanding";
import { useProjects } from "@/hooks/useProjects";

type CompanyMode = "new" | "existing" | null;
type PlanTab = "intake" | "output" | "validation" | "existing";

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
  const [hasResearch, setHasResearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    { id: "validation" as PlanTab, label: "Validation & Understanding" },
  ];
  const existingTabs = [
    { id: "existing" as PlanTab, label: "GAUGE plan forward" },
    { id: "output" as PlanTab, label: "Plan Output" },
    { id: "validation" as PlanTab, label: "Validation & Understanding" },
  ];
  const tabs = companyMode === "existing" ? existingTabs : newTabs;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Business Plan Workspace</h1>
        <p className="mt-2 muted">Build from your IIDATECH market research report, uploads, and notes — same flow as Streamlit.</p>
      </div>

      {projects.length === 0 ? (
        <section className="iid-card">
          <p className="muted">No projects yet.</p>
          <Link href="/app/projects" className="iid-btn iid-btn-primary mt-4 inline-flex">Create your first project</Link>
        </section>
      ) : (
        <>
          <section className="iid-card space-y-4">
            <ProjectPicker projects={projects} selectedId={selectedId} onChange={setSelectedId} />
          </section>

          {!companyMode ? (
            <section className="iid-card space-y-4">
              <h2 className="font-display text-lg font-bold">What are you planning?</h2>
              <p className="text-sm muted">Pick new company for a startup-style plan, or existing company for GAUGE audit and a forward operating plan.</p>
              <div className="flex flex-wrap gap-3">
                <button type="button" className="iid-btn iid-btn-primary" onClick={() => pickMode("new")}>Build plan for new company</button>
                <button type="button" className="iid-btn iid-btn-ghost" onClick={() => pickMode("existing")}>Build plan for existing company</button>
              </div>
            </section>
          ) : (
            <>
              <button type="button" className="text-sm text-[var(--iid-blue)] hover:underline" onClick={() => pickMode(null)}>← Choose a different company type</button>

              <div className="flex flex-wrap gap-2 border-b border-[var(--iid-line)] pb-2">
                {tabs.map((t) => (
                  <button key={t.id} type="button" className={`px-3 py-1.5 text-xs font-semibold rounded-full ${activeTab === t.id ? "bg-[var(--iid-blue)] text-white" : "border border-[var(--iid-line)] text-[var(--iid-muted)]"}`} onClick={() => setActiveTab(t.id)}>{t.label}</button>
                ))}
              </div>

              {activeTab === "intake" && companyMode === "new" && (
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
                  <button type="button" className="iid-btn iid-btn-primary" onClick={generatePlan} disabled={loading}>{loading ? "Building agentic business plan…" : "Build Agentic Business Plan"}</button>
                </section>
              )}

              {activeTab === "output" && (
                <section className="iid-card">
                  <h2 className="font-display text-xl font-bold">Readable plan</h2>
                  {markdown ? <pre className="mt-4 whitespace-pre-wrap text-sm leading-relaxed">{markdown}</pre> : <p className="muted mt-4">No plan yet — complete Intake and build your plan.</p>}
                </section>
              )}

              {activeTab === "existing" && companyMode === "existing" && selectedId && (
                <ExistingCompanyPlanForward
                  key={selectedId}
                  workspaceId={selectedId}
                  onPlanReady={(md) => {
                    setMarkdown(md);
                    setActiveTab("output");
                  }}
                />
              )}

              {activeTab === "validation" && <ValidationUnderstanding />}
            </>
          )}
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