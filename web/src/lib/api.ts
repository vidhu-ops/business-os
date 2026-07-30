const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const REQUEST_TIMEOUT_MS = 15_000;
const BOOTSTRAP_TIMEOUT_MS = 90_000;
const LONG_REQUEST_TIMEOUT_MS = 30 * 60 * 1000;
/** Agent chat, checklist runs, and office actions can take several minutes. */
const OS2_REQUEST_TIMEOUT_MS = 10 * 60 * 1000;
/** GAUGE audit: Perplexity market read + LLM synthesis can take several minutes. */
const GAUGE_REQUEST_TIMEOUT_MS = 5 * 60 * 1000;
const RESEARCH_POLL_MS = 4_000;
const RESEARCH_POLL_MAX = 450;

export function isDemoEmail(email: string | null | undefined): boolean {
  return String(email || "").trim().toLowerCase() === "demo@local";
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("iida_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("iida_token", token);
  else localStorage.removeItem("iida_token");
}

export type User = { email: string; name: string; member_since?: string; plan?: PlanSnapshot; is_demo?: boolean; audit?: AuditStatus };
export type PlanSnapshot = {
  id: string;
  name: string;
  price_label: string;
  period?: string;
  tagline?: string;
  credits_remaining?: number | null;
  credits_total?: number | null;
  is_unlimited?: boolean;
  upgrade_href?: string;
};
export type DashboardActivity = { type: string; title: string; detail: string; at: string };
export type AuditStatus = {
  free_audit_granted: number;
  free_audit_used: number;
  free_audit_available: boolean;
};
export type DashboardData = {
  user: { email: string; name: string; member_since: string };
  plan: PlanSnapshot;
  audit?: AuditStatus;
  stats: {
    projects: number;
    reports_ready: number;
    plans_ready: number;
    saved_files: number;
    credits_remaining: number | null;
    credits_used: number | null;
  };
  projects: Project[];
  recent_files: Array<Record<string, string | number>>;
  recent_activity: DashboardActivity[];
  is_demo?: boolean;
};
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

function timeoutMessage(timeoutMs: number): string {
  if (timeoutMs > REQUEST_TIMEOUT_MS) {
    return "Request timed out while waiting for the server. On Render, the service can take up to a minute to wake from sleep — please retry.";
  }
  if (!API_BASE) {
    return "Request timed out — the server may still be starting. Wait a moment and retry.";
  }
  return "Request timed out — check that the API is running on port 8000.";
}

async function request<T>(
  path: string,
  init?: RequestInit,
  opts?: { auth?: boolean; timeoutMs?: number },
): Promise<T> {
  const useAuth = opts?.auth !== false;
  const token = useAuth ? getToken() : null;
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), opts?.timeoutMs ?? REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      credentials: "include",
      signal: controller.signal,
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers || {}),
      },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = (data as { detail?: unknown }).detail;
      if (res.status === 402 && detail && typeof detail === "object" && detail !== null) {
        const d = detail as { message?: string; required?: number; remaining?: number; upgrade_href?: string };
        const href = d.upgrade_href || "/pricing";
        throw new Error(
          d.message || `Not enough credits (need ${d.required ?? "?"}, have ${d.remaining ?? 0}). Upgrade at ${href}.`,
        );
      }
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail || res.statusText));
    }
    return data as T;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(timeoutMessage(opts?.timeoutMs ?? REQUEST_TIMEOUT_MS));
    }
    throw err;
  } finally {
    window.clearTimeout(timer);
  }
}

/** Require a real login token — does not silently create a demo session. */
export async function requireAuthSession(): Promise<User> {
  const token = getToken();
  if (!token) {
    throw new Error("NOT_AUTHENTICATED");
  }
  try {
    return await request<User>("/api/v1/auth/me", undefined, { timeoutMs: BOOTSTRAP_TIMEOUT_MS });
  } catch {
    setToken(null);
    throw new Error("NOT_AUTHENTICATED");
  }
}

/** @deprecated Use requireAuthSession — kept for checkout flows that require any logged-in user. */
export async function ensureSession(): Promise<User> {
  return requireAuthSession();
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
  auditStatus: () => request<AuditStatus>("/api/v1/audit/status"),
  ensureAuditWorkspace: () =>
    request<{ workspace_id: string; project: Project; is_demo?: boolean }>("/api/v1/audit/workspace"),
  dashboard: () => request<DashboardData>("/api/v1/dashboard"),
  logout: async () => {
    const data = await request<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" });
    setToken(null);
    return data;
  },
  projects: () => request<{ projects: Project[]; is_demo?: boolean }>("/api/v1/projects"),
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
  researchOptions: (workspace_id?: string) =>
    request<{
      research_ready: boolean;
      setup_hint?: string | null;
      countries: string[];
      options: Array<{ section_count: number; titles: string[] }>;
    }>(`/api/v1/research/options${workspace_id ? `?workspace_id=${encodeURIComponent(workspace_id)}` : ""}`),
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
      { timeoutMs: 15_000 },
    );

    // Legacy sync response (full report returned immediately).
    if (started.status !== "running") {
      if (started.success) return started;
      throw new Error(String(started.error || started.detail || "Report failed to start"));
    }

    for (let i = 0; i < RESEARCH_POLL_MAX; i += 1) {
      await sleep(RESEARCH_POLL_MS);
      const data = await request<{
        job?: { status?: string; error?: string; section_count?: number };
        research: Record<string, unknown>;
      }>(`/api/v1/research/${workspace_id}`, undefined, { timeoutMs: 60_000 });
      const job = data.job || {};
      if (job.status === "failed") {
        throw new Error(String(job.error || "Report generation failed"));
      }
      const research = data.research || {};
      const done =
        job.status === "completed" ||
        (research.available && Number(research.section_count) === section_count);
      if (done) {
        const full = research.full_result as Record<string, unknown> | undefined;
        if (full && typeof full === "object") return full;
        if (research.available) return research;
      }
    }
    throw new Error("Report is still generating. Wait a minute and refresh this page — your report may already be saved.");
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
      gauge_forward_plan?: Record<string, unknown>;
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
  getOs2: (workspace_id: string) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}`, undefined, { timeoutMs: BOOTSTRAP_TIMEOUT_MS }),
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
    request<Record<string, unknown>>(
      `/api/v1/os2/${workspace_id}/chat/${harness_id}`,
      { method: "POST", body: JSON.stringify({ message }) },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
  buildOs2Checklist: (workspace_id: string) =>
    request<{ checklist: Record<string, unknown> }>(
      `/api/v1/os2/${workspace_id}/checklist/build`,
      { method: "POST", body: "{}" },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
  runOs2ChecklistNext: (workspace_id: string, auto_approve_external = false) =>
    request<Record<string, unknown>>(
      `/api/v1/os2/${workspace_id}/checklist/run-next`,
      { method: "POST", body: JSON.stringify({ auto_approve_external }) },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
  getTaylorPulse: (workspace_id: string) =>
    request<{ pulse: Record<string, unknown> }>(`/api/v1/os2/${workspace_id}/pulse`),
  getOs2Command: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/command`),
  getOs2WarRoom: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/war-room`),
  getOs2Office: (workspace_id: string) => request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/office`),
  runOs2OfficeAction: (workspace_id: string, action: string, goals?: string[], auto_approve?: boolean) =>
    request<Record<string, unknown>>(
      `/api/v1/os2/${workspace_id}/office/action`,
      { method: "POST", body: JSON.stringify({ action, goals: goals || [], auto_approve: Boolean(auto_approve) }) },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
  runTaylorAction: (workspace_id: string, action: string) =>
    request<Record<string, unknown>>(
      `/api/v1/os2/${workspace_id}/taylor/action`,
      { method: "POST", body: JSON.stringify({ action }) },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
  runOs2TaskAction: (workspace_id: string, task_id: string, action: string) =>
    request<Record<string, unknown>>(
      `/api/v1/os2/${workspace_id}/tasks/${task_id}/action`,
      { method: "POST", body: JSON.stringify({ action }) },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
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
  getOs2Departments: (workspace_id: string) =>
    request<{
      catalog: Array<Record<string, unknown>>;
      hired: Array<Record<string, unknown>>;
      agents: Array<Record<string, unknown>>;
    }>(`/api/v1/os2/${workspace_id}/departments`),
  setOs2Departments: (workspace_id: string, departments: Array<{ id: string; name?: string; headcount: number }>) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/departments`, {
      method: "PATCH",
      body: JSON.stringify({ departments }),
    }),
  getOs2OrgChart: (workspace_id: string) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/org-chart`),
  getOs2Humans: (workspace_id: string) =>
    request<{ humans: Array<Record<string, unknown>> }>(`/api/v1/os2/${workspace_id}/humans`),
  addOs2Human: (workspace_id: string, body: { name: string; role?: string; departments?: string[] }) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/humans`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  removeOs2Human: (workspace_id: string, human_id: string) =>
    request<{ humans: Array<Record<string, unknown>> }>(`/api/v1/os2/${workspace_id}/humans/${human_id}`, {
      method: "DELETE",
    }),
  getOs2Collaboration: (workspace_id: string) =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/collaboration`),
  postOs2Broadcast: (workspace_id: string, message: string, from_agent = "taylor") =>
    request<Record<string, unknown>>(`/api/v1/os2/${workspace_id}/chat/broadcast`, {
      method: "POST",
      body: JSON.stringify({ message, from_agent }),
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
    request<{ audit: Record<string, unknown>; profile: Record<string, unknown> }>(
      `/api/v1/plan/${workspace_id}/gauge/audit`,
      { method: "POST", body: "{}" },
      { timeoutMs: GAUGE_REQUEST_TIMEOUT_MS },
    ),
  buildGaugePlan: (workspace_id: string) =>
    request<Record<string, unknown>>(
      `/api/v1/plan/${workspace_id}/gauge/build-plan`,
      { method: "POST", body: "{}" },
      { timeoutMs: GAUGE_REQUEST_TIMEOUT_MS },
    ),
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
    request<Record<string, unknown>>(
      "/api/v1/team/run",
      { method: "POST", body: JSON.stringify({ workspace_id, harness_id, message }) },
      { timeoutMs: OS2_REQUEST_TIMEOUT_MS },
    ),
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
  registerPartner: (form: FormData) =>
    request<{ ok: boolean; id: string; message: string; provider: Record<string, unknown> }>(
      "/api/v1/partners/register",
      { method: "POST", body: form },
      { auth: false },
    ),
  listPartners: () =>
    request<{ providers: Array<Record<string, unknown>>; count: number }>("/api/v1/partners", {}, { auth: false }),
  listFeaturedPartners: () =>
    request<{ partners: Array<{ id: string; company_name: string; logo_url?: string; website?: string }>; count: number }>(
      "/api/v1/partners/featured",
      {},
      { auth: false },
    ),
  paymentPlans: () =>
    request<{ plans: Array<Record<string, unknown>>; gateway: Record<string, unknown> }>(
      "/api/v1/payments/plans",
      {},
      { auth: false },
    ),
  startCheckout: (plan_id: string) =>
    request<{
      order: Record<string, unknown>;
      checkout: {
        checkout_url: string;
        merchant_id: string;
        enc_data: string;
        fields: { merchantId: string; encData: string };
      };
    }>("/api/v1/payments/checkout", { method: "POST", body: JSON.stringify({ plan_id }) }),
  getPaymentOrder: (order_id: string) =>
    request<{ order: Record<string, unknown> }>(`/api/v1/payments/orders/${encodeURIComponent(order_id)}`),
  getCredits: () =>
    request<{
      credits_remaining: number | null;
      credits_total?: number | null;
      is_unlimited: boolean;
      plan: string;
      costs: Record<string, number>;
      labels: Record<string, string>;
    }>("/api/v1/credits"),
};
