"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";
import { api, getToken, type User } from "@/lib/api";

type Props = {
  showDemo?: boolean;
  compact?: boolean;
  className?: string;
  onNavigate?: () => void;
};

/** Single auth CTA (+ optional See demo) for headers next to ThemeToggle. */
export function AuthNavLinks({ showDemo = false, compact = false, className = "", onNavigate }: Props) {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(() => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setReady(true);
      return;
    }
    api
      .me()
      .then((u) => setUser(u))
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setReady(false);
    const token = getToken();
    if (!token) {
      setUser(null);
      setReady(true);
      return;
    }
    api
      .me()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  useEffect(() => {
    const onFocus = () => refresh();
    const onStorage = (e: StorageEvent) => {
      if (e.key === "iida_token") refresh();
    };
    window.addEventListener("focus", onFocus);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("storage", onStorage);
    };
  }, [refresh]);

  const wrap = `auth-nav-links${compact ? " auth-nav-links-compact" : ""}${className ? ` ${className}` : ""}`;

  if (!ready) {
    return <div className={wrap} aria-hidden />;
  }

  if (user?.email) {
    const first = (user.name || user.email).split(/\s+/)[0];
    return (
      <div className={wrap}>
        <Link
          href="/app/dashboard"
          className={`iid-btn iid-btn-primary auth-nav-cta${compact ? " auth-nav-cta-compact" : ""}`}
          onClick={onNavigate}
        >
          Dashboard
        </Link>
        <Link
          href="/app/profile"
          className={`iid-btn iid-btn-ghost auth-nav-demo${compact ? " auth-nav-cta-compact" : ""}`}
          onClick={onNavigate}
          title={user.email}
        >
          {first}
        </Link>
      </div>
    );
  }

  return (
    <div className={wrap}>
      <Link
        href="/login"
        className={`iid-btn iid-btn-primary auth-nav-cta${compact ? " auth-nav-cta-compact" : ""}`}
        onClick={onNavigate}
      >
        Sign in
      </Link>
      {showDemo ? (
        <WorkspaceEntryLink className="iid-btn iid-btn-ghost auth-nav-demo" onClick={onNavigate}>
          See demo
        </WorkspaceEntryLink>
      ) : null}
    </div>
  );
}
