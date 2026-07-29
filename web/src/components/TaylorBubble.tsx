"use client";

import { useEffect, useRef, useState } from "react";

type Suggestion = { kind?: string; label?: string; harness_id?: string; prompt?: string };
type Pulse = {
  headline?: string;
  approvals?: Array<Record<string, unknown>>;
  failed?: Array<Record<string, unknown>>;
  qc_failed?: Array<Record<string, unknown>>;
  done?: Array<Record<string, unknown>>;
  suggestions?: Suggestion[];
  progress?: { done?: number; total?: number };
  signature?: string;
};

type Props = {
  pulse: Pulse | null;
  onAction: (action: string, extra?: { harness_id?: string; prompt?: string }) => void;
  loading?: boolean;
};

export function TaylorBubble({ pulse, onAction, loading }: Props) {
  const [open, setOpen] = useState(false);
  const [voice, setVoice] = useState(false);
  const seen = useRef<string>("");

  const approvals = pulse?.approvals || [];
  const failed = pulse?.failed || [];
  const qcFailed = pulse?.qc_failed || [];
  const done = pulse?.done || [];
  const suggestions = pulse?.suggestions || [];
  const progress = pulse?.progress || {};
  const headline = String(pulse?.headline || "Taylor — Team Leader");
  const badge = qcFailed.length ? ` (${qcFailed.length} QC)` : approvals.length ? ` (${approvals.length})` : failed.length ? ` (${failed.length})` : "";

  useEffect(() => {
    const sig = String(pulse?.signature || "");
    if (!sig || sig === seen.current) return;
    seen.current = sig;
    if (voice && headline && typeof window !== "undefined" && "speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance(headline.slice(0, 220));
      u.rate = 1.02;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    }
  }, [pulse?.signature, voice, headline]);

  if (!pulse) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[9999]">
      {open && (
        <div className="mb-3 w-[min(360px,calc(100vw-3rem))] rounded-2xl border border-[var(--iid-line)] bg-[var(--iid-panel)] p-4 shadow-2xl space-y-3 max-h-[70vh] overflow-y-auto">
          <p className="font-semibold text-sm">{headline}</p>
          {Number(progress.total) > 0 && (
            <div>
              <div className="h-2 rounded-full bg-[var(--iid-line)] overflow-hidden">
                <div className="h-full bg-[var(--iid-blue)]" style={{ width: `${Math.min(100, ((Number(progress.done) || 0) / Number(progress.total)) * 100)}%` }} />
              </div>
              <p className="text-xs muted mt-1">{progress.done}/{progress.total} tasks delivered</p>
            </div>
          )}
          <label className="flex items-center gap-2 text-xs">
            <input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} className="accent-[var(--iid-blue)]" />
            Voice updates
          </label>
          {qcFailed.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-red-300">QC failed</p>
              {qcFailed.slice(0, 3).map((r, i) => (
                <p key={i} className="text-xs muted">- {String(r.title)}</p>
              ))}
              <button type="button" className="iid-btn iid-btn-primary text-xs mt-2" disabled={loading} onClick={() => onAction("retry_failed")}>Retry failed</button>
            </div>
          )}
          {approvals.length > 0 && (
            <div>
              <p className="text-xs font-semibold">Needs approval</p>
              {approvals.slice(0, 4).map((r, i) => (
                <p key={i} className="text-xs muted">- {String(r.title)}</p>
              ))}
              <button type="button" className="iid-btn iid-btn-primary text-xs mt-2" disabled={loading} onClick={() => onAction("approve_all")}>Approve all {approvals.length}</button>
            </div>
          )}
          {suggestions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  className="iid-btn iid-btn-ghost text-xs"
                  disabled={loading}
                  onClick={() => {
                    if (s.kind === "employee_prompt" && s.harness_id && s.prompt) {
                      onAction("employee_prompt", { harness_id: s.harness_id, prompt: s.prompt });
                    } else if (s.kind === "run_next") onAction("run_next");
                    else if (s.kind === "retry_failed") onAction("retry_failed");
                    else if (s.kind === "review_approvals") setOpen(true);
                    else onAction(String(s.kind || "run_next"));
                  }}
                >
                  {s.label || s.kind}
                </button>
              ))}
            </div>
          )}
          {done.length > 0 && <p className="text-xs muted">{done.length} delivered recently</p>}
        </div>
      )}
      <button
        type="button"
        className="rounded-full px-5 py-3 font-semibold text-white shadow-lg"
        style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
        onClick={() => setOpen((v) => !v)}
      >
        Taylor{badge}
      </button>
    </div>
  );
}
