"use client";

import { Project } from "@/lib/api";

export function ProjectPicker({
  projects,
  selectedId,
  onChange,
}: {
  projects: Project[];
  selectedId: string;
  onChange: (id: string) => void;
}) {
  if (projects.length === 0) return null;
  return (
    <div>
      <label className="block text-sm muted">Active project</label>
      <select className="iid-input mt-1" value={selectedId} onChange={(e) => onChange(e.target.value)}>
        {projects.map((p) => (
          <option key={p.workspace_id} value={p.workspace_id}>
            {p.idea} | {p.country} | {p.industry}
          </option>
        ))}
      </select>
    </div>
  );
}