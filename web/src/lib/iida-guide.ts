export type IidaTour = { title: string; blurb: string; hook: string };

const TOURS: Record<string, IidaTour> = {
  "/app/dashboard": {
    title: "Command deck",
    blurb: "Home base for credits, projects, and your next move.",
    hook: "Start an audit or open a project — I will narrate every step.",
  },
  "/app/projects": {
    title: "Project vault",
    blurb: "Every idea lives here as a workspace.",
    hook: "Open one to continue, or create something new.",
  },
  "/app/audit": {
    title: "Company Audit",
    blurb: "Stress-test an existing company for gaps and upside.",
    hook: "Answer straight — I turn that into a diagnosis you can act on.",
  },
  "/app/research": {
    title: "Market Research",
    blurb: "Cited market sizing, competitors, and demand.",
    hook: "Run research, then ask me to walk the report.",
  },
  "/app/plan": {
    title: "Business Plan",
    blurb: "Research becomes a plan you can staff and pitch.",
    hook: "Generate the plan, then we hire in Employee OS.",
  },
  "/app/team": {
    title: "Employee OS",
    blurb: "Your office floor — Taylor leads, you approve, the team executes.",
    hook: "I am your personal aide. I can brief Taylor anytime.",
  },
  "/app/automation": {
    title: "Automation",
    blurb: "Repeatable workflows so the office keeps shipping.",
    hook: "Wire one high-leverage flow first.",
  },
  "/app/profile": {
    title: "Profile",
    blurb: "Plan, credits, and account settings.",
    hook: "Tell me your goal and I tailor the path.",
  },
  "/app/saved": {
    title: "Saved files",
    blurb: "Exports and deliverables from across the product.",
    hook: "I can remind you what each file is for.",
  },
  "/app/partners": {
    title: "Partners",
    blurb: "Humans who can help you ship faster.",
    hook: "Browse when you are ready for outside help.",
  },
};

export function normalizeAppPath(pathname: string | null | undefined): string {
  const p = (pathname || "/app/dashboard").split("?")[0].replace(/\/$/, "") || "/app/dashboard";
  return p.startsWith("/") ? p : `/${p}`;
}

export function tourForPath(pathname: string | null | undefined): IidaTour {
  const p = normalizeAppPath(pathname);
  if (TOURS[p]) return TOURS[p];
  const hit = Object.keys(TOURS).find((k) => p.startsWith(k));
  return (
    (hit && TOURS[hit]) || {
      title: "IIDATECH workspace",
      blurb: "You are inside the product. I stay one tap away.",
      hook: "Ask what this page is for, or what to do next.",
    }
  );
}

/** Lightweight screen read from the live DOM — headings + live regions. */
export function readScreenSummary(maxLen = 280): string {
  if (typeof document === "undefined") return "";
  const bits: string[] = [];
  const h1 = document.querySelector("h1");
  if (h1?.textContent) bits.push(h1.textContent.trim());
  document.querySelectorAll("h2").forEach((el, i) => {
    if (i < 4 && el.textContent) bits.push(el.textContent.trim());
  });
  const live = document.querySelector("[data-iida-live]");
  if (live?.textContent) bits.push(live.textContent.trim().slice(0, 80));
  const joined = Array.from(new Set(bits.filter(Boolean))).join(" · ");
  return joined.slice(0, maxLen);
}

export function firstNameFrom(email: string, name?: string): string {
  const raw = (name || "").trim() || (email || "").split("@")[0] || "founder";
  const token = raw.split(/[\s._-]+/)[0] || "founder";
  return token.charAt(0).toUpperCase() + token.slice(1, 24);
}