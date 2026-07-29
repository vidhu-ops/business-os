"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState, type ComponentProps } from "react";
import { api } from "@/lib/api";
import { DeliverablePreview } from "@/components/DeliverablePreview";
import { TaylorBubble } from "@/components/TaylorBubble";
import { ProjectPicker } from "@/components/ProjectPicker";
import { useProjects } from "@/hooks/useProjects";

type Agent = { id: string; name?: string; role?: string; tagline?: string; starters?: string[]; department?: string };
type TabDef = { id: string; label: string };
type ChatTurn = { role: string; content?: string; artifacts?: string[] };

const FULL_TABS: TabDef[] = [
  { id: "office", label: "The Office" },
  { id: "tasks", label: "Tasks & approvals" },
  { id: "war_room", label: "War room" },
  { id: "command", label: "Command center" },
  { id: "agents", label: "Agents & team" },
  { id: "integrations", label: "Integrations" },
  { id: "advanced", label: "Advanced" },
];
const DEPT_TABS: TabDef[] = [
  { id: "office", label: "Department office" },
  { id: "tasks", label: "Task queue" },
  { id: "agents", label: "Department agents" },
  { id: "integrations", label: "Setup & connect" },
];
const EMP_TABS: TabDef[] = [
  { id: "agents", label: "Employee chat" },
  { id: "tasks", label: "Their tasks" },
  { id: "integrations", label: "Setup & connect" },
];

function tabsForMode(mode: string): TabDef[] {
  if (mode === "department") return DEPT_TABS;
  if (mode === "employee") return EMP_TABS;
  return FULL_TABS;
}

function TeamContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [bootstrap, setBootstrap] = useState<Record<string, unknown> | null>(null);

  const [scopeMode, setScopeMode] = useState("full_office");
  const [departments, setDepartments] = useState<string[]>([]);
  const [harnessIds, setHarnessIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState("office");

  const [activeAgent, setActiveAgent] = useState("");
  const [chat, setChat] = useState<ChatTurn[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const [checklist, setChecklist] = useState<Record<string, unknown> | null>(null);
  const [pulse, setPulse] = useState<Record<string, unknown> | null>(null);
  const [taskMsg, setTaskMsg] = useState("");
  const [command, setCommand] = useState<Record<string, unknown> | null>(null);
  const [warRoom, setWarRoom] = useState<Record<string, unknown> | null>(null);
  const [office, setOffice] = useState<Record<string, unknown> | null>(null);
  const [oauthProviders, setOauthProviders] = useState<Array<Record<string, unknown>>>([]);
  const [companyMemory, setCompanyMemory] = useState<Record<string, unknown> | null>(null);
  const [customHarnesses, setCustomHarnesses] = useState<Array<Record<string, unknown>>>([]);
  const [employees, setEmployees] = useState<Array<Record<string, unknown>>>([]);
  const [catalogRoles, setCatalogRoles] = useState<Array<Record<string, unknown>>>([]);
  const [coreRoles, setCoreRoles] = useState<string[]>([]);
  const [hireName, setHireName] = useState("");
  const [hireRole, setHireRole] = useState("");
  const [harnessName, setHarnessName] = useState("");
  const [harnessBase, setHarnessBase] = useState("sales_lead");
  const [harnessTagline, setHarnessTagline] = useState("Custom workflows");
  const [harnessStarters, setHarnessStarters] = useState("");
  const [goalsText, setGoalsText] = useState("");
  const [autoApprove, setAutoApprove] = useState(false);
  const [actionLoading, setActionLoading] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [activeKeyProviders, setActiveKeyProviders] = useState<string[]>([]);
  const [perplexityKey, setPerplexityKey] = useState("");
  const [llmKey, setLlmKey] = useState("");
  const [llmProvider, setLlmProvider] = useState("openai");
  const [manualHubspot, setManualHubspot] = useState("");
  const [manualLinkedinToken, setManualLinkedinToken] = useState("");
  const [manualLinkedinUrn, setManualLinkedinUrn] = useState("");
  const [manualGmailPassword, setManualGmailPassword] = useState("");

  const agents = (bootstrap?.agents as Agent[]) || [];
  const deptOptions = (bootstrap?.departments as string[]) || [];
  const scopeConfigured = scopeMode === "full_office" || (scopeMode === "department" && departments.length > 0) || (scopeMode === "employee" && harnessIds.length > 0);
  const tabs = useMemo(() => tabsForMode(scopeMode), [scopeMode]);

  const refresh = useCallback(async () => {
    if (!selectedId) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.getOs2(selectedId);
      setBootstrap(data);
      const scope = (data.scope as Record<string, unknown>) || {};
      setScopeMode(String(scope.mode || "full_office"));
      setDepartments((scope.departments as string[]) || []);
      setHarnessIds((scope.harness_ids as string[]) || []);
      setChecklist((data.checklist as Record<string, unknown>) || null);
      setPulse((data.taylor_pulse as Record<string, unknown>) || null);
      setActiveKeyProviders((data.active_key_providers as string[]) || []);
      const officeData = await api.getOs2Office(selectedId).catch(() => null);
      if (officeData) {
        setOffice(officeData);
        const g = (officeData.goals as string[]) || [];
        if (g.length && !goalsText) setGoalsText(g.join("\n"));
      }
      if (!activeAgent && (data.agents as Agent[])?.[0]?.id) {
        setActiveAgent((data.agents as Agent[])[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load Employee OS");
    } finally {
      setLoading(false);
    }
  }, [selectedId, activeAgent]);

  useEffect(() => {
    refresh().catch(() => setBootstrap(null));
  }, [refresh]);

  useEffect(() => {
    if (!selectedId || !activeAgent) return;
    api.getOs2Chat(selectedId, activeAgent).then((d) => setChat((d.chat as ChatTurn[]) || [])).catch(() => setChat([]));
  }, [selectedId, activeAgent]);

  useEffect(() => {
    if (!tabs.find((t) => t.id === activeTab)) setActiveTab(tabs[0]?.id || "agents");
  }, [tabs, activeTab]);

  useEffect(() => {
    if (!selectedId || !scopeConfigured) return;
    if (activeTab === "command") api.getOs2Command(selectedId).then(setCommand).catch(() => setCommand(null));
    if (activeTab === "war_room") api.getOs2WarRoom(selectedId).then(setWarRoom).catch(() => setWarRoom(null));
    if (activeTab === "integrations") api.getOs2OAuth(selectedId).then((d) => setOauthProviders(d.providers || [])).catch(() => setOauthProviders([]));
    if (activeTab === "advanced") api.getOs2Memory(selectedId).then((d) => setCompanyMemory(d.memory || {})).catch(() => setCompanyMemory(null));
    if (activeTab === "advanced" || activeTab === "agents") api.getOs2Harnesses(selectedId).then((d) => setCustomHarnesses(d.custom || [])).catch(() => setCustomHarnesses([]));
    if (activeTab === "agents") api.getOs2Employees(selectedId).then((d) => { setEmployees(d.employees || []); setCatalogRoles(d.catalog_roles || []); setCoreRoles(d.core_roles || []); }).catch(() => { setEmployees([]); setCatalogRoles([]); setCoreRoles([]); });
  }, [selectedId, activeTab, scopeConfigured]);

  async function saveScope() {
    if (!selectedId) return;
    setError("");
    setSuccessMsg("");
    try {
      await api.setOs2Scope(selectedId, { mode: scopeMode, departments, harness_ids: harnessIds });
      setSuccessMsg("Workspace saved — you can use the tabs below.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save workspace");
    }
  }

  async function saveApiKeys() {
    if (!selectedId) return;
    setActionLoading("keys");
    setError("");
    setSuccessMsg("");
    try {
      const keys: Record<string, string> = {};
      if (perplexityKey.trim()) keys.perplexity = perplexityKey.trim();
      if (llmKey.trim()) keys[llmProvider] = llmKey.trim();
      if (!Object.keys(keys).length) {
        setError("Enter at least one API key to save.");
        return;
      }
      const data = await api.setOs2Keys(selectedId, keys);
      setActiveKeyProviders(data.active_key_providers || []);
      setPerplexityKey("");
      setLlmKey("");
      setSuccessMsg("API keys saved for this session.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save API keys");
    } finally {
      setActionLoading("");
    }
  }

  async function saveManualOAuth(provider: string) {
    if (!selectedId) return;
    setActionLoading(`oauth-${provider}`);
    setError("");
    setSuccessMsg("");
    try {
      const body: Record<string, string> = {};
      if (provider === "hubspot" && manualHubspot.trim()) body.access_token = manualHubspot.trim();
      if (provider === "linkedin") {
        if (manualLinkedinToken.trim()) body.access_token = manualLinkedinToken.trim();
        if (manualLinkedinUrn.trim()) body.author_urn = manualLinkedinUrn.trim();
      }
      if (provider === "gmail" && manualGmailPassword.trim()) body.smtp_app_password = manualGmailPassword.trim();
      if (!Object.keys(body).length) {
        setError("Enter the credentials before saving.");
        return;
      }
      await api.saveManualOAuth(selectedId, provider, body);
      setSuccessMsg(`${provider} connection saved.`);
      const data = await api.getOs2OAuth(selectedId);
      setOauthProviders(data.providers || []);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save connection");
    } finally {
      setActionLoading("");
    }
  }

  async function sendChat(starter?: string) {
    if (!selectedId || !activeAgent) return;
    const msg = starter || chatInput;
    if (!msg.trim()) return;
    setChatLoading(true);
    setError("");
    try {
      const data = await api.postOs2Chat(selectedId, activeAgent, msg);
      setChat((data.chat as ChatTurn[]) || []);
      setChatInput("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent task failed");
    } finally {
      setChatLoading(false);
    }
  }

  async function buildChecklist() {
    if (!selectedId) return;
    setActionLoading("checklist");
    setError("");
    setSuccessMsg("");
    try {
      const data = await api.buildOs2Checklist(selectedId);
      setChecklist(data.checklist as Record<string, unknown>);
      setSuccessMsg("Task checklist built from your business plan.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not build checklist — add a business plan first");
    } finally {
      setActionLoading("");
    }
  }

  async function runNextTask() {
    if (!selectedId) return;
    setActionLoading("run-next");
    setError("");
    setSuccessMsg("");
    try {
      const data = await api.runOs2ChecklistNext(selectedId, autoApprove);
      setTaskMsg(String(data.message || "Task processed"));
      setSuccessMsg(String(data.message || "Next task processed."));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Task run failed — check API keys in Integrations");
    } finally {
      setActionLoading("");
    }
  }

  async function runOfficeAction(action: string) {
    if (!selectedId) return;
    setActionLoading(action);
    setError("");
    try {
      const goals = goalsText.split("\n").map((g) => g.trim()).filter(Boolean);
      const data = await api.runOs2OfficeAction(selectedId, action, goals, autoApprove);
      if (data.office) setOffice(data.office as Record<string, unknown>);
      if (data.checklist) setChecklist(data.checklist as Record<string, unknown>);
      setTaskMsg(String((data.step as Record<string, unknown>)?.message || `${action} complete`));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Office action failed");
    } finally {
      setActionLoading("");
    }
  }

  async function handleTaylorAction(action: string, extra?: { harness_id?: string; prompt?: string }) {
    if (action === "employee_prompt" && extra?.harness_id && extra?.prompt) {
      setActiveTab("agents");
      setActiveAgent(extra.harness_id);
      await sendChat(extra.prompt);
      return;
    }
    await runTaylor(action);
  }

  async function runTaylor(kind: string) {
    if (!selectedId) return;
    setActionLoading(kind);
    try {
      await api.runTaylorAction(selectedId, kind);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Taylor action failed");
    } finally {
      setActionLoading("");
    }
  }

  async function runTaskAction(taskId: string, action: string) {
    if (!selectedId) return;
    setActionLoading(`${action}-${taskId}`);
    try {
      const data = await api.runOs2TaskAction(selectedId, taskId, action);
      if (data.checklist) setChecklist(data.checklist as Record<string, unknown>);
      if (data.office) setOffice(data.office as Record<string, unknown>);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Task action failed");
    } finally {
      setActionLoading("");
    }
  }

  async function addHarness() {
    if (!selectedId || !harnessName.trim()) return;
    setActionLoading("harness");
    try {
      const data = await api.addOs2Harness(selectedId, {
        name: harnessName.trim(),
        base_harness_id: harnessBase,
        tagline: harnessTagline,
        starters: harnessStarters.split("\n").map((s) => s.trim()).filter(Boolean),
      });
      setCustomHarnesses(data.custom || []);
      setHarnessName("");
      setHarnessStarters("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Harness create failed");
    } finally {
      setActionLoading("");
    }
  }

  async function hireEmployee(catalog = false, roleOverride = "") {
    if (!selectedId) return;
    const role = roleOverride || hireRole;
    if (!role) return;
    if (!catalog && !hireName.trim()) return;
    setActionLoading("hire");
    try {
      const data = await api.hireOs2Employee(selectedId, { name: hireName, role, catalog }) as {
        employees?: Array<Record<string, unknown>>;
        catalog_roles?: Array<Record<string, unknown>>;
      };
      setEmployees(data.employees || []);
      setCatalogRoles(data.catalog_roles || []);
      setHireName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hire failed");
    } finally {
      setActionLoading("");
    }
  }

  const baseHarnessOptions = [
    { id: "sales_lead", label: "Sales Lead" },
    { id: "growth_marketer", label: "Growth Marketer" },
    { id: "research_analyst", label: "Research Analyst" },
    { id: "creative_producer", label: "Creative Producer" },
    { id: "ops_manager", label: "Operations Manager" },
  ];

  function renderArtifacts(artifacts: unknown[], reply = "") {
    const paths = (artifacts || []).slice(0, 5).map((a) => String(a));
    const title = paths[0]?.split(/[/\\]/).pop() || "Deliverable";
    return (
      <div className="space-y-1">
        {paths.map((path) => {
          const name = path.split(/[/\\]/).pop() || path;
          return (
            <button key={path} type="button" className="text-xs text-[var(--iid-blue)] hover:underline mr-2" onClick={() => api.downloadFile(path, name).catch(() => setError("Download failed"))}>
              {name}
            </button>
          );
        })}
        {(reply || paths.length > 0) && <DeliverablePreview title={title} reply={reply} artifacts={paths} />}
      </div>
    );
  }

  const checklistItems = ((checklist?.items as Array<Record<string, unknown>>) || []);
  const setupRows = (bootstrap?.setup_requirements as Array<Record<string, unknown>>) || [];
  const oauthRows = (bootstrap?.oauth_status as Array<Record<string, unknown>>) || [];
  const notifications = (pulse?.notifications as string[]) || [];
  const suggestions = (pulse?.suggestions as Array<Record<string, unknown>>) || [];
  const setupComplete = setupRows.filter((r) => r.ok).length;
  const hasLlmKeys = activeKeyProviders.some((p) => p !== "perplexity");
  const hasPerplexity = activeKeyProviders.includes("perplexity");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Team & Execution</h1>
        <p className="mt-2 muted">
          Your virtual team runs tasks from your business plan. Start with <strong>Full office</strong>, connect API keys under Integrations, then chat with agents or run The Office day.
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
            {bootstrap && (
              <p className="text-sm muted">Project: <strong>{String(bootstrap.topic)}</strong> | {String(bootstrap.geography)} | report {String(bootstrap.report_id)}</p>
            )}
          </section>

          <section className="iid-card space-y-4">
            <h2 className="font-display text-lg font-bold">Step 1 — Choose your workspace</h2>
            <div className="flex flex-wrap gap-2">
              {["full_office", "department", "employee"].map((m) => (
                <button key={m} type="button" className={`iid-btn ${scopeMode === m ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setScopeMode(m)}>
                  {m === "full_office" ? "Full office" : m === "department" ? "Department" : "Employee / team"}
                </button>
              ))}
            </div>
            {scopeMode === "department" && (
              <div className="flex flex-wrap gap-2">
                {deptOptions.map((d) => (
                  <button key={d} type="button" className={`iid-btn text-xs ${departments.includes(d) ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setDepartments((prev) => prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d])}>{d}</button>
                ))}
              </div>
            )}
            {scopeMode === "employee" && (
              <div className="flex flex-wrap gap-2">
                {agents.map((a) => (
                  <button key={a.id} type="button" className={`iid-btn text-xs ${harnessIds.includes(a.id) ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setHarnessIds((prev) => prev.includes(a.id) ? prev.filter((x) => x !== a.id) : [...prev, a.id])}>{a.name}</button>
                ))}
              </div>
            )}
            <button type="button" className="iid-btn iid-btn-primary text-sm" onClick={saveScope}>Save workspace</button>
            {scopeMode !== "full_office" && (
              <p className="text-xs muted">Pick at least one department or employee, then save.</p>
            )}
          </section>

          {!scopeConfigured ? (
            <section className="iid-card">
              <p className="text-amber-300 text-sm">
                {scopeMode === "department"
                  ? "Select one or more departments above, then click Save workspace."
                  : "Select at least one employee above, then click Save workspace."}
              </p>
            </section>
          ) : (
            <>
              <section className="iid-card space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold">Setup checklist</h3>
                  <span className="text-xs muted">{setupComplete}/{setupRows.length} ready</span>
                </div>
                <p className="text-xs muted">Green items are ready. Open <strong>Integrations</strong> to add API keys and connect apps.</p>
                <div className="grid gap-2 md:grid-cols-2 text-sm">
                  {setupRows.map((row) => (
                    <div key={String(row.need)} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                      <span>{row.ok ? "✅" : "⬜"}</span> <strong>{String(row.need)}</strong>
                      <p className="muted text-xs">{String(row.required)}</p>
                    </div>
                  ))}
                </div>
                {!hasLlmKeys && (
                  <p className="text-sm text-amber-300">
                    No LLM API key detected yet. Agents need OpenAI, Anthropic, or similar — add one in Integrations.
                  </p>
                )}
                {hasLlmKeys && !hasPerplexity && (
                  <p className="text-sm muted">Tip: add a Perplexity key for live research and lead search.</p>
                )}
              </section>

              {pulse && (
                <section className="iid-card border border-[var(--iid-blue)]/40 space-y-3">
                  <h2 className="font-display text-lg font-bold">Taylor — Team Leader (COO)</h2>
                  {notifications.map((n, i) => <p key={i} className="text-sm">{n}</p>)}
                  {suggestions.slice(0, 3).map((s, i) => (
                    <p key={i} className="text-sm muted">→ {String(s.label || s.action || JSON.stringify(s))}</p>
                  ))}
                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="iid-btn iid-btn-primary text-xs" disabled={!!actionLoading} onClick={() => runTaylor("approve_all")}>Approve all external</button>
                    <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={!!actionLoading} onClick={() => runTaylor("retry_failed")}>Retry failed</button>
                    <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={!!actionLoading} onClick={() => runTaylor("run_next")}>Run next task</button>
                  </div>
                </section>
              )}

              <div>
                <h2 className="font-display text-lg font-bold mb-3">Step 2 — Work in your workspace</h2>
                <div className="flex flex-wrap gap-2 border-b border-[var(--iid-line)] pb-2">
                  {tabs.map((t) => (
                    <button key={t.id} type="button" className={`rounded-full px-3 py-1.5 text-xs font-semibold ${activeTab === t.id ? "bg-[var(--iid-blue)] text-white" : "text-[var(--iid-muted)] border border-[var(--iid-line)]"}`} onClick={() => setActiveTab(t.id)}>{t.label}</button>
                  ))}
                </div>
              </div>

              {error && (
                <section className="iid-card border border-red-500/40">
                  <p className="text-sm text-red-300">{error}</p>
                  <p className="text-xs muted mt-1">Fix the issue above and try again. Most problems are missing API keys or OAuth connections.</p>
                </section>
              )}
              {successMsg && <p className="text-sm text-emerald-300">{successMsg}</p>}
              {loading && <p className="text-sm muted">Loading workspace…</p>}

              {activeTab === "office" && (
                <section className="iid-card space-y-4">
                  <h3 className="font-semibold">The Office</h3>
                  <p className="text-sm muted">Clock in → standup → execution → agent sync → delivery. Same phases as Streamlit.</p>
                  <p className="text-sm">Phase: <strong>{String(office?.phase || (bootstrap?.office_state as Record<string, unknown>)?.phase || "arrival")}</strong></p>
                  {office?.last_mentor ? (
                    <div className="rounded-lg border border-[var(--iid-line)] bg-[var(--iid-panel)] p-3 text-sm">
                      <strong>Taylor:</strong> {String(office.last_mentor)}
                    </div>
                  ) : null}
                  <label className="block text-sm font-semibold">Priorities today</label>
                  <textarea className="iid-input min-h-[80px]" value={goalsText} onChange={(e) => setGoalsText(e.target.value)} placeholder="One goal per line" />
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={autoApprove} onChange={(e) => setAutoApprove(e.target.checked)} className="accent-[var(--iid-blue)]" />
                    Auto-approve external actions (LinkedIn, email, HubSpot)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {[
                      { id: "clock_in", label: "Clock in" },
                      { id: "standup", label: "Standup" },
                      { id: "next_task", label: "Next task" },
                      { id: "agent_sync", label: "Agent sync" },
                      { id: "delivery", label: "Delivery" },
                    ].map((b) => (
                      <button key={b.id} type="button" className="iid-btn iid-btn-ghost text-xs" disabled={actionLoading === b.id} onClick={() => runOfficeAction(b.id)}>
                        {actionLoading === b.id ? "…" : b.label}
                      </button>
                    ))}
                    <button type="button" className="iid-btn iid-btn-primary text-xs" disabled={!!actionLoading} onClick={() => runOfficeAction("full_day")}>
                      {actionLoading === "full_day" ? "Running…" : "Run full office day"}
                    </button>
                    <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={actionLoading === "checklist"} onClick={buildChecklist}>
                      {actionLoading === "checklist" ? "Building…" : "Build checklist from plan"}
                    </button>
                  </div>
                  {taskMsg && <p className="text-sm text-emerald-300">{taskMsg}</p>}
                  {((office?.board as Array<Record<string, unknown>>) || []).length > 0 && (
                    <>
                      <h4 className="font-semibold text-sm">Task board</h4>
                      <ul className="space-y-2 text-sm">
                        {((office?.board as Array<Record<string, unknown>>) || []).map((row) => (
                          <li key={String(row.id)} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                            <span className="font-semibold">{String(row.assignee)}</span> — {String(row.title)}
                            <span className="muted"> ({String(row.status)})</span>
                            {row.mentor_note ? <p className="text-xs muted mt-1">{String(row.mentor_note).slice(0, 200)}</p> : null}
                            <div className="mt-1">{renderArtifacts((row.artifacts as unknown[]) || [])}</div>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </section>
              )}

              {activeTab === "tasks" && (
                <section className="iid-card space-y-3">
                  <h3 className="font-semibold">Tasks & approvals</h3>
                  <p className="text-sm muted">External posts, emails, and CRM syncs pause here until you approve.</p>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={autoApprove} onChange={(e) => setAutoApprove(e.target.checked)} className="accent-[var(--iid-blue)]" />
                    Auto-approve external actions
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="iid-btn iid-btn-primary" disabled={actionLoading === "checklist"} onClick={buildChecklist}>
                      {actionLoading === "checklist" ? "Building…" : "Build checklist from plan"}
                    </button>
                    <button type="button" className="iid-btn iid-btn-ghost" disabled={actionLoading === "run-next"} onClick={runNextTask}>
                      {actionLoading === "run-next" ? "Running…" : "Approve & run next"}
                    </button>
                    <button type="button" className="iid-btn iid-btn-ghost" onClick={() => runTaylor("approve_all")}>Approve all</button>
                  </div>
                  {checklistItems.length === 0 ? (
                    <p className="text-sm muted">No tasks yet. Click <strong>Build checklist from plan</strong> after you have a business plan.</p>
                  ) : null}
                  <ul className="space-y-2 text-sm">
                    {checklistItems.map((item) => (
                      <li key={String(item.id)} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                        <span className="font-semibold">{String(item.title)}</span>
                        <span className="muted"> — {String(item.status)}</span>
                        <div className="mt-1">{renderArtifacts((item.artifacts as unknown[]) || [])}</div>
                        {(item.status === "awaiting_approval" || item.status === "qc_failed" || item.status === "failed") && (
                          <div className="mt-2 flex gap-2">
                            {item.status === "awaiting_approval" && (
                              <button type="button" className="iid-btn iid-btn-primary text-xs" onClick={() => runTaskAction(String(item.id), "approve")}>Approve</button>
                            )}
                            {(item.status === "qc_failed" || item.status === "failed") && (
                              <>
                                <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => runTaskAction(String(item.id), "retry")}>Retry</button>
                                <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => runTaskAction(String(item.id), "skip")}>Skip</button>
                              </>
                            )}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {activeTab === "war_room" && (
                <section className="iid-card space-y-4">
                  <h3 className="font-semibold">War room</h3>
                  <div className="space-y-2">
                    <p className="text-sm font-semibold">Team channel</p>
                    {((warRoom?.channel as Array<Record<string, string>>) || []).length === 0 ? (
                      <p className="text-sm muted">Messages appear when agents debate or complete tasks.</p>
                    ) : (
                      ((warRoom?.channel as Array<Record<string, string>>) || []).map((msg, i) => (
                        <div key={i} className="text-sm border-b border-[var(--iid-line)] pb-2">
                          <strong>{msg.from}</strong> · {msg.when}
                          <p className="muted mt-1">{msg.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                  <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={!!actionLoading} onClick={() => runOfficeAction("debate_sync")}>
                    Run team debate sync
                  </button>
                </section>
              )}

              {activeTab === "command" && (
                <section className="iid-card space-y-4">
                  <h3 className="font-semibold">Command center</h3>
                  {command?.metrics ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      {Object.entries(command.metrics as Record<string, number>).map(([k, v]) => (
                        <div key={k} className="rounded-lg border border-[var(--iid-line)] p-3">
                          <p className="text-xs muted uppercase">{k.replace(/_/g, " ")}</p>
                          <p className="text-xl font-bold">{v}</p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {((command?.roster as Array<Record<string, unknown>>) || []).length > 0 && (
                    <>
                      <h4 className="text-sm font-semibold">Team status</h4>
                      <ul className="text-sm space-y-1">
                        {((command?.roster as Array<Record<string, unknown>>) || []).map((r, i) => (
                          <li key={i}>{String(r.name)} — {String(r.status)} · {String(r.open_tasks)} open</li>
                        ))}
                      </ul>
                    </>
                  )}
                  <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={!!actionLoading} onClick={() => runOfficeAction("company_cycle")}>
                    Run full company cycle
                  </button>
                </section>
              )}

              {activeTab === "agents" && (
                <section className="iid-card space-y-4">
                  <h3 className="font-semibold">Agents & team</h3>
                  <div className="flex flex-wrap gap-2">
                    {agents.map((a) => (
                      <button key={a.id} type="button" className={`iid-btn text-xs ${activeAgent === a.id ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setActiveAgent(a.id)}>{a.name}</button>
                    ))}
                  </div>
                  {activeAgent && (
                    <>
                      <p className="text-sm muted">{agents.find((a) => a.id === activeAgent)?.tagline}</p>
                      <div className="max-h-64 overflow-y-auto space-y-2 rounded-xl border border-[var(--iid-line)] p-3">
                        {chat.map((turn, i) => (
                          <div key={i} className={turn.role === "user" ? "text-right" : ""}>
                            <p className="text-xs muted">{turn.role}</p>
                            <p className="text-sm whitespace-pre-wrap">{turn.content}</p>
                            {turn.role === "assistant" ? (
                              <div className="mt-1 text-left">{renderArtifacts(turn.artifacts || [], String(turn.content || ""))}</div>
                            ) : turn.artifacts && turn.artifacts.length > 0 ? (
                              <div className="mt-1">{renderArtifacts(turn.artifacts)}</div>
                            ) : null}
                          </div>
                        ))}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {(agents.find((a) => a.id === activeAgent)?.starters || []).map((s) => (
                          <button key={s} type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => sendChat(s)} disabled={chatLoading}>{s}</button>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input className="iid-input flex-1" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Tell this agent what to deliver…" onKeyDown={(e) => e.key === "Enter" && sendChat()} />
                        <button type="button" className="iid-btn iid-btn-primary" onClick={() => sendChat()} disabled={chatLoading}>{chatLoading ? "Working…" : "Send"}</button>
                      </div>
                    </>
                  )}

                  <div className="border-t border-[var(--iid-line)] pt-4 space-y-3">
                    <h4 className="font-semibold text-sm">Team and hiring</h4>
                    {employees.length > 0 ? (
                      <ul className="text-sm space-y-1">
                        {employees.map((e, i) => (
                          <li key={i}>{String(e.name)} — {String(e.role)} · {String(e.department || "")}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm muted">No hires yet — add catalog roles or a custom team member.</p>
                    )}
                    {catalogRoles.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {catalogRoles.map((r) => (
                          <button
                            key={String(r.role)}
                            type="button"
                            className="iid-btn iid-btn-ghost text-xs"
                            disabled={actionLoading === "hire"}
                            onClick={() => hireEmployee(true, String(r.role))}
                          >
                            Hire {String(r.role)}
                          </button>
                        ))}
                      </div>
                    )}
                    <div className="grid gap-2 md:grid-cols-3">
                      <input className="iid-input" value={hireName} onChange={(e) => setHireName(e.target.value)} placeholder="Custom hire name" />
                      <select className="iid-input" value={hireRole} onChange={(e) => setHireRole(e.target.value)}>
                        <option value="">Role template…</option>
                        {(coreRoles.length ? coreRoles : ["Sales Lead", "Growth Marketer", "Research Analyst", "Operations Manager"]).map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                      <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "hire"} onClick={() => hireEmployee(false)}>
                        Add to roster
                      </button>
                    </div>
                  </div>
                </section>
              )}

              {activeTab === "integrations" && (
                <section className="iid-card space-y-6">
                  <div className="space-y-3">
                    <h3 className="font-semibold">API keys (required for agents)</h3>
                    <p className="text-sm muted">
                      Keys are stored for your browser session only — not saved to disk. Your server can also provide keys via environment variables.
                    </p>
                    {activeKeyProviders.length > 0 ? (
                      <p className="text-sm text-emerald-300">Active: {activeKeyProviders.join(", ")}</p>
                    ) : (
                      <p className="text-sm text-amber-300">No keys active — agents cannot run until you add at least one LLM key.</p>
                    )}
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase muted">Perplexity (research & leads)</label>
                        <input
                          className="iid-input"
                          type="password"
                          value={perplexityKey}
                          onChange={(e) => setPerplexityKey(e.target.value)}
                          placeholder="pplx-…"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase muted">LLM key</label>
                        <div className="flex gap-2">
                          <select className="iid-input w-36" value={llmProvider} onChange={(e) => setLlmProvider(e.target.value)}>
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="deepseek">DeepSeek</option>
                            <option value="groq">Groq</option>
                          </select>
                          <input
                            className="iid-input flex-1"
                            type="password"
                            value={llmKey}
                            onChange={(e) => setLlmKey(e.target.value)}
                            placeholder="sk-…"
                          />
                        </div>
                      </div>
                    </div>
                    <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "keys"} onClick={saveApiKeys}>
                      {actionLoading === "keys" ? "Saving…" : "Save API keys"}
                    </button>
                  </div>

                  <div className="border-t border-[var(--iid-line)] pt-4 space-y-3">
                    <h3 className="font-semibold">Connect apps (OAuth)</h3>
                    <p className="text-sm muted">Needed only when tasks send email, post to LinkedIn, or sync CRM data.</p>
                    {(oauthProviders.length ? oauthProviders : oauthRows).map((row) => {
                      const provider = String(row.provider || row.App || "").toLowerCase();
                      const label = String(row.label || row.App || provider);
                      const status = String(row.status || row.Status || "unknown");
                      const envReady = row.env_ready !== false;
                      return (
                        <div key={provider || label} className="rounded-lg border border-[var(--iid-line)] p-3 text-sm space-y-2">
                          <p>
                            <strong>{label}</strong> — <span className={status === "connected" ? "text-emerald-300" : "muted"}>{status}</span>
                          </p>
                          {row.authorize_url ? (
                            <a href={String(row.authorize_url)} target="_blank" rel="noreferrer" className="iid-btn iid-btn-primary text-xs inline-flex">
                              Connect with {label}
                            </a>
                          ) : envReady === false ? (
                            <p className="text-xs text-amber-300">OAuth app not configured on server — use manual token below or ask your admin to set client ID/secret.</p>
                          ) : null}
                          {row.error ? <p className="text-xs text-amber-300">{String(row.error)}</p> : null}
                        </div>
                      );
                    })}
                  </div>

                  <div className="border-t border-[var(--iid-line)] pt-4 space-y-4">
                    <h3 className="font-semibold text-sm">Manual tokens (alternative)</h3>
                    <p className="text-xs muted">Paste tokens if OAuth redirect is not set up yet.</p>
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold">HubSpot private app token</label>
                        <input className="iid-input" type="password" value={manualHubspot} onChange={(e) => setManualHubspot(e.target.value)} placeholder="pat-…" />
                        <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={actionLoading === "oauth-hubspot"} onClick={() => saveManualOAuth("hubspot")}>
                          Save HubSpot
                        </button>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold">LinkedIn access token</label>
                        <input className="iid-input" type="password" value={manualLinkedinToken} onChange={(e) => setManualLinkedinToken(e.target.value)} placeholder="Access token" />
                        <input className="iid-input" value={manualLinkedinUrn} onChange={(e) => setManualLinkedinUrn(e.target.value)} placeholder="Author URN (urn:li:person:…)" />
                        <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={actionLoading === "oauth-linkedin"} onClick={() => saveManualOAuth("linkedin")}>
                          Save LinkedIn
                        </button>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold">Gmail app password</label>
                        <input className="iid-input" type="password" value={manualGmailPassword} onChange={(e) => setManualGmailPassword(e.target.value)} placeholder="16-character app password" />
                        <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={actionLoading === "oauth-gmail"} onClick={() => saveManualOAuth("gmail")}>
                          Save Gmail SMTP
                        </button>
                      </div>
                    </div>
                  </div>
                </section>
              )}

              {activeTab === "advanced" && (
                <section className="iid-card space-y-4">
                  <h3 className="font-semibold">Advanced</h3>
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold">Custom harnesses</h4>
                    {customHarnesses.length > 0 ? (
                      <ul className="text-sm space-y-1">
                        {customHarnesses.map((h) => (
                          <li key={String(h.id)}>{String(h.name)} → {String(h.base_harness_id)}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm muted">No custom agents yet.</p>
                    )}
                    <div className="grid gap-2 md:grid-cols-2">
                      <input className="iid-input" value={harnessName} onChange={(e) => setHarnessName(e.target.value)} placeholder="Name (e.g. Priya - Partnerships)" />
                      <select className="iid-input" value={harnessBase} onChange={(e) => setHarnessBase(e.target.value)}>
                        {baseHarnessOptions.map((o) => (
                          <option key={o.id} value={o.id}>{o.label}</option>
                        ))}
                      </select>
                      <input className="iid-input md:col-span-2" value={harnessTagline} onChange={(e) => setHarnessTagline(e.target.value)} placeholder="Tagline" />
                      <textarea className="iid-input md:col-span-2 min-h-[80px]" value={harnessStarters} onChange={(e) => setHarnessStarters(e.target.value)} placeholder="Starters (one per line)" />
                      <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "harness"} onClick={addHarness}>Create harness</button>
                    </div>
                  </div>
                  <div className="border-t border-[var(--iid-line)] pt-4 space-y-2">
                    <h4 className="text-sm font-semibold">Company memory</h4>
                    <p className="text-sm muted">Shared memory populated as agents run tools (same as Streamlit Advanced tab).</p>
                    <pre className="text-xs overflow-auto max-h-96 rounded-lg border border-[var(--iid-line)] p-3">
                      {JSON.stringify(companyMemory || {}, null, 2)}
                    </pre>
                  </div>
                </section>
              )}
            </>
          )}
        </>
      )}
      {selectedId && pulse && (
        <TaylorBubble
          pulse={pulse as ComponentProps<typeof TaylorBubble>["pulse"]}
          onAction={handleTaylorAction}
          loading={!!actionLoading}
        />
      )}
    </div>
  );
}

export default function TeamPage() {
  return (
    <Suspense fallback={<p className="muted">Loading...</p>}>
      <TeamContent />
    </Suspense>
  );
}