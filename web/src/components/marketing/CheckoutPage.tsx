"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { ensureSession } from "@/lib/api";

type PlanRow = {
  id: string;
  name: string;
  amount_paise?: number;
  currency?: string;
  price_label?: string;
  tagline?: string;
  description?: string;
};

function formatInr(paise?: number) {
  if (!paise) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(
    paise / 100,
  );
}

function CheckoutContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const planId = (searchParams.get("plan") || "growth").toLowerCase();
  const [plans, setPlans] = useState<PlanRow[]>([]);
  const [gatewayReady, setGatewayReady] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [userEmail, setUserEmail] = useState("");

  const selected = plans.find((p) => p.id === planId) || plans[0];

  useEffect(() => {
    api.paymentPlans().then((data) => {
      setPlans((data.plans as PlanRow[]) || []);
      setGatewayReady(Boolean((data.gateway as { configured?: boolean })?.configured));
    }).catch(() => setGatewayReady(false));
    ensureSession()
      .then((user) => setUserEmail(user.email))
      .catch(() => router.replace(`/login?next=${encodeURIComponent(`/checkout?plan=${planId}`)}`));
  }, [planId, router]);

  async function payNow() {
    if (!selected) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.startCheckout(selected.id);
      const checkout = data.checkout;
      if (!checkout?.checkout_url || !checkout?.fields) {
        setError("Checkout session could not be created.");
        return;
      }
      const form = formRef.current;
      if (!form) return;
      form.action = checkout.checkout_url;
      form.method = "POST";
      form.innerHTML = "";
      Object.entries(checkout.fields).forEach(([name, value]) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = String(value);
        form.appendChild(input);
      });
      form.submit();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Payment could not start";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="mkt-eyebrow">Checkout</p>
        <h1 className="mkt-page-title">Complete your upgrade</h1>
        <p className="mkt-lead mkt-page-lead">
          Pay securely with UPI, cards, or net banking via Freecharge Payment Gateway.
        </p>
      </div>

      {gatewayReady === false ? (
        <div className="iid-card border border-amber-500/40 bg-amber-500/10">
          <p className="font-semibold text-amber-200">Payments not live yet</p>
          <p className="mt-2 text-sm text-amber-100/90">
            Add your Freecharge merchant credentials to Render (<code>FREECHARGE_MERCHANT_ID</code>,{" "}
            <code>FREECHARGE_SECRET_KEY</code>, <code>FREECHARGE_AES_KEY</code>). You can still use the free Starter plan.
          </p>
          <Link href="/pricing" className="iid-btn iid-btn-ghost mt-4 inline-flex">
            Back to pricing
          </Link>
        </div>
      ) : null}

      <section className="iid-card space-y-4 max-w-xl">
        <h2 className="font-display text-xl font-bold">{selected?.name || "Plan"}</h2>
        {selected?.tagline ? <p className="muted text-sm">{selected.tagline}</p> : null}
        <p className="font-display text-3xl font-bold text-[var(--iid-blue)]">
          {selected?.price_label || formatInr(selected?.amount_paise)}
          <span className="text-base font-normal text-[var(--iid-muted)]"> / month</span>
        </p>
        {userEmail ? <p className="text-sm muted">Account: {userEmail}</p> : null}
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="iid-btn iid-btn-primary"
            disabled={loading || gatewayReady === false || !selected}
            onClick={payNow}
          >
            {loading ? "Redirecting to Freecharge…" : "Pay with Freecharge"}
          </button>
          <Link href="/pricing" className="iid-btn iid-btn-ghost">
            Change plan
          </Link>
        </div>
        <p className="text-xs muted">
          You will be redirected to Freecharge to complete payment. Your plan upgrades automatically after successful payment.
        </p>
      </section>

      <form ref={formRef} className="hidden" aria-hidden />
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
