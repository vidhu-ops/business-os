import Link from "next/link";
import { ContactForm } from "./ContactForm";
import { AgentBadge, DocPreview, GlowOrb, HeroVisual, HumanScene, MarketingPhoto, PhotoCollage, PhotoStrip, ProductVideo, VideoShowcase } from "./illustrations";
import { IconAuto, IconChart, IconClock, IconGlobe, IconGrowth, IconMail, IconPhone, IconPin, IconSearch, IconUser } from "./icons";
import { IndustryBanner } from "./IndustryBanner";
import { PartnersBanner } from "./PartnersBanner";
import { MarketingShell } from "./MarketingShell";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";

const FEATURES = [
  { Icon: IconChart, tag: "RESEARCH", title: "Market Intelligence", body: "Multi-source reports, competitor maps, and TAM/SAM/SOM for your vertical." },
  { Icon: IconSearch, tag: "STRATEGY", title: "Business Planning", body: "Submission-ready plans with ICP, GTM, and financial models." },
  { Icon: IconGrowth, tag: "GROWTH", title: "BD and CRM", body: "Lead lists, enrichment, and outreach on the same data as research." },
  { Icon: IconAuto, tag: "AUTOMATION", title: "Workflow Automation", body: "Agent-built automations across CRM, inbox, and reporting." },
];

const REVIEWS = [
  { quote: "We replaced a two-lakh consulting sprint with a 40-page market report in one afternoon.", name: "Arjun K.", role: "SaaS Founder, Bengaluru", initials: "AK", tone: "blue" },
  { quote: "Finally something built for MSMEs like ours. Our bank loan deck was ready the same day.", name: "Priya S.", role: "MSME Owner, Pune", initials: "PS", tone: "violet" },
  { quote: "The AI workforce handled research and outreach while we focused on product.", name: "Rahul M.", role: "D2C Founder, Mumbai", initials: "RM", tone: "emerald" },
];

const AGENTS = [
  { title: "Research Analyst", initials: "RA", tone: "c1", body: "Follow-up competitor scans, TAM deep-dives, and cited briefs from your report." },
  { title: "Strategy Associate", initials: "SA", tone: "c2", body: "ICP, positioning, and GTM recommendations tied to your plan." },
  { title: "Report Writer", initials: "RW", tone: "c3", body: "Investor memos, executive summaries, and polished deliverables." },
  { title: "BD and Outreach", initials: "BD", tone: "c4", body: "Lead lists, email drafts, and LinkedIn outreach — approved before send." },
  { title: "Automation Engineer", initials: "AE", tone: "c5", body: "CRM syncs, inbox rules, and recurring workflows across your stack." },
  { title: "Deck Designer", initials: "DD", tone: "c6", body: "Pitch decks and one-pagers structured from your business plan." },
];

export function LandingPage() {
  return (
    <MarketingShell>
      <GlowOrb className="mkt-glow-hero" />

      <section className="mkt-wrap mkt-hero">
        <div className="mkt-hero-grid">
          <div className="mkt-hero-copy">
            <p className="mkt-eyebrow">IIDATECH / BUSINESS ECOSYSTEM</p>
            <h1 className="mkt-hero-title">
              <span className="mkt-hero-os">Your</span>
              <span className="mkt-hero-accent">
                <span className="mkt-hero-accent-word">BUSINESS</span>
                <span className="mkt-hero-accent-word">ECOSYSTEM</span>
              </span>
            </h1>
            <div className="mkt-pipe">
              <span>RESEARCH</span><i>→</i><span>PLAN</span><i>→</i><span>EXECUTE</span><i>→</i><span>AUTOMATE</span>
            </div>
            <p className="mkt-lead">
              Market-intelligence and business-execution for founders — self-serve as a SaaS tool, or done-for-you as a service.
            </p>
            <div className="mkt-hero-cta">
              <Link href="/login?intent=audit&mode=register" className="iid-btn iid-btn-primary">
                Run free audit for company
              </Link>
              <WorkspaceEntryLink href="/app/research?project=demo_readonly" className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
            </div>
            <p className="mkt-lead" style={{ fontSize: "0.9rem", marginTop: "0.75rem", opacity: 0.85 }}>
              One free GAUGE health audit when you sign up — no card required.
            </p>
          </div>
          <HeroVisual />
        </div>
      </section>

      <IndustryBanner />

      <section id="why" className="mkt-wrap mkt-section">
        <div className="mkt-split mkt-split-problem">
          <div className="mkt-split-copy">
            <span className="mkt-label">01 / The Problem</span>
            <h2 className="mkt-h2">Good decisions still run on guesswork.</h2>
            <p className="mkt-sub">7.86 Cr MSMEs employ 34.6 crore people — most without a dedicated research or strategy function.</p>
          </div>
          <HumanScene
            variant="founder"
            photoId="msme-business"
            cardA={{ label: "MSMEs globally", value: "7.86 Cr" }}
            cardB={{ label: "Without research teams", value: "< 5%" }}
          />
        </div>
        <div className="mkt-stat-row">
          <div className="mkt-stat-box"><strong>7.86 Cr</strong><span>MSMEs globally</span></div>
          <div className="mkt-stat-box"><strong>34.6 Cr</strong><span>People employed</span></div>
          <div className="mkt-stat-box"><strong>&lt;5%</strong><span>Have research teams</span></div>
        </div>
        <div className="mkt-pain-row">
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconSearch /></span><strong>No research team</strong><p>No in-house analysts or strategy bench.</p></div>
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconClock /></span><strong>Slow consulting</strong><p>Weeks of back-and-forth before you can act.</p></div>
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconUser /></span><strong>Small teams stretched thin</strong><p>Wearing every hat from research to outreach.</p></div>
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconGlobe /></span><strong>Global tools miss local context</strong><p>Regulation, pricing, and buyers stay opaque.</p></div>
        </div>
      </section>

      <section id="demo" className="mkt-wrap mkt-section-tight">
        <VideoShowcase
          title="See IIDATECH in action"
          subtitle="Watch founders go from idea to a sourced market report in minutes."
          videoId="9No-FiEInLA"
        />
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-split">
          <HumanScene variant="mobile" />
          <div className="mkt-split-copy">
            <span className="mkt-label">Mobile-first</span>
            <h2 className="mkt-h2">Built for how you actually work.</h2>
            <p className="mkt-sub">
              Review reports on your phone, approve plans between meetings, and manage Employee OS from anywhere — with generous spacing and touch-friendly controls.
            </p>
            <Link href="/pricing" className="iid-btn iid-btn-primary">View pricing</Link>
          </div>
        </div>
      </section>

      <PartnersBanner />

      <section id="features" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">02 / The Solution</span>
          <h2 className="mkt-h2">One OS. Four functions your business is missing.</h2>
        </div>
        <PhotoStrip ids={["market-research", "analytics", "presentation", "collaboration"]} />
        <div className="mkt-grid-4 mkt-features-grid">
          {FEATURES.map(({ Icon, tag, title, body }) => (
            <article key={title} className="mkt-feature-card">
              <span className="mkt-icon-ring lg"><Icon className="h-6 w-6" /></span>
              <span className="mkt-tag">{tag}</span>
              <h3 className="mkt-feature-title">{title}</h3>
              <p className="mkt-feature-body">{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head"><span className="mkt-label">What teams say</span><h2 className="mkt-h2">Shipped in hours, not weeks.</h2></div>
        <div className="mkt-reviews-grid">
          {REVIEWS.map((r) => (
            <article key={r.name} className="mkt-review-card">
              <p className="mkt-stars">★★★★★</p>
              <p className="mkt-review-quote">&ldquo;{r.quote}&rdquo;</p>
              <div className="mkt-reviewer">
                <AgentBadge initials={r.initials} tone={r.tone} />
                <div><strong>{r.name}</strong><span>{r.role}</span></div>
              </div>
            </article>
          ))}
        </div>
        <div className="mkt-metrics-strip">
          <div className="mkt-metric-tile"><strong>4.9</strong><span>Avg. user rating</span></div>
          <div className="mkt-metric-tile"><strong>40+</strong><span>Page reports</span></div>
          <div className="mkt-metric-tile"><strong>₹1L+</strong><span>Saved vs consulting</span></div>
          <div className="mkt-metric-tile"><strong>6</strong><span>AI employees day one</span></div>
        </div>
      </section>

      <section id="services" className="mkt-section-dark">
        <div className="mkt-wrap mkt-section-inner">
          <div className="mkt-split mkt-split-reverse mkt-services-split">
            <PhotoCollage ids={["workspace", "strategy-meeting", "presentation"]} />
            <div className="mkt-split-copy">
              <span className="mkt-label">Services</span>
              <h2 className="mkt-h2">Six tools. One platform.</h2>
              <p className="mkt-sub">Show proof, not pitch decks. Generate what you need, then act on it.</p>
              <div className="mkt-services-grid mkt-services-list">
                {["Research", "Business Plan", "Execution", "Mentorship", "Automation", "Brand"].map((t, i) => (
                  <article key={t} className="mkt-service">
                    <span className="mkt-service-num">0{i + 1}</span>
                    <h3 className="mkt-feature-title">{t}</h3>
                  </article>
                ))}
              </div>
              <Link href="/login?mode=register" className="iid-btn iid-btn-primary mkt-section-cta">Sign up free</Link>
              <WorkspaceEntryLink className="iid-btn iid-btn-ghost mkt-section-cta">Open demo</WorkspaceEntryLink>
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">How it works</span>
          <h2 className="mkt-h2">Six steps — click this, get that.</h2>
          <p className="mkt-sub">Create a project → generate research → build a plan → run Employee OS. Button names match the app.</p>
        </div>
        <div className="mkt-process">
          <div className="mkt-process-step"><p className="mkt-step-big">01</p><h4>Projects</h4><p>Click <strong>Create project</strong></p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">02</p><h4>Research</h4><p>Click <strong>Generate report</strong></p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">03</p><h4>Plan</h4><p>Click <strong>Build Agentic Business Plan</strong></p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">04</p><h4>Reference</h4><p>Open <strong>Reference</strong> tab</p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">05</p><h4>Employee OS</h4><p>Click <strong>Run full office day</strong></p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">06</p><h4>Ship</h4><p><strong>Approve</strong> tasks &amp; export</p></div>
        </div>
        <Link href="/how-it-works#employee-os" className="iid-btn iid-btn-ghost mkt-section-cta-inline">Full walkthrough + Employee OS guide →</Link>
      </section>

      <section className="mkt-wrap mkt-section">
        <ProductVideo
          poster="https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80"
          src="https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
        />
      </section>

      <section id="automation" className="mkt-wrap mkt-section">
        <div className="mkt-split">
          <div className="mkt-split-copy">
            <span className="mkt-label">AI Workforce</span>
            <h2 className="mkt-h2">Employee OS — your virtual company.</h2>
            <p className="mkt-sub">
              Taylor (COO) coordinates six specialists. Click <strong>Build checklist from plan</strong> to turn your business plan into tasks,
              then <strong>Run full office day</strong> to execute. External emails and posts pause at <strong>Tasks &amp; approvals</strong> until you click <strong>Approve</strong>.
            </p>
            <Link href="/how-it-works#employee-os" className="iid-btn iid-btn-primary">Employee OS guide</Link>
          </div>
          <HumanScene
            variant="team"
            cardA={{ label: "AI employees", value: "6 agents day one" }}
            cardB={{ label: "Taylor COO", value: "Orchestrates all" }}
          />
        </div>
        <div className="mkt-grid-3 mkt-agents-grid">
          {AGENTS.map((a) => (
            <article key={a.title} className="mkt-agent-card">
              <AgentBadge initials={a.initials} tone={a.tone} />
              <h3 className="mkt-feature-title">{a.title}</h3>
              <p className="mkt-feature-body">{a.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-section-head"><span className="mkt-label">Deliverables</span><h2 className="mkt-h2">Sample outputs you can generate today.</h2></div>
        <div className="mkt-samples-grid">
          <div className="mkt-sample-card"><DocPreview variant="report" /><div className="mkt-sample-body"><span className="mkt-tag">RESEARCH</span><h3>Market Report</h3><p>40+ pages across 18 topics with sources.</p></div></div>
          <div className="mkt-sample-card"><DocPreview variant="plan" /><div className="mkt-sample-body"><span className="mkt-tag">PLAN</span><h3>Investor Plan</h3><p>30-page bank-ready business plan.</p></div></div>
          <div className="mkt-sample-card"><DocPreview variant="exec" /><div className="mkt-sample-body"><span className="mkt-tag">EXECUTION</span><h3>Roadmap</h3><p>35-page checklist with vendors and hiring.</p></div></div>
        </div>
      </section>

      <section id="work" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">Our work</span>
          <h2 className="mkt-h2">Built for your vertical</h2>
          <p className="mkt-sub">From clinics to warehouses to SaaS — IIDATECH adapts research and plans to your industry.</p>
        </div>
        <div className="mkt-vertical-photos">
          <MarketingPhoto id="healthcare" />
          <MarketingPhoto id="logistics" />
          <MarketingPhoto id="retail" />
          <MarketingPhoto id="analytics" />
        </div>
        <div className="mkt-industry-grid">
          {["FinTech", "Healthcare", "SaaS", "D2C", "Manufacturing", "Logistics", "Education", "Real Estate"].map((n) => (
            <div key={n} className="mkt-industry-tile"><span>{n}</span></div>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Ready to ship?</span>
          <h2 className="mkt-h2">Start with 1 free company audit.</h2>
          <p className="mkt-sub">No card required. GAUGE health read in minutes.</p>
          <div className="mkt-hero-cta mkt-cta-banner-actions">
            <Link href="/login?intent=audit&mode=register" className="iid-btn iid-btn-primary">
              Run free audit
            </Link>
            <Link href="/pricing" className="iid-btn iid-btn-ghost">See pricing</Link>
          </div>
        </div>
      </section>

      <section id="contact" className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-section-head"><span className="mkt-label">Contact</span><h2 className="mkt-h2">Talk to the team.</h2></div>
        <div className="mkt-contact-grid">
          <div className="mkt-contact-visual">
            <MarketingPhoto id="founder-team" />
            <div className="mkt-contact-stack">
            <div className="mkt-contact-card"><span className="mkt-icon-ring sm"><IconMail /></span><div><strong>Email</strong><a href="mailto:vidhugupta1996@gmail.com">vidhugupta1996@gmail.com</a></div></div>
            <div className="mkt-contact-card"><span className="mkt-icon-ring sm"><IconPhone /></span><div><strong>Phone</strong><a href="tel:+919545403431">+91 95454 03431</a></div></div>
            <div className="mkt-contact-card"><span className="mkt-icon-ring sm"><IconPin /></span><div><strong>Based in</strong><span>Serving companies globally</span></div></div>
            </div>
          </div>
          <ContactForm />
        </div>
      </section>
    </MarketingShell>
  );
}
