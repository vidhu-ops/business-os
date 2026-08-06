export type IidaTour = { title: string; blurb: string; hook: string };

const TOURS: Record<string, IidaTour> = {
  "/": {
    title: "IIDATECH home",
    blurb: "Research, plan, and run your company with an AI office.",
    hook: "Scroll the story - I will explain each section. Or jump to Pricing / Log in.",
  },
  "/pricing": {
    title: "Pricing",
    blurb: "Plans and credits so you can pick the right runway.",
    hook: "Compare tiers - I will tell you which fits founders vs teams.",
  },
  "/how-it-works": {
    title: "How it works",
    blurb: "The path from idea to office execution.",
    hook: "Follow the steps - ask me what to do first.",
  },
  "/login": {
    title: "Sign in",
    blurb: "Enter your workspace or try the demo.",
    hook: "Continue with demo to tour Employee OS instantly.",
  },
  "/checkout": {
    title: "Checkout",
    blurb: "Activate a plan so the office can run for real.",
    hook: "I will keep you oriented while you complete payment.",
  },
  "/partners": {
    title: "Partners",
    blurb: "Humans and firms who help you ship faster.",
    hook: "Browse when you want outside help alongside IIDA.",
  },
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

const SECTION_HINTS: Array<{ match: RegExp; line: string }> = [
  { match: /office|floor|phase/i, line: "This is the live floor — people, tasks, and chatter in one view." },
  { match: /hiring|build your team|department/i, line: "Hiring is where you staff departments. Expand Build your team to adjust headcount." },
  { match: /task|approval|checklist/i, line: "Tasks & approvals — review what needs your yes before agents send or post." },
  { match: /war room/i, line: "War Room surfaces blockers and failures so you can unblock fast." },
  { match: /command center/i, line: "Command Center is readiness — credits, integrations, and what is still missing." },
  { match: /agent|team member|human/i, line: "Agents & Team — chat people, add humans, and see who owns what." },
  { match: /integration|oauth|key/i, line: "Integrations connect email, LinkedIn, CRM, and LLM keys the office needs." },
  { match: /taylor|team leader|coo/i, line: "Taylor is your COO on the floor — chat, approve, or ask for the next move." },
  { match: /activit(y|ies)|feed|live/i, line: "Activity feed is the office ticker — who just shipped or needs you." },
  { match: /research|market|competitor/i, line: "Research turns your idea into cited evidence you can defend." },
  { match: /plan|investor|financial/i, line: "Business Plan packages the story, numbers, and next actions." },
  { match: /audit|company/i, line: "Company Audit diagnoses an existing business — gaps and upside." },
  { match: /project|workspace/i, line: "Projects are your opportunity workspaces — pick one to keep going." },
  { match: /credit|plan|pricing|upgrade/i, line: "Credits and plan control how much you can run — I will steer high-value steps." },
  { match: /automation|workflow/i, line: "Automation wires repeatable flows so the office keeps moving." },
  { match: /pricing|starter|credits|plan tier/i, line: "This is how billing works - pick a tier that matches how hard you want the office to run." },
  { match: /how it works|product journey/i, line: "This step is part of the product journey - idea to research to plan to team." },
  { match: /build your business|minutes/i, line: "This is the pitch - IIDATECH turns an idea into research, plan, and an AI office." },
  { match: /sign in|log in|register|demo/i, line: "Sign in to your workspace, or Continue with demo to explore without committing." },

  { match: /priorit|goal|today/i, line: "Priorities tell Taylor what to push today — keep them short and sharp." },
];

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

export type SectionCue = { id: string; title: string; blurb: string; explain: string };

function cleanText(s: string, max = 160): string {
  return s.replace(/\s+/g, " ").trim().slice(0, max);
}

/** Build a fast, catchy one-liner for a scrolled-into-view section. */
export function explainSection(title: string, body = "", pageTitle = ""): string {
  const t = cleanText(title, 80);
  const snippet = cleanText(body.replace(title, ""), 100);
  for (const hint of SECTION_HINTS) {
    if (hint.match.test(`${t} ${snippet} ${pageTitle}`)) {
      return `${t}: ${hint.line}`;
    }
  }
  if (snippet && snippet.toLowerCase() !== t.toLowerCase()) {
    return `${t} - ${snippet}${snippet.length >= 100 ? "..." : ""}`;
  }
  if (pageTitle && t.toLowerCase() !== pageTitle.toLowerCase()) {
    return `${t} - part of ${pageTitle}. Scroll on and I will keep briefing you.`;
  }
  return `You're looking at ${t}. I will summarize each block as you scroll - tap me to ask anything.`;
}

/** Collect scrollable section nodes from the main app content. */
export function collectSectionNodes(root: ParentNode = document): HTMLElement[] {
  const main =
    (root as Document).querySelector?.(".app-shell-main") ||
    (root as Document).querySelector?.("main") ||
    (root as Document).body ||
    root;
  const nodes = Array.from(
    (main as Element).querySelectorAll?.(
      "h1, h2, h3, section, article, [data-iida-section], .iid-card, [role='tabpanel'], aside",
    ) || [],
  ) as HTMLElement[];
  return nodes.filter((el) => {
    const text = (el.innerText || el.textContent || "").trim();
    if (text.length < 8) return false;
    if (el.closest("[data-iida-root]")) return false;
    return true;
  });
}

export function sectionCueFromElement(el: HTMLElement, pageTitle = ""): SectionCue {
  const heading =
    el.matches("h1,h2,h3")
      ? el
      : (el.querySelector("h1,h2,h3,.font-semibold,.font-bold") as HTMLElement | null);
  const title = cleanText(heading?.innerText || el.getAttribute("aria-label") || el.innerText || "This section", 72);
  const body = cleanText(el.innerText || "", 140);
  const id = `${title}::${body.slice(0, 40)}`;
  return {
    id,
    title,
    blurb: body,
    explain: explainSection(title, body, pageTitle),
  };
}