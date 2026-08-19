"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ensureSession } from "@/lib/api";

const WHATSAPP = "https://wa.me/919545403431";
const TEL = "tel:+919545403431";
const PHONE_LABEL = "+91 95454 03431";

type PlanRow = {
  id: string;
  name: string;
  tagline?: string;
  description?: string;
};

function CheckoutContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const planId = (searchParams.get("plan") || "growth").toLowerCase();
  const [plans, setPlans] = useState<PlanRow[]>([]);
  const [userEmail, setUserEmail] = useState("");

  const selected = plans.find((p) => p.id === planId) || plans[0];

  useEffect(() => {
    api
      .paymentPlans()
      .then((data) => setPlans((data.plans as PlanRow[]) || []))
      .catch(() => setPlans([]));
    ensureSession()
      .then((user) => setUserEmail(user.email))
      .catch(() => router.replace(`/login?next=${encodeURIComponent(`/checkout?plan=${planId}`)}`));
  }, [planId, router]);

  return (
    <div className="space-y-6">
      <div>
        <p className="mkt-eyebrow">Checkout</p>
        <h1 className="mkt-page-title">Paid plans coming soon</h1>
        <p className="mkt-lead mkt-page-lead">
          Online checkout is paused while we finalize pricing. Enjoy the demo and free credits until then — or call / WhatsApp to talk about your plan.
        </p>
      </div>

      <section className="iid-card space-y-4 max-w-xl">
        <h2 className="font-display text-xl font-bold">{selected?.name || "Plan"}</h2>
        {selected?.tagline ? <p className="muted text-sm">{selected.tagline}</p> : null}
        <p className="font-display text-2xl font-bold text-[var(--iid-blue)]">Price coming soon</p>
        <p className="text-sm muted">Enjoy demo & free credits till then.</p>
        {userEmail ? <p className="text-sm muted">Account: {userEmail}</p> : null}
        <div className="flex flex-wrap gap-3">
          <a href={WHATSAPP} target="_blank" rel="noreferrer" className="iid-btn iid-btn-primary">
            WhatsApp {PHONE_LABEL}
          </a>
          <a href={TEL} className="iid-btn iid-btn-ghost">
            Call now
          </a>
          <Link href="/pricing" className="iid-btn iid-btn-ghost">
            Back to pricing
          </Link>
          <Link href="/app/dashboard" className="iid-btn iid-btn-ghost">
            Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}

export function CheckoutPage() {
  return (
    <Suspense fallback={<p className="muted">Loading checkout…</p>}>
      <CheckoutContent />
    </Suspense>
  );
}
