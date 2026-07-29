"use client";

import { useState } from "react";
import { VALIDATION_SECTIONS, type ValidationSectionId } from "@/lib/referenceApp";
import { HubReferencePanel } from "@/components/HubReferencePanel";

export function ValidationUnderstanding() {
  const [section, setSection] = useState<ValidationSectionId>("plan-it-out");
  const active = VALIDATION_SECTIONS.find((s) => s.id === section) ?? VALIDATION_SECTIONS[0];

  return (
    <section className="iid-card space-y-5">
      <div>
        <h2 className="font-display text-xl font-bold">Validation &amp; Understanding</h2>
        <p className="text-sm muted mt-2">
          Plan It Out and Business Plan — same experience as the Business Intelligence Hub, embedded in IIDATECH.
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
      </div>

      <HubReferencePanel mode={section} />
    </section>
  );
}
