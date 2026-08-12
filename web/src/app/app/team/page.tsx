"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState, type ComponentProps, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { DeliverablePreview } from "@/components/DeliverablePreview";
import { OfficeFloor } from "@/components/OfficeFloor";
import { TaylorBubble } from "@/components/TaylorBubble";
import { ProjectPicker } from "@/components/ProjectPicker";
import { AgentChatDrawer } from "@/components/employee-os/AgentChatDrawer";
import { EmployeeOsChrome } from "@/components/employee-os/EmployeeOsChrome";
import { useProjects } from "@/hooks/useProjects";

type Agent = { id: string; name?: string; role?: string; tagline?: string; starters?: string[]; department?: string; is_leader?: boolean };
type FloorMember = { id: string; name: string; role?: string; department?: string; is_leader?: boolean };
type DeptCatalogRow = { id: string; name: string; description?: string; parent?: string | null };
type OrgNode = {
  id: string;
  name: string;
  headcount?: number;
  agents?: Array<Record<string, unknown>>;
  humans?: Array<Record<string, unknown>>;
  children?: OrgNode[];
};
type TabDef = { id: string; label: string };
type ChatTurn = { role: string; content?: string; artifacts?: string[] };

const FULL_TABS: TabDef[] = [
  { id: "office", label: "The Office" },
  { id: "hiring", label: "Hiring" },
  { id: "tasks", label: "Tasks & Approvals" },
  { id: "war_room", label: "War Room" },
  { id: "command", label: "Command Center" },
  { id: "agents", label: "Agents & Team" },
  { id: "integrations", label: "Integrations" },
  { id: "advanced", label: "Advanced" },
];
const EMP_TABS: TabDef[] = [
  { id: "agents", label: "Agents & Team" },
  { id: "tasks", label: "Tasks & Approvals" },
  { id: "hiring", label: "Hiring" },
  { id: "integrations", label: "Integrations" },
];

function tabsForMode(mode: string): TabDef[] {
  // Keep the full Nexus-style chrome for every scope so working tabs stay one click away.
  if (mode === "employee") return EMP_TABS;
  return FULL_TABS;
}

function TeamContent() {
  const { projects, selectedId, setSelectedId } = useProjects();
  const searchParams = useSearchParams();
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

  const [deptCatalog, setDeptCatalog] = useState<DeptCatalogRow[]>([]);
  const [deptHeadcounts, setDeptHeadcounts] = useState<Record<string, number>>({});
  const [hiredDepartments, setHiredDepartments] = useState<Array<{ id: string; name: string; headcount: number }>>([]);
  const [orgTree, setOrgTree] = useState<{ roots?: OrgNode[] } | null>(null);
  const [humans, setHumans] = useState<Array<Record<string, unknown>>>([]);
  const [collaboration, setCollaboration] = useState<Record<string, unknown> | null>(null);
  const [humanName, setHumanName] = useState("");
  const [humanRole, setHumanRole] = useState("");
  const [humanDepts, setHumanDepts] = useState<string[]>([]);
  const [broadcastInput, setBroadcastInput] = useState("");
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);
  const [taskFilter, setTaskFilter] = useState("all");
  const [hirePanelOpen, setHirePanelOpen] = useState(true);
  const isDemoReadonly = Boolean(bootstrap?.demo_readonly);

  const agents = (bootstrap?.agents as Agent[]) || [];
  const hiredAgents = (bootstrap?.hired_agents as Agent[]) || [];
  const floorMembers = useMemo(() => {
    const leader: FloorMember = {
      id: "taylor",
      name: "Taylor — Team Leader (COO)",
      role: "COO",
      department: "Operations",
      is_leader: true,
    };
    const hired = hiredAgents.map((a) => ({
      id: String((a as Record<string, unknown>).harness_id || a.id),
      name: String(a.name || a.role || "Teammate"),
      role: a.role,
      department: a.department,
      is_leader: false,
    }));
    return [leader, ...hired];
  }, [hiredAgents]);
  const chatAgents: Agent[] = floorMembers.length > 1
    ? floorMembers.map((m) => ({ ...m, tagline: m.is_leader ? "Orchestrates your virtual team" : "", starters: [] as string[] }))
    : [
        { id: "taylor", name: "Taylor — Team Leader (COO)", role: "COO", tagline: "Orchestrates your virtual team", department: "Operations", is_leader: true, starters: [] },
        ...hiredAgents.map((a) => ({
          id: String((a as Record<string, unknown>).harness_id || a.id),
          name: a.name,
          role: a.role,
          department: a.department,
          tagline: "",
          starters: [] as string[],
        })),
      ];
  const deptOptions = (bootstrap?.departments as string[]) || [];
  const scopeConfigured = scopeMode === "full_office" || hiredDepartments.length > 0 || (scopeMode === "department" && departments.length > 0) || (scopeMode === "employee" && harnessIds.length > 0);
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
      if (!activeAgent && chatAgents[0]?.id) {
        setActiveAgent(chatAgents[0].id);
      }
      const hired = (data.hired_departments as Array<{ id: string; name: string; headcount: number }>) || [];
      setHiredDepartments(hired);
      setHirePanelOpen(hired.length === 0);
      const counts: Record<string, number> = {};
      hired.forEach((h) => { counts[h.id] = h.headcount; });
      setDeptHeadcounts(counts);
      setHumans((data.humans as Array<Record<string, unknown>>) || []);
      setCollaboration((data.collaboration as Record<string, unknown>) || null);
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
    if (!selectedId || !actionLoading) return;
    const officeActions = new Set(["full_day", "clock_in", "standup", "next_task", "agent_sync", "delivery", "debate_sync", "company_cycle"]);
    if (!officeActions.has(actionLoading)) return;
    const timer = window.setInterval(() => {
      api.getOs2Office(selectedId).then((data) => setOffice(data)).catch(() => null);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [selectedId, actionLoading]);

  useEffect(() => {
    if (!selectedId) return;
    api.getOs2Departments(selectedId).then((d) => setDeptCatalog((d.catalog as DeptCatalogRow[]) || [])).catch(() => {});
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId || !activeAgent) return;
    api.getOs2Chat(selectedId, activeAgent).then((d) => setChat((d.chat as ChatTurn[]) || [])).catch(() => setChat([]));
  }, [selectedId, activeAgent]);

  useEffect(() => {
    if (!tabs.find((t) => t.id === activeTab)) setActiveTab(tabs[0]?.id || "agents");
  }, [tabs, activeTab]);

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab && tabs.some((t) => t.id === tab)) setActiveTab(tab);
    const agent = searchParams.get("agent");
    if (agent) {
      setActiveAgent(agent);
      setChatDrawerOpen(true);
    }
  }, [searchParams, tabs]);

  useEffect(() => {
    if (!selectedId || !scopeConfigured) return;
    if (activeTab === "command") api.getOs2Command(selectedId).then(setCommand).catch(() => setCommand(null));
    if (activeTab === "war_room") api.getOs2WarRoom(selectedId).then(setWarRoom).catch(() => setWarRoom(null));
    if (activeTab === "integrations") api.getOs2OAuth(selectedId).then((d) => setOauthProviders(d.providers || [])).catch(() => setOauthProviders([]));
    if (activeTab === "advanced") api.getOs2Memory(selectedId).then((d) => setCompanyMemory(d.memory || {})).catch(() => setCompanyMemory(null));
    if (activeTab === "advanced" || activeTab === "agents") api.getOs2Harnesses(selectedId).then((d) => setCustomHarnesses(d.custom || [])).catch(() => setCustomHarnesses([]));
    if (activeTab === "agents" || activeTab === "hiring" || activeTab === "organization") {
      api.getOs2Employees(selectedId).then((d) => { setEmployees(d.employees || []); setCatalogRoles(d.catalog_roles || []); setCoreRoles(d.core_roles || []); }).catch(() => { setEmployees([]); setCatalogRoles([]); setCoreRoles([]); });
    }
    if (activeTab === "hiring" || activeTab === "organization" || activeTab === "office") {
      api.getOs2Departments(selectedId).then((d) => {
        setDeptCatalog((d.catalog as DeptCatalogRow[]) || []);
        const hired = (d.hired as Array<{ id: string; name: string; headcount: number }>) || [];
        setHiredDepartments(hired);
        const counts: Record<string, number> = {};
        hired.forEach((h) => { counts[h.id] = h.headcount; });
        setDeptHeadcounts(counts);
      }).catch(() => setDeptCatalog([]));
      api.getOs2OrgChart(selectedId).then((d) => setOrgTree((d.tree as { roots?: OrgNode[] }) || null)).catch(() => setOrgTree(null));
    }
    if (activeTab === "agents" || activeTab === "tasks") {
      api.getOs2Collaboration(selectedId).then(setCollaboration).catch(() => setCollaboration(null));
      api.getOs2Humans(selectedId).then((d) => setHumans(d.humans || [])).catch(() => setHumans([]));
    }
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

  async function hireDepartments() {
    if (!selectedId) return;
    const rows = Object.entries(deptHeadcounts)
      .filter(([, n]) => n > 0)
      .map(([id, headcount]) => ({
        id,
        name: deptCatalog.find((d) => d.id === id)?.name || id,
        headcount,
      }));
    if (!rows.length) {
      setError("Select at least one department and set headcount.");
      return;
    }
    setActionLoading("hire-depts");
    setError("");
    setSuccessMsg("");
    try {
      await api.setOs2Departments(selectedId, rows);
      setSuccessMsg(`Hired team across ${rows.length} department(s).`);
      if (scopeMode === "employee") setScopeMode("full_office");
      setActiveTab("office");
      await refresh();
      const chart = await api.getOs2OrgChart(selectedId);
      setOrgTree((chart.tree as { roots?: OrgNode[] }) || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not hire departments");
    } finally {
      setActionLoading("");
    }
  }

  function toggleDeptHeadcount(deptId: string, delta: number) {
    setDeptHeadcounts((prev) => {
      const next = Math.max(0, Math.min(10, (prev[deptId] || 0) + delta));
      return { ...prev, [deptId]: next };
    });
  }

  async function addHumanMember() {
    if (!selectedId || !humanName.trim()) return;
    setActionLoading("add-human");
    setError("");
    try {
      const data = await api.addOs2Human(selectedId, { name: humanName.trim(), role: humanRole, departments: humanDepts });
      setHumans((data.humans as Array<Record<string, unknown>>) || []);
      setHumanName("");
      setHumanRole("");
      setHumanDepts([]);
      setSuccessMsg("Human team member added.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add team member");
    } finally {
      setActionLoading("");
    }
  }

  async function removeHuman(humanId: string) {
    if (!selectedId) return;
    setActionLoading(`rm-${humanId}`);
    try {
      const data = await api.removeOs2Human(selectedId, humanId);
      setHumans(data.humans || []);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove team member");
    } finally {
      setActionLoading("");
    }
  }

  function openAgentChat(harnessId: string) {
    setActiveAgent(harnessId);
    setChatDrawerOpen(true);
  }

  function applyHirePreset(preset: "solo" | "lean" | "full") {
    const next: Record<string, number> = {};
    if (preset === "solo") next.operations = 1;
    if (preset === "lean") {
      next.operations = 1;
      next.sales = 1;
      next.marketing = 1;
      next.research = 1;
    }
    if (preset === "full") {
      (deptCatalog.length ? deptCatalog : [{ id: "sales" }, { id: "marketing" }, { id: "operations" }, { id: "research" }]).forEach((d) => {
        next[d.id] = 1;
      });
    }
    setDeptHeadcounts(next);
  }

  async function sendBroadcast() {
    if (!selectedId || !broadcastInput.trim()) return;
    setActionLoading("broadcast");
    try {
      await api.postOs2Broadcast(selectedId, broadcastInput.trim());
      setBroadcastInput("");
      setSuccessMsg("Message sent to the team channel.");
      if (activeTab === "war_room") {
        const data = await api.getOs2WarRoom(selectedId);
        setWarRoom(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Broadcast failed");
    } finally {
      setActionLoading("");
    }
  }

  function renderOrgNode(node: OrgNode, depth = 0): ReactNode {
    const agentCount = (node.agents || []).length;
    const humanCount = (node.humans || []).length;
    return (
      <li key={node.id} className="org-tree-node" style={{ marginLeft: depth * 16 }}>
        <div className="rounded-lg border border-[var(--iid-line)] px-3 py-2 mb-2 bg-[var(--iid-panel)]">
          <p className="font-semibold text-sm">{node.name}</p>
          <p className="text-xs muted">
            {node.headcount ? `${node.headcount} AI · ` : ""}
            {agentCount} agent{agentCount !== 1 ? "s" : ""}
            {humanCount ? ` · ${humanCount} human${humanCount !== 1 ? "s" : ""}` : ""}
          </p>
          {(node.agents || []).length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {(node.agents || []).map((a) => {
                const hid = String(a.harness_id || a.id || "");
                return (
                  <button
                    key={hid}
                    type="button"
                    className="iid-btn iid-btn-ghost text-xs py-1"
                    onClick={() => openAgentChat(hid)}
                  >
                    {String(a.name || hid)}
                  </button>
                );
              })}
            </div>
          )}
        </div>
        {(node.children || []).length > 0 && (
          <ul className="space-y-1 border-l border-[var(--iid-line)] ml-2 pl-3">
            {(node.children || []).map((child) => renderOrgNode(child, depth + 1))}
          </ul>
        )}
      </li>
    );
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
    if (!reply && paths.length === 0) return null;
    return <DeliverablePreview title={title} reply={reply} artifacts={paths} />;
  }

  const liveChatSnippet = useMemo(() => {
    const last = [...chat].reverse().find((m) => m.role === "assistant");
    return last?.content ? String(last.content) : "";
  }, [chat]);
  const checklistItems = ((checklist?.items as Array<Record<string, unknown>>) || []);
  const setupRows = (bootstrap?.setup_requirements as Array<Record<string, unknown>>) || [];
  const oauthRows = (bootstrap?.oauth_status as Array<Record<string, unknown>>) || [];
  const notifications = (pulse?.notifications as string[]) || [];
  const suggestions = (pulse?.suggestions as Array<Record<string, unknown>>) || [];
  const setupComplete = setupRows.filter((r) => r.ok).length;
  const hasLlmKeys = activeKeyProviders.some((p) => p !== "perplexity");
  const hasPerplexity = activeKeyProviders.includes("perplexity");

  const approvalCount = checklistItems.filter((i) => String(i.status) === "awaiting_approval").length;
  const tickerLines = useMemo(() => {
    const lines: string[] = [];
    notifications.slice(0, 2).forEach((n) => lines.push(n));
    (((office?.activity as Array<Record<string, unknown>>) || [])).slice(0, 4).forEach((a) => {
      const text = String(a.text || a.message || "");
      if (text) lines.push(`${String(a.from || "Team")}: ${text.slice(0, 72)}`);
    });
    return lines;
  }, [notifications, office]);
  const filteredTasks = taskFilter === "all"
    ? checklistItems
    : checklistItems.filter((i) => String(i.status) === taskFilter);
  const phaseLabel = String(office?.phase || (bootstrap?.office_state as Record<string, unknown>)?.phase || "arrival");

  if (projects.length === 0) {
    return (
      <section className="iid-card space-y-3">
        <h1 className="font-display text-2xl font-bold">Employee OS</h1>
        <p className="muted">No projects yet.</p>
        <Link href="/app/projects" className="iid-btn iid-btn-primary inline-flex">Create your first project</Link>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <EmployeeOsChrome
        title="Employee OS"
        subtitle={`${floorMembers.length} on the floor · phase: ${phaseLabel}${bootstrap ? ` · ${String(bootstrap.topic || "")}` : ""}`}
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        approvalCount={approvalCount}
        onTalkToTaylor={() => openAgentChat("taylor")}
        onOpenApprovals={() => setActiveTab("tasks")}
        ticker={tickerLines}
        demoReadonly={isDemoReadonly}
        team={floorMembers.map((m) => ({ id: m.id, name: m.name, role: m.role, isLeader: Boolean(m.is_leader) }))}
        activeChatId={chatDrawerOpen ? activeAgent : undefined}
        onChatMember={(id) => openAgentChat(id)}
        projectPicker={
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px]">
              <ProjectPicker projects={projects} selectedId={selectedId} onChange={setSelectedId} />
            </div>
            <p className="text-[11px] muted hidden lg:block shrink-0" data-iida-live>
              IIDA is your personal aide below — she can brief Taylor anytime.
            </p>
            {isDemoReadonly ? (
              <Link href="/login?mode=register" className="text-xs text-amber-200 underline shrink-0">Sign up to run real work</Link>
            ) : null}
          </div>
        }
      >
        {error ? (
          <div className="mb-4 rounded-xl border border-red-500/40 bg-red-500/5 px-3 py-2 text-sm text-red-200">
            {error}
            {(isDemoReadonly || /demo|read-only|view-only/i.test(error)) ? (
              <Link href="/login?mode=register" className="iid-btn iid-btn-primary text-xs mt-2 inline-flex">Create free account</Link>
            ) : null}
          </div>
        ) : null}
        {successMsg ? <p className="mb-3 text-sm text-emerald-300">{successMsg}</p> : null}
        {loading ? <p className="mb-3 text-sm muted">Loading workspace…</p> : null}

        {activeTab === "hiring" && (
          <div className="space-y-4 max-w-5xl">
            <div>
              <h2 className="font-semibold text-base">Hiring</h2>
              <p className="text-sm muted mt-1">
                Add departments here. The Office, Tasks, and Team bar stay in the chrome above — no scrolling through hiring to work.
              </p>
            </div>

            <details
              className="rounded-xl border border-[var(--iid-line)] bg-[var(--iid-panel)]/40 px-4 py-3 group"
              open={hirePanelOpen}
              onToggle={(e) => setHirePanelOpen(e.currentTarget.open)}
            >
              <summary className="cursor-pointer font-semibold text-sm flex items-center justify-between gap-2">
                <span>Build your team</span>
                <span className="text-[11px] muted font-normal">
                  {hiredDepartments.length
                    ? `${hiredDepartments.reduce((n, h) => n + h.headcount, 0)} hired · expand to adjust`
                    : "Pick departments & headcount"}
                </span>
              </summary>
              <div className="mt-4 space-y-4 border-t border-[var(--iid-line)] pt-4">
                <div className="flex flex-wrap gap-2">
                  <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => applyHirePreset("solo")}>Solo founder</button>
                  <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => applyHirePreset("lean")}>Lean team</button>
                  <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => applyHirePreset("full")}>Full company</button>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {(deptCatalog.length ? deptCatalog : [{ id: "sales", name: "Sales" }, { id: "marketing", name: "Marketing" }, { id: "operations", name: "Operations" }]).map((d) => {
                    const count = deptHeadcounts[d.id] || 0;
                    const hired = hiredDepartments.find((h) => h.id === d.id)?.headcount || 0;
                    return (
                      <div key={d.id} className={`rounded-xl border px-3 py-2.5 text-sm ${count > 0 || hired > 0 ? "border-[var(--iid-blue)]" : "border-[var(--iid-line)]"}`}>
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-semibold truncate">{d.name}</p>
                            <p className="text-[11px] muted truncate">{d.description || ""}{hired ? ` · ${hired} hired` : ""}</p>
                          </div>
                          <div className="flex items-center gap-1 shrink-0">
                            <button type="button" className="iid-btn iid-btn-ghost text-xs px-2" onClick={() => toggleDeptHeadcount(d.id, -1)}>−</button>
                            <span className="w-6 text-center font-bold font-mono">{count}</span>
                            <button type="button" className="iid-btn iid-btn-ghost text-xs px-2" onClick={() => toggleDeptHeadcount(d.id, 1)}>+</button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "hire-depts" || isDemoReadonly} onClick={hireDepartments}>
                  {actionLoading === "hire-depts" ? "Hiring…" : "Hire team"}
                </button>
                {hiredDepartments.length > 0 ? (
                  <p className="text-xs text-emerald-300">Active: {hiredDepartments.map((h) => `${h.name} (${h.headcount})`).join(" · ")}</p>
                ) : null}
              </div>
            </details>

            <details className="text-sm rounded-xl border border-[var(--iid-line)] px-4 py-3">
              <summary className="cursor-pointer font-medium text-sm">Organization chart & scope</summary>
              <div className="mt-3 space-y-3 border-t border-[var(--iid-line)] pt-3">
                {(orgTree?.roots || []).length === 0 ? (
                  <p className="text-sm muted">Open Build your team above to hire, then the org chart appears here.</p>
                ) : (
                  <ul className="space-y-2">{(orgTree?.roots || []).map((n) => renderOrgNode(n))}</ul>
                )}
                <div className="flex flex-wrap gap-2 pt-2 border-t border-[var(--iid-line)]">
                  {["full_office", "department", "employee"].map((m) => (
                    <button key={m} type="button" className={`iid-btn text-xs ${scopeMode === m ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setScopeMode(m)}>
                      {m === "full_office" ? "Full office" : m === "department" ? "Department" : "Employee"}
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
                <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={isDemoReadonly} onClick={saveScope}>Save scope</button>
              </div>
            </details>
          </div>
        )}

        {activeTab === "office" && (
          <div className="space-y-4">
            {floorMembers.length <= 1 ? (
              <div className="rounded-xl border border-dashed border-[var(--iid-line)] p-8 text-center space-y-3">
                <p className="font-semibold">Your office is empty</p>
                <p className="text-sm muted">Hire at least one department to put people on the floor.</p>
                <button type="button" className="iid-btn iid-btn-primary text-sm" onClick={() => setActiveTab("hiring")}>Go to Hiring</button>
              </div>
            ) : (
              <>
                <div className="rounded-xl border border-[var(--iid-blue)]/30 bg-[var(--iid-blue)]/5 p-3 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">Taylor — Team Leader (COO)</p>
                    <p className="text-xs muted mt-0.5">
                      Phase: {phaseLabel} · {approvalCount} pending · {checklistItems.filter((i) => String(i.status) === "pending").length} queued
                    </p>
                    {String(pulse?.headline || "") ? (
                      <p className="text-xs mt-1 text-[var(--iid-ink)]">{String(pulse?.headline)}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => openAgentChat("taylor")}>Chat</button>
                    <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={!!actionLoading || isDemoReadonly} onClick={() => runTaylor("approve_all")}>Approve all</button>
                    <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={!!actionLoading || isDemoReadonly} onClick={() => runTaylor("run_next")}>Run next</button>
                  </div>
                </div>
                {suggestions.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {suggestions.slice(0, 4).map((s, i) => {
                      const kind = String(s.kind || "");
                      const label = String(s.label || "Next step");
                      return (
                        <button
                          key={`${kind}-${i}`}
                          type="button"
                          className="iid-btn iid-btn-ghost text-xs"
                          disabled={!!actionLoading || isDemoReadonly}
                          onClick={() => {
                            if (kind === "open_keys") setActiveTab("integrations");
                            else if (kind === "review_approvals") setActiveTab("tasks");
                            else if (kind === "retry_failed") void runTaylor("retry_failed");
                            else if (kind === "run_next") void runTaylor("run_next");
                            else if (kind === "employee_prompt" && s.harness_id) {
                              void openAgentChat(String(s.harness_id));
                            } else {
                              void openAgentChat("taylor");
                            }
                          }}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                ) : null}
                <div className="grid gap-4 xl:grid-cols-3">
                  <div className="xl:col-span-2 space-y-4">
                    <div className="rounded-xl border border-[var(--iid-line)] bg-[var(--iid-panel)]/40 p-3 space-y-3">
                      <textarea className="iid-input min-h-[72px] text-sm" value={goalsText} onChange={(e) => setGoalsText(e.target.value)} placeholder="Today's priorities (one per line)…" />
                      <label className="flex items-center gap-2 text-xs muted">
                        <input type="checkbox" checked={autoApprove} onChange={(e) => setAutoApprove(e.target.checked)} className="accent-[var(--iid-blue)]" disabled={isDemoReadonly} />
                        Auto-approve LinkedIn, email, and HubSpot actions
                      </label>
                      <div className="flex flex-wrap gap-2">
                        <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={!!actionLoading || isDemoReadonly} onClick={buildChecklist}>
                          {actionLoading === "checklist" ? "Building…" : "Build task checklist"}
                        </button>
                        <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={!!actionLoading || isDemoReadonly} onClick={() => runOfficeAction("full_day")}>
                          {actionLoading === "full_day" ? "Running…" : "Run office day"}
                        </button>
                        <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={!!actionLoading || isDemoReadonly} onClick={runNextTask}>Run next task</button>
                      </div>
                      {taskMsg ? <p className="text-xs text-emerald-300">{taskMsg}</p> : null}
                    </div>
                    <OfficeFloor
                      members={floorMembers}
                      phase={phaseLabel}
                      board={(office?.board as Array<Record<string, unknown>>) || []}
                      activity={(office?.activity as Array<Record<string, unknown>>) || []}
                      lastMentor={String(office?.last_mentor || "")}
                      activeAgentId={activeAgent}
                      chatLoading={chatLoading}
                      liveChatSnippet={liveChatSnippet}
                      officeRunning={Boolean(actionLoading && ["full_day", "clock_in", "standup", "next_task", "agent_sync", "delivery"].includes(actionLoading))}
                      onSelectMember={(id) => openAgentChat(id)}
                    />
                  </div>
                  <aside className="rounded-xl border border-[var(--iid-line)] bg-[var(--iid-panel)]/40 flex flex-col max-h-[70vh]">
                    <div className="px-3 py-2.5 border-b border-[var(--iid-line)] text-sm font-semibold">Activity feed</div>
                    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2 text-sm">
                      {(((office?.activity as Array<Record<string, unknown>>) || []).length === 0) ? (
                        <p className="text-xs muted py-4">Activity appears as the team works. Use the Team bar above to chat with anyone.</p>
                      ) : ((office?.activity as Array<Record<string, unknown>>) || []).map((a, i) => (
                        <div key={i} className="border-b border-[var(--iid-line)] pb-2">
                          <p className="text-[10px] muted font-mono">{String(a.when || "")}</p>
                          <p><strong>{String(a.from || "Team")}</strong> — {String(a.text || a.message || "")}</p>
                        </div>
                      ))}
                    </div>
                  </aside>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === "tasks" && (
          <div className="space-y-3 max-w-4xl">
            <div>
              <h2 className="font-semibold">Tasks & Approvals</h2>
              <p className="text-sm muted mt-1">External posts, emails, and CRM syncs pause here until you approve.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "checklist" || isDemoReadonly} onClick={buildChecklist}>Build checklist</button>
              <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={!!actionLoading || isDemoReadonly} onClick={runNextTask}>Approve & run next</button>
              <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={isDemoReadonly} onClick={() => runTaylor("approve_all")}>Approve all</button>
              <button type="button" className="iid-btn iid-btn-ghost text-sm" disabled={isDemoReadonly} onClick={() => runTaylor("retry_failed")}>Retry failed</button>
            </div>
            {checklistItems.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {["all", "pending", "awaiting_approval", "completed", "failed", "qc_failed"].map((f) => (
                  <button key={f} type="button" className={`px-2.5 py-1 rounded-full text-xs border ${taskFilter === f ? "bg-[var(--iid-blue)]/20 border-[var(--iid-blue)]/40" : "border-[var(--iid-line)] muted"}`} onClick={() => setTaskFilter(f)}>{f.replace(/_/g, " ")}</button>
                ))}
              </div>
            ) : (
              <p className="text-sm muted">No tasks yet. Build a checklist from The Office after you have a plan.</p>
            )}
            <ul className="space-y-2 text-sm">
              {filteredTasks.map((item) => (
                <li key={String(item.id)} className="rounded-xl border border-[var(--iid-line)] px-3 py-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{String(item.title)}</span>
                    <span className={`text-xs rounded-full px-2 py-0.5 ${item.assignee_type === "human" ? "bg-amber-500/20 text-amber-200" : "bg-[var(--iid-blue)]/20"}`}>
                      {item.assignee_type === "human" ? "You" : "AI"}
                    </span>
                    <span className="muted text-xs">— {String(item.status)}</span>
                  </div>
                  {item.human_action ? <p className="text-xs text-amber-300 mt-1">{String(item.human_action)}</p> : null}
                  {item.ai_action ? <p className="text-xs muted mt-1">{String(item.ai_action)}</p> : null}
                  <div className="mt-1">{renderArtifacts((item.artifacts as unknown[]) || [], String(item.result || ""))}</div>
                  {(item.status === "awaiting_approval" || item.status === "qc_failed" || item.status === "failed") && !isDemoReadonly ? (
                    <div className="mt-2 flex gap-2">
                      {item.status === "awaiting_approval" ? (
                        <button type="button" className="iid-btn iid-btn-primary text-xs" onClick={() => runTaskAction(String(item.id), "approve")}>Approve</button>
                      ) : null}
                      {(item.status === "qc_failed" || item.status === "failed") ? (
                        <>
                          <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => runTaskAction(String(item.id), "retry")}>Retry</button>
                          <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => runTaskAction(String(item.id), "skip")}>Skip</button>
                        </>
                      ) : null}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
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
                  <div className="flex gap-2">
                    <input className="iid-input flex-1" value={broadcastInput} onChange={(e) => setBroadcastInput(e.target.value)} placeholder="Message the whole team…" onKeyDown={(e) => e.key === "Enter" && sendBroadcast()} />
                    <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "broadcast"} onClick={sendBroadcast}>Send</button>
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
                  <div className="grid gap-4 lg:grid-cols-[200px_1fr]">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold uppercase muted mb-2">Chat with</p>
                      {chatAgents.map((a) => (
                        <button
                          key={a.id}
                          type="button"
                          className={`w-full text-left rounded-lg px-3 py-2 text-xs ${activeAgent === a.id ? "bg-[var(--iid-blue)] text-white" : "border border-[var(--iid-line)]"}`}
                          onClick={() => {
                            setActiveAgent(a.id);
                            setChatDrawerOpen(true);
                          }}
                        >
                          <span className="font-semibold block">{a.name}</span>
                          <span className="opacity-70">{a.department || a.role}</span>
                        </button>
                      ))}
                    </div>
                    <div className="space-y-3">
                      {activeAgent ? (
                        <>
                          <p className="text-sm muted">{chatAgents.find((a) => a.id === activeAgent)?.tagline}</p>
                          <p className="text-xs muted">
                            Open the full chat drawer for a clearer thread, starters, and deliverables.
                          </p>
                          <button
                            type="button"
                            className="iid-btn iid-btn-primary text-sm"
                            onClick={() => setChatDrawerOpen(true)}
                          >
                            Open chat with {String(chatAgents.find((a) => a.id === activeAgent)?.name || "agent").split("—")[0].trim()}
                          </button>
                          {(chatAgents.find((a) => a.id === activeAgent)?.starters || []).length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                              {(chatAgents.find((a) => a.id === activeAgent)?.starters || []).map((s) => (
                                <button
                                  key={s}
                                  type="button"
                                  className="iid-btn iid-btn-ghost text-xs"
                                  onClick={() => {
                                    setChatDrawerOpen(true);
                                    void sendChat(s);
                                  }}
                                  disabled={chatLoading}
                                >
                                  {s}
                                </button>
                              ))}
                            </div>
                          ) : null}
                        </>
                      ) : (
                        <p className="text-sm muted">Pick an agent on the left to open chat.</p>
                      )}
                    </div>
                  </div>

                  <div className="border-t border-[var(--iid-line)] pt-4 space-y-3">
                    <h4 className="font-semibold text-sm">Human team members</h4>
                    <p className="text-xs muted">Humans observe AI work, handle approvals, and get assigned action items.</p>
                    {humans.length > 0 ? (
                      <ul className="text-sm space-y-2">
                        {humans.map((h) => (
                          <li key={String(h.id)} className="flex items-center justify-between rounded-lg border border-[var(--iid-line)] px-3 py-2">
                            <span><strong>{String(h.name)}</strong> — {String(h.role)}</span>
                            <button type="button" className="iid-btn iid-btn-ghost text-xs" disabled={!!actionLoading} onClick={() => removeHuman(String(h.id))}>Remove</button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm muted">No human team members yet.</p>
                    )}
                    <div className="grid gap-2 md:grid-cols-2">
                      <input className="iid-input" value={humanName} onChange={(e) => setHumanName(e.target.value)} placeholder="Name" />
                      <input className="iid-input" value={humanRole} onChange={(e) => setHumanRole(e.target.value)} placeholder="Role (e.g. Founder)" />
                    </div>
                    <div>
                      <p className="text-xs muted mb-1">Departments they work with</p>
                      <div className="flex flex-wrap gap-2">
                        {(deptCatalog.length ? deptCatalog : hiredDepartments.map((h) => ({ id: h.id, name: h.name }))).map((d) => (
                          <button
                            key={d.id}
                            type="button"
                            className={`iid-btn text-xs ${humanDepts.includes(d.id) ? "iid-btn-primary" : "iid-btn-ghost"}`}
                            onClick={() => setHumanDepts((prev) => prev.includes(d.id) ? prev.filter((x) => x !== d.id) : [...prev, d.id])}
                          >
                            {d.name}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button type="button" className="iid-btn iid-btn-primary text-sm" disabled={actionLoading === "add-human"} onClick={addHumanMember}>Add human team member</button>
                  </div>

                  {collaboration?.summary ? (
                    <div className="border-t border-[var(--iid-line)] pt-4 space-y-3">
                      <h4 className="font-semibold text-sm">AI vs human work split</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                        <div className="rounded-lg border border-[var(--iid-line)] p-2">
                          <p className="text-xs muted">AI tasks</p>
                          <p className="font-bold">{String((collaboration.summary as Record<string, number>).ai_done || 0)}/{(collaboration.summary as Record<string, number>).ai_total || 0}</p>
                        </div>
                        <div className="rounded-lg border border-[var(--iid-line)] p-2">
                          <p className="text-xs muted">Your tasks</p>
                          <p className="font-bold">{String((collaboration.summary as Record<string, number>).human_done || 0)}/{(collaboration.summary as Record<string, number>).human_total || 0}</p>
                        </div>
                        <div className="rounded-lg border border-[var(--iid-line)] p-2">
                          <p className="text-xs muted">AI agents</p>
                          <p className="font-bold">{String((collaboration.summary as Record<string, number>).agents_active || 0)}</p>
                        </div>
                        <div className="rounded-lg border border-[var(--iid-line)] p-2">
                          <p className="text-xs muted">Humans</p>
                          <p className="font-bold">{String((collaboration.summary as Record<string, number>).humans_on_team || 0)}</p>
                        </div>
                      </div>
                      {((collaboration.human_queue as Array<Record<string, unknown>>) || []).length > 0 && (
                        <>
                          <p className="text-xs font-semibold">Your action queue</p>
                          <ul className="text-sm space-y-1">
                            {((collaboration.human_queue as Array<Record<string, unknown>>) || []).slice(0, 5).map((item, i) => (
                              <li key={i} className="text-amber-300">→ {String(item.action)} <span className="muted">({String(item.status)})</span></li>
                            ))}
                          </ul>
                        </>
                      )}
                    </div>
                  ) : null}

                  <div className="border-t border-[var(--iid-line)] pt-4 space-y-3">
                    <h4 className="font-semibold text-sm">Legacy hiring</h4>
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
                      Keys merge with any server env keys (including the embedded Perplexity key). Saving one provider no longer wipes the others.
                      Research &amp; leads need Perplexity — use a paid key for complex multi-market work. LLM keys power copy and documents.
                    </p>
                    {activeKeyProviders.length > 0 ? (
                      <p className="text-sm text-emerald-300">Active: {activeKeyProviders.join(", ")}</p>
                    ) : (
                      <p className="text-sm text-amber-300">No keys active — add Perplexity for research, or an LLM key for copy. Server env keys also count when present.</p>
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
                    <p className="text-sm muted">Connect Canva for visuals, Gmail/LinkedIn/HubSpot for outreach automations.</p>
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
                          {row.use_in_automations ? <p className="text-xs muted">{String(row.use_in_automations)}</p> : null}
                          {row.authorize_url ? (
                            <a
                              href={String(row.authorize_url)}
                              target={String(row.authorize_url).startsWith("/") ? "_self" : "_blank"}
                              rel="noreferrer"
                              className="iid-btn iid-btn-primary text-xs inline-flex"
                            >
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
      </EmployeeOsChrome>

      <AgentChatDrawer
        open={chatDrawerOpen && Boolean(activeAgent)}
        onClose={() => setChatDrawerOpen(false)}
        name={String(chatAgents.find((a) => a.id === activeAgent)?.name || "Agent")}
        role={String(chatAgents.find((a) => a.id === activeAgent)?.role || chatAgents.find((a) => a.id === activeAgent)?.department || "")}
        chat={chat}
        input={chatInput}
        onInput={setChatInput}
        onSend={(msg) => sendChat(msg)}
        loading={chatLoading}
        readOnly={isDemoReadonly}
        starters={chatAgents.find((a) => a.id === activeAgent)?.starters || []}
        renderArtifacts={(arts, reply) => renderArtifacts(arts, reply)}
      />
      {selectedId && pulse ? (
        <TaylorBubble
          pulse={pulse as ComponentProps<typeof TaylorBubble>["pulse"]}
          onAction={handleTaylorAction}
          loading={!!actionLoading}
        />
      ) : null}
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