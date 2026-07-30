"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, ensureSession } from "@/lib/api";

function CallbackContent() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id") || "";
  const [status, setStatus] = useState<string>("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!orderId) {
      setStatus("missing");
      return;
    }
    ensureSession()
      .then(() => api.getPaymentOrder(orderId))
      .then((data) => setStatus(String(data.order?.status || "pending")))
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not verify payment");
        setStatus("error");
      });
  }, [orderId]);

  if (status === "loading") {
    return <p className="muted">Confirming your payment…</p>;
  }

  if (status === "paid") {
    return (
      <div className="iid-card space-y-4 max-w-lg">
        <p className="font-display text-2xl font-bold text-emerald-400">Payment successful</p>
        <p className="muted">Your Growth plan is active. Employee OS and unlimited research are unlocked.</p>
        <Link href="/app/dashboard" className="iid-btn iid-btn-primary inline-flex">
          Go to dashboard
        </Link>
      </div>
    );
  }

  if (status === "pending" || status === "created") {
    return (
      <div className="iid-card space-y-4 max-w-lg">
        <p className="font-display text-xl font-bold">Payment processing</p>
        <p className="muted">
          We are waiting for confirmation from Freecharge. Refresh in a minute or check your dashboard.
        </p>
        <Link href="/app/dashboard" className="iid-btn iid-btn-primary inline-flex">
          Open dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="iid-card space-y-4 max-w-lg">
      <p className="font-display text-xl font-bold text-red-400">Payment not completed</p>
      <p className="muted">{error || "The transaction failed or was cancelled. You can try again from pricing."}</p>
      <Link href="/checkout?plan=growth" className="iid-btn iid-btn-primary inline-flex">
        Try again
      </Link>
    </div>
  );
}

export function PaymentCallbackPage() {
  return (
    <Suspense fallback={<p className="muted">Loading…</p>}>
      <CallbackContent />
    </Suspense>
  );
}
