"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type BizType = { id: string; label: string };

type StageOption = { id: string; label: string };

type IndustryPosition = {
  industry_label?: string;
  geography?: string;
  standing_tier?: string;
  percentile_estimate?: string;
  standing_summary?: string;
  vs_industry?: Array<{
    dimension?: string;
    your_read?: string;
    industry_typical?: string;
    standing?: string;
  }>;
  industry_gaps?: string[];
  momentum?: string;
};

type MiniDraft = {
  company_name: string;
  geography: string;
  gauge_type: string;
  industry_vertical: string;
  industry: string;
  target_customer: string;
  business_stage: string;
  years_operating: string;
  revenue_model: string;
  competitors: string;
  differentiation: string;
  biggest_challenge: string;
  growth_goal_12m: string;
  website: string;
  linkedin_url: string;
  instagram_url: string;
  other_urls: string;
  description: string;
  monthly_revenue: string;
  active_customers: string;
  team_size: string;
  currency: string;
};

const EMPTY: MiniDraft = {
  company_name: "",
  geography: "",
  gauge_type: "other",
  industry_vertical: "",
  industry: "",
  target_customer: "",
  business_stage: "",
  years_operating: "",
  revenue_model: "",
  competitors: "",
  differentiation: "",
  biggest_challenge: "",
  growth_goal_12m: "",
  website: "",
  linkedin_url: "",
  instagram_url: "",
  other_urls: "",
  description: "",
  monthly_revenue: "",
  active_customers: "",
  team_size: "",
  currency: "USD",
};

const DEFAULT_STAGES: StageOption[] = [
  { id: "pre_revenue", label: "Pre-revenue / validating" },
  { id: "early", label: "Early revenue" },
  { id: "growing", label: "Growing" },
  { id: "scaling", label: "Scaling" },
  { id: "mature", label: "Mature / established" },
];

const DEFAULT_INDUSTRY_VERTICALS: StageOption[] = [
  { id: "b2b_saas", label: "B2B SaaS / Software" },
  { id: "ecommerce", label: "E-commerce / D2C" },
  { id: "fintech", label: "Fintech / Financial services" },
  { id: "healthcare", label: "Healthcare / Clinics" },
  { id: "edtech", label: "EdTech / Training" },
  { id: "agency", label: "Agency / Professional services" },
  { id: "retail", label: "Retail / Brick & mortar" },
  { id: "food_hospitality", label: "Food & hospitality" },
  { id: "logistics", label: "Logistics / Operations" },
  { id: "manufacturing", label: "Manufacturing / Industrial" },
  { id: "other", label: "Other / describe below" },
];

const DEFAULT_REVENUE_MODELS: StageOption[] = [
  { id: "subscription", label: "Subscription / SaaS" },
  { id: "transaction", label: "Transaction / marketplace" },
  { id: "services", label: "Services / project fees" },
  { id: "product", label: "Product / D2C sales" },
  { id: "hybrid", label: "Hybrid" },
  { id: "other", label: "Other" },
];

function statusEmoji(status: string) {
  const s = status.toLowerCase();
  if (s === "strong") return "🟢";
  if (s === "watch") return "🟡";
  if (s === "risk") return "🔴";
  return "⚪";
}

function standingLabel(standing?: string) {
  const s = (standing || "inline").toLowerCase();
  if (s === "above") return { text: "Above peers", className: "mini-gauge-standing-above" };
  if (s === "below") return { text: "Below peers", className: "mini-gauge-standing-below" };
  return { text: "In line", className: "mini-gauge-standing-inline" };
}

function IndustryStandingBlock({
  position,
  industryFallback,
}: {
  position: IndustryPosition;
  industryFallback?: string;
}) {
  const industry = position.industry_label || industryFallback || "your industry";
  const rows = position.vs_industry || [];
  const gaps = position.industry_gaps || [];

  return (
    <section className="mini-gauge-industry-block space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="font-semibold text-base">Where you stand in {industry}</h4>
          {position.geography ? <p className="text-xs muted mt-0.5">Market: {position.geography}</p> : null}
        </div>
        {position.standing_tier ? (
          <span className="mini-gauge-tier-pill">{position.standing_tier}</span>
        ) : null}
      </div>

      {position.percentile_estimate ? (
        <p className="text-sm mini-gauge-percentile">{position.percentile_estimate}</p>
      ) : null}

      {position.standing_summary ? (
        <p className="text-sm leading-relaxed">{position.standing_summary}</p>
      ) : null}

      {rows.length > 0 && (
        <div className="mini-gauge-vs-table">
          <div className="mini-gauge-vs-head">
            <span>Dimension</span>
            <span>Your read</span>
            <span>Typical in industry</span>
            <span>Standing</span>
          </div>
          {rows.map((row, i) => {
            const badge = standingLabel(row.standing);
            return (
              <div key={i} className="mini-gauge-vs-row">
                <strong>{row.dimension}</strong>
                <span>{row.your_read}</span>
                <span className="muted">{row.industry_typical}</span>
                <span className={`mini-gauge-standing-pill ${badge.className}`}>{badge.text}</span>
              </div>
            );
          })}
        </div>
      )}

      {gaps.length > 0 && (
        <div>
          <h5 className="font-semibold text-sm mb-2">Gaps vs typical {industry} players</h5>
          <ul className="text-sm space-y-1.5 list-disc ml-5">
            {gaps.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        </div>
      )}

      {position.momentum ? (
        <p className="text-xs muted">Momentum signal: {position.momentum}</p>
      ) : null}
    </section>
  );
}

function field(
  label: string,
  value: string,
  onChange: (v: string) => void,
  opts?: { placeholder?: string; type?: string },
) {
  return (
    <label className="block space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      <input
        className="iid-input w-full"
        type={opts?.type || "text"}
        value={value}
        placeholder={opts?.placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

export function MiniGaugePanel({ demoMode = false }: { demoMode?: boolean }) {
  const [draft, setDraft] = useState<MiniDraft>(EMPTY);
  const [types, setTypes] = useState<BizType[]>([]);
  const [stages, setStages] = useState<StageOption[]>(DEFAULT_STAGES);
  const [revenueModels, setRevenueModels] = useState<StageOption[]>(DEFAULT_REVENUE_MODELS);
  const [industryVerticals, setIndustryVerticals] = useState<StageOption[]>(DEFAULT_INDUSTRY_VERTICALS);
  const [audit, setAudit] = useState<Record<string, unknown> | null>(null);
  const [urlsFetched, setUrlsFetched] = useState<Array<{ label?: string; url?: string; fetched?: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [fullAuditAvailable, setFullAuditAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [meta, state] = await Promise.all([api.miniGaugeMetadata(), api.getMiniGauge()]);
        if (cancelled) return;
        const biz = (meta.business_types as BizType[]) || [];
        setTypes(biz);
        const metaStages = (meta.business_stages as StageOption[]) || [];
        const metaModels = (meta.revenue_models as StageOption[]) || [];
        if (metaStages.length) setStages(metaStages);
        if (metaModels.length) setRevenueModels(metaModels);
        const metaIndustries = (meta.industry_verticals as StageOption[]) || [];
        if (metaIndustries.length) setIndustryVerticals(metaIndustries);
        const incoming = (state.draft || {}) as Partial<MiniDraft>;
        setDraft({
          ...EMPTY,
          ...incoming,
          gauge_type: String(incoming.gauge_type || "other"),
          industry_vertical: String(incoming.industry_vertical || ""),
        });
        setAudit(state.audit);
        const savedFetched = (state.urls_fetched as Array<{ label?: string; url?: string; fetched?: string }>) || [];
        if (savedFetched.length) {
          setUrlsFetched(savedFetched);
        } else if (state.audit && Array.isArray((state.audit as Record<string, unknown>)._urls_fetched)) {
          setUrlsFetched((state.audit as Record<string, unknown>)._urls_fetched as Array<{ label?: string; url?: string; fetched?: string }>);
        }
        const st = state.status || state.full_audit_status;
        if (st && typeof st.free_audit_available === "boolean") {
          setFullAuditAvailable(st.free_audit_available);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load Mini Gauge");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const set = (key: keyof MiniDraft, value: string) => {
    setDraft((d) => ({ ...d, [key]: value }));
  };

  const canRun = useMemo(() => {
    const hasIndustry =
      Boolean(draft.industry_vertical && draft.industry_vertical !== "other") ||
      (draft.industry_vertical === "other" && Boolean(draft.industry.trim())) ||
      Boolean(draft.industry.trim());
    return Boolean(draft.company_name.trim() && draft.geography.trim() && hasIndustry);
  }, [draft.company_name, draft.geography, draft.industry, draft.industry_vertical]);

  function setIndustryVertical(verticalId: string) {
    const match = industryVerticals.find((v) => v.id === verticalId);
    setDraft((d) => ({
      ...d,
      industry_vertical: verticalId,
      industry: verticalId && verticalId !== "other" ? match?.label || d.industry : d.industry,
    }));
  }

  async function saveQuiet(next: MiniDraft) {
    try {
      await api.saveMiniGauge(next as unknown as Record<string, unknown>);
    } catch {
      /* ignore autosave failures while typing */
    }
  }

  async function run() {
    if (demoMode) {
      setError("Demo is read-only. Sign up to run Mini Gauge on your company.");
      return;
    }
    setRunning(true);
    setError("");
    try {
      await api.saveMiniGauge(draft as unknown as Record<string, unknown>);
      const result = await api.runMiniGauge(draft as unknown as Record<string, unknown>);
      setAudit(result.audit);
      setUrlsFetched(result.urls_fetched || []);
      if (result.full_audit_status) {
        setFullAuditAvailable(Boolean(result.full_audit_status.free_audit_available));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mini Gauge failed");
    } finally {
      setRunning(false);
    }
  }

  async function reset() {
    if (demoMode) return;
    setRunning(true);
    setError("");
    try {
      await api.resetMiniGauge();
      setDraft(EMPTY);
      setAudit(null);
      setUrlsFetched([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return <p className="muted text-sm">Loading Mini Gauge…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm muted max-w-2xl">
            Quick company pulse: basics, a few positioning questions, and public links (website, LinkedIn, Instagram).
            We research what we can and benchmark you against competitors in your industry. Full GAUGE adds checklist depth and a forward plan.
          </p>
        </div>
        <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={running || demoMode} onClick={reset}>
          Start over
        </button>
      </div>

      {error && (
        <section className="iid-card border border-red-500/40">
          <p className="text-sm text-red-400">{error}</p>
        </section>
      )}

      <section className="iid-card space-y-4">
        <h2 className="font-semibold text-lg">Company basics</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {field("Company name *", draft.company_name, (v) => set("company_name", v), {
            placeholder: "Acme Labs",
          })}
          {field("Primary market / geography *", draft.geography, (v) => set("geography", v), {
            placeholder: "India · Mumbai / US · Remote",
          })}
          <label className="block space-y-1 text-sm">
            <span className="font-medium">Business type</span>
            <select
              className="iid-input w-full"
              value={draft.gauge_type}
              onChange={(e) => set("gauge_type", e.target.value)}
            >
              {(types.length ? types : [{ id: "other", label: "Other" }]).map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1 text-sm">
            <span className="font-medium">Industry *</span>
            <select
              className="iid-input w-full"
              value={draft.industry_vertical}
              onChange={(e) => setIndustryVertical(e.target.value)}
            >
              <option value="">Select your industry</option>
              {industryVerticals.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.label}
                </option>
              ))}
            </select>
          </label>
          {draft.industry_vertical === "other" ? (
            field("Describe your industry", draft.industry, (v) => set("industry", v), {
              placeholder: "e.g. Climate tech for agriculture",
            })
          ) : null}
        </div>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">What do you sell? (1–2 sentences)</span>
          <textarea
            className="iid-input w-full min-h-[88px]"
            value={draft.description}
            placeholder="We help SMBs automate invoicing and collections."
            onChange={(e) => set("description", e.target.value)}
            onBlur={() => saveQuiet(draft)}
          />
        </label>
      </section>

      <section className="iid-card space-y-4">
        <h2 className="font-semibold text-lg">Industry & positioning</h2>
        <p className="text-sm muted">
          A few extra answers help us place your company in the market and score competitive position more accurately.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          {field("Who is your target customer?", draft.target_customer, (v) => set("target_customer", v), {
            placeholder: "SMB founders, clinic owners, D2C shoppers…",
          })}
          <label className="block space-y-1 text-sm">
            <span className="font-medium">Business stage</span>
            <select
              className="iid-input w-full"
              value={draft.business_stage}
              onChange={(e) => set("business_stage", e.target.value)}
            >
              <option value="">Select stage</option>
              {stages.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          {field("Years operating", draft.years_operating, (v) => set("years_operating", v), {
            placeholder: "e.g. 2.5",
          })}
          <label className="block space-y-1 text-sm">
            <span className="font-medium">Revenue model</span>
            <select
              className="iid-input w-full"
              value={draft.revenue_model}
              onChange={(e) => set("revenue_model", e.target.value)}
            >
              <option value="">Select model</option>
              {revenueModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          {field("Main competitors (2–3 names)", draft.competitors, (v) => set("competitors", v), {
            placeholder: "Competitor A, Competitor B…",
          })}
        </div>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">What makes you different?</span>
          <textarea
            className="iid-input w-full min-h-[72px]"
            value={draft.differentiation}
            placeholder="Why customers choose you vs alternatives in your space."
            onChange={(e) => set("differentiation", e.target.value)}
          />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-1 text-sm">
            <span className="font-medium">Biggest challenge right now</span>
            <textarea
              className="iid-input w-full min-h-[72px]"
              value={draft.biggest_challenge}
              placeholder="Acquisition, retention, ops, hiring…"
              onChange={(e) => set("biggest_challenge", e.target.value)}
            />
          </label>
          <label className="block space-y-1 text-sm">
            <span className="font-medium">12-month growth priority</span>
            <textarea
              className="iid-input w-full min-h-[72px]"
              value={draft.growth_goal_12m}
              placeholder="Hit ₹X MRR, launch new market, improve margins…"
              onChange={(e) => set("growth_goal_12m", e.target.value)}
            />
          </label>
        </div>
      </section>

      <section className="iid-card space-y-4">
        <h2 className="font-semibold text-lg">Public links to read</h2>
        <p className="text-sm muted">We’ll attempt to fetch page text and fold it into the score. Social profiles that block scrapers still inform the analysis via the URL.</p>
        <div className="grid gap-4 md:grid-cols-2">
          {field("Website", draft.website, (v) => set("website", v), { placeholder: "https://…" })}
          {field("LinkedIn", draft.linkedin_url, (v) => set("linkedin_url", v), {
            placeholder: "https://linkedin.com/company/…",
          })}
          {field("Instagram", draft.instagram_url, (v) => set("instagram_url", v), {
            placeholder: "https://instagram.com/…",
          })}
          <label className="block space-y-1 text-sm md:col-span-2">
            <span className="font-medium">Other URLs (one per line)</span>
            <textarea
              className="iid-input w-full min-h-[72px]"
              value={draft.other_urls}
              placeholder={"https://crunchbase.com/…\nhttps://x.com/…"}
              onChange={(e) => set("other_urls", e.target.value)}
            />
          </label>
        </div>
      </section>

      <section className="iid-card space-y-4">
        <h2 className="font-semibold text-lg">Optional quick numbers</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {field("Monthly revenue", draft.monthly_revenue, (v) => set("monthly_revenue", v), {
            placeholder: "e.g. 85000",
          })}
          {field("Active customers", draft.active_customers, (v) => set("active_customers", v), {
            placeholder: "e.g. 120",
          })}
          {field("Team size", draft.team_size, (v) => set("team_size", v), { placeholder: "e.g. 6" })}
        </div>
      </section>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="iid-btn iid-btn-primary"
          disabled={!canRun || running || demoMode}
          onClick={run}
        >
          {running ? "Running Mini Gauge…" : "Run Mini Gauge"}
        </button>
        <Link href="/app/audit" className="iid-btn iid-btn-ghost">
          Full company audit →
        </Link>
        {fullAuditAvailable === false && (
          <Link href="/pricing" className="text-sm muted underline-offset-2 hover:underline">
            Upgrade for more full audits
          </Link>
        )}
      </div>

      {audit && (
        <section className="iid-card space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold text-lg">Mini GAUGE report</h3>
            <span className="text-xs uppercase tracking-wider muted">
              {String(audit._route || "snapshot").startsWith("perplexity")
                ? "Web research"
                : String(audit._route || "").includes("openai")
                  ? "Model audit"
                  : String(audit._fallback)
                    ? "Signal baseline"
                    : "Initial snapshot"}
            </span>
          </div>
          <p className="text-lg">
            Overall: <strong>{String(audit.overall_score)}/100</strong> — {String(audit.overall_label)}
          </p>
          <p className="text-sm">{String(audit.overall_summary || "")}</p>
          {audit.plain_english_read ? (
            <div className="rounded-lg border border-[var(--iid-blue)]/40 p-3 text-sm">
              {String(audit.plain_english_read)}
            </div>
          ) : null}

          <IndustryStandingBlock
            position={(audit.industry_position as IndustryPosition) || {}}
            industryFallback={String(audit.industry_selected || draft.industry || "")}
          />

          {audit.market_position ? (
            <div className="rounded-lg border border-[var(--iid-line)] p-3 text-sm">
              <h4 className="font-semibold text-sm mb-1">Market position</h4>
              <p>{String(audit.market_position)}</p>
            </div>
          ) : null}

          {audit.industry_landscape ? (
            <div className="rounded-lg border border-[var(--iid-line)] p-3 text-sm">
              <h4 className="font-semibold text-sm mb-1">Industry landscape</h4>
              <p>{String(audit.industry_landscape)}</p>
            </div>
          ) : null}

          <div className="grid gap-3 md:grid-cols-3">
            {((audit.categories as Array<Record<string, unknown>>) || []).map((cat) => (
              <div key={String(cat.name)} className="rounded-lg border border-[var(--iid-line)] p-3 text-sm">
                <p>
                  {statusEmoji(String(cat.status))} <strong>{String(cat.name)}</strong> — {String(cat.score)}/100
                </p>
                <p className="muted text-xs mt-1">{String(cat.summary || "")}</p>
              </div>
            ))}
          </div>

          {Array.isArray(audit.key_metrics) && (audit.key_metrics as Array<Record<string, string>>).length > 0 && (
            <div className="grid gap-2 sm:grid-cols-2">
              {(audit.key_metrics as Array<Record<string, string>>).map((m) => (
                <div key={m.label} className="rounded border border-[var(--iid-line)] px-3 py-2 text-sm">
                  <span className="muted">{m.label}</span> · <strong>{m.value}</strong>
                  {m.benchmark ? <span className="text-xs muted"> (bench: {m.benchmark})</span> : null}
                </div>
              ))}
            </div>
          )}

          {Array.isArray(audit.risks) && (audit.risks as string[]).length > 0 && (
            <div>
              <h4 className="font-semibold text-sm">Risks to watch</h4>
              <ul className="mt-2 text-sm list-disc ml-5 space-y-1">
                {(audit.risks as string[]).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          {Array.isArray(audit.top_actions) && (audit.top_actions as Array<Record<string, string>>).length > 0 && (
            <div>
              <h4 className="font-semibold text-sm">Priority actions</h4>
              <ul className="mt-2 space-y-2 text-sm">
                {(audit.top_actions as Array<Record<string, string>>).map((a, i) => (
                  <li key={i} className="rounded border border-[var(--iid-line)] p-2">
                    <strong>{a.title}</strong> — {a.why}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(urlsFetched.length > 0 || (Array.isArray(audit.sources) && (audit.sources as string[]).length > 0)) && (
            <div>
              <h4 className="font-semibold text-sm">Sources considered</h4>
              <ul className="mt-2 text-xs muted space-y-1">
                {urlsFetched.map((u, i) => (
                  <li key={i}>
                    {u.label}: {u.url} {u.fetched === "yes" ? "(fetched)" : "(URL only)"}
                  </li>
                ))}
                {(audit.sources as string[] | undefined)?.map((s, i) => (
                  <li key={`src-${i}`}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-xl border border-[var(--iid-line)] bg-[var(--iid-panel)]/40 p-4 space-y-2">
            <p className="font-semibold text-sm">Want the full instrument?</p>
            <p className="text-sm muted">
              Full GAUGE adds the category checklist, deeper operating metrics, founder forward questions, and a plan-forward build.
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <Link href="/app/audit" className="iid-btn iid-btn-primary text-sm">
                Unlock full GAUGE audit →
              </Link>
              {fullAuditAvailable === false ? (
                <Link href="/pricing" className="iid-btn iid-btn-ghost text-sm">
                  View pricing
                </Link>
              ) : null}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}