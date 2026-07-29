"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { ProjectPicker } from "@/components/ProjectPicker";
import { useProjects } from "@/hooks/useProjects";

type ResearchOption = { section_count: number; titles: string[]; budget_usd: number };
type UsageLedgerRow = { phase?: string; cost_usd?: number };
type TabId = "report" | "closed";

function brandText(text: string) {
  return text
    .replaceAll("Perplexity Sonar Pro", "IIDATECH Research Engine")
    .replaceAll("Perplexity-powered", "IIDATECH-powered")
    .replaceAll("Perplexity", "IIDATECH")
    .replaceAll(/anthropic\/claude[^\s,)]+/gi, "IIDATECH engine")
    .replaceAll(/openai\/[^\s,)]+/gi, "IIDATECH engine")
    .replaceAll(/sonar-pro/gi, "research engine")
    .replaceAll(/sonar/gi, "research engine");
}

function downloadFilename(topic: string) {
  const slug = (topic || "market").slice(0, 40).replace(/\s+/g, "_");
  return `IIDATECH_MarketReport_${slug}.md`;
}

function ResearchContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const [activeTab, setActiveTab] = useState<TabId>("report");
  const [sectionCount, setSectionCount] = useState(8);
  const [options, setOptions] = useState<ResearchOption[]>([]);
  const [countries, setCountries] = useState<string[]>(["Global"]);
  const [researchReady, setResearchReady] = useState(true);
  const [setupHint, setSetupHint] = useState("");
  const [perplexityKey, setPerplexityKey] = useState("");
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
  const [showLedger, setShowLedger] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [savingIntake, setSavingIntake] = useState(false);

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
        estimated_cost_usd: research.estimated_cost_usd,
        within_budget: research.within_budget,
        usage_totals: research.usage_totals,
        usage_ledger: research.usage_ledger,
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
  const budget = selectedOption?.budget_usd ?? 0;

  const markdown = useMemo(
    () => brandText(String(result?.report_markdown || result?.markdown || "")),
    [result],
  );

  const showResult =
    Boolean(result?.success) &&
    String(result?.topic || "").trim() === String(idea || "").trim() &&
    Number(result?.section_count || 0) === Number(sectionCount);

  async function savePerplexityKey() {
    if (!selectedId || !perplexityKey.trim()) return;
    setSavingKey(true);
    setError("");
    try {
      await api.setOs2Keys(selectedId, { perplexity: perplexityKey.trim() });
      setPerplexityKey("");
      refreshResearchOptions(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save API key");
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
          ? `${msg} Stop dev servers and run .\\scripts\\dev_start.ps1 again so the API uses background report jobs. Reports take several minutes — keep this tab open.`
          : msg,
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

  const totals = (result?.usage_totals as Record<string, number>) || {};
  const ledger = (result?.usage_ledger as UsageLedgerRow[]) || [];
  const warnings = (result?.warnings as string[]) || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Understand your market</h1>
        <p className="mt-2 muted">Enter your niche, industry, and market. IIDATECH returns sourced sections you can download as markdown.</p>
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
          </section>

          <div className="flex gap-2 border-b border-[var(--iid-line)]">
            <button
              type="button"
              className={`px-4 py-2 text-sm font-semibold ${activeTab === "report" ? "border-b-2 border-[var(--iid-blue)] text-white" : "text-[var(--iid-muted)]"}`}
              onClick={() => setActiveTab("report")}
            >
              Market research report
            </button>
            <button
              type="button"
              className={`px-4 py-2 text-sm font-semibold ${activeTab === "closed" ? "border-b-2 border-[var(--iid-blue)] text-white" : "text-[var(--iid-muted)]"}`}
              onClick={() => setActiveTab("closed")}
            >
              Closed for public use
            </button>
          </div>

          {activeTab === "closed" ? (
            <section className="iid-card space-y-3">
              <h2 className="font-display text-xl font-bold">Closed for public use</h2>
              <p className="muted text-sm">
                The previous multi-pass research engine is retired from public use. Use the
                <strong> Market research report </strong>
                tab (IIDATECH, 3/8/16/25 sections).
              </p>
            </section>
          ) : (
            <section className="iid-card space-y-4">
              <h2 className="font-display text-xl font-bold">Market research report</h2>

              <label className="block text-sm font-semibold">Report depth (sections)</label>
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
                Boardroom- and funding-ready report with research, sizing, competitors, and analyst review ({sectionCount} sections).
                Budget cap <strong>${budget.toFixed(2)}</strong>. Market: <strong>{marketLabel || country}</strong>.
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
                    <p className="font-semibold">Perplexity API key required</p>
                    <p className="mt-2 text-amber-100/90">
                      {setupHint ||
                        "Paste your key below for this session, or add PERPLEXITY_API_KEY to the project .env file and restart the API."}
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                    <input
                      type="password"
                      className="iid-input flex-1"
                      value={perplexityKey}
                      onChange={(e) => setPerplexityKey(e.target.value)}
                      placeholder="pplx-..."
                      autoComplete="off"
                    />
                    <button
                      type="button"
                      className="iid-btn iid-btn-primary shrink-0"
                      onClick={savePerplexityKey}
                      disabled={savingKey || !perplexityKey.trim() || !selectedId}
                    >
                      {savingKey ? "Saving…" : "Save key"}
                    </button>
                  </div>
                  <p className="text-xs text-amber-100/70">
                    Local: edit <code className="rounded bg-black/30 px-1">.env</code> in the repo root. Render: add{" "}
                    <code className="rounded bg-black/30 px-1">PERPLEXITY_API_KEY</code> in Environment.
                  </p>
                </div>
              )}
              {!scopeOk && (
                <p className="text-sm text-amber-300">Narrow the topic in the fields above before generating.</p>
              )}
              {error && <p className="text-sm text-red-400">{error}</p>}

              <div className="flex flex-wrap gap-3">
                <button
                  className="iid-btn iid-btn-primary"
                  type="button"
                  onClick={runResearch}
                  disabled={loading || !researchReady || !selectedId || !scopeOk || !idea.trim()}
                >
                  {loading ? `Building ${sectionCount}-section report — this can take several minutes…` : "Generate report"}
                </button>
                {showResult && markdown && (
                  <button className="iid-btn iid-btn-ghost" type="button" onClick={downloadReport}>
                    Download report (Markdown)
                  </button>
                )}
              </div>
            </section>
          )}

          {activeTab === "report" && showResult && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <div className="iid-card"><p className="label">Sections</p><p className="value">{sectionCount}</p></div>
                <div className="iid-card"><p className="label">Est. cost</p><p className="value">${Number(result?.estimated_cost_usd || 0).toFixed(3)}</p></div>
                <div className="iid-card"><p className="label">Budget cap</p><p className="value">${budget.toFixed(2)}</p></div>
                <div className="iid-card"><p className="label">Within budget</p><p className="value">{result?.within_budget === false ? "No" : "Yes"}</p></div>
              </div>

              {totals.calls ? (
                <p className="text-sm muted">{totals.calls} research passes completed</p>
              ) : null}

              {ledger.length > 0 && (
                <section className="iid-card">
                  <button type="button" className="font-semibold" onClick={() => setShowLedger((v) => !v)}>
                    Cost by pass {showLedger ? "▾" : "▸"}
                  </button>
                  {showLedger && (
                    <ul className="mt-3 space-y-1 text-sm muted">
                      {ledger.map((row, i) => (
                        <li key={i}><strong>{row.phase}</strong>: ${Number(row.cost_usd || 0).toFixed(4)}</li>
                      ))}
                    </ul>
                  )}
                </section>
              )}

              {warnings.map((warn, i) => (
                <p key={i} className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">{warn.slice(0, 400)}</p>
              ))}

              {markdown && (
                <article className="iid-card prose-report">
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed">{markdown}</pre>
                </article>
              )}
            </>
          )}

          {activeTab === "report" && result && !result.success && (
            <section className="iid-card">
              <p className="text-sm text-red-400">{String(result.error || "Report failed")}</p>
              {Array.isArray(result.traces) && (
                <pre className="mt-3 max-h-64 overflow-auto text-xs">{JSON.stringify(result.traces, null, 2)}</pre>
              )}
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