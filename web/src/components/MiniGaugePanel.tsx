"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type BizType = { id: string; label: string };

type MiniDraft = {
  company_name: string;
  geography: string;
  gauge_type: string;
  industry: string;
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
  industry: "",
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

function statusEmoji(status: string) {
  const s = status.toLowerCase();
  if (s === "strong") return "🟢";
  if (s === "watch") return "🟡";
  if (s === "risk") return "🔴";
  return "⚪";
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
        const incoming = (state.draft || {}) as Partial<MiniDraft>;
        setDraft({ ...EMPTY, ...incoming, gauge_type: String(incoming.gauge_type || "other") });
        setAudit(state.audit);
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
    return Boolean(draft.company_name.trim() && draft.geography.trim());
  }, [draft.company_name, draft.geography]);

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
            Quick company pulse: name, market, and public links (website, LinkedIn, Instagram, or others).
            We pull what we can and return GAUGE-style scores. Unlock the full audit for checklist depth and forward planning.
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
          {field("Industry (optional)", draft.industry, (v) => set("industry", v), {
            placeholder: "B2B SaaS, D2C beauty…",
          })}
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
            <span className="text-xs uppercase tracking-wider muted">Initial snapshot</span>
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

          {urlsFetched.length > 0 && (
            <div>
              <h4 className="font-semibold text-sm">Sources considered</h4>
              <ul className="mt-2 text-xs muted space-y-1">
                {urlsFetched.map((u, i) => (
                  <li key={i}>
                    {u.label}: {u.url} {u.fetched === "yes" ? "(fetched)" : "(URL only)"}
                  </li>
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