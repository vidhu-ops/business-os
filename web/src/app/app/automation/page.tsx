"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ProjectPicker } from "@/components/ProjectPicker";
import { useProjects } from "@/hooks/useProjects";

type Step = { id: string; label: string; role?: string; needs_approval?: boolean };
type QueueItem = { id?: string; label?: string; status?: string; result?: string };

function AutomationContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const [steps, setSteps] = useState<Step[]>([]);
  const [picked, setPicked] = useState<string[]>([]);
  const [flowName, setFlowName] = useState("My company workflow");
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [log, setLog] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.automationWorkflows().then((data) => {
      const catalog = (data.steps || []) as Step[];
      setSteps(catalog);
      if (catalog.length >= 3) {
        setPicked([catalog[0].id, catalog[1].id, catalog[9]?.id || catalog[2].id].filter(Boolean));
      }
    }).catch(() => setSteps([]));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api.getAutomation(selectedId).then((data) => {
      const queue = data.queue as { items?: QueueItem[] };
      setQueueItems(queue?.items || []);
      const auto = data.automation as { log?: Array<Record<string, unknown>> };
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
      const data = await api.runAutomationNext(selectedId, false);
      const queue = data.queue as { items?: QueueItem[] };
      setQueueItems(queue?.items || []);
      const auto = (await api.getAutomation(selectedId)).automation as { log?: Array<Record<string, unknown>> };
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
        <p className="mt-2 muted">Pick steps and run them with your agent team — same catalog and queue as Streamlit.</p>
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
            {error && <p className="text-sm text-red-400">{error}</p>}
            <div className="flex flex-wrap gap-3">
              <button className="iid-btn iid-btn-primary" type="button" onClick={buildFlow} disabled={loading === "build"}>
                {loading === "build" ? "Building…" : "Build automation from steps"}
              </button>
              <button className="iid-btn iid-btn-ghost" type="button" onClick={runNext} disabled={!hasQueued || loading === "run"}>
                {loading === "run" ? "Running step…" : "Run next step with agent team"}
              </button>
            </div>
          </section>

          {queueItems.length > 0 && (
            <section className="iid-card">
              <h2 className="font-display text-xl font-bold">Queue</h2>
              <ul className="mt-4 space-y-2 text-sm">
                {queueItems.map((item, i) => (
                  <li key={i} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                    <span className="font-semibold">{item.label}</span>
                    <span className="muted"> — {item.status}</span>
                    {item.result && <p className="mt-1 muted">{String(item.result).slice(0, 240)}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {log.length > 0 && (
            <section className="iid-card">
              <h2 className="font-display text-xl font-bold">Run log</h2>
              <pre className="mt-4 max-h-80 overflow-auto text-xs">{JSON.stringify(log.slice(0, 5), null, 2)}</pre>
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