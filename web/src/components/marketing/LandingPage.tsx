import Link from "next/link";
import { ContactForm } from "./ContactForm";
import { AgentBadge, DocPreview, GlowOrb, HeroVisual } from "./illustrations";
import { IconAuto, IconChart, IconClock, IconGlobe, IconGrowth, IconMail, IconPhone, IconPin, IconSearch, IconUser } from "./icons";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";

const NAV = [
  { label: "Problem", href: "#why" },
  { label: "Solution", href: "#features" },
  { label: "Services", href: "#services" },
  { label: "How", href: "#how" },
  { label: "Workforce", href: "#automation" },
  { label: "Contact", href: "#contact" },
];

const FEATURES = [
  { Icon: IconChart, tag: "RESEARCH", title: "Market Intelligence", body: "Multi-source reports, competitor maps, and TAM/SAM/SOM for Indian verticals." },
  { Icon: IconSearch, tag: "STRATEGY", title: "Business Planning", body: "Submission-ready plans with ICP, GTM, and financial models." },
  { Icon: IconGrowth, tag: "GROWTH", title: "BD and CRM", body: "Lead lists, enrichment, and outreach on the same data as research." },
  { Icon: IconAuto, tag: "AUTOMATION", title: "Workflow Automation", body: "Agent-built automations across CRM, inbox, and reporting." },
];

const REVIEWS = [
  { quote: "We replaced a two-lakh consulting sprint with a 40-page market report in one afternoon.", name: "Arjun K.", role: "SaaS Founder, Bengaluru", initials: "AK", tone: "blue" },
  { quote: "Finally something built for Indian MSMEs. Our bank loan deck was ready the same day.", name: "Priya S.", role: "MSME Owner, Pune", initials: "PS", tone: "violet" },
  { quote: "The AI workforce handled research and outreach while we focused on product.", name: "Rahul M.", role: "D2C Founder, Mumbai", initials: "RM", tone: "emerald" },
];

const AGENTS = [
  { title: "Research Analyst", initials: "RA", tone: "c1" },
  { title: "Strategy Associate", initials: "SA", tone: "c2" },
  { title: "Report Writer", initials: "RW", tone: "c3" },
  { title: "BD and Outreach", initials: "BD", tone: "c4" },
  { title: "Automation Engineer", initials: "AE", tone: "c5" },
  { title: "Deck Designer", initials: "DD", tone: "c6" },
];

export function LandingPage() {
  return (
    <main className="mkt-page">
      <GlowOrb className="mkt-glow-hero" />
      <header className="mkt-nav-shell">
        <div className="mkt-wrap mkt-nav">
          <Link href="/" className="mkt-logo">IIDA<span>TECH</span></Link>
          <nav className="mkt-nav-links hidden lg:flex">
            {NAV.map((item) => (<a key={item.href} href={item.href}>{item.label}</a>))}
          </nav>
          <div className="mkt-nav-actions">
            <Link href="/login" className="mkt-nav-login">Log in</Link>
            <WorkspaceEntryLink className="iid-btn iid-btn-primary">Start now</WorkspaceEntryLink>
          </div>
        </div>
      </header>

      <section className="mkt-wrap mkt-hero">
        <div className="mkt-hero-grid">
          <div className="mkt-hero-copy">
            <p className="mkt-eyebrow">IIDATECH / BUSINESS OS</p>
            <h1 className="mkt-hero-title">
              <span className="mkt-hero-os">The operating system for</span>
              <span className="mkt-hero-accent">BUSINESSES</span>
            </h1>
            <div className="mkt-pipe">
              <span>RESEARCH</span><i>→</i><span>PLAN</span><i>→</i><span>EXECUTE</span><i>→</i><span>AUTOMATE</span>
            </div>
            <p className="mkt-lead">
              Market-intelligence and business-execution for companies and teams — self-serve as a tool, or done-for-you as a service.
            </p>
            <div className="mkt-hero-cta">
              <WorkspaceEntryLink className="iid-btn iid-btn-primary">Start free now</WorkspaceEntryLink>
              <WorkspaceEntryLink className="iid-btn iid-btn-ghost">See demo</WorkspaceEntryLink>
            </div>
          </div>
          <HeroVisual />
        </div>
      </section>

      <section className="mkt-wrap mkt-trust">
        <span className="mkt-trust-label">Trusted across India</span>
        <div className="mkt-trust-logos">
          {["FinTech", "Healthcare", "SaaS", "D2C", "Real Estate", "Manufacturing"].map((n) => (
            <span key={n} className="mkt-trust-chip">{n}</span>
          ))}
        </div>
      </section>

      <section id="why" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">01 / The Problem</span>
          <h2 className="mkt-h2">Good decisions still run on guesswork.</h2>
          <p className="mkt-sub">7.86 Cr MSMEs employ 34.6 crore people — most without a dedicated research or strategy function.</p>
        </div>
        <div className="mkt-stat-row">
          <div className="mkt-stat-box"><strong>7.86 Cr</strong><span>MSMEs in India</span></div>
          <div className="mkt-stat-box"><strong>34.6 Cr</strong><span>People employed</span></div>
          <div className="mkt-stat-box"><strong>&lt;5%</strong><span>Have research teams</span></div>
        </div>
        <div className="mkt-pain-row">
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconSearch /></span><strong>No research team</strong><p>No in-house analysts or strategy bench.</p></div>
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconClock /></span><strong>Slow consulting</strong><p>Weeks of back-and-forth before you can act.</p></div>
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconUser /></span><strong>Small teams stretched thin</strong><p>Wearing every hat from research to outreach.</p></div>
          <div className="mkt-pain-tile"><span className="mkt-icon-ring"><IconGlobe /></span><strong>Global tools miss India</strong><p>Regulation, pricing, and buyers stay opaque.</p></div>
        </div>
      </section>

      <section id="features" className="mkt-wrap mkt-section">
        <div className="mkt-section-head">
          <span className="mkt-label">02 / The Solution</span>
          <h2 className="mkt-h2">One OS. Four functions your business is missing.</h2>
        </div>
        <div className="mkt-grid-4">
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
          <div className="mkt-section-head"><span className="mkt-label">Services</span><h2 className="mkt-h2">Six tools. One platform.</h2><p className="mkt-sub">Show proof, not pitch decks. Generate what you need, then act on it.</p></div>
          <div className="mkt-services-grid">
            {["Research", "Business Plan", "Execution", "Mentorship", "Automation", "Brand"].map((t, i) => (
              <article key={t} className="mkt-service">
                <span className="mkt-service-num">0{i + 1}</span>
                <h3 className="mkt-feature-title">{t}</h3>
                <p className="mkt-feature-body">Generate, review, and export from your IIDA workspace.</p>
              </article>
            ))}
          </div>
          <WorkspaceEntryLink className="iid-btn iid-btn-primary mkt-section-cta">Open workspace</WorkspaceEntryLink>
        </div>
      </section>

      <section id="how" className="mkt-wrap mkt-section">
        <div className="mkt-section-head"><span className="mkt-label">How it works</span><h2 className="mkt-h2">Three steps. One minute.</h2></div>
        <div className="mkt-process">
          <div className="mkt-process-step"><p className="mkt-step-big">01</p><h4>Register</h4><p>Get 30 free credits. No card required.</p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">02</p><h4>Input</h4><p>Idea, market, and industry — then generate.</p></div>
          <div className="mkt-process-step"><p className="mkt-step-big">03</p><h4>Result</h4><p>Sourced report ready to export and share.</p></div>
        </div>
      </section>

      <section id="automation" className="mkt-wrap mkt-section">
        <div className="mkt-section-head"><span className="mkt-label">AI Workforce</span><h2 className="mkt-h2">Hire the team you cannot afford yet.</h2></div>
        <div className="mkt-grid-3">
          {AGENTS.map((a) => (
            <article key={a.title} className="mkt-agent-card">
              <AgentBadge initials={a.initials} tone={a.tone} />
              <h3 className="mkt-feature-title">{a.title}</h3>
              <p className="mkt-feature-body">Specialized AI agent in your workspace.</p>
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
        <div className="mkt-section-head"><span className="mkt-label">Our work</span><h2 className="mkt-h2">Built for Indian verticals</h2></div>
        <div className="mkt-industry-grid">
          {["FinTech", "Healthcare", "SaaS", "D2C", "Manufacturing", "Logistics", "Education", "Real Estate"].map((n) => (
            <div key={n} className="mkt-industry-tile"><span>{n}</span></div>
          ))}
        </div>
      </section>

      <section className="mkt-wrap mkt-section">
        <div className="mkt-cta-banner">
          <span className="mkt-label">Ready to ship?</span>
          <h2 className="mkt-h2">Start with 30 free credits.</h2>
          <p className="mkt-sub">No card required. Your first report in under a minute.</p>
          <WorkspaceEntryLink className="iid-btn iid-btn-primary mkt-section-cta">Start free now</WorkspaceEntryLink>
        </div>
      </section>

      <section id="contact" className="mkt-wrap mkt-section mkt-section-last">
        <div className="mkt-section-head"><span className="mkt-label">Contact</span><h2 className="mkt-h2">Talk to the team.</h2></div>
        <div className="mkt-contact-grid">
          <div className="mkt-contact-stack">
            <div className="mkt-contact-card"><span className="mkt-icon-ring sm"><IconMail /></span><div><strong>Email</strong><a href="mailto:vidhugupta1996@gmail.com">vidhugupta1996@gmail.com</a></div></div>
            <div className="mkt-contact-card"><span className="mkt-icon-ring sm"><IconPhone /></span><div><strong>Phone</strong><a href="tel:+919545403431">+91 95454 03431</a></div></div>
            <div className="mkt-contact-card"><span className="mkt-icon-ring sm"><IconPin /></span><div><strong>Based in</strong><span>India — serving companies globally</span></div></div>
          </div>
          <ContactForm />
        </div>
      </section>

      <footer className="mkt-footer">
        <div className="mkt-wrap mkt-footer-grid">
          <div><h4>Product</h4><p><a href="#features">Solution</a><br /><a href="#services">Services</a></p></div>
          <div><h4>Company</h4><p><a href="#contact">Contact</a></p></div>
          <div><h4>Email</h4><p><a href="mailto:vidhu@pronto.me">vidhu@pronto.me</a></p></div>
        </div>
        <p className="mkt-wrap mkt-footer-copy">IIDATECH — Business Operating System · India</p>
      </footer>
    </main>
  );
}