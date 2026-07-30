"use client";

import { AppNav } from "@/components/AppNav";
import { AppProductNav } from "@/components/AppProductNav";
import { DemoBanner } from "@/components/DemoBanner";
import { ensureSession } from "@/lib/api";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showProductNav = ["/app/research", "/app/plan", "/app/team", "/app/automation", "/app/workspace"].some(
    (p) => pathname === p || pathname?.startsWith(p + "/"),
  );
  const [email, setEmail] = useState<string>("");
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const boot = async () => {
      setError(null);
      try {
        const user = await ensureSession();
        if (!cancelled) {
          setEmail(user.email);
          setReady(true);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not start workspace session");
        }
      }
    };
    boot();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-sm text-red-600">{error}</p>
        <p className="text-sm text-[var(--iid-muted)]">
          On Render, free-tier services sleep when idle and can take up to a minute to wake. Click Retry, or check the
          service logs in the Render dashboard if this keeps failing.
        </p>
        <button
          type="button"
          className="iid-btn iid-btn-primary"
          onClick={() => {
            setReady(false);
            setError(null);
            ensureSession()
              .then((user) => {
                setEmail(user.email);
                setReady(true);
              })
              .catch((err) => setError(err instanceof Error ? err.message : "Could not start workspace session"));
          }}
        >
          Retry
        </button>
        <Link href="/" className="text-sm text-[var(--iid-blue)] hover:underline">
          ← Back to home
        </Link>
      </main>
    );
  }

  if (!ready) {
    return <main className="flex min-h-screen items-center justify-center text-sm text-[var(--iid-muted)]">Loading…</main>;
  }

  return (
    <div className="app-shell">
      <AppNav email={email} />
      <div className="app-shell-main">
        {showProductNav ? <AppProductNav /> : null}
        <DemoBanner />
        {children}
      </div>
      <footer className="app-shell-footer">
        <Link href="/">← Back to marketing site</Link>
      </footer>
    </div>
  );
}
