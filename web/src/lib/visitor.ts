const VID_KEY = "iida_vid";
const SID_KEY = "iida_sid";
const SID_AT_KEY = "iida_sid_at";
const SESSION_TIMEOUT_MS = 30 * 60 * 1000;

function randomId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `v${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
}

function readCookie(name: string): string {
  if (typeof document === "undefined") return "";
  const prefix = `${name}=`;
  const hit = document.cookie.split("; ").find((row) => row.startsWith(prefix));
  return hit ? decodeURIComponent(hit.slice(prefix.length)) : "";
}

function writeCookie(name: string, value: string, maxAgeSec: number) {
  if (typeof document === "undefined") return;
  const secure = typeof location !== "undefined" && location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSec}; SameSite=Lax${secure}`;
}

export function getVisitorId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem(VID_KEY) || readCookie(VID_KEY);
  if (!id || id.length < 8) {
    id = randomId();
  }
  localStorage.setItem(VID_KEY, id);
  writeCookie(VID_KEY, id, 60 * 60 * 24 * 365);
  return id;
}

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  const now = Date.now();
  const last = Number(sessionStorage.getItem(SID_AT_KEY) || 0);
  let id = sessionStorage.getItem(SID_KEY) || readCookie(SID_KEY);
  if (!id || !last || now - last > SESSION_TIMEOUT_MS) {
    id = randomId();
  }
  sessionStorage.setItem(SID_KEY, id);
  sessionStorage.setItem(SID_AT_KEY, String(now));
  writeCookie(SID_KEY, id, 60 * 30);
  return id;
}

export function visitorIds(): { visitor_id: string; session_id: string } {
  return { visitor_id: getVisitorId(), session_id: getSessionId() };
}

export function parseUtms(search = ""): Record<string, string> {
  const params = new URLSearchParams(search.startsWith("?") ? search : search ? `?${search}` : "");
  const utm: Record<string, string> = {};
  for (const key of ["source", "medium", "campaign", "term", "content"]) {
    const value = params.get(`utm_${key}`) || "";
    if (value) utm[key] = value.slice(0, 120);
  }
  return utm;
}

export function parseClickIds(search = ""): Record<string, string> {
  const params = new URLSearchParams(search.startsWith("?") ? search : search ? `?${search}` : "");
  const out: Record<string, string> = {};
  for (const key of ["gclid", "fbclid", "msclkid", "ttclid", "li_fat_id"]) {
    const value = params.get(key) || "";
    if (value) out[key] = value.slice(0, 120);
  }
  return out;
}

export function collectClientContext(): Record<string, unknown> {
  if (typeof window === "undefined") return {};
  const nav = window.navigator as Navigator & {
    connection?: { effectiveType?: string; downlink?: number };
    deviceMemory?: number;
    userAgentData?: { mobile?: boolean; platform?: string };
  };
  const connection = nav.connection;
  return {
    language: nav.language || "",
    languages: Array.isArray(nav.languages) ? nav.languages.slice(0, 6) : [],
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    tz_offset: new Date().getTimezoneOffset(),
    screen_w: window.screen?.width,
    screen_h: window.screen?.height,
    viewport_w: window.innerWidth,
    viewport_h: window.innerHeight,
    dpr: window.devicePixelRatio,
    platform: nav.platform || nav.userAgentData?.platform || "",
    vendor: nav.vendor || "",
    device_memory: nav.deviceMemory,
    hardware_concurrency: nav.hardwareConcurrency,
    connection_type: connection?.effectiveType,
    downlink: connection?.downlink,
    is_touch: "ontouchstart" in window || (nav.maxTouchPoints || 0) > 0,
    max_touch_points: nav.maxTouchPoints || 0,
    prefers_dark: window.matchMedia?.("(prefers-color-scheme: dark)")?.matches,
    user_agent: nav.userAgent || "",
  };
}

export function scrollPercent(): number {
  if (typeof document === "undefined") return 0;
  const el = document.documentElement;
  const scrollTop = window.scrollY || el.scrollTop || 0;
  const height = el.scrollHeight - el.clientHeight;
  if (height <= 0) return 100;
  return Math.max(0, Math.min(100, Math.round((scrollTop / height) * 100)));
}
