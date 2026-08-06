"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DeliverablePreview } from "@/components/DeliverablePreview";
import { ProjectPicker } from "@/components/ProjectPicker";
import { useProjects } from "@/hooks/useProjects";

type Step = { id: string; label: string; role?: string; needs_approval?: boolean };
type QueueItem = { id?: string; label?: string; status?: string; result?: string; artifacts?: string[] };
type LogEntry = {
  success?: boolean;
  item?: QueueItem;
};

function artifactPaths(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  return raw.slice(0, 5).map((item) => String(item));
}

function StepResult({ label, status, result, artifacts }: { label: string; status?: string; result?: string; artifacts?: string[] }) {
  const paths = artifacts || [];
  const reply = String(result || "").trim();
  if (!reply && paths.length === 0) {
    return <span className="muted"> — {status || "pending"}</span>;
  }
  return (
    <div className="mt-2 space-y-1">
      <p className="text-xs muted">Status: {status || "done"}</p>
      <DeliverablePreview title={label || "Automation step"} reply={reply} artifacts={paths} />
    </div>
  );
}

function AutomationContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const [steps, setSteps] = useState<Step[]>([]);
  const [picked, setPicked] = useState<string[]>([]);
  const [flowName, setFlowName] = useState("My company workflow");
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [setupRequirements, setSetupRequirements] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [isDemo, setIsDemo] = useState(false);
  const [autoApprove, setAutoApprove] = useState(false);

  useEffect(() => {
    api.me().then((u) => setIsDemo(Boolean(u.is_demo))).catch(() => setIsDemo(false));
  }, []);

  useEffect(() => {
    api.automationWorkflows().then((data) => {
      const catalog = (data.steps || []) as Step[];
      setSteps(catalog);
      const preset = ["find_leads", "draft_outreach_per_lead", "send_email_queue"];
      const hasPreset = preset.every((id) => catalog.some((s) => s.id === id));
      setPicked(hasPreset ? preset : [catalog[0].id, catalog[1].id, catalog[2]?.id].filter(Boolean));
    }).catch(() => setSteps([]));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api.getAutomation(selectedId).then((data) => {
      const queue = data.queue as { items?: QueueItem[] };
      setQueueItems(queue?.items || []);
      const auto = data.automation as { log?: LogEntry[] };
      setLog(auto?.log || []);
    }).catch(() => {
      setQueueItems([]);
      setLog([]);
    });
  }, [selectedId]);

  function toggleStep(id: string) {
    setPicked((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function buildFlow() {
    if (!selectedId || picked.length === 0) {
      setError("Pick at least one step.");
      return;
    }
    setLoading("build");
    setError("");
    try {
      const data = await api.buildAutomation(selectedId, picked, flowName);
      const queue = data.queue as { items?: QueueItem[] };
      setQueueItems(queue?.items || []);
      setSetupRequirements((data.setup_requirements as Array<Record<string, unknown>>) || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Build failed");
    } finally {
      setLoading("");
    }
  }

  async function runNext() {
    if (!selectedId) return;
    setLoading("run");
    setError("");
    try {
      const data = await api.runAutomationNext(selectedId, autoApprove);
      const queue = data.queue as { items?: QueueItem[] };
      setQueueItems(queue?.items || []);
      if (data.setup_requirements) {
        setSetupRequirements((data.setup_requirements as Array<Record<string, unknown>>) || []);
      }
      const auto = (await api.getAutomation(selectedId)).automation as { log?: LogEntry[] };
      setLog(auto?.log || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setLoading("");
    }
  }

  const hasQueued = queueItems.some((it) => it.status === "queued" || it.status === "running");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Automation builder</h1>
        <p className="mt-2 muted">
          {isDemo
            ? "Sample completed agent workflow — watch the walkthrough below. Sign up to build and run your own automations."
            : 'Pick steps (or use Find leads → Personalize → Send) and run them. You can also ask Taylor in Employee OS: "find 90 leads and email them".'}
        </p>
        {!isDemo && (
        <p className="mt-1 text-xs muted">Build: 8 credits · each step run: 8 credits. Connect apps under Employee OS → Integrations.</p>
        )}
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

            {isDemo ? (
              <>
                <div className="rounded-xl border border-[var(--iid-line)] bg-black/20 overflow-hidden">
                  <div className="flex aspect-video items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 p-8 text-center">
                    <div>
                      <p className="text-sm font-semibold text-slate-200">Agent automation walkthrough</p>
                      <p className="mt-2 text-xs muted max-w-md">
                        Video demo coming soon — you will embed your walkthrough here. Below is a sample completed workflow queue.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <>
            <label className="block text-sm muted">Steps (in order — click to toggle)</label>
            <div className="flex flex-wrap gap-2">
              {steps.map((step) => (
                <button
                  key={step.id}
                  type="button"
                  className={`iid-btn text-xs ${picked.includes(step.id) ? "iid-btn-primary" : "iid-btn-ghost"}`}
                  onClick={() => toggleStep(step.id)}
                >
                  {step.label}{step.needs_approval ? " [approval]" : ""}
                </button>
              ))}
            </div>
            <input className="iid-input" value={flowName} onChange={(e) => setFlowName(e.target.value)} placeholder="Automation name" />
            <div className="flex flex-wrap gap-2 items-center">
              <button
                type="button"
                className="iid-btn iid-btn-ghost text-xs"
                onClick={() => {
                  setPicked(["find_leads", "draft_outreach_per_lead", "send_email_queue"]);
                  setFlowName("Daily leads + personalized email");
                }}
              >
                Use: Find leads → Personalize → Send
              </button>
              <label className="text-xs muted inline-flex items-center gap-2">
                <input type="checkbox" checked={autoApprove} onChange={(e) => setAutoApprove(e.target.checked)} />
                Auto-approve external sends
              </label>
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <div className="flex flex-wrap gap-3">
              <button className="iid-btn iid-btn-primary" type="button" onClick={buildFlow} disabled={loading === "build"}>
                {loading === "build" ? "Building…" : "Build automation from steps"}
              </button>
              <button className="iid-btn iid-btn-ghost" type="button" onClick={runNext} disabled={!hasQueued || loading === "run"}>
                {loading === "run" ? "Running step…" : "Run next step with agent team"}
              </button>
            </div>
              </>
            )}
          </section>

          {setupRequirements.length > 0 && (
            <section className="iid-card space-y-3">
              <h2 className="font-display text-xl font-bold">Setup required</h2>
              <p className="text-sm muted">Your workflow was created. Connect or add the items below before steps can complete.</p>
              <ul className="space-y-2 text-sm">
                {setupRequirements.map((row, i) => (
                  <li key={i} className={`rounded-lg border px-3 py-2 ${row.ok ? "border-emerald-500/40" : "border-amber-500/40"}`}>
                    <span className="font-semibold">{String(row.need || row.connector)}</span>
                    <span className="muted"> — {row.ok ? "Ready" : String(row.required || "Not connected")}</span>
                  </li>
                ))}
              </ul>
              <Link href="/app/team" className="iid-btn iid-btn-ghost text-xs inline-flex">Open Employee OS integrations</Link>
            </section>
          )}

          {queueItems.length > 0 && (
            <section className="iid-card">
              <h2 className="font-display text-xl font-bold">Queue</h2>
              <ul className="mt-4 space-y-3 text-sm">
                {queueItems.map((item, i) => (
                  <li key={i} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                    <span className="font-semibold">{item.label}</span>
                    <StepResult
                      label={String(item.label || "Step")}
                      status={item.status}
                      result={item.result}
                      artifacts={artifactPaths(item.artifacts)}
                    />
                  </li>
                ))}
              </ul>
            </section>
          )}

          {log.length > 0 && (
            <section className="iid-card">
              <h2 className="font-display text-xl font-bold">Recent results</h2>
              <ul className="mt-4 space-y-3">
                {log.slice(0, 5).map((entry, i) => {
                  const item = entry.item;
                  if (!item) return null;
                  return (
                    <li key={i} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                      <span className="font-semibold text-sm">{item.label || "Automation step"}</span>
                      <StepResult
                        label={String(item.label || "Automation step")}
                        status={item.status}
                        result={item.result}
                        artifacts={artifactPaths(item.artifacts)}
                      />
                    </li>
                  );
                })}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default function AutomationPage() {
  return (
    <Suspense fallback={<p className="muted">Loading...</p>}>
      <AutomationContent />
    </Suspense>
  );
}
