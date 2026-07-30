import Link from "next/link";
import { HumanScene, StepIllustration, VideoShowcase } from "./illustrations";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";

const STEPS = [
  {
    num: "01",
    title: "Create your project",
    body: "Every idea gets its own vault — research, plans, and Employee OS tasks stay tied to one project.",
    clicks: [
      "Click **Start free now** and sign up (email or Google).",
      "Open **Projects** in the top nav.",
      "Enter your idea, industry, and market → click **Create project**.",
      "Open **Dashboard** to see credits and your project list.",
    ],
    youGet: ["30 free credits", "One project vault per idea", "Dashboard with plan + activity"],
    visual: "signup" as const,
  },
  {
    num: "02",
    title: "Run market research",
    body: "Turn a niche question into a sourced intelligence report you can download or feed into planning.",
    clicks: [
      "Go to **Market Research** and pick your project from the dropdown.",
      "Fill **Topic / idea**, **Industry**, and **Country / market**.",
      "Choose report depth (e.g. **8 sections**) → click **Generate report**.",
      "When ready, click **Download report (Markdown)** or read it on the page.",
    ],
    youGet: ["40+ page cited report", "Competitor & TAM maps", "Markdown export"],
    visual: "research" as const,
  },
  {
    num: "03",
    title: "Build your business plan",
    body: "Generate an investor- or bank-ready plan from your research — or paste your own notes.",
    clicks: [
      "Open **Business Plan** and select the same project.",
      "Click **Build plan for new company** (startup) or **Build plan for existing company** (GAUGE audit).",
      "On the **Intake** tab, fill your idea and check **Use latest IIDATECH market research report**.",
      "Click **Build Agentic Business Plan** → switch to **Plan Output** to read the result.",
    ],
    youGet: ["Investor-ready sections", "Financial framing", "Loan / visa application mode"],
    visual: "plan" as const,
  },
  {
    num: "04",
    title: "Use the Reference hub",
    body: "Embedded Plan It Out and Business Plan tools — same experience as our Business Intelligence Hub.",
    clicks: [
      "In **Business Plan**, open the **Reference** tab.",
      "Use **Plan It Out** for step-by-step action plans with vendors and milestones.",
      "Use **Business Plan** for location-specific budgets and full plan generation.",
      "Copy insights back into your main plan or share with stakeholders.",
    ],
    youGet: ["35+ page action plans", "Location-specific budgets", "Full business plan generator"],
    visual: "reference" as const,
  },
  {
    num: "05",
    title: "Set up Employee OS",
    body: "Your virtual team turns the plan into tasks — outreach, research follow-ups, CRM sync, and automations.",
    clicks: [
      "Go to **Employee OS** and pick your project.",
      "Step 1: choose **Full office** → click **Save workspace**.",
      "Open **Integrations** → add an LLM key → click **Save API keys**.",
      "Optional: click **Connect with Gmail / LinkedIn / HubSpot** for live outreach.",
    ],
    youGet: ["6 specialized agents", "Taylor (COO) orchestration", "OAuth + API key setup"],
    visual: "team" as const,
  },
  {
    num: "06",
    title: "Execute and ship",
    body: "Run the office day, approve tasks, and export everything when you are ready to share.",
    clicks: [
      "In **The Office** tab, click **Build checklist from plan** then **Run full office day**.",
      "Review pending items under **Tasks & approvals** → click **Approve** or **Approve & run next**.",
      "Chat with any agent under **Agents & team** — type a task or click a starter prompt.",
      "Save exports from **Dashboard** or download reports anytime.",
    ],
    youGet: ["Live task board", "Email / LinkedIn / CRM outputs", "Saved deliverables library"],
    visual: "ship" as const,
  },
];

const EMPLOYEE_OS_MODES = [
  {
    mode: "Full office",
    when: "You want the whole virtual company — research, sales, ops, and Taylor coordinating.",
    setup: "Step 1 → click **Full office** → **Save workspace**. All tabs unlock.",
  },
  {
    mode: "Department",
    when: "You only need one function — e.g. Sales or Research.",
    setup: "Step 1 → click **Department** → pick department chips → **Save workspace**.",
  },
  {
    mode: "Employee / team",
    when: "You want to work with one or two specific agents only.",
    setup: "Step 1 → click **Employee / team** → select agent names → **Save workspace**.",
  },
];

const EMPLOYEE_OS_TABS = [
  {
    tab: "The Office",
    summary: "Your daily operating rhythm — clock in, standup, execute tasks, sync agents, deliver outputs.",
    clicks: [
      "Add **Priorities today** (one goal per line).",
      "Click **Clock in** → **Standup** → **Next task** to advance phase by phase.",
      "Or click **Run full office day** to run the entire cycle at once.",
      "Click **Build checklist from plan** to turn your business plan into a task board.",
    ],
    output: "Task board with assignees, status, and downloadable artifacts per task.",
  },
  {
    tab: "Tasks & approvals",
    summary: "Human-in-the-loop gate before anything goes external — emails, LinkedIn posts, CRM writes.",
    clicks: [
      "Click **Build checklist from plan** if the queue is empty.",
      "Toggle **Auto-approve external actions** if you trust the agents to send without review.",
      "For each pending item, click **Approve**, **Retry**, or **Skip**.",
      "Click **Approve & run next** to process the queue in order.",
    ],
    output: "Approved outreach, CRM updates, and research deliverables with audit trail.",
  },
  {
    tab: "War room",
    summary: "See agents debate strategy and sync on complex decisions before executing.",
    clicks: [
      "Open **War room** after tasks have run at least once.",
      "Read the **Team channel** for agent-to-agent messages.",
      "Click **Run team debate sync** to trigger a fresh strategy discussion.",
    ],
    output: "Shared channel log — who said what, when, and which decision was taken.",
  },
  {
    tab: "Command center",
    summary: "Bird's-eye metrics — open tasks, completions, roster status, company-wide cycle.",
    clicks: [
      "Open **Command center** to see live metrics (tasks open, done, failed).",
      "Review **Team status** for each agent's workload.",
      "Click **Run full company cycle** to orchestrate all departments in one pass.",
    ],
    output: "Metrics dashboard + roster snapshot updated after each cycle.",
  },
  {
    tab: "Agents & team",
    summary: "Chat directly with any AI employee — research, outreach, automation, deck design.",
    clicks: [
      "Click an agent name (e.g. **BD and Outreach**) to open their chat.",
      "Click a **starter prompt** chip or type your own instruction → **Send**.",
      "Under **Team and hiring**, click **Hire {role}** or fill a custom name + role → **Add to roster**.",
    ],
    output: "Chat transcripts, file artifacts, and a growing team roster per project.",
  },
  {
    tab: "Integrations",
    summary: "Connect the keys and apps agents need before they can work.",
    clicks: [
      "Add **Perplexity** key (research & lead search) and an **LLM key** (OpenAI / Anthropic) → **Save API keys**.",
      "Click **Connect with Gmail**, **LinkedIn**, or **HubSpot** for OAuth.",
      "If OAuth is not configured, paste manual tokens under **Manual tokens** → **Save**.",
    ],
    output: "Green setup checklist items — agents unlock once LLM + optional OAuth are ready.",
  },
];

const AGENTS = [
  { name: "Research Analyst", role: "Deep-dives on competitors, TAM, and follow-up questions from your report." },
  { name: "Strategy Associate", role: "Turns research into positioning, ICP, and GTM recommendations." },
  { name: "Report Writer", role: "Polishes deliverables into investor-ready memos and summaries." },
  { name: "BD and Outreach", role: "Builds lead lists, drafts emails, and queues LinkedIn outreach." },
  { name: "Automation Engineer", role: "Wires CRM syncs, inbox rules, and recurring workflows." },
  { name: "Deck Designer", role: "Structures pitch slides and one-pagers from your plan data." },
];

const DELIVERABLES = [
  { title: "Market intelligence report", pages: "40+", topics: "18 sourced topics" },
  { title: "Business plan", pages: "30+", topics: "ICP, GTM, financials" },
  { title: "Action plan", pages: "35+", topics: "Vendors, hiring, milestones" },
  { title: "Employee OS outputs", pages: "Live", topics: "Emails, leads, automations" },
];

function renderClicks(clicks: string[]) {
  return (
    <ul>
      {clicks.map((item) => (
        <li key={item}>
          {item.split(/\*\*(.*?)\*\*/g).map((part, i) =>
            i % 2 === 1 ? <strong key={i}>{part}</strong> : part,
          )}
        </li>
      ))}
    </ul>
  );
}

export function HowItWorksPage() {
  return (
    <>
      <section className="mkt-wrap mkt-page-hero">
        <p className="mkt-eyebrow">How it works</p>
        <h1 className="mkt-page-title">Click this → get that. Six steps, no guesswork.</h1>
        <p className="mkt-lead mkt-page-lead">
          Every screen tells you what to press next. Research, planning, reference tools, and Employee OS — one workspace, one flow.
        </p>
        <div className="mkt-hero-cta">
          <WorkspaceEntryLink className="iid-btn iid-btn-primary">Start free now</WorkspaceEntryLink>
          <Link href="/pricing" className="iid-btn iid-btn-ghost">
            View pricing
          </Link>
        </div>
      </section>

      <section className="mkt-wrap mkt-section-tight">
        <VideoShowcase
          title="See the full flow"
          subtitle="Research → Plan → Reference → Employee OS in one workspace."
          videoId="9No-FiEInLA"
        />
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Workflow</span>
          <h2 className="mkt-h2">Six steps — what to click at each stage</h2>
          <p className="mkt-sub">Button names match the app exactly so you can follow along inside your workspace.</p>
        </div>
        <div className="mkt-steps-timeline">
          {STEPS.map((step, index) => (
            <article key={step.num} className="mkt-step-card">
              <div className="mkt-step-visual">
                <StepIllustration variant={step.visual} />
              </div>
              <div className="mkt-step-copy">
                <p className="mkt-step-big">{step.num}</p>
                <h2 className="mkt-h3">{step.title}</h2>
                <p className="mkt-sub">{step.body}</p>
                <div className="mkt-you-get mkt-click-path">
                  <strong>What to click</strong>
                  {renderClicks(step.clicks)}
                </div>
                <div className="mkt-you-get">
                  <strong>What you get</strong>
                  <ul>
                    {step.youGet.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              {index < STEPS.length - 1 ? <div className="mkt-step-connector" aria-hidden /> : null}
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-section-dark" id="employee-os">
        <div className="mkt-wrap mkt-section-inner">
          <div className="mkt-section-head">
            <span className="mkt-label">Employee OS</span>
            <h2 className="mkt-h2">Your AI workforce — explained in detail</h2>
            <p className="mkt-sub">
              Employee OS is not a chatbot sidebar. It is a full execution layer: Taylor (your COO) coordinates six specialists,
              turns your business plan into a task checklist, and runs outreach only after you approve.
            </p>
          </div>

          <div className="mkt-os-modes">
            {EMPLOYEE_OS_MODES.map((m) => (
              <article key={m.mode} className="mkt-os-mode-card">
                <h3 className="mkt-feature-title">{m.mode}</h3>
                <p className="mkt-feature-body">{m.when}</p>
                <p className="mkt-os-setup">{m.setup}</p>
              </article>
            ))}
          </div>

          <div className="mkt-section-head mkt-section-head-spaced">
            <span className="mkt-label">Inside Employee OS</span>
            <h3 className="mkt-h3">Every tab — what it does and what to click</h3>
          </div>
          <div className="mkt-os-tabs-grid">
            {EMPLOYEE_OS_TABS.map((t) => (
              <article key={t.tab} className="mkt-os-tab-card">
                <h3 className="mkt-feature-title">{t.tab}</h3>
                <p className="mkt-feature-body">{t.summary}</p>
                <div className="mkt-you-get mkt-click-path mkt-click-path-compact">
                  <strong>Click path</strong>
                  {renderClicks(t.clicks)}
                </div>
                <p className="mkt-os-output">
                  <strong>Output:</strong> {t.output}
                </p>
              </article>
            ))}
          </div>

          <div className="mkt-section-head mkt-section-head-spaced">
            <span className="mkt-label">The team</span>
            <h3 className="mkt-h3">Six agents you get on day one</h3>
          </div>
          <div className="mkt-os-agents-grid">
            {AGENTS.map((a) => (
              <article key={a.name} className="mkt-os-agent-card">
                <h4 className="mkt-feature-title">{a.name}</h4>
                <p className="mkt-feature-body">{a.role}</p>
              </article>
            ))}
          </div>

          <div className="mkt-os-taylor">
            <h3 className="mkt-h3">Taylor — Team Leader (COO)</h3>
            <p className="mkt-sub">
              Taylor sits above the agents. She reads your setup checklist, surfaces notifications, and offers one-click actions:
              <strong> Approve all external</strong>, <strong>Retry failed</strong>, and <strong>Run next task</strong>. When you run The Office day, Taylor mentors each phase
              and posts notes on the task board.
            </p>
            <WorkspaceEntryLink className="iid-btn iid-btn-primary mkt-section-cta">Open Employee OS</WorkspaceEntryLink>
          </div>
        </div>
      </section>

      <section className="mkt-section-dark">
        <div className="mkt-wrap mkt-section-inner">
          <div className="mkt-section-head">
            <span className="mkt-label">Deliverables</span>
            <h2 className="mkt-h2">What lands in your workspace</h2>
            <p className="mkt-sub">Real outputs — not placeholder lorem. Every section is exportable and shareable.</p>
          </div>
          <div className="mkt-deliverables-grid">
            {DELIVERABLES.map((d) => (
              <article key={d.title} className="mkt-deliverable-card">
                <h3>{d.title}</h3>
                <p className="mkt-deliverable-stat">{d.pages}</p>
                <span>{d.topics}</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-split mkt-split-reverse">
          <HumanScene variant="team" />
          <div className="mkt-split-copy">
            <span className="mkt-label">Built for humans</span>
            <h2 className="mkt-h2">Designed for founders who wear every hat.</h2>
            <p className="mkt-sub">
              Mobile-friendly, generous spacing, and clear next steps — so you spend time deciding, not fighting the tool.
            </p>
            <WorkspaceEntryLink className="iid-btn iid-btn-primary">Open your workspace</WorkspaceEntryLink>
          </div>
        </div>
      </section>

      <section className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Ready?</span>
          <h2 className="mkt-h2">Your first report in under a minute.</h2>
          <p className="mkt-sub">No card required. 30 free credits to start.</p>
          <WorkspaceEntryLink className="iid-btn iid-btn-primary mkt-section-cta">Start free now</WorkspaceEntryLink>
        </div>
      </section>
    </>
  );
}
