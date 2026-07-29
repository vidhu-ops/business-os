"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email: string; name: string } | null>(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold">Profile</h1>
        <p className="mt-2 muted">Account settings for your IIDA workspace.</p>
      </div>
      <section className="iid-card space-y-2">
        <p><strong>Name:</strong> {user?.name || "User"}</p>
        <p><strong>Email:</strong> {user?.email || "-"}</p>
        <button
          className="iid-btn iid-btn-ghost mt-4"
          type="button"
          onClick={async () => {
            await api.logout();
            router.push("/");
          }}
        >
          Log out
        </button>
      </section>
    </div>
  );
}
