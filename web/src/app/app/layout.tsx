"use client";

import { AppNav } from "@/components/AppNav";
import { AppProductNav } from "@/components/AppProductNav";
import { DemoBanner } from "@/components/DemoBanner";
import { ensureSession } from "@/lib/api";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const showProductNav = ["/app/research", "/app/plan", "/app/team", "/app/automation", "/app/workspace", "/app/audit"].some(
    (p) => pathname === p || pathname?.startsWith(p + "/"),
  );
  const [email, setEmail] = useState<string>("");
  const [ready, setReady] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const boot = async () => {
      setError(null);
      const token = typeof window !== "undefined" ? localStorage.getItem("iida_token") : null;
      if (!token) {
        setRedirecting(true);
        router.replace(`/login?next=${encodeURIComponent(pathname || "/app/dashboard")}`);
        return;
      }
      setRedirecting(false);
      // Show shell immediately when a token exists — avoids a full-screen block on every navigation.
      setReady(true);
      try {
        const user = await ensureSession();
        if (!cancelled) {
          setEmail(user.email);
        }
      } catch (err) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "";
          if (msg === "NOT_AUTHENTICATED") {
            setReady(false);
            router.replace(`/login?next=${encodeURIComponent(pathname || "/app/dashboard")}`);
            return;
          }
          setError(msg || "Could not start workspace session");
        }
      }
    };
    boot();
    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  if (redirecting) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--iid-line)] border-t-[var(--iid-blue)]" />
        <p className="text-sm text-[var(--iid-muted)]">Redirecting to sign in…</p>
        <p className="max-w-sm text-xs text-[var(--iid-muted)]">
          On Render free tier, the first visit after idle sleep can take up to a minute to wake.
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-sm text-red-600">{error}</p>
        <p className="text-sm text-[var(--iid-muted)]">
          On Render, free-tier services sleep when idle and can take up to a minute to wake. Click Retry, or check the
          service logs in the Render dashboard if this keeps failing.
        </p>
        <Link href="/login" className="iid-btn iid-btn-primary">
          Log in
        </Link>
        <button
          type="button"
          className="iid-btn iid-btn-ghost"
          onClick={() => {
            setReady(false);
            setError(null);
            ensureSession()
              .then((user) => {
                setEmail(user.email);
                setReady(true);
              })
              .catch((err) => {
                const msg = err instanceof Error ? err.message : "";
                if (msg === "NOT_AUTHENTICATED") {
                  router.replace(`/login?next=${encodeURIComponent(pathname || "/app/dashboard")}`);
                  return;
                }
                setError(msg || "Could not start workspace session");
              });
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
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--iid-line)] border-t-[var(--iid-blue)]" />
        <p className="text-sm text-[var(--iid-muted)]">Starting workspace…</p>
        <p className="max-w-sm text-xs text-[var(--iid-muted)]">
          Waking the server — this can take 30–90 seconds on the free tier after idle sleep.
        </p>
      </main>
    );
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
