"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function OAuthCallbackContent() {
  const params = useSearchParams();
  const success = params.get("success");
  const error = params.get("error");
  const provider = params.get("provider");

  return (
    <div className="min-h-[50vh] flex items-center justify-center p-8">
      <section className="iid-card max-w-md w-full space-y-4 text-center">
        {success ? (
          <>
            <h1 className="font-display text-xl font-bold">Connected</h1>
            <p className="text-sm muted">{provider ? `${provider} is now linked to your workspace.` : "OAuth connection saved."}</p>
          </>
        ) : (
          <>
            <h1 className="font-display text-xl font-bold">Connection failed</h1>
            <p className="text-sm text-red-300">{error || "Unknown error"}</p>
          </>
        )}
        <Link href="/app/team" className="iid-btn iid-btn-primary inline-flex">Back to Employee OS</Link>
      </section>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={<p className="muted p-8">Processing OAuth…</p>}>
      <OAuthCallbackContent />
    </Suspense>
  );
}
