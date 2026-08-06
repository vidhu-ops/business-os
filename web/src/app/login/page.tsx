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
  const initialMode = searchParams.get("mode") === "register" ? "register" : "login";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get("mode") === "register") setMode("register");
  }, [searchParams]);

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
          <form className="mt-8 space-y-4" onSubmit={onSubmit}>
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
