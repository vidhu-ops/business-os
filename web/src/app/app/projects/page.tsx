"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, Project } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [idea, setIdea] = useState("");
  const [industry, setIndustry] = useState("");
  const [country, setCountry] = useState("Global");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const data = await api.projects();
    setProjects(data.projects);
  }

  useEffect(() => {
    refresh().catch(() => setProjects([]));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.createProject(idea, industry, country);
      setIdea("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create project");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold">Projects</h1>
        <p className="mt-2 text-[var(--iid-muted)]">Create and open founder workspaces.</p>
      </div>

      <form className="iid-card space-y-3" onSubmit={onCreate}>
        <h2 className="font-display text-xl font-bold">Create project</h2>
        <textarea className="iid-input min-h-28" placeholder="Project idea / topic" value={idea} onChange={(e) => setIdea(e.target.value)} required />
        <div className="grid gap-3 md:grid-cols-2">
          <input className="iid-input" placeholder="Industry" value={industry} onChange={(e) => setIndustry(e.target.value)} required />
          <input className="iid-input" placeholder="Country / market" value={country} onChange={(e) => setCountry(e.target.value)} required />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="iid-btn iid-btn-primary" type="submit" disabled={loading}>{loading ? "Creating..." : "Create project"}</button>
      </form>

      <section className="iid-card">
        <h2 className="font-display text-xl font-bold">Saved projects</h2>
        {projects.length === 0 ? (
          <p className="mt-3 text-sm text-[var(--iid-muted)]">No saved projects yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[var(--iid-muted)]"><tr><th className="pb-2">Idea</th><th className="pb-2">Market</th><th className="pb-2">Industry</th><th className="pb-2">Report</th></tr></thead>
              <tbody>
                {projects.map((p) => (
                  <tr key={p.workspace_id} className="border-t border-[var(--iid-line)]">
                    <td className="py-2 pr-4">{p.idea}</td>
                    <td className="py-2 pr-4">{p.country}</td>
                    <td className="py-2 pr-4">{p.industry}</td>
                    <td className="py-2">{p.has_report ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
