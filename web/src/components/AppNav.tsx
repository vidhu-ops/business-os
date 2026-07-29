import Link from "next/link";

const links = [
  { href: "/app/dashboard", label: "Dashboard" },
  { href: "/app/projects", label: "Projects" },
  { href: "/app/workspace", label: "Workspace" },
  { href: "/app/saved", label: "Saved Files" },
  { href: "/app/profile", label: "Profile" },
];

export function AppNav({ email }: { email?: string }) {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--iid-line)] bg-[rgba(5,7,15,0.92)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="font-display text-sm font-extrabold tracking-[0.2em] text-white uppercase">
            IIDA<span className="text-[var(--iid-blue)]">TECH</span>
          </Link>
          <span className="hidden text-xs text-[var(--iid-muted)] sm:inline">Founder app</span>
        </div>
        <nav className="flex flex-wrap items-center gap-2">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-3 py-1.5 text-xs font-semibold text-[var(--iid-muted)] transition hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="text-xs text-[var(--iid-muted)]">{email || ""}</div>
      </div>
    </header>
  );
}
