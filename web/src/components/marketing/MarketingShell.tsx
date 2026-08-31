"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { AuthNavLinks } from "@/components/AuthNavLinks";
import { ThemeToggle } from "@/components/ThemeToggle";
import { SITE_EMAIL, SITE_PHONE, SITE_PHONE_TEL, SITE_WHATSAPP } from "@/lib/site";

const NAV = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Services", href: "/#services" },
  { label: "Pricing", href: "/pricing" },
  { label: "Partners", href: "/partners" },
  { label: "Contact", href: "/#contact" },
];

const MORE_LINKS = [
  { label: "How it works", href: "/how-it-works" },
  { label: "Business topics", href: "/topics" },
  { label: "Market research", href: "/services/research" },
  { label: "Business plan", href: "/services/plan" },
  { label: "Business consultation", href: "/services/mentor" },
  { label: "Privacy", href: "/privacy" },
  { label: "Terms", href: "/terms" },
];

export function MarketingShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const onHome = pathname === "/";

  return (
    <main className="mkt-page">
      <header className="mkt-nav-shell">
        <div className="mkt-wrap mkt-nav-grid">
          <Link href="/" className="mkt-logo mkt-nav-brand" onClick={() => setOpen(false)}>
            IIDA<span>TECH</span>
          </Link>

          <nav className="mkt-nav-links" aria-label="Main">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="mkt-nav-actions">
            <ThemeToggle className="mkt-nav-desktop-only" />
            <AuthNavLinks showDemo className="mkt-nav-desktop-only" />
            <button
              type="button"
              className="mkt-mobile-menu-btn"
              aria-label={open ? "Close menu" : "Open menu"}
              onClick={() => setOpen((v) => !v)}
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {open ? (
          <div className="mkt-mobile-nav">
            <div className="mkt-wrap mkt-mobile-nav-inner">
              {(onHome ? NAV : [...NAV, ...MORE_LINKS]).map((item) => (
                <Link key={item.href} href={item.href} onClick={() => setOpen(false)}>
                  {item.label}
                </Link>
              ))}
              {onHome
                ? MORE_LINKS.map((item) => (
                    <Link key={item.href} href={item.href} onClick={() => setOpen(false)} className="mkt-mobile-more">
                      {item.label}
                    </Link>
                  ))
                : null}
              <div className="mkt-mobile-nav-actions">
                <ThemeToggle />
                <AuthNavLinks showDemo onNavigate={() => setOpen(false)} />
              </div>
            </div>
          </div>
        ) : null}
      </header>

      {children}

      <footer className="mkt-footer">
        <div className="mkt-wrap mkt-footer-about">
          <h3 className="mkt-footer-brand">
            IIDA<span>TECH</span>
          </h3>
          <p>
            IIDATECH is a business OS for founders, startups, and B2B companies. Use it for market research, business
            planning, founder mentoring, new business growth, business consultation workflows, Employee OS execution, and
            automation — so you can validate ideas and ship decisions without slow agency cycles.
          </p>
          <p className="mkt-footer-keywords" aria-label="Popular IIDATECH topics">
            <Link href="/topics/market-research-for-founders">Market research for founders</Link>
            <Link href="/topics/business-consultation">Business consultation</Link>
            <Link href="/topics/new-business-growth">New business growth</Link>
            <Link href="/topics/startup-business-plan">Startup business plan</Link>
            <Link href="/topics/business-research">Business research</Link>
            <Link href="/topics/msme-business-growth">MSME growth</Link>
            <Link href="/topics/ai-business-planning">AI business planning</Link>
            <Link href="/topics/company-growth-audit">Company growth audit</Link>
            <Link href="/topics">All business topics</Link>
          </p>
        </div>
        <div className="mkt-wrap mkt-footer-grid">
          <div>
            <h4>Product</h4>
            <p>
              <Link href="/how-it-works">How it works</Link>
              <br />
              <Link href="/about">About IIDATECH</Link>
              <br />
              <Link href="/pricing">Pricing</Link>
              <br />
              <Link href="/partners">Become a partner</Link>
            </p>
          </div>
          <div>
            <h4>Grow with IIDATECH</h4>
            <p>
              <Link href="/topics/market-research-for-founders">Market research for founders</Link>
              <br />
              <Link href="/topics/startup-business-plan">Startup business plan</Link>
              <br />
              <Link href="/topics/business-consultation">Business consultation</Link>
              <br />
              <Link href="/topics/new-business-growth">New business growth</Link>
              <br />
              <Link href="/topics/msme-business-growth">MSME business growth</Link>
              <br />
              <Link href="/topics">All business topics</Link>
            </p>
          </div>
          <div>
            <h4>Workspace</h4>
            <p>
              <Link href="/login">Sign in</Link>
              <br />
              <Link href="/login?mode=register">Start free</Link>
              <br />
              <Link href="/app/research?project=demo_readonly">See demo</Link>
              <br />
              <Link href="/app/dashboard">Dashboard</Link>
            </p>
          </div>
          <div>
            <h4>Contact</h4>
            <p>
              <a href={`mailto:${SITE_EMAIL}`}>{SITE_EMAIL}</a>
              <br />
              <a href={SITE_PHONE_TEL}>{SITE_PHONE}</a>
              <br />
              <a href={SITE_WHATSAPP} target="_blank" rel="noreferrer">
                WhatsApp
              </a>
              <br />
              <Link href="/privacy">Privacy Policy</Link>
              <br />
              <Link href="/terms">Terms of Service</Link>
            </p>
          </div>
        </div>
        <p className="mkt-wrap mkt-footer-copy">
          © {new Date().getFullYear()} IIDATECH — market research, business planning, consultation, and growth OS for
          founders and B2B companies.
        </p>
      </footer>
    </main>
  );
}
