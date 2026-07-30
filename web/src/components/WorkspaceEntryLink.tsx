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

  return (
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
        try {
          await api.demoLogin();
          router.push(href);
        } catch {
          router.push(href);
        } finally {
          setBusy(false);
        }
      }}
      {...rest}
    >
      {busy ? "Opening workspace…" : children}
    </Link>
  );
}
