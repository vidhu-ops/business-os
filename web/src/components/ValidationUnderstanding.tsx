"use client";

const REFERENCE_APP_URL = "https://crushing-learning.vercel.app";

export function ValidationUnderstanding() {
  return (
    <section className="iid-card space-y-4">
      <div>
        <h2 className="font-display text-xl font-bold">Reference</h2>
        <p className="text-sm muted mt-2">
          Plan It Out, Business Plan, and related tools from the Business Intelligence Hub.
        </p>
      </div>

      <div className="rounded-xl border border-[var(--iid-line)] overflow-hidden bg-black/20">
        <iframe
          title="Business Intelligence Hub"
          src={REFERENCE_APP_URL}
          className="w-full min-h-[80vh] border-0 bg-white"
          allow="clipboard-read; clipboard-write; fullscreen"
          referrerPolicy="strict-origin-when-cross-origin"
        />
      </div>
    </section>
  );
}
