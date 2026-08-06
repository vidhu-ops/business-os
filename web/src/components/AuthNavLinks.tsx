"use client";

import Link from "next/link";
import { WorkspaceEntryLink } from "@/components/WorkspaceEntryLink";

type Props = {
  /** Show a secondary See demo entry */
  showDemo?: boolean;
  /** Compact styling for app chrome */
  compact?: boolean;
  className?: string;
  onNavigate?: () => void;
};

/** Single auth CTA (+ optional See demo) for headers next to ThemeToggle. */
export function AuthNavLinks({ showDemo = false, compact = false, className = "", onNavigate }: Props) {
  return (
    <div className={`auth-nav-links${compact ? " auth-nav-links-compact" : ""}${className ? ` ${className}` : ""}`}>
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
