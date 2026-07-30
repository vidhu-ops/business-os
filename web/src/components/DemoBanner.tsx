"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type User } from "@/lib/api";

export function DemoBanner() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  if (!user?.is_demo) return null;

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-sm text-amber-950">
      <strong>Demo mode</strong> — you are viewing a sample report. You cannot run research or save changes.{" "}
      <Link href="/login?mode=register" className="font-medium underline">
        Sign up free
      </Link>{" "}
      to create your own projects.
    </div>
  );
}