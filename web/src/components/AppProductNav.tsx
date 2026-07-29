"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const modules = [
  { href: "/app/research", label: "Market Research", short: "Research" },
  { href: "/app/plan", label: "Business Plan", short: "Plan" },
  { href: "/app/team", label: "Employee OS", short: "Team" },
  { href: "/app/automation", label: "Automation", short: "Automation" },
];

export function AppProductNav() {
  const pathname = usePathname();
  return (
    <nav className="mb-8 flex flex-wrap gap-2 border-b border-[var(--iid-line)] pb-4">
      {modules.map((m) => {
        const active = pathname === m.href || pathname?.startsWith(m.href + "/");
        return (
          <Link
            key={m.href}
            href={m.href}
            className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
              active
                ? "bg-[var(--iid-blue)] text-white"
                : "border border-[var(--iid-line)] text-[var(--iid-muted)] hover:border-[var(--iid-blue)] hover:text-white"
            }`}
          >
            <span className="hidden sm:inline">{m.label}</span>
            <span className="sm:hidden">{m.short}</span>
          </Link>
        );
      })}
    </nav>
  );
}