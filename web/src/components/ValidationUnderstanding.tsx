"use client";

import { useState } from "react";
import {
  REFERENCE_REPLIT_APP_URL,
  VALIDATION_SECTIONS,
  type ValidationSectionId,
} from "@/lib/referenceApp";

export function ValidationUnderstanding() {
  const [section, setSection] = useState<ValidationSectionId>("plan-it-out");
  const active = VALIDATION_SECTIONS.find((s) => s.id === section) ?? VALIDATION_SECTIONS[0];

  return (
    <section className="iid-card space-y-4">
      <div>
        <h2 className="font-display text-xl font-bold">Validation &amp; Understanding</h2>
        <p className="text-sm muted mt-2">
          Cross-check your IIDATECH plan with the Business Intelligence Hub. Use the same idea here and in{" "}
          <strong>Plan Output</strong> to compare results.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {VALIDATION_SECTIONS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`iid-btn text-left ${section === item.id ? "iid-btn-primary" : "iid-btn-ghost"}`}
            onClick={() => setSection(item.id)}
          >
            <span className="block font-semibold">{item.label}</span>
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-[var(--iid-line)] bg-black/20 p-4 space-y-2">
        <p className="text-sm font-semibold">{active.label}</p>
        <p className="text-sm muted">{active.description}</p>
        <p className="text-sm text-[var(--iid-blue)]">
          In the embedded app below, choose <strong>{active.hubButton}</strong> from the hub menu.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--iid-line)] bg-black">
        <iframe
          key={section}
          title={`IIDATECH validation - ${active.label}`}
          src={REFERENCE_REPLIT_APP_URL}
          className="w-full border-0"
          style={{ height: "720px" }}
          loading="lazy"
          allow="clipboard-write"
        />
      </div>
    </section>
  );
}