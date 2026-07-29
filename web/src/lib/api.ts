const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const REQUEST_TIMEOUT_MS = 15_000;
const LONG_REQUEST_TIMEOUT_MS = 30 * 60 * 1000;
const RESEARCH_POLL_MS = 4_000;
const RESEARCH_POLL_MAX = 450;

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("iida_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("iida_token", token);
  else localStorage.removeItem("iida_token");
}

export type User = { email: string; name: string };
export type Project = {
  workspace_id: string;
  idea: string;
  country: string;
  industry: string;
  current_path?: string;
  updated_at?: string;
  path?: string;
  has_report?: boolean;
  has_plan?: boolean;
};

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function request<T>(
  path: string,
  init?: RequestInit,
  opts?: { auth?: boolean; timeoutMs?: number },
): Promise<T> {
  const useAuth = opts?.auth !== false;
  const token = useAuth ? getToken() : null;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), opts?.timeoutMs ?? REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      credentials: "include",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers || {}),
      },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = (data as { detail?: unknown }).detail;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || res.statusText));
    }
    return data as T;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      const long = (opts?.timeoutMs ?? REQUEST_TIMEOUT_MS) > REQUEST_TIMEOUT_MS;
      throw new Error(
        long
          ? "This operation took too long. Try again or use fewer report sections."
          : "Request timed out — check that the API is running.",
      );
    }
    throw err;
  } finally {
    window.clearTimeout(timer);
  }
}

/** Ensure a demo session exists before entering /app routes. */
export async function ensureSession(): Promise<User> {
  const token = getToken();
  if (token) {
    try {
      return await request<User>("/api/v1/auth/me");
    } catch {
      setToken(null);
    }
  }
  const data = await request<User & { token: string }>("/api/v1/auth/demo", { method: "POST", body: "{}" }, { auth: false });
  setToken(data.token);
  return data;
}

export const api = {
  demoLogin: async () => {
    setToken(null);
    const data = await request<User & { token: string }>("/api/v1/auth/demo", { method: "POST", body: "{}" }, { auth: false });
    setToken(data.token);
    return data;
  },
  login: async (email: string, password: string) => {
    setToken(null);
    const data = await request<User & { token: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      { auth: false },
    );
    setToken(data.token);
    return data;
  },
  register: async (email: string, password: string, name: string) => {
    setToken(null);
    const data = await request<User & { token: string }>(
      "/api/v1/auth/register",
      { method: "POST", body: JSON.stringify({ email, password, name }) },
      { auth: false },
    );
    setToken(data.token);
    return data;
  },
  me: () => request<User>("/api/v1/auth/me"),
  logout: async () => {
    const data = await request<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" });
    setToken(null);
    return data;
  },
  projects: () => request<{ projects: Project[] }>("/api/v1/projects"),
  createProject: (idea: string, industry: string, country: string, areas = "") =>
    request<{ project: Project }>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify({ idea, industry, country, areas }),
    }),
  project: (id: string) => request<{ project: Record<string, unknown> }>(`/api/v1/projects/${id}`),
  updateIntake: (workspace_id: string, idea: string, industry: string, country: string, areas = "") =>
    request<{ project: Record<string, unknown>; scope: Record<string, unknown> }>(`/api/v1/projects/${workspace_id}/intake`, {
      method: "PATCH",
      body: JSON.stringify({ idea, industry, country, areas }),
    }),
  researchOptions: () =>
    request<{
      research_ready: boolean;
      setup_hint?: string | null;
      countries: string[];
      options: Array<{ section_count: number; titles: string[]; budget_usd: number }>;
    }>("/api/v1/research/options"),
  previewScope: (idea: string, industry: string, country: string, areas = "") =>
    request<{ scope: Record<string, unknown>; market_label: string }>("/api/v1/research/scope", {
      method: "POST",
      body: JSON.stringify({ idea, industry, country, areas }),
    }),
  runResearch: async (
    workspace_id: string,
    section_count: number,
    intake?: { idea: string; industry: string; country: string; areas?: string },
  ) => {
    const started = await request<Record<string, unknown>>(
      "/api/v1/research/run",
      {
        method: "POST",
        body: JSON.stringify({ workspace_id, section_count, ...intake }),
      },
      { timeoutMs: 60_000 },
    );
    if (started.status !== "running") return started;

    for (let i = 0; i < RESEARCH_POLL_MAX; i += 1) {
      await sleep(RESEARCH_POLL_MS);
      const data = await request<{
        job?: { status?: string; error?: string; section_count?: number };
        research: Record<string, unknown>;
      }>(`/api/v1/research/${workspace_id}`);
      const job = data.job || {};
      if (job.status === "failed") {
        throw new Error(String(job.error || "Report generation failed"));
      }
      const research = data.research || {};
      if (research.available && Number(research.section_count) === section_count) {
        const full = research.full_result as Record<string, unknown> | undefined;
        return full && typeof full === "object" ? full : research;
      }
    }
    throw new Error("Report generation is still running or timed out. Refresh the page in a minute.");
  },
  getResearch: (workspace_id: string) =>
    request<{
      job?: { status?: string; error?: string; section_count?: number };
      research: Record<string, unknown>;
      intake: {
        idea: string;
        industry: string;
        country: string;
        areas: string;
        market_label: string;
        scope_ok: boolean;
        scope_issues: string[];
        scope_suggestions: string[];
      };
    }>(`/api/v1/research/${workspace_id}`),
  getPlan: (workspace_id: string) =>
    request<{
      plan: Record<string, unknown>;
      has_research: boolean;
      company_mode?: string | null;
      intake: Record<string, unknown>;
    }>(`/api/v1/plan/${workspace_id}`),
  setPlanMode: (workspace_id: string, company_mode: string | null) =>
    request<{ company_mode: string | null }>(`/api/v1/plan/${workspace_id}/mode`, {
      method: "PATCH",
      body: JSON.stringify({ company_mode }),
    }),
  savePlanIntake: (workspace_id: string, intake: Record<string, unknown>) =>
    request<{ intake: Record<string, unknown> }>(`/api/v1/plan/${workspace_id}/intake`, {
      method: "PATCH",
      body: JSON.stringify(intake),
    }),
  runPlan: (workspace_id: string, use_research = true) =>
    request<Record<string, unknown>>(
      "/api/v1/plan/run",
      {
        method: "POST",
        body: JSON.stringify({ workspace_id, use_research }),
      },
      { timeoutMs: LONG_REQUEST_TIMEOUT_MS },
    ),
  getOs2: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}`),
  setOs2Scope: (workspace_id: string, scope: { mode: string; departments?: string[]; harness_ids?: string[] }) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/scope`, {
      method: "PATCH",
      body: JSON.stringify(scope),
    }),
  setOs2Keys: (workspace_id: string, keys: Record<string, string>) =>
    request<{ active_key_providers: string[] }>(`/api/v1/os2/${workspace_id}/keys`, {
      method: "PATCH",
      body: JSON.stringify({ keys }),
    }),
  getOs2Chat: (workspace_id: string, harness_id: string) =>
    request<{ chat: Array<Record<string, unknown>> }>(`/api/v1/os2/${workspace_id}/chat/${harness_id}`),
  postOs2Chat: (workspace_id: string, harness_id: string, message: string) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/chat/${harness_id}`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  buildOs2Checklist: (workspace_id: string) =>
    request<{ checklist: Record<string, unknown> }>(`/api/v1/os2/${workspace_id}/checklist/build`, { method: "POST", body: "{}" }),
  runOs2ChecklistNext: (workspace_id: string, auto_approve_external = false) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/checklist/run-next`, {
      method: "POST",
      body: JSON.stringify({ auto_approve_external }),
    }),
  getTaylorPulse: (workspace_id: string) =>
    request<{ pulse: Record<string, unknown> }>(`/api/v1/os2/${workspace_id}/pulse`),
  getOs2Command: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/command`),
  getOs2WarRoom: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/war-room`),
  getOs2Office: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/office`),
  runOs2OfficeAction: (workspace_id: string, action: string, goals?: string[], auto_approve?: boolean) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/office/action`, {
      method: "POST",
      body: JSON.stringify({ action, goals: goals || [], auto_approve: Boolean(auto_approve) }),
    }),
  runTaylorAction: (workspace_id: string, action: string) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/taylor/action`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  runOs2TaskAction: (workspace_id: string, task_id: string, action: string) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/tasks/${task_id}/action`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  getOs2OAuth: (workspace_id: string) =>
    request<{ providers: Array<Record<string, unknown>> }>(`/api/v1/os2/${workspace_id}/oauth`),
  getOs2Memory: (workspace_id: string) =>
    request<{ memory: Record<string, unknown> }>(`/api/v1/os2/${workspace_id}/memory`),
  getOs2Harnesses: (workspace_id: string) =>
    request<{ custom: Array<Record<string, unknown>> }>(`/api/v1/os2/${workspace_id}/harnesses`),
  addOs2Harness: (workspace_id: string, body: Record<string, unknown>) =>
    request<{ custom: Array<Record<string, unknown>> }>(`/api/v1/os2/${workspace_id}/harnesses`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getOs2Employees: (workspace_id: string) =>
    request<{ employees: Array<Record<string, unknown>>; catalog_roles: Array<Record<string, unknown>>; core_roles: string[] }>(
      `/api/v1/os2/${workspace_id}/employees`,
    ),
  hireOs2Employee: (workspace_id: string, body: { name?: string; role: string; catalog?: boolean }) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/employees`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  saveManualOAuth: (workspace_id: string, provider: string, body: Record<string, string>) =>
    request<{ ok: boolean }>(`/api/v1/oauth/${workspace_id}/${provider}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  previewDeliverable: (body: { title: string; reply?: string; artifacts?: string[] }) =>
    request<Record<string, unknown>>("/api/v1/deliverables/preview", { method: "POST", body: JSON.stringify(body) }),
  exportDeliverable: async (body: { title: string; reply?: string; artifacts?: string[] }, format: "pdf" | "docx") => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/api/v1/deliverables/export?format=${format}`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("Export failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${body.title}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  },
  gaugeMetadata: () => request<Record<string, unknown>>("/api/v1/plan/gauge/metadata"),
  getGauge: (workspace_id: string) =>
    request<{ draft: Record<string, unknown>; audit: Record<string, unknown> | null; step: number }>(`/api/v1/plan/${workspace_id}/gauge`),
  resetGauge: (workspace_id: string) =>
    request<{ ok: boolean; step: number }>(`/api/v1/plan/${workspace_id}/gauge`, { method: "DELETE" }),
  saveGaugeDraft: (workspace_id: string, draft: Record<string, unknown>) =>
    request<{ draft: Record<string, unknown> }>(`/api/v1/plan/${workspace_id}/gauge`, {
      method: "PATCH",
      body: JSON.stringify({ draft }),
    }),
  runGaugeAudit: (workspace_id: string) =>
    request<{ audit: Record<string, unknown>; profile: Record<string, unknown> }>(`/api/v1/plan/${workspace_id}/gauge/audit`, {
      method: "POST",
      body: "{}",
    }),
  buildGaugePlan: (workspace_id: string) =>
    request<Record<string, unknown>>(`/api/v1/plan/${workspace_id}/gauge/build-plan`, { method: "POST", body: "{}" }),
  downloadFile: async (path: string, filename?: string) => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/api/v1/files/download?path=${encodeURIComponent(path)}`, {
      credentials: "include",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || path.split("/").pop() || "download";
    a.click();
    URL.revokeObjectURL(url);
  },
  teamRoster: () => request<{ agents: Array<Record<string, unknown>> }>("/api/v1/team/roster"),
  getTeam: (workspace_id: string) =>
    request<{ team: Record<string, unknown>; report_id?: string; has_research?: boolean }>(`/api/v1/team/${workspace_id}`),
  runTeamTask: (workspace_id: string, harness_id: string, message: string) =>
    request<Record<string, unknown>>("/api/v1/team/run", {
      method: "POST",
      body: JSON.stringify({ workspace_id, harness_id, message }),
    }),
  automationWorkflows: () => request<{ steps: Array<Record<string, unknown>> }>("/api/v1/automation/steps"),
  getAutomation: (workspace_id: string) =>
    request<{ automation: Record<string, unknown>; queue: Record<string, unknown>; steps_catalog: Array<Record<string, unknown>> }>(
      `/api/v1/automation/${workspace_id}`,
    ),
  buildAutomation: (workspace_id: string, step_ids: string[], name: string) =>
    request<Record<string, unknown>>("/api/v1/automation/build", {
      method: "POST",
      body: JSON.stringify({ workspace_id, step_ids, name }),
    }),
  runAutomationNext: (workspace_id: string, auto_approve_external = false) =>
    request<Record<string, unknown>>("/api/v1/automation/run-next", {
      method: "POST",
      body: JSON.stringify({ workspace_id, auto_approve_external }),
    }),
  files: () => request<{ files: Array<Record<string, string | number>> }>("/api/v1/files"),
};
