"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

type BizType = { id: string; label: string };
type GaugeChecklists = Record<string, Record<string, string[]>>;
type CheckEntry = { checked: boolean; value: string };

const SCALARS = [
  "company_name", "website", "geography", "industry", "currency", "plan_purpose", "public_links", "description",
  "monthly_revenue", "monthly_costs", "active_customers", "churn_pct", "months_in_operation", "team_size",
  "competitors", "gauge_notes", "growth_goal", "target_revenue_y3", "funding_needed",
  "biggest_bottleneck", "priority_12_months", "success_12_months", "willing_to_invest", "stop_doing",
  "why_customers_choose", "why_customers_leave", "competitive_threat",
] as const;

type Props = {
  workspaceId: string;
  onPlanReady?: (markdown: string) => void;
};

function statusEmoji(status: string) {
  return status === "strong" ? "🟢" : status === "watch" ? "🟡" : status === "risk" ? "🔴" : "⚪";
}

export function ExistingCompanyPlanForward({ workspaceId, onPlanReady }: Props) {
  const [step, setStep] = useState(1);
  const [types, setTypes] = useState<BizType[]>([]);
  const [checklists, setChecklists] = useState<GaugeChecklists>({});
  const [purposes, setPurposes] = useState<string[]>([]);
  const [gaugeType, setGaugeType] = useState("other");
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [checkState, setCheckState] = useState<Record<string, Record<string, CheckEntry[]>>>({});
  const [planForward, setPlanForward] = useState<Record<string, string>>({});
  const [audit, setAudit] = useState<Record<string, unknown> | null>(null);
  const [planMd, setPlanMd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const mergedScalars = useCallback(() => {
    const out: Record<string, string> = {};
    SCALARS.forEach((k) => { out[k] = planForward[k] || draft[k] || ""; });
    return out;
  }, [draft, planForward]);

  const persist = useCallback(async (nextStep: number, extra: Record<string, unknown> = {}) => {
    const body = {
      step: nextStep,
      gauge_type: gaugeType,
      checklists: checkState,
      plan_forward: { ...planForward, ...mergedScalars() },
      ...mergedScalars(),
      ...extra,
    };
    await api.saveGaugeDraft(workspaceId, body);
  }, [workspaceId, gaugeType, checkState, planForward, mergedScalars]);

  useEffect(() => {
    let cancelled = false;
    api.gaugeMetadata().then((m) => {
      if (cancelled) return;
      setTypes((m.business_types as BizType[]) || []);
      setChecklists((m.checklists as GaugeChecklists) || {});
      setPurposes((m.plan_purpose_options as string[]) || []);
    });
    api.getGauge(workspaceId).then((g) => {
      if (cancelled) return;
      const d = g.draft || {};
      setStep(Number(g.step || d.step || 1));
      setGaugeType(String(d.gauge_type || "other"));
      setCheckState((d.checklists as typeof checkState) || {});
      const pf = (d.plan_forward as Record<string, string>) || {};
      setPlanForward(pf);
      const scalars: Record<string, string> = {};
      SCALARS.forEach((k) => { scalars[k] = String(pf[k] || d[k] || ""); });
      setDraft(scalars);
      setAudit(g.audit || null);
      setPlanMd("");
    }).catch(() => {
      if (!cancelled) {
        setStep(1);
        setAudit(null);
      }
    });
    return () => { cancelled = true; };
  }, [workspaceId]);

  async function resetReport() {
    setLoading(true);
    setError("");
    try {
      await api.resetGauge(workspaceId);
      setStep(1);
      setGaugeType("other");
      setDraft({});
      setPlanForward({});
      setCheckState({});
      setAudit(null);
      setPlanMd("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reset GAUGE report");
    } finally {
      setLoading(false);
    }
  }

  async function go(next: number) {
    setError("");
    try {
      await persist(next);
      setStep(next);
      if (next < 5) setAudit(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    }
  }

  async function runAudit() {
    setLoading(true);
    setError("");
    try {
      await persist(5);
      const data = await api.runGaugeAudit(workspaceId);
      setAudit(data.audit);
      setStep(5);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Audit failed");
    } finally {
      setLoading(false);
    }
  }

  async function buildPlan() {
    setLoading(true);
    setError("");
    try {
      const data = await api.buildGaugePlan(workspaceId);
      const md = String(data.markdown || data.report_markdown || "");
      setPlanMd(md);
      onPlanReady?.(md);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Plan build failed");
    } finally {
      setLoading(false);
    }
  }

  const checklist = checklists[gaugeType] || checklists.other || {};
  const entries = checkState[gaugeType] || {};

  function setCheck(category: string, index: number, patch: Partial<CheckEntry>) {
    setCheckState((prev) => {
      const cat = [...(prev[gaugeType]?.[category] || [])];
      while (cat.length <= index) cat.push({ checked: false, value: "" });
      cat[index] = { ...cat[index], ...patch };
      return { ...prev, [gaugeType]: { ...(prev[gaugeType] || {}), [category]: cat } };
    });
  }

  function pf(key: string) {
    return planForward[key] || draft[key] || "";
  }

  function setPf(key: string, value: string) {
    setPlanForward((p) => ({ ...p, [key]: value }));
    setDraft((d) => ({ ...d, [key]: value }));
  }

  const steps = ["Business", "Checklist", "Data", "Forward", "Report"];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm muted">Run the GAUGE health audit on your real numbers, then build a forward-looking business plan.</p>
        <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={loading} onClick={resetReport}>
          Start new GAUGE report
        </button>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        {steps.map((label, i) => (
          <span key={label} className={`px-2 py-1 rounded-full border ${step === i + 1 ? "border-[var(--iid-blue)] text-white bg-[var(--iid-blue)]" : "border-[var(--iid-line)] muted"}`}>
            {step > i + 1 ? "✓" : step === i + 1 ? "●" : "○"} {i + 1}. {label}
          </span>
        ))}
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {step === 1 && (
        <section className="iid-card space-y-4">
          <h3 className="font-semibold">Step 1 — What kind of business is this?</h3>
          <div className="space-y-2">
            {types.map((t) => (
              <label key={t.id} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="radio" name="gauge_type" checked={gaugeType === t.id} onChange={() => setGaugeType(t.id)} className="accent-[var(--iid-blue)]" />
                {t.label}
              </label>
            ))}
          </div>
          <button type="button" className="iid-btn iid-btn-primary" onClick={() => go(2)}>Next: Checklist →</button>
        </section>
      )}
      {step === 2 && (
        <section className="iid-card space-y-4">
          <h3 className="font-semibold">Step 2 — Tick what&apos;s actually in place</h3>
          <p className="text-sm muted">When you tick a box, add the actual number if you have it — that feeds the audit directly.</p>
          {Object.entries(checklist).map(([category, items]) => (
            <details key={category} open className="rounded-lg border border-[var(--iid-line)] p-3">
              <summary className="font-semibold text-sm cursor-pointer">{category}</summary>
              <div className="mt-2 space-y-2">
                {items.map((item, idx) => {
                  const row = entries[category]?.[idx] || { checked: false, value: "" };
                  return (
                    <div key={idx}>
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={row.checked} onChange={(e) => setCheck(category, idx, { checked: e.target.checked })} className="accent-[var(--iid-blue)]" />
                        {item}
                      </label>
                      {row.checked && (
                        <input className="iid-input mt-1 text-sm" placeholder="Value for this item (e.g. 4% churn, 200000 MRR)" value={row.value} onChange={(e) => setCheck(category, idx, { value: e.target.value })} />
                      )}
                    </div>
                  );
                })}
              </div>
            </details>
          ))}
          <div className="flex gap-2">
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(1)}>← Back</button>
            <button type="button" className="iid-btn iid-btn-primary" onClick={() => go(3)}>Next: Operating data →</button>
          </div>
        </section>
      )}
      {step === 3 && (
        <section className="iid-card space-y-3">
          <h3 className="font-semibold">Step 3 — Operating numbers and identity</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {[
              ["company_name", "Company name"],
              ["website", "Website"],
              ["geography", "Primary market / geography"],
              ["industry", "Industry (optional)"],
              ["monthly_revenue", "Monthly revenue"],
              ["monthly_costs", "Monthly costs"],
              ["active_customers", "Active customers"],
              ["churn_pct", "Monthly churn %"],
              ["months_in_operation", "Months in operation"],
              ["team_size", "Team size"],
            ].map(([key, label]) => (
              <label key={key} className="block text-sm">
                <span className="muted">{label}</span>
                <input className="iid-input mt-1" value={draft[key] || ""} onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.value }))} />
              </label>
            ))}
            <label className="block text-sm md:col-span-2">
              <span className="muted">Public links (LinkedIn, Crunchbase...)</span>
              <input className="iid-input mt-1" value={draft.public_links || ""} onChange={(e) => setDraft((d) => ({ ...d, public_links: e.target.value }))} />
            </label>
            <label className="block text-sm">
              <span className="muted">Currency</span>
              <select className="iid-input mt-1" value={draft.currency || "USD"} onChange={(e) => setDraft((d) => ({ ...d, currency: e.target.value }))}>
                {["USD", "INR", "EUR", "GBP", "AUD", "CAD", "SGD", "AED"].map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <label className="block text-sm">
              <span className="muted">Plan purpose</span>
              <select className="iid-input mt-1" value={draft.plan_purpose || purposes[0] || ""} onChange={(e) => setDraft((d) => ({ ...d, plan_purpose: e.target.value }))}>
                {purposes.map((p) => <option key={p}>{p}</option>)}
              </select>
            </label>
          </div>
          <label className="block text-sm">
            <span className="muted">What does the business do today?</span>
            <textarea className="iid-input mt-1 min-h-[80px]" value={draft.description || ""} onChange={(e) => setDraft((d) => ({ ...d, description: e.target.value }))} />
          </label>
          <label className="block text-sm">
            <span className="muted">Main competitors (comma separated)</span>
            <input className="iid-input mt-1" value={draft.competitors || ""} onChange={(e) => setDraft((d) => ({ ...d, competitors: e.target.value }))} />
          </label>
          <label className="block text-sm">
            <span className="muted">Paste P&L, reports, or notes</span>
            <textarea className="iid-input mt-1 min-h-[80px]" value={draft.gauge_notes || ""} onChange={(e) => setDraft((d) => ({ ...d, gauge_notes: e.target.value }))} />
          </label>
          <div className="flex gap-2">
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(2)}>← Back</button>
            <button type="button" className="iid-btn iid-btn-primary" onClick={() => go(4)}>Next: Forward plan questions →</button>
          </div>
        </section>
      )}
      {step === 4 && (
        <section className="iid-card space-y-3">
          <h3 className="font-semibold">Step 4 — Where you want to go</h3>
          <p className="text-sm muted">These answers shape the forward plan and plain-language guidance.</p>
          {[
            ["biggest_bottleneck", "Biggest bottleneck right now"],
            ["priority_12_months", "#1 priority for the next 12 months"],
            ["success_12_months", "What does success look like in 12 months?"],
            ["willing_to_invest", "Time/money you can invest in the next 6 months"],
            ["stop_doing", "What you would stop doing to hit the goal"],
            ["why_customers_choose", "Why customers choose you today"],
            ["why_customers_leave", "Why customers leave or say no"],
            ["competitive_threat", "Biggest competitive threat or market shift"],
          ].map(([key, label]) => (
            <label key={key} className="block text-sm">
              <span className="muted">{label}</span>
              <textarea className="iid-input mt-1 min-h-[60px]" value={pf(key)} onChange={(e) => setPf(key, e.target.value)} />
            </label>
          ))}
          <label className="block text-sm">
            <span className="muted">Growth goal (12-24 months)</span>
            <input className="iid-input mt-1" value={draft.growth_goal || ""} onChange={(e) => setDraft((d) => ({ ...d, growth_goal: e.target.value }))} />
          </label>
          <label className="block text-sm">
            <span className="muted">Target revenue — Year 3</span>
            <input className="iid-input mt-1" value={draft.target_revenue_y3 || ""} onChange={(e) => setDraft((d) => ({ ...d, target_revenue_y3: e.target.value }))} />
          </label>
          <label className="block text-sm">
            <span className="muted">Funding needed (if any)</span>
            <input className="iid-input mt-1" value={draft.funding_needed || ""} onChange={(e) => setDraft((d) => ({ ...d, funding_needed: e.target.value }))} />
          </label>
          <div className="flex gap-2">
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(3)}>← Back</button>
            <button type="button" className="iid-btn iid-btn-primary" disabled={loading} onClick={runAudit}>{loading ? "Running GAUGE…" : "Run GAUGE audit →"}</button>
          </div>
        </section>
      )}
      {step >= 5 && audit && (
        <section className="iid-card space-y-4">
          <h3 className="font-semibold">GAUGE audit report</h3>
          <p className="text-lg">Overall: <strong>{String(audit.overall_score)}/100</strong> — {String(audit.overall_label)}</p>
          <p className="text-sm">{String(audit.overall_summary || "")}</p>
          <div className="rounded-lg border border-[var(--iid-blue)]/40 p-3 text-sm">{String(audit.plain_english_read || "")}</div>
          {Array.isArray(audit.focus_areas) && (audit.focus_areas as string[]).length > 0 && (
            <div>
              <h4 className="font-semibold text-sm">What to focus on next</h4>
              <ul className="text-sm list-disc ml-5">{(audit.focus_areas as string[]).map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          )}
          <div className="grid gap-3 md:grid-cols-3">
            {((audit.categories as Array<Record<string, unknown>>) || []).map((cat) => (
              <div key={String(cat.name)} className="rounded-lg border border-[var(--iid-line)] p-3 text-sm">
                <p>{statusEmoji(String(cat.status))} <strong>{String(cat.name)}</strong> — {String(cat.score)}/100</p>
                <p className="muted text-xs mt-1">{String(cat.summary || "")}</p>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="iid-btn iid-btn-primary" disabled={loading} onClick={buildPlan}>{loading ? "Building plan…" : "Build forward business plan from this audit"}</button>
            <button type="button" className="iid-btn iid-btn-ghost" onClick={runAudit}>Re-run GAUGE audit</button>
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(1)}>← Edit business type</button>
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(2)}>← Edit checklist</button>
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(3)}>← Edit operating data</button>
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => go(4)}>← Edit forward questions</button>
          </div>
          {planMd && (
            <div>
              <h4 className="font-semibold mt-4">Forward business plan</h4>
              <pre className="mt-2 whitespace-pre-wrap text-sm leading-relaxed max-h-96 overflow-y-auto rounded-lg border border-[var(--iid-line)] p-4">{planMd}</pre>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
