"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useState, type ComponentProps } from "react";

type Props = Omit<ComponentProps<typeof Link>, "href"> & {
  href?: string;
};

/** Signs in (demo session) before navigating into the workspace. */
export function WorkspaceEntryLink({ href = "/app/research?project=demo_readonly", className, children, onClick, ...rest }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  return (
    <span className="inline-flex flex-col items-stretch gap-1">
      <Link
      href={href}
      className={className}
      aria-busy={busy}
      onClick={async (e) => {
        onClick?.(e);
        if (e.defaultPrevented) return;
        e.preventDefault();
        if (busy) return;
        setBusy(true);
        setError("");
        try {
          await api.demoLogin();
          router.push(href);
        } catch (err) {
          const msg = err instanceof Error ? err.message : "Demo login failed";
          setError(msg);
        } finally {
          setBusy(false);
        }
      }}
      {...rest}
    >
      {busy ? "Opening workspace…" : children}
    </Link>
    {error ? <span className="text-xs text-red-400">{error}</span> : null}
    </span>
  );
}
