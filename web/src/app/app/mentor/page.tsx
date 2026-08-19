"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };
type Brief = {
  idea?: string;
  industry?: string;
  country?: string;
  market_label?: string;
  research_ready?: boolean;
  plan_ready?: boolean;
  audit_ready?: boolean;
  checklist_status?: string;
  automation_status?: string;
  next_move?: string;
  org_completeness?: { pct?: number };
  execution_loop?: {
    phase?: string;
    goal_progress_avg?: number;
    goals?: Array<{ id?: string; label?: string; progress_pct?: number; current?: string; status?: string }>;
    pending_approvals?: Array<{ id?: string; title?: string; detail?: string }>;
  };
  org_profile?: Record<string, string>;
};

type ProjectOpt = {
  workspace_id?: string;
  idea?: string;
  industry?: string;
  country?: string;
  has_report?: boolean;
  has_plan?: boolean;
};

export default function MentorPage() {
  const [workspaceId, setWorkspaceId] = useState("");
  const [projects, setProjects] = useState<ProjectOpt[]>([]);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  async function boot(wid?: string) {
    setLoading(true);
    setError("");
    try {
      const data = await api.mentorBootstrap(wid || undefined);
      setProjects(data.projects || []);
      const id = String(data.workspace_id || wid || "");
      setWorkspaceId(id);
      setBrief((data.brief as Brief) || null);
      setMessages([{ role: "assistant", content: data.opening || "I am your industry Mentor. Ask what to do next." }]);
      if (id) {
        try {
          const org = await api.orgMemoryProject(id);
          setBrief((prev) => ({
            ...(prev || {}),
            ...(data.brief as Brief),
            org_completeness: org.completeness,
            execution_loop: org.execution_loop as Brief["execution_loop"],
            org_profile: org.effective_profile,
          }));
        } catch {
          /* optional */
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load Mentor");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(typeof window !== "undefined" ? window.location.search : "");
    const wid = params.get("project") || params.get("workspace_id") || "";
    boot(wid).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const title = useMemo(() => {
    if (!brief) return "Mentor";
    return `Mentor · ${brief.industry || "Industry"} · ${brief.market_label || brief.country || "Market"}`;
  }, [brief]);

  async function onSend(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    const nextHistory = [...messages, { role: "user" as const, content: text }];
    setMessages(nextHistory);
    setSending(true);
    setError("");
    try {
      const res = await api.mentorChat({
        message: text,
        workspace_id: workspaceId || undefined,
        history: nextHistory.map((m) => ({ role: m.role, content: m.content })),
      });
      if (res.brief) setBrief((prev) => ({ ...(prev || {}), ...(res.brief as Brief) }));
      if (res.workspace_id) setWorkspaceId(String(res.workspace_id));
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply || "…" }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mentor chat failed");
    } finally {
      setSending(false);
    }
  }

  async function approvePending(id: string) {
    if (!workspaceId) return;
    try {
      const out = await api.orgMemoryLoop({
        workspace_id: workspaceId,
        resolve_approval_id: id,
        event: `Founder approved ${id}`,
        phase: "execute",
      });
      setBrief((prev) => ({ ...(prev || {}), execution_loop: out.execution_loop as Brief["execution_loop"] }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    }
  }

  if (loading) return <p className="muted">Loading your Mentor…</p>;

  const loop = brief?.execution_loop;
  const goals = loop?.goals || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">{title}</h1>
          <p className="mt-2 muted max-w-2xl">
            Step-by-step coach with your organizational memory, GAUGE, research, plan, and live agent loop. Approve external actions; we measure progress against your goals.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href={workspaceId ? `/app/onboarding?project=${encodeURIComponent(workspaceId)}` : "/app/onboarding"} className="iid-btn iid-btn-ghost">
            Org memory
          </Link>
          <Link href={workspaceId ? `/app/team?project=${encodeURIComponent(workspaceId)}` : "/app/team"} className="iid-btn iid-btn-ghost">
            Employee OS
          </Link>
        </div>
      </div>

      {projects.length > 0 ? (
        <label className="block max-w-xl space-y-1">
          <span className="label">Project context</span>
          <select
            className="iid-input w-full"
            value={workspaceId}
            onChange={(e) => {
              const wid = e.target.value;
              setWorkspaceId(wid);
              boot(wid).catch(() => undefined);
            }}
          >
            {projects.map((p) => (
              <option key={String(p.workspace_id)} value={String(p.workspace_id || "")}>
                {(p.idea || "Untitled") + " · " + (p.industry || "?") + " · " + (p.country || "?")}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="iid-card">
          <p className="label">Org memory</p>
          <p className="font-semibold">{brief?.org_completeness?.pct ?? 0}%</p>
        </div>
        <div className="iid-card">
          <p className="label">Loop phase</p>
          <p className="font-semibold capitalize">{String(loop?.phase || "intake")}</p>
        </div>
        <div className="iid-card">
          <p className="label">Goal progress</p>
          <p className="font-semibold">{Number(loop?.goal_progress_avg || 0)}%</p>
        </div>
        <div className="iid-card">
          <p className="label">Research / Plan</p>
          <p className="text-sm">{brief?.research_ready ? "Research ready" : "Research open"} · {brief?.plan_ready ? "Plan ready" : "Plan open"}</p>
        </div>
        <div className="iid-card">
          <p className="label">Next move</p>
          <p className="text-sm">{brief?.next_move || "—"}</p>
        </div>
      </div>

      {goals.length ? (
        <section className="iid-card space-y-3">
          <h2 className="font-display text-lg font-bold">Goals vs progress</h2>
          {goals.map((g) => (
            <div key={String(g.id)} className="space-y-1">
              <div className="flex justify-between gap-2 text-sm">
                <span>{g.label}</span>
                <span className="muted">{Number(g.progress_pct || 0)}%</span>
              </div>
              <div className="h-2 rounded-full bg-[var(--iid-line)]">
                <div className="h-2 rounded-full bg-[var(--iid-blue)]" style={{ width: `${Math.max(0, Math.min(100, Number(g.progress_pct || 0)))}%` }} />
              </div>
            </div>
          ))}
        </section>
      ) : null}

      {(loop?.pending_approvals || []).length ? (
        <section className="iid-card space-y-3">
          <h2 className="font-display text-lg font-bold">Approvals waiting</h2>
          {(loop?.pending_approvals || []).map((a) => (
            <div key={String(a.id)} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--iid-line)] py-2">
              <div>
                <p className="text-sm font-semibold">{a.title}</p>
                <p className="text-xs muted">{a.detail}</p>
              </div>
              <button type="button" className="iid-btn iid-btn-primary text-xs" onClick={() => approvePending(String(a.id))}>
                Approve
              </button>
            </div>
          ))}
        </section>
      ) : null}

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <section className="iid-card flex min-h-[28rem] flex-col">
        <div className="flex-1 space-y-3 overflow-y-auto pr-1" style={{ maxHeight: "28rem" }}>
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "ml-8 rounded-lg bg-[var(--iid-blue)]/10 px-3 py-2 text-sm"
                  : "mr-8 rounded-lg border border-[var(--iid-line)] px-3 py-2 text-sm"
              }
            >
              <p className="mb-1 text-[10px] uppercase tracking-wide text-[var(--iid-muted)]">{m.role === "user" ? "You" : "Mentor"}</p>
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          ))}
        </div>
        <form className="mt-4 flex gap-2" onSubmit={onSend}>
          <input
            className="iid-input flex-1"
            placeholder="Ask what to do next, or paste a blocker…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
          />
          <button type="submit" className="iid-btn iid-btn-primary" disabled={sending || !input.trim()}>
            {sending ? "…" : "Send"}
          </button>
        </form>
      </section>
    </div>
  );
}
