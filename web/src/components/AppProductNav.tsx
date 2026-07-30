"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const modules = [
  { href: "/app/audit", label: "Company Audit", short: "Audit" },
  { href: "/app/research", label: "Market Research", short: "Research" },
  { href: "/app/plan", label: "Business Plan", short: "Plan" },
  { href: "/app/team", label: "Employee OS", short: "Team" },
  { href: "/app/automation", label: "Automation", short: "Automation" },
];

export function AppProductNav() {
  const pathname = usePathname();
  return (
    <nav className="app-product-nav" aria-label="Workspace modules">
      <div className="app-product-nav-scroll">
        {modules.map((m) => {
          const active = pathname === m.href || pathname?.startsWith(m.href + "/");
          return (
            <Link
              key={m.href}
              href={m.href}
              className={`app-product-pill ${active ? "is-active" : ""}`}
            >
              <span className="hidden sm:inline">{m.label}</span>
              <span className="sm:hidden">{m.short}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
