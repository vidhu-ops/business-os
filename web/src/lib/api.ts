const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getToken(): string | null {
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
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
}

export const api = {
  demoLogin: async () => {
    const data = await request<User & { token: string }>("/api/v1/auth/demo", { method: "POST", body: "{}" });
    setToken(data.token);
    return data;
  },
  login: async (email: string, password: string) => {
    const data = await request<User & { token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(data.token);
    return data;
  },
  register: async (email: string, password: string, name: string) => {
    const data = await request<User & { token: string }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
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
  createProject: (idea: string, industry: string, country: string) =>
    request<{ project: Project }>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify({ idea, industry, country }),
    }),
  project: (id: string) => request<{ project: Record<string, unknown> }>(`/api/v1/projects/${id}`),
  researchOptions: () =>
    request<{ perplexity_enabled: boolean; options: Array<{ section_count: number; titles: string[]; budget_usd: number }> }>(
      "/api/v1/research/options",
    ),
  runResearch: (workspace_id: string, section_count: number) =>
    request<Record<string, unknown>>("/api/v1/research/run", {
      method: "POST",
      body: JSON.stringify({ workspace_id, section_count }),
    }),
  files: () => request<{ files: Array<Record<string, string | number>> }>("/api/v1/files"),
};
