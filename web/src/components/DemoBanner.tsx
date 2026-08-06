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
    <div className="demo-banner-bar">
      <p className="demo-banner-copy">
        <strong>Demo mode</strong> - browse the sample workspace. Research, hiring, and saves stay locked until you create an account.
      </p>
      <div className="demo-banner-actions">
        <Link href="/login" className="iid-btn iid-btn-primary demo-banner-signup">
          Sign in
        </Link>
      </div>
    </div>
  );
}