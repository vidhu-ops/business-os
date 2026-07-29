import Link from "next/link";

export default function LandingPage() {
  return (
    <main>
      <header className="sticky top-0 z-50 border-b border-[var(--iid-line)] bg-[rgba(5,7,15,0.9)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <p className="font-display text-sm font-extrabold tracking-[0.2em] uppercase">
            IIDA<span className="text-[var(--iid-blue)]">TECH</span>
          </p>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-xs font-semibold text-[var(--iid-muted)] hover:text-white">
              Log in
            </Link>
            <Link href="/login" className="iid-btn iid-btn-primary">
              Start free
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-5 py-20 text-center">
        <p className="text-xs font-bold tracking-[0.28em] text-[var(--iid-muted)] uppercase">Business OS for founders</p>
        <h1 className="font-display mt-4 text-5xl leading-tight font-bold tracking-tight md:text-6xl">
          Turn your idea into a fundable business plan
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-[var(--iid-muted)]">
          Research your market, generate investor-ready reports, and run execution with an AI team — without months of
          manual work.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/login" className="iid-btn iid-btn-primary">
            Start free now
          </Link>
          <a href="#features" className="iid-btn iid-btn-ghost">
            See how it works
          </a>
        </div>
      </section>

      <section id="features" className="mx-auto grid max-w-6xl gap-4 px-5 pb-20 md:grid-cols-3">
        {[
          ["Research", "18-topic market reports with sourced evidence and sizing."],
          ["Business plan", "Submission-ready plans with ICP, GTM, and financials."],
          ["Execution", "Employee OS for outreach, campaigns, ops, and automations."],
        ].map(([title, body]) => (
          <article key={title} className="iid-card">
            <h3 className="font-display text-xl font-bold">{title}</h3>
            <p className="mt-2 text-sm text-[var(--iid-muted)]">{body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
