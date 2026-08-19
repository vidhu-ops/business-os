"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

type Field = { id: string; label: string; hint?: string };
type Integ = { id: string; label: string; kind?: string };

function OnboardingInner() {
  const params = useSearchParams();
  const projectId = params.get("project") || "";

  const [step, setStep] = useState<"mode" | "profile" | "integrations" | "done">("profile");
  const [mode, setMode] = useState<"new" | "existing">("new");
  const [fields, setFields] = useState<Field[]>([]);
  const [integrations, setIntegrations] = useState<Integ[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [conn, setConn] = useState<Record<string, { url: string; credential: string; notes: string; connected: boolean }>>({});
  const [saveAccount, setSaveAccount] = useState(true);
  const [completeness, setCompleteness] = useState(0);
  const [loop, setLoop] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setError("Open onboarding from a project (missing ?project=).");
      setLoading(false);
      return;
    }
    api
      .orgMemoryProject(projectId)
      .then((data) => {
        setFields(data.catalog?.profile_fields || []);
        setIntegrations(data.catalog?.integrations || []);
        const eff = data.effective_profile || {};
        setAnswers(Object.fromEntries((data.catalog?.profile_fields || []).map((f) => [f.id, String(eff[f.id] || "")])));
        setMode((data.mode as "new" | "existing") || "new");
        setCompleteness(Number(data.completeness?.pct || 0));
        setLoop(data.execution_loop || null);
        const ints = data.integrations || {};
        const seed: Record<string, { url: string; credential: string; notes: string; connected: boolean }> = {};
        for (const row of data.catalog?.integrations || []) {
          const cur = (ints[row.id] as Record<string, unknown>) || {};
          seed[row.id] = {
            url: String(cur.url || ""),
            credential: "",
            notes: String(cur.notes || ""),
            connected: Boolean(cur.connected),
          };
        }
        setConn(seed);
        if (!data.business_profile || !(data.business_profile as { onboarding_complete?: boolean }).onboarding_complete) {
          setStep("profile");
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load org memory"))
      .finally(() => setLoading(false));
  }, [projectId]);

  const missing = useMemo(() => fields.filter((f) => !String(answers[f.id] || "").trim()).map((f) => f.label), [fields, answers]);

  async function saveProfile(complete = false) {
    if (!projectId) return;
    setSaving(true);
    setError("");
    try {
      const res = await api.orgMemorySaveProfile(projectId, {
        answers,
        mode,
        save_to_account: saveAccount,
        onboarding_complete: complete ? true : undefined,
      });
      const loopData = (res.execution_loop as Record<string, unknown>) || null;
      setLoop(loopData);
      setCompleteness(Number((res as { completeness?: { pct?: number } }).completeness?.pct || completeness));
      if (complete) setStep("done");
      else setStep("integrations");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function saveIntegration(id: string) {
    if (!projectId) return;
    const row = conn[id] || { url: "", credential: "", notes: "", connected: true };
    setSaving(true);
    setError("");
    try {
      await api.orgMemorySaveIntegration({
        integration_id: id,
        connected: true,
        url: row.url,
        credential: row.credential,
        notes: row.notes,
        save_to_account: saveAccount,
        workspace_id: projectId,
      });
      setConn((prev) => ({ ...prev, [id]: { ...row, connected: true, credential: "" } }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save integration");
    } finally {
      setSaving(false);
    }
  }

  async function finish(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.orgMemorySaveProfile(projectId, {
        answers,
        mode,
        save_to_account: saveAccount,
        onboarding_complete: true,
      });
      await api.orgMemoryLoop({
        workspace_id: projectId,
        phase: mode === "existing" ? "gauge" : "research",
        event: "Onboarding complete — Mentor will guide the next build step",
      });
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not finish onboarding");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="muted">Loading organizational memory…</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">Organizational memory</h1>
          <p className="mt-2 muted max-w-2xl">
            Answer once. Connect tools once. Every research answer, plan, Mentor reply, and agent task uses this business context.
            Credentials save to your account so other projects can reuse them.
          </p>
        </div>
        <Link href={projectId ? `/app/mentor?project=${encodeURIComponent(projectId)}` : "/app/mentor"} className="iid-btn iid-btn-ghost">
          Open Mentor
        </Link>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        {(["profile", "integrations", "done"] as const).map((s) => (
          <button
            key={s}
            type="button"
            className={`rounded-full border px-3 py-1 ${step === s ? "border-[var(--iid-blue)] text-[var(--iid-blue)]" : "border-[var(--iid-line)] muted"}`}
            onClick={() => setStep(s)}
          >
            {s === "profile" ? "1 · Business profile" : s === "integrations" ? "2 · Integrations" : "3 · Ready"}
          </button>
        ))}
        <span className="ml-auto text-sm muted">Profile {completeness}% · Loop {(loop?.phase as string) || "intake"}</span>
      </div>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      {step === "profile" ? (
        <section className="iid-card space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" className={`iid-btn ${mode === "new" ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setMode("new")}>
              New business
            </button>
            <button type="button" className={`iid-btn ${mode === "existing" ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setMode("existing")}>
              Existing business (GAUGE)
            </button>
          </div>
          <p className="text-sm muted">
            {mode === "existing"
              ? "After this profile, Mentor will send you through the GAUGE audit so research and agents ground on your real company."
              : "We will use these answers to brief research, plan, Mentor, and Employee OS."}
          </p>
          <div className="space-y-3">
            {fields.map((f) => (
              <label key={f.id} className="block space-y-1">
                <span className="label">{f.label}</span>
                <textarea
                  className="iid-input min-h-20"
                  placeholder={f.hint || ""}
                  value={answers[f.id] || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, [f.id]: e.target.value }))}
                />
              </label>
            ))}
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={saveAccount} onChange={(e) => setSaveAccount(e.target.checked)} />
            Save to account (reuse on other projects)
          </label>
          {missing.length ? <p className="text-xs muted">Still empty: {missing.slice(0, 4).join(", ")}{missing.length > 4 ? "…" : ""}</p> : null}
          <div className="flex flex-wrap gap-2">
            <button type="button" className="iid-btn iid-btn-primary" disabled={saving} onClick={() => saveProfile(false)}>
              {saving ? "Saving…" : "Save & connect tools"}
            </button>
            <button type="button" className="iid-btn iid-btn-ghost" disabled={saving} onClick={() => saveProfile(true)}>
              Save & finish
            </button>
          </div>
        </section>
      ) : null}

      {step === "integrations" ? (
        <form className="iid-card space-y-4" onSubmit={finish}>
          <p className="text-sm muted">Connect what you already use. Paste tokens/URLs now, or OAuth later in Employee OS. Account-level saves apply to future projects.</p>
          <div className="space-y-4">
            {integrations.map((integ) => {
              const row = conn[integ.id] || { url: "", credential: "", notes: "", connected: false };
              return (
                <div key={integ.id} className="rounded-xl border border-[var(--iid-line)] p-3 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold">{integ.label}</p>
                    <span className="text-xs muted">{row.connected ? "Connected" : "Not connected"}</span>
                  </div>
                  <input
                    className="iid-input"
                    placeholder="URL / workspace link"
                    value={row.url}
                    onChange={(e) => setConn((c) => ({ ...c, [integ.id]: { ...row, url: e.target.value } }))}
                  />
                  <input
                    className="iid-input"
                    placeholder="API token / credential (stored for reuse)"
                    value={row.credential}
                    onChange={(e) => setConn((c) => ({ ...c, [integ.id]: { ...row, credential: e.target.value } }))}
                  />
                  <input
                    className="iid-input"
                    placeholder="Notes"
                    value={row.notes}
                    onChange={(e) => setConn((c) => ({ ...c, [integ.id]: { ...row, notes: e.target.value } }))}
                  />
                  <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={saving} onClick={() => saveIntegration(integ.id)}>
                    Save {integ.label}
                  </button>
                </div>
              );
            })}
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={saveAccount} onChange={(e) => setSaveAccount(e.target.checked)} />
            Save credentials to account for all projects
          </label>
          <button type="submit" className="iid-btn iid-btn-primary" disabled={saving}>
            {saving ? "Finishing…" : "Finish onboarding"}
          </button>
        </form>
      ) : null}

      {step === "done" ? (
        <section className="iid-card space-y-4">
          <h2 className="font-display text-xl font-bold">Memory is live</h2>
          <p className="text-sm muted">
            Mentor will guide you step-by-step. Taylor will turn the plan into tasks, ask for approval on external actions, execute in real time, measure against your goals, and propose readjustments.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {mode === "existing" ? (
              <Link href={`/app/audit?project=${encodeURIComponent(projectId)}`} className="iid-btn iid-btn-primary">
                Continue to GAUGE audit
              </Link>
            ) : (
              <Link href={`/app/research?project=${encodeURIComponent(projectId)}`} className="iid-btn iid-btn-primary">
                Run market research
              </Link>
            )}
            <Link href={`/app/mentor?project=${encodeURIComponent(projectId)}`} className="iid-btn iid-btn-ghost">
              Talk to Mentor
            </Link>
            <Link href={`/app/team?project=${encodeURIComponent(projectId)}`} className="iid-btn iid-btn-ghost">
              Open Employee OS
            </Link>
            <button type="button" className="iid-btn iid-btn-ghost" onClick={() => setStep("profile")}>
              Edit answers
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}


export default function OnboardingPage() {
  return (
    <Suspense fallback={<p className="muted">Loading organizational memory…</p>}>
      <OnboardingInner />
    </Suspense>
  );
}
