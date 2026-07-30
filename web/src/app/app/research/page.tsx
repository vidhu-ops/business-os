"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { ProjectPicker } from "@/components/ProjectPicker";
import { useProjects } from "@/hooks/useProjects";
import { brandReportText, filterClientWarnings, sanitizeReportMarkdown } from "@/lib/reportBrand";
import { ReportMarkdown } from "@/components/ReportMarkdown";

type ResearchOption = { section_count: number; titles: string[] };
type TabId = "report";

function downloadFilename(topic: string) {
  const slug = (topic || "market").slice(0, 40).replace(/\s+/g, "_");
  return `IIDATECH_MarketReport_${slug}.md`;
}

function ResearchContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const [activeTab] = useState<TabId>("report");
  const [sectionCount, setSectionCount] = useState(8);
  const [options, setOptions] = useState<ResearchOption[]>([]);
  const [countries, setCountries] = useState<string[]>(["Global"]);
  const [researchReady, setResearchReady] = useState(true);
  const [setupHint, setSetupHint] = useState("");
  const [researchKey, setResearchKey] = useState("");
  const [savingKey, setSavingKey] = useState(false);

  const [idea, setIdea] = useState("");
  const [industry, setIndustry] = useState("");
  const [country, setCountry] = useState("Global");
  const [areas, setAreas] = useState("");

  const [scopeOk, setScopeOk] = useState(true);
  const [scopeIssues, setScopeIssues] = useState<string[]>([]);
  const [scopeSuggestions, setScopeSuggestions] = useState<string[]>([]);
  const [showScopeTips, setShowScopeTips] = useState(false);
  const [marketLabel, setMarketLabel] = useState("");

  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [showSections, setShowSections] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [savingIntake, setSavingIntake] = useState(false);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    api.me().then((u) => setIsDemo(Boolean(u.is_demo))).catch(() => setIsDemo(false));
  }, []);

  const refreshResearchOptions = useCallback((workspaceId?: string) => {
    api.researchOptions(workspaceId).then((data) => {
      setOptions(data.options);
      setCountries(data.countries?.length ? data.countries : ["Global"]);
      setResearchReady(data.research_ready !== false);
      setSetupHint(data.setup_hint || "");
    }).catch(() => setOptions([]));
  }, []);

  useEffect(() => {
    refreshResearchOptions(selectedId || undefined);
  }, [selectedId, refreshResearchOptions]);

  const loadWorkspace = useCallback(async (workspaceId: string) => {
    const data = await api.getResearch(workspaceId);
    const intake = data.intake;
    setIdea(String(intake.idea || ""));
    setIndustry(String(intake.industry || ""));
    setCountry(String(intake.country || "Global"));
    setAreas(String(intake.areas || ""));
    setScopeOk(intake.scope_ok);
    setScopeIssues(intake.scope_issues || []);
    setScopeSuggestions(intake.scope_suggestions || []);
    setMarketLabel(intake.market_label || "");

    const research = data.research || {};
    const full = (research.full_result as Record<string, unknown>) || null;
    if (full?.success) {
      setResult(full);
      if (typeof research.section_count === "number") setSectionCount(research.section_count);
    } else if (research.available) {
      setResult({
        success: true,
        topic: research.topic,
        section_count: research.section_count,
        report_markdown: research.report_markdown || research.markdown,
        warnings: research.warnings,
      });
      if (typeof research.section_count === "number") setSectionCount(research.section_count);
    } else {
      setResult(null);
    }
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    loadWorkspace(selectedId).catch(() => setResult(null));
  }, [selectedId, loadWorkspace]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!idea.trim() && !industry.trim()) return;
      api.previewScope(idea, industry, country, areas).then((data) => {
        const scope = data.scope || {};
        setScopeOk(Boolean(scope.ok ?? true));
        setScopeIssues((scope.issues as string[]) || []);
        setScopeSuggestions((scope.suggestions as string[]) || []);
        setMarketLabel(data.market_label || "");
      }).catch(() => undefined);
    }, 400);
    return () => clearTimeout(timer);
  }, [idea, industry, country, areas]);

  const selectedOption = options.find((o) => o.section_count === sectionCount);

  const markdown = useMemo(
    () => sanitizeReportMarkdown(String(result?.report_markdown || result?.markdown || "")),
    [result],
  );

  const clientWarnings = useMemo(
    () => filterClientWarnings((result?.warnings as string[]) || []),
    [result],
  );

  const showResult = isDemo
    ? Boolean(markdown)
    : Boolean(result?.success) &&
      String(result?.topic || "").trim() === String(idea || "").trim() &&
      Number(result?.section_count || 0) === Number(sectionCount);

  async function saveResearchKey() {
    if (!selectedId || !researchKey.trim()) return;
    setSavingKey(true);
    setError("");
    try {
      await api.setOs2Keys(selectedId, { perplexity: researchKey.trim() });
      setResearchKey("");
      refreshResearchOptions(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save research access key");
    } finally {
      setSavingKey(false);
    }
  }

  async function saveIntake() {
    if (!selectedId) return;
    setSavingIntake(true);
    try {
      const data = await api.updateIntake(selectedId, idea, industry, country, areas);
      const scope = data.scope || {};
      setScopeOk(Boolean(scope.ok ?? true));
      setScopeIssues((scope.issues as string[]) || []);
      setScopeSuggestions((scope.suggestions as string[]) || []);
    } finally {
      setSavingIntake(false);
    }
  }

  async function runResearch() {
    if (!selectedId) {
      setError("Create a project first.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await saveIntake();
      const data = await api.runResearch(selectedId, sectionCount, { idea, industry, country, areas });
      setResult(data);
      if (data.success === false) setError(String(data.error || "Report failed"));
      else await loadWorkspace(selectedId);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Report failed";
      setError(
        msg.includes("timed out")
          ? `${msg} Keep this tab open — IIDATECH reports can take several minutes to prepare.`
          : brandReportText(msg),
      );
    } finally {
      setLoading(false);
    }
  }

  function downloadReport() {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = downloadFilename(idea);
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Understand your market</h1>
        <p className="mt-2 muted">
          {isDemo
            ? "Sample completed market research — browse the report below. Sign up to run research on your own niche."
            : "Enter your niche, industry, and market. IIDATECH prepares a sourced report you can download and share."}
        </p>
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

            {!isDemo ? (
              <>
            <label className="block text-sm font-semibold">Topic / idea</label>
            <textarea
              className="iid-input min-h-[110px]"
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              placeholder="Product, category, buyer, or market question you want researched."
            />

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="block text-sm muted">Industry</label>
                <input className="iid-input mt-1" value={industry} onChange={(e) => setIndustry(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm muted">Country / market</label>
                <select className="iid-input mt-1" value={country} onChange={(e) => setCountry(e.target.value)}>
                  {countries.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm muted">Cities / metro areas (optional)</label>
              <input
                className="iid-input mt-1"
                value={areas}
                onChange={(e) => setAreas(e.target.value)}
                placeholder="e.g. Mumbai, Bangalore, Austin TX, Greater London"
              />
            </div>

            {!scopeOk && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
                <button type="button" className="text-sm font-semibold text-amber-200" onClick={() => setShowScopeTips((v) => !v)}>
                  Scope suggestions {showScopeTips ? "▾" : "▸"}
                </button>
                {showScopeTips && (
                  <div className="mt-3 space-y-2 text-sm text-amber-100/90">
                    {scopeIssues.map((issue) => (
                      <p key={issue}>• {issue}</p>
                    ))}
                    {scopeSuggestions.map((s) => (
                      <code key={s} className="block rounded bg-black/30 px-2 py-1 text-xs">{s}</code>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={saveIntake} disabled={savingIntake || !selectedId}>
              {savingIntake ? "Saving…" : "Save workspace inputs"}
            </button>
              </>
            ) : (
              <div className="rounded-lg border border-[var(--iid-line)] bg-black/20 p-4 text-sm">
                <p><strong>Sample topic:</strong> {idea}</p>
                <p className="mt-1 muted">{industry} · {country}</p>
              </div>
            )}
          </section>

          {activeTab === "report" && (
            <section className="iid-card space-y-4">
              <h2 className="font-display text-xl font-bold">IIDATECH market research report</h2>

              {!isDemo && (
              <>
              <label className="block text-sm font-semibold">Report depth</label>
              <div className="flex flex-wrap gap-2">
                {options.map((opt) => {
                  const preview = opt.titles.slice(0, 3).join(", ");
                  const suffix = opt.section_count > 3 ? "…" : "";
                  return (
                    <button
                      key={opt.section_count}
                      type="button"
                      className={`iid-btn text-left ${sectionCount === opt.section_count ? "iid-btn-primary" : "iid-btn-ghost"}`}
                      onClick={() => setSectionCount(opt.section_count)}
                    >
                      <span className="block font-semibold">{opt.section_count} sections</span>
                      <span className="block text-xs opacity-80">{preview}{suffix}</span>
                    </button>
                  );
                })}
              </div>

              <p className="text-sm muted">
                Boardroom- and funding-ready report with research, sizing, competitors, and analyst review.
                Market: <strong>{marketLabel || country}</strong>.
              </p>

              <button type="button" className="text-sm text-[var(--iid-blue)] hover:underline" onClick={() => setShowSections((v) => !v)}>
                {showSections ? "Hide" : "Show"} sections included
              </button>
              {showSections && selectedOption && (
                <ol className="list-decimal space-y-1 pl-5 text-sm muted">
                  {selectedOption.titles.map((title) => (
                    <li key={title}>{title}</li>
                  ))}
                </ol>
              )}

              {!researchReady && (
                <div className="space-y-3 rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-100">
                  <div>
                    <p className="font-semibold">Research service not available</p>
                    <p className="mt-2 text-amber-100/90">
                      {setupHint || "An administrator must enable research access in server settings."}
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                    <input
                      type="password"
                      className="iid-input flex-1"
                      value={researchKey}
                      onChange={(e) => setResearchKey(e.target.value)}
                      placeholder="Research access key"
                      autoComplete="off"
                    />
                    <button
                      type="button"
                      className="iid-btn iid-btn-primary shrink-0"
                      onClick={saveResearchKey}
                      disabled={savingKey || !researchKey.trim() || !selectedId}
                    >
                      {savingKey ? "Saving…" : "Save key"}
                    </button>
                  </div>
                </div>
              )}
              {!scopeOk && (
                <p className="text-sm text-amber-300">Narrow the topic in the fields above before generating.</p>
              )}
              {error && <p className="text-sm text-red-400">{error}</p>}

              {!isDemo && (
              <>
              <p className="text-xs muted">Each report run uses 5 credits (Growth plan: unlimited).</p>
              <div className="flex flex-wrap gap-3">
                <button
                  className="iid-btn iid-btn-primary"
                  type="button"
                  onClick={runResearch}
                  disabled={loading || !researchReady || !selectedId || !scopeOk || !idea.trim()}
                >
                  {loading ? `Preparing your ${sectionCount}-section report…` : "Generate report"}
                </button>
                {showResult && markdown && (
                  <button className="iid-btn iid-btn-ghost" type="button" onClick={downloadReport}>
                    Download report (Markdown)
                  </button>
                )}
              </div>
              </>
              )}
              {isDemo && showResult && markdown && (
                <button className="iid-btn iid-btn-ghost" type="button" onClick={downloadReport}>
                  Download sample report (Markdown)
                </button>
              )}
            </section>
          )}

          {activeTab === "report" && showResult && (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="iid-card"><p className="label">Sections</p><p className="value">{sectionCount}</p></div>
                <div className="iid-card"><p className="label">Prepared by</p><p className="value">IIDATECH</p></div>
              </div>

              {clientWarnings.map((warn, i) => (
                <p key={i} className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">{warn.slice(0, 400)}</p>
              ))}

              {markdown && (
                <article className="iid-card iid-report-shell">
                  <ReportMarkdown
                    markdown={markdown}
                    title="IIDATECH market research report"
                    subtitle={marketLabel || country}
                  />
                </article>
              )}
            </>
          )}

          {activeTab === "report" && result && !result.success && (
            <section className="iid-card">
              <p className="text-sm text-red-400">{brandReportText(String(result.error || "Report failed"))}</p>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default function ResearchPage() {
  return (
    <Suspense fallback={<p className="muted">Loading...</p>}>
      <ResearchContent />
    </Suspense>
  );
}
