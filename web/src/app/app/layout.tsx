"use client";

import { AppNav } from "@/components/AppNav";
import { api } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [email, setEmail] = useState<string>("");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api
      .me()
      .then((user) => {
        setEmail(user.email);
        setReady(true);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  if (!ready) {
    return <main className="flex min-h-screen items-center justify-center text-sm text-[var(--iid-muted)]">Loading…</main>;
  }

  return (
    <div>
      <AppNav email={email} />
      <div className="mx-auto max-w-6xl px-5 py-8">{children}</div>
      <footer className="mx-auto max-w-6xl px-5 pb-10 pt-4 text-xs text-[var(--iid-muted)]">
        <Link href="/">← Back to marketing site</Link>
      </footer>
    </div>
  );
}
