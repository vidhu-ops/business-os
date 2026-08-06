export type IidaTour = { title: string; blurb: string; hook: string };

const TOURS: Record<string, IidaTour> = {
  "/": {
    title: "IIDATECH home",
    blurb: "Research, plan, and run a company from one business ecosystem  -  not five disconnected tools.",
    hook: "Start with the free company audit if you already operate; otherwise scroll  -  I brief each block with a concrete next move.",
  },
  "/pricing": {
    title: "Pricing",
    blurb: "Self-serve tiers, done-for-you packages, and credit packs  -  runway for how hard you want the office to work.",
    hook: "Solo and validating? Free or Starter. Running research + plan + employees weekly? Growth. I will flag which block matches your stage as you scroll.",
  },
  "/how-it-works": {
    title: "How it works",
    blurb: "Six click-steps from project to research to plan to Employee OS  -  what to press, what lands.",
    hook: "Treat this as the map. Pick the step you are on today; I will tell you the single click that unlocks the next deliverable.",
  },
  "/login": {
    title: "Sign in",
    blurb: "Your workspace gate  -  register, log in, or tour the demo office without a card.",
    hook: "Want the full product feel in under a minute? Continue with demo. Ready to keep your own audits and plans? Create account.",
  },
  "/checkout": {
    title: "Checkout",
    blurb: "Activating a paid plan so credits and the AI office can run for real.",
    hook: "Finish payment cleanly  -  afterward open Dashboard and spend the first credits on one high-value run (audit or research), not ten tiny experiments.",
  },
  "/partners": {
    title: "Partners",
    blurb: "Service providers who get discovered when founders need human help beside IIDA.",
    hook: "Applying? Lead with niche + proof. Founders: browse after you have a clear gap from an audit or plan.",
  },
  "/app/dashboard": {
    title: "Command deck",
    blurb: "Your account home  -  plan, credits, projects, and the shortest path to the next deliverable.",
    hook: "If credits and a free audit remain, run Company Audit first. If a project already has research, open Plan or Employee OS  -  do not start a second unfinished workspace.",
  },
  "/app/projects": {
    title: "Project vault",
    blurb: "Each idea becomes a workspace that owns research, plan, and the office roster.",
    hook: "Open the project you will actually finish this week. Creating many empty shells burns focus and credits later.",
  },
  "/app/audit": {
    title: "Company Audit (GAUGE)",
    blurb: "Four honest steps that score an existing business and surface priority gaps  -  free on eligible plans.",
    hook: "Answer what is true today, not aspirational. Weak checklist answers produce sharper priorities than polished guesses.",
  },
  "/app/research": {
    title: "Market Research",
    blurb: "Project-scoped market sizing, competitors, and demand  -  cited so you can defend the story.",
    hook: "Lock topic, industry, and country before you generate. Vague scope burns credits and returns generic markets.",
  },
  "/app/plan": {
    title: "Business Plan",
    blurb: "Turns research (or a GAUGE audit) into a readable plan you can pitch and staff.",
    hook: "New company? Build from research. Existing company? Use GAUGE plan forward. Generate once with solid inputs, then staff in Employee OS.",
  },
  "/app/team": {
    title: "Employee OS",
    blurb: "Live office floor  -  Taylor leads, you approve outbound work, departments execute.",
    hook: "If a task says no deliverable: open Integrations, confirm Perplexity is active (server key covers basic research; paid key for complex passes), then Retry. I can brief Taylor so she retries with the right keys.",
  },
  "/app/automation": {
    title: "Automation",
    blurb: "Multi-step agent workflows that keep shipping after you leave the tab.",
    hook: "Wire one high-leverage flow (outreach or report refresh) after Integrations are connected  -  empty queues mean keys or OAuth are still missing.",
  },
  "/app/profile": {
    title: "Profile",
    blurb: "Identity, plan context, and sign-out  -  thin settings, big effect on what I recommend.",
    hook: "Tell me your goal (validate, raise, or operate) and I will route you to audit, research, or Employee OS instead of wandering.",
  },
  "/app/saved": {
    title: "Saved files",
    blurb: "Exports and deliverables from research, plans, and office runs.",
    hook: "Open the newest market report or plan first  -  older files are history; the live project still owns the next decision.",
  },
};

type SectionRule = { match: RegExp; tip: string };

/** Path-scoped first so home "plan" never steals Employee OS meanings. */
const PAGE_SECTIONS: Record<string, SectionRule[]> = {
  "/": [
    {
      match: /business ecosystem for|iidatech\s*\/\s*business ecosystem|operating system for|iidatech\s*\/\s*business os|RESEARCH\s*->\s*PLAN\s*->\s*EXECUTE/i,
      tip: "Hero pitch: one OS from research to execute. Best first click for operators is Run free audit; for new ideas, See demo then Pricing.",
    },
    {
      match: /industries we work with/i,
      tip: "These verticals already have playbooks  -  pick the closest to yours when you create a project later.",
    },
    {
      match: /good decisions still run on guesswork|the problem|no research team|slow consulting/i,
      tip: "Problem block: guesswork is the MSME default. Your edge here is cited research plus an office that executes.",
    },
    {
      match: /see iidatech in action/i,
      tip: "Watch for the research -> plan -> Employee OS loop  -  that sequence is the product, not any single report.",
    },
    {
      match: /built for how you actually work|mobile-first/i,
      tip: "Mobile-first promise: approve and nudge the office from your phone. Heavy builds stay on desktop; approvals travel with you.",
    },
    {
      match: /trusted service partners/i,
      tip: "Partners fill human gaps IIDA cannot. Use them after an audit names a clear missing capability.",
    },
    {
      match: /one os\. four functions|market intelligence|business planning|bd and crm|workflow automation/i,
      tip: "Four missing functions in most small firms. Start with Market Intelligence or Planning  -  automation without a plan accelerates noise.",
    },
    {
      match: /shipped in hours|what teams say/i,
      tip: "Social proof. Measure success as hours-to-first-cited-report, not vanity features.",
    },
    {
      match: /six tools\. one platform/i,
      tip: "Six tools, one login. You do not need all six today  -  research + plan + Employee OS is the core loop.",
    },
    {
      match: /six steps|click this, get that|employee os, ship/i,
      tip: "Click-path overview. Your shortcut: Projects -> Research -> Plan -> Employee OS. Skip Reference until you have a draft plan.",
    },
    {
      match: /employee os  -  your virtual company|research analyst|strategy associate|automation engineer/i,
      tip: "AI workforce pitch. Hire lean (Research + BD) before Full company  -  unused agents still need approvals and integrations.",
    },
    {
      match: /sample outputs you can generate|sample outputs/i,
      tip: "Sample deliverables. Decide whether you need a market report, investor plan, or roadmap first  -  that choice sets your first credit spend.",
    },
    {
      match: /built for your vertical/i,
      tip: "Vertical tiles: same OS, different defaults. When you create a project, name industry + country tightly so research stays local.",
    },
    {
      match: /start with 1 free company audit|ready to ship/i,
      tip: "Conversion moment. Free audit is highest signal if you already sell; new-idea founders should See pricing then Start free.",
    },
    {
      match: /talk to the team/i,
      tip: "Human contact for partnerships and sales  -  product questions can stay with me; commercial terms go to this form.",
    },
  ],
  "/pricing": [
    {
      match: /transparent pricing|every stage/i,
      tip: "Pricing hero. Decide stage first: validating (Free/Starter), shipping weekly (Growth), or multi-seat ops (Business / sales).",
    },
    {
      match: /self-serve platform access/i,
      tip: "Self-serve tiers. Free proves the loop; Starter fits weekly research; Growth fits when Employee OS becomes a habit.",
    },
    {
      match: /done-for-you|startup package|scale package/i,
      tip: "Bundles buy human + product help. Choose them when you lack time to operate the OS yourself  -  not instead of knowing your niche.",
    },
    {
      match: /who each tier is for/i,
      tip: "Stage cards map who each tier fits. Match your real cadence (monthly vs weekly runs), not aspirational headcount.",
    },
    {
      match: /buy credits when you need more/i,
      tip: "Credit packs top up without changing tier. Useful after a heavy research week  -  cheaper than jumping plans early.",
    },
    {
      match: /what each credit is worth/i,
      tip: "Credit table = unit economics of the product. One deep research run beats five shallow regenerations.",
    },
    {
      match: /individual service|a la carte|à la carte|ai employees|automations/i,
      tip: "A la carte prices for one-off buys. Prefer a tier if you will touch research + plan + agents in the same month.",
    },
    {
      match: /every plan includes the full os/i,
      tip: "Full OS on every plan  -  tiers change capacity and support, not which modules exist. Pick runway, not feature checkboxes.",
    },
    {
      match: /2-minute walkthrough|watch a/i,
      tip: "Short walkthrough. Watch where credits get spent so your first paid action is intentional.",
    },
    {
      match: /common questions/i,
      tip: "FAQ. Stuck between Starter and Growth? Tell me your weekly workload and I will pick the cheaper safe tier.",
    },
  ],
  "/how-it-works": [
    {
      match: /six steps, no guesswork|click this/i,
      tip: "Map page. Do not memorize six steps  -  pick the one you have not finished and do only that today.",
    },
    {
      match: /see the full flow/i,
      tip: "Full-flow video. Note the handoff into Employee OS  -  plans without staffing stall.",
    },
    {
      match: /what to click at each stage|create your project|run market research|build your business plan/i,
      tip: "Step list. Project scope quality (industry + country) decides whether research is useful  -  fix that before generating.",
    },
    {
      match: /your ai workforce|every tab  -  what it does|the office|war room|command center/i,
      tip: "Employee OS deep dive. Office = floor, Tasks = approval gate, Hiring = roster, Integrations = oxygen for outbound agents.",
    },
    {
      match: /six agents you get|taylor  -  team leader/i,
      tip: "Day-one agents + Taylor as COO. Brief Taylor with one priority, not ten  -  the floor mirrors whatever you emphasize.",
    },
    {
      match: /what lands in your workspace/i,
      tip: "Deliverables land in Saved files and the project. Treat them as decisions-in-waiting, not archive clutter.",
    },
    {
      match: /designed for founders who wear every hat/i,
      tip: "Founder reality check: use IIDA for research and drafting; keep irreversible outbound behind Approvals.",
    },
    {
      match: /first report in under a minute/i,
      tip: "Speed claim holds when scope is tight. Open workspace, create one project, generate once  -  then read before regenerating.",
    },
  ],
  "/login": [
    {
      match: /build your business in minutes|free company audit|no card/i,
      tip: "Promise on the door: audit and reports without a card. Demo tours the office; account keeps your files.",
    },
    {
      match: /welcome back|create account|continue with demo/i,
      tip: "Auth choice. Demo = browse Employee OS safely. Create account when you want the free audit and saved projects to stick.",
    },
  ],
  "/partners": [
    {
      match: /become a service provider/i,
      tip: "Partner entry. You show up when founders hit a gap IIDA flagged  -  niche clarity beats a long service menu.",
    },
    {
      match: /reach founders|get discovered|no listing fee/i,
      tip: "Why partner: discovery at decision time. List the one outcome you own, not everything you could do.",
    },
    {
      match: /partner application|submit service provider/i,
      tip: "Application. Strong submissions pair a clear niche with proof (logo + registration). Vague consulting rarely gets featured.",
    },
  ],
  "/checkout": [
    {
      match: /checkout|pay|subscribe|card/i,
      tip: "Checkout. After success, spend first credits on one decisive run  -  audit or scoped research  -  then staff the plan.",
    },
  ],
  "/app/dashboard": [
    {
      match: /welcome back/i,
      tip: "Command deck. Glance credits and free audit first  -  they decide whether you explore or ship today.",
    },
    {
      match: /your profile/i,
      tip: "Profile snapshot. Keep name and goals current; I use them to prefer audit vs research vs office routes.",
    },
    {
      match: /current plan|credits|free company audit/i,
      tip: "Plan and credits are your runway meter. Protect credits for scoped research and plans; use demo for UI tours.",
    },
    {
      match: /your projects/i,
      tip: "Project list. Finish the hottest workspace before creating another  -  parallel empty projects dilute research quality.",
    },
    {
      match: /recent activity/i,
      tip: "Activity is a memory aid. If the last event was research, next click is Plan or Employee OS  -  not another research regen.",
    },
    {
      match: /previous deliverables/i,
      tip: "Past deliverables. Open the latest report only if you will act on it today; otherwise jump to Quick actions.",
    },
    {
      match: /quick actions/i,
      tip: "Shortcuts. Best default: unused free audit, else Market research on the active project, else Employee OS to execute.",
    },
  ],
  "/app/projects": [
    {
      match: /create project/i,
      tip: "Create with a sharp niche + geography. Vague titles produce vague markets and wasted generations.",
    },
    {
      match: /saved projects|open workspace/i,
      tip: "Saved workspaces. Open one, complete research -> plan -> team, then stop juggling three half-done ideas.",
    },
    {
      match: /^projects$/i,
      tip: "Project vault. One finished workspace beats five empty shells  -  open the idea you will finish this week.",
    },
  ],
  "/app/audit": [
    {
      match: /company audit|gauge/i,
      tip: "GAUGE audit. Four steps: business type -> checklist -> numbers -> forward goals. Honesty beats optimism for useful priorities.",
    },
    {
      match: /what kind of business|step 1/i,
      tip: "Step 1 sets scoring context. Pick the closest operating model  -  wrong type skews every later priority.",
    },
    {
      match: /tick what's actually|checklist|step 2/i,
      tip: "Step 2 checklist: tick only what exists in production. Gaps here become your focus list  -  that is the point.",
    },
    {
      match: /operating numbers|step 3/i,
      tip: "Step 3 numbers ground the diagnosis. Rough ranges beat blanks; invented precision misleads the forward plan.",
    },
    {
      match: /where you want to go|step 4|forward plan questions/i,
      tip: "Step 4 goals. Name one primary outcome (cash, margin, or market) so priority actions do not scatter.",
    },
    {
      match: /gauge audit report|what to focus on|priority actions/i,
      tip: "Results: read Priority actions before building a forward plan. The plan should attack the top gaps, not restart from zero.",
    },
    {
      match: /build forward business plan|re-run gauge/i,
      tip: "Next: Build forward plan from this audit, or re-run only if inputs were wrong  -  regenerating for comfort wastes the free pass.",
    },
  ],
  "/app/research": [
    {
      match: /understand your market/i,
      tip: "Research home. Scope beats eloquence: tight topic + industry + country yields citable numbers you can defend.",
    },
    {
      match: /topic \/ idea|industry|country \/ market|scope suggestions|save workspace/i,
      tip: "Intake fields. Save inputs before Generate  -  changing country after a run orphans the old report.",
    },
    {
      match: /market research report|generate report|download report|report depth/i,
      tip: "Report stage. Generate once, read competitors and demand, then Plan. Regenerating without new scope rarely improves truth.",
    },
  ],
  "/app/plan": [
    {
      match: /business plan workspace|what are you planning/i,
      tip: "Choose new vs existing company. Wrong mode wastes a generation  -  existing operators should prefer GAUGE forward.",
    },
    {
      match: /build plan for new company|build plan for existing/i,
      tip: "Mode fork. New = agentic plan from research. Existing = GAUGE forward from audit truth.",
    },
    {
      match: /build agentic|build plan(?! for)/i,
      tip: "Intake: feed the research you trust. Thin intake -> thin plan. Then staff the plan in Employee OS  -  do not stop at a PDF.",
    },
    {
      match: /readable plan|plan output/i,
      tip: "Readable plan output. Pull 3 actions Taylor can own this week  -  a plan without owners is a brochure.",
    },
    {
      match: /gauge plan forward|gauge forward/i,
      tip: "GAUGE forward plan: growth path tied to audit gaps. Keep priorities aligned with the report's top weaknesses.",
    },
    {
      match: /\breference\b/i,
      tip: "Reference hub: supporting tools and numbers. Use after you have a draft narrative, not as a place to hide from deciding.",
    },
  ],
  "/app/team": [
    {
      match: /no deliverable|failed|qc_failed|retry|using: openai|using: perplexity/i,
      tip: "Empty deliverable usually means the research tool ran without writing a file, or the Perplexity key was rejected. Confirm Active keys under Integrations, then Retry. Complex competitor/pricing passes often need a paid Perplexity key — tell Taylor to retry after you paste it.",
    },
    {
      match: /integration|api keys|connect apps|oauth|hubspot|linkedin|gmail/i,
      tip: "Integrations are oxygen. Perplexity powers research/leads (server embed works for basics; paid for complex). LLM keys power copy. Saving one key no longer wipes the other.",
    },
    {
      match: /employee os|talk to taylor/i,
      tip: "Employee OS chrome. Talk to Taylor for floor leadership; I stay as your aide and can brief her without you rewriting context.",
    },
    {
      match: /the office|your office is empty|activity feed|run office day|run next task/i,
      tip: "The Office is the live floor. Empty? Hire first. Populated? Set one priority, Run office day, then clear Approvals  -  do not chat every agent.",
    },
    {
      match: /hiring|build your team|organization chart|hire team|solo founder|lean team|full company/i,
      tip: "Hiring tab staffs departments and OS scope. Lean team beats Full company until Integrations and approval habits exist.",
    },
    {
      match: /tasks & approvals|tasks and approvals|approve & run|approve all|retry failed/i,
      tip: "Tasks and Approvals = your control gate for email, LinkedIn, CRM. Review before Approve all  -  that is how the office stays safe. Failed research? Retry after keys are green.",
    },
    {
      match: /war room|team debate|team channel/i,
      tip: "War Room is for blockers and multi-agent debate. Use when stuck; skip it when a single Approve unblocks the queue.",
    },
    {
      match: /command center|team status|run full company cycle/i,
      tip: "Command Center = readiness and company cycle. Run full cycle only after Hiring + Integrations are sane  -  otherwise you amplify idle work.",
    },
    {
      match: /agents & team|agents and team|human team members|ai vs human|chat with/i,
      tip: "Agents and Team: chat specialists and add humans. Humans own judgment calls; agents draft and queue  -  Approvals still decide send.",
    },
    {
      match: /advanced|custom harness|company memory/i,
      tip: "Advanced: custom harnesses and memory. Leave this until the default six agents ship useful work  -  early custom agents add chaos.",
    },
  ],
  "/app/automation": [
    {
      match: /automation builder/i,
      tip: "Automation builder. Design one flow that removes a weekly chore  -  then attach agents who already have Integrations.",
    },
    {
      match: /build automation from steps|run next step/i,
      tip: "Step composer. Toggle only steps you will monitor. Run next step after the queue shows green prerequisites.",
    },
    {
      match: /setup required|open employee os integrations/i,
      tip: "Setup gate: automations stall without Integrations. Fix keys/OAuth in Employee OS before blaming the builder.",
    },
    {
      match: /\bqueue\b/i,
      tip: "Queue is truth. Empty or failed items usually mean missing integrations or an unapproved prior step.",
    },
    {
      match: /recent results/i,
      tip: "Results log. Read failures before adding more steps  -  expanding a broken flow multiplies noise.",
    },
  ],
  "/app/profile": [
    {
      match: /profile|log out/i,
      tip: "Profile is identity + exit. Tell me validate / raise / operate and I will route the next page  -  settings alone will not.",
    },
  ],
  "/app/saved": [
    {
      match: /saved files/i,
      tip: "Saved files archive. Sort by Modified, open the newest plan or report, and decide one action  -  browsing is not progress.",
    },
  ],
};

const GLOBAL_SECTIONS: SectionRule[] = [
  {
    match: /taylor|team leader|\bcoo\b/i,
    tip: "Taylor is floor COO. Give her one priority and let Approvals catch risk  -  I can brief her so you do not retype context.",
  },
  {
    match: /iida is your personal aide/i,
    tip: "That live hint is me. Use the floating assistant for page sense; use Talk to Taylor when the floor must move.",
  },
];

export function normalizeAppPath(pathname: string | null | undefined): string {
  const raw = (pathname || "/").split("?")[0] || "/";
  if (raw === "/") return "/";
  const p = raw.replace(/\/$/, "") || "/";
  return p.startsWith("/") ? p : `/${p}`;
}

export function tourForPath(pathname: string | null | undefined): IidaTour {
  const p = normalizeAppPath(pathname);
  if (TOURS[p]) return TOURS[p];
  const hit = Object.keys(TOURS)
    .filter((k) => k !== "/")
    .sort((a, b) => b.length - a.length)
    .find((k) => p === k || p.startsWith(k + "/"));
  return (
    (hit && TOURS[hit]) || {
      title: "IIDATECH workspace",
      blurb: "You are inside the product. I read the screen and stay one tap away.",
      hook: "Ask what this page is for, or what one action unlocks the next deliverable.",
    }
  );
}

function rulesForPath(pathname: string): SectionRule[] {
  const p = normalizeAppPath(pathname);
  if (PAGE_SECTIONS[p]) return PAGE_SECTIONS[p];
  const hit = Object.keys(PAGE_SECTIONS)
    .filter((k) => k !== "/")
    .sort((a, b) => b.length - a.length)
    .find((k) => p === k || p.startsWith(k + "/"));
  return hit ? PAGE_SECTIONS[hit] : [];
}

function matchTip(rules: SectionRule[], hay: string, title = ""): string | null {
  let best: string | null = null;
  let bestScore = 0;
  for (const rule of rules) {
    const m = hay.match(rule.match);
    if (!m) continue;
    let score = m[0].length;
    if (title && rule.match.test(title)) score += 40;
    if (score > bestScore) {
      bestScore = score;
      best = rule.tip;
    }
  }
  return best;
}

/** Lightweight screen read from the live DOM  -  headings + live regions. */
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
  const joined = Array.from(new Set(bits.filter(Boolean))).join("  |  ");
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

function insightFallback(title: string, pathname: string): string {
  const tour = tourForPath(pathname);
  const t = cleanText(title, 60);
  if (t && t.toLowerCase() !== tour.title.toLowerCase()) {
    const blurbLead = tour.blurb.split("  -  ")[0] || tour.blurb;
    const hookLead = tour.hook.split(".")[0];
    return `On ${tour.title}: "${t}" ties into ${blurbLead}. Next move: ${hookLead}.`;
  }
  return `${tour.title}: ${tour.hook}`;
}

/** Crafted insight for a scrolled-into-view section  -  path-aware, never a raw text dump. */
export function explainSection(
  title: string,
  body = "",
  pageTitle = "",
  pathname = "",
): string {
  const t = cleanText(title, 80);
  const snippet = cleanText(body.replace(title, ""), 120);
  const hay = `${t} \n ${snippet} \n ${pageTitle}`;
  const pathTip = matchTip(rulesForPath(pathname), hay, t);
  if (pathTip) return pathTip;
  const globalTip = matchTip(GLOBAL_SECTIONS, hay, t);
  if (globalTip) return globalTip;
  return insightFallback(t, pathname);
}

/** Collect scrollable section nodes from the main app content. */
export function collectSectionNodes(root: ParentNode = document): HTMLElement[] {
  const doc = root as Document;
  const main =
    doc.querySelector?.(".app-shell-main") ||
    doc.querySelector?.("main") ||
    (typeof document !== "undefined" ? document.body : null) ||
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

export function sectionCueFromElement(
  el: HTMLElement,
  pageTitle = "",
  pathname = "",
): SectionCue {
  const heading = el.matches("h1,h2,h3")
    ? el
    : (el.querySelector("h1,h2,h3,.font-semibold,.font-bold") as HTMLElement | null);
  const title = cleanText(
    heading?.innerText || el.getAttribute("aria-label") || el.innerText || "This section",
    72,
  );
  const body = cleanText(el.innerText || "", 140);
  const id = `${normalizeAppPath(pathname)}::${title}::${body.slice(0, 40)}`;
  return {
    id,
    title,
    blurb: body,
    explain: explainSection(title, body, pageTitle, pathname),
  };
}
