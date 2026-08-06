"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { isDemoEmail } from "@/lib/api";

const links = [
  { href: "/", label: "Home" },
  { href: "/app/dashboard", label: "Dashboard" },
  { href: "/app/projects", label: "Projects" },
  { href: "/app/research", label: "Research" },
  { href: "/app/plan", label: "Plan" },
  { href: "/app/team", label: "Employee OS" },
  { href: "/app/automation", label: "Automation" },
  { href: "/app/saved", label: "Saved Files" },
  { href: "/partners", label: "Partners" },
  { href: "/app/profile", label: "Profile" },
];

export function AppNav({ email }: { email?: string }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const demo = isDemoEmail(email);

  return (
    <header className="app-nav-shell">
      <div className="app-nav-inner">
        <div className="flex items-center gap-3">
          <Link href="/" className="font-display text-sm font-extrabold tracking-[0.2em] uppercase app-nav-logo">
            IIDA<span className="text-[var(--iid-blue)]">TECH</span>
          </Link>
          <span className="hidden text-xs text-[var(--iid-muted)] sm:inline">Workspace</span>
        </div>

        <nav className="app-nav-links" aria-label="Workspace">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`app-nav-link ${link.href === "/" ? (pathname === "/" ? "is-active" : "") : pathname === link.href || pathname?.startsWith(link.href + "/") ? "is-active" : ""}`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle className="mkt-nav-desktop-only" />
          {demo ? (
            <div className="auth-nav-links auth-nav-links-compact mkt-nav-desktop-only">
              <Link href="/login" className="auth-nav-signin">
                Sign in
              </Link>
              <Link href="/login?mode=register" className="iid-btn iid-btn-primary auth-nav-signup-compact">
                Sign up free
              </Link>
            </div>
          ) : (
            <span className="app-nav-email text-xs text-[var(--iid-muted)] mkt-nav-desktop-only">{email || ""}</span>
          )}
          <button
            type="button"
            className="app-mobile-menu-btn"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open ? (
        <nav className="app-mobile-nav" aria-label="Workspace mobile">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? "is-active" : ""}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="mkt-mobile-nav-actions">
            <ThemeToggle />
            {demo ? (
              <div className="auth-nav-links auth-nav-links-compact">
                <Link href="/login" className="auth-nav-signin" onClick={() => setOpen(false)}>
                  Sign in
                </Link>
                <Link href="/login?mode=register" className="iid-btn iid-btn-primary auth-nav-signup-compact" onClick={() => setOpen(false)}>
                  Sign up free
                </Link>
              </div>
            ) : email ? (
              <span className="text-xs text-[var(--iid-muted)]">{email}</span>
            ) : null}
          </div>
        </nav>
      ) : null}
    </header>
  );
}