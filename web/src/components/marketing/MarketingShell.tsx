"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { AuthNavLinks } from "@/components/AuthNavLinks";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";

const NAV = [
  { label: "Home", href: "/" },
  { label: "Pricing", href: "/pricing" },
  { label: "Problem", href: "/#why" },
  { label: "Solution", href: "/#features" },
  { label: "Services", href: "/#services" },
  { label: "How", href: "/#how" },
  { label: "Workforce", href: "/#automation" },
  { label: "Partners", href: "/partners" },
  { label: "Contact", href: "/#contact" },
];

const MORE_LINKS = [
  { label: "How it works", href: "/how-it-works" },
  { label: "Pricing", href: "/pricing" },
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
              {!onHome
                ? null
                : MORE_LINKS.map((item) => (
                    <Link key={item.href} href={item.href} onClick={() => setOpen(false)} className="mkt-mobile-more">
                      {item.label}
                    </Link>
                  ))}
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
        <div className="mkt-wrap mkt-footer-grid">
          <div>
            <h4>Product</h4>
            <p>
              <Link href="/how-it-works">How it works</Link>
              <br />
              <Link href="/pricing">Pricing</Link>
              <br />
              <Link href="/partners">Become a partner</Link>
            </p>
          </div>
          <div>
            <h4>Workspace</h4>
            <p>
              <Link href="/login">Sign in</Link>
              <br />
              <WorkspaceEntryLink>See demo</WorkspaceEntryLink>
            </p>
          </div>
          <div>
            <h4>Contact</h4>
            <p>
              <a href="mailto:vidhu@pronto.me">vidhu@pronto.me</a>
              <br />
              <a href="tel:+919545403431">+91 95454 03431</a>
            </p>
          </div>
        </div>
        <p className="mkt-wrap mkt-footer-copy">IIDATECH - Business Ecosystem</p>
      </footer>
    </main>
  );
}