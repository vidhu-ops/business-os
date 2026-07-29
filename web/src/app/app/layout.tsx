"use client";

import { AppNav } from "@/components/AppNav";
import { AppProductNav } from "@/components/AppProductNav";
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
        <p className="text-sm text-[var(--iid-muted)]">Make sure the API is running on port 8000, then retry.</p>
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
    <div>
      <AppNav email={email} />
      <div className="mx-auto max-w-6xl px-5 py-8">
        {showProductNav ? <AppProductNav /> : null}
        {children}
      </div>
      <footer className="mx-auto max-w-6xl px-5 pb-10 pt-4 text-xs text-[var(--iid-muted)]">
        <Link href="/">← Back to marketing site</Link>
      </footer>
    </div>
  );
}
