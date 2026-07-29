"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Section = { kind: string; title?: string; body?: string; rows?: Array<Record<string, string>> };

function MarkdownBody({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="prose prose-invert prose-sm max-w-none space-y-2">
      {lines.map((line, i) => {
        if (line.startsWith("### ")) return <h4 key={i} className="font-semibold mt-3">{line.slice(4)}</h4>;
        if (line.startsWith("## ")) return <h3 key={i} className="font-bold mt-3">{line.slice(3)}</h3>;
        if (line.startsWith("# ")) return <h2 key={i} className="font-display font-bold mt-3">{line.slice(2)}</h2>;
        if (line.startsWith("- ")) return <p key={i} className="ml-3 text-sm">• {line.slice(2)}</p>;
        if (line.startsWith("**") && line.endsWith("**")) return <p key={i} className="font-semibold text-sm">{line.slice(2, -2)}</p>;
        if (!line.trim()) return <br key={i} />;
        return <p key={i} className="text-sm whitespace-pre-wrap">{line}</p>;
      })}
    </div>
  );
}

type Props = {
  title: string;
  reply?: string;
  artifacts?: string[];
};

export function DeliverablePreview({ title, reply = "", artifacts = [] }: Props) {
  const [doc, setDoc] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!title && !reply && artifacts.length === 0) return;
    setLoading(true);
    api.previewDeliverable({ title, reply, artifacts })
      .then(setDoc)
      .catch(() => setDoc(null))
      .finally(() => setLoading(false));
  }, [title, reply, artifacts.join("|")]);

  const sections = (doc?.sections as Section[]) || [];
  if (loading) return <p className="text-xs muted">Loading preview…</p>;
  if (!sections.length && !reply) return null;

  return (
    <div className="rounded-lg border border-[var(--iid-line)] bg-[var(--iid-panel)] p-3 space-y-3 mt-2">
      <div className="flex flex-wrap gap-2 items-center justify-between">
        <p className="text-sm font-semibold">{String(doc?.title || title)}</p>
        <div className="flex gap-2">
          <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => api.exportDeliverable({ title, reply, artifacts }, "pdf").catch(() => {})}>PDF</button>
          <button type="button" className="iid-btn iid-btn-ghost text-xs" onClick={() => api.exportDeliverable({ title, reply, artifacts }, "docx").catch(() => {})}>Word</button>
        </div>
      </div>
      {reply && <MarkdownBody text={reply} />}
      {sections.map((sec, i) => (
        <div key={i}>
          {sec.title && <p className="text-xs font-semibold uppercase muted mb-1">{sec.title}</p>}
          {sec.kind === "markdown" || sec.kind === "text" ? <MarkdownBody text={String(sec.body || "")} /> : null}
          {sec.kind === "table" && sec.rows && (
            <div className="overflow-x-auto">
              <table className="text-xs w-full border-collapse">
                <tbody>
                  {sec.rows.slice(0, 12).map((row, ri) => (
                    <tr key={ri} className="border-t border-[var(--iid-line)]">
                      {Object.values(row).map((v, ci) => (
                        <td key={ci} className="px-2 py-1">{v}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
