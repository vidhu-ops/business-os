"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api } from "@/lib/api";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const intent = searchParams.get("intent");
  const nextPath = searchParams.get("next");
  const oauthError = searchParams.get("error");
  const initialMode = searchParams.get("mode") === "register" ? "register" : "login";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(true);

  useEffect(() => {
    if (searchParams.get("mode") === "register") setMode("register");
  }, [searchParams]);

  useEffect(() => {
    if (oauthError) setError(decodeURIComponent(oauthError));
  }, [oauthError]);

  useEffect(() => {
    api.googleAuthStatus()
      .then((d) => setGoogleEnabled(Boolean(d.enabled)))
      .catch(() => setGoogleEnabled(false));
  }, []);

  const afterAuthPath =
    nextPath && nextPath.startsWith("/app")
      ? nextPath
      : intent === "audit"
        ? "/app/audit"
        : "/app/dashboard";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "login") {
        await api.login(email, password);
      } else {
        await api.register(email, password, name);
      }
      router.push(afterAuthPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  async function startDemo() {
    setLoading(true);
    setError("");
    try {
      await api.demoLogin();
      router.push("/app/research?project=demo_readonly");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo login failed");
    } finally {
      setLoading(false);
    }
  }

  function startGoogle() {
    setLoading(true);
    window.location.href = api.googleAuthStartUrl(afterAuthPath);
  }

  return (
    <main className="login-shell">
      <div className="login-grid">
        <section className="login-brand">
          <div className="login-brand-top">
            <Link href="/" className="mkt-logo">IIDA<span>TECH</span></Link>
            <ThemeToggle />
          </div>
          <h1 className="login-title">Build your business in minutes.</h1>
          <p className="login-lead">Research, plan, and execute in one business ecosystem — built for companies and teams.</p>
          <div className="login-pills">
            <span>1 free company audit</span>
            <span>No card required</span>
            <span>Reports in minutes</span>
          </div>
        </section>
        <section className="login-panel iid-card">
          <h2 className="font-display text-2xl font-bold tracking-tight">{mode === "login" ? "Welcome back" : "Create account"}</h2>
          <p className="mt-3 text-sm text-[var(--iid-muted)]">Your IIDA workspace awaits.</p>

          {googleEnabled ? (
            <button
              type="button"
              className="mt-6 flex w-full items-center justify-center gap-3 rounded-xl border border-[var(--iid-line)] bg-white px-4 py-3 text-sm font-semibold text-neutral-800 shadow-sm transition hover:bg-neutral-50 disabled:opacity-60"
              onClick={startGoogle}
              disabled={loading}
            >
              <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden>
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
              </svg>
              {mode === "login" ? "Continue with Google" : "Sign up with Google"}
            </button>
          ) : null}

          {googleEnabled ? (
            <div className="my-5 flex items-center gap-3 text-xs text-[var(--iid-muted)]">
              <span className="h-px flex-1 bg-[var(--iid-line)]" />
              or use email
              <span className="h-px flex-1 bg-[var(--iid-line)]" />
            </div>
          ) : (
            <div className="mt-6" />
          )}

          <form className="space-y-4" onSubmit={onSubmit}>
            {mode === "register" && (
              <input className="iid-input" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
            )}
            <input
              className="iid-input"
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <input
              className="iid-input"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && <p className="text-sm text-red-400">{error}</p>}
            <button className="iid-btn iid-btn-primary w-full" type="submit" disabled={loading}>
              {loading ? "Working…" : mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
          <button className="iid-btn iid-btn-ghost mt-3 w-full" type="button" onClick={startDemo} disabled={loading}>
            Continue with demo
          </button>
          <button
            className="mt-4 text-xs text-[var(--iid-muted)] underline"
            type="button"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
          </button>
        </section>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="login-shell"><p className="muted p-8">Loading…</p></main>}>
      <LoginForm />
    </Suspense>
  );
}