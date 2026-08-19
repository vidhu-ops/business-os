"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Project } from "@/lib/api";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isDemo, setIsDemo] = useState(false);
  const [idea, setIdea] = useState("");
  const [industry, setIndustry] = useState("");
  const [country, setCountry] = useState("Global");
  const [areas, setAreas] = useState("");
  const [mode, setMode] = useState<"new" | "existing">("new");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const data = await api.projects();
    setProjects(data.projects);
  }

  useEffect(() => {
    api.me().then((u) => setIsDemo(Boolean(u.is_demo))).catch(() => setIsDemo(false));
    refresh().catch(() => setProjects([]));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.createProject(idea, industry, country, areas, mode);
      const wid = res.project?.workspace_id;
      setIdea("");
      setAreas("");
      await refresh();
      if (wid) {
        router.push(`/app/onboarding?project=${encodeURIComponent(wid)}`);
        return;
      }
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
        <p className="mt-2 text-[var(--iid-muted)]">
          {isDemo
            ? "Demo shows one sample project only. Sign up to create your own."
            : "Create a project, capture organizational memory, then let Mentor guide research → plan → agents."}
        </p>
      </div>

      {!isDemo && (
        <form className="iid-card space-y-3" onSubmit={onCreate}>
          <h2 className="font-display text-xl font-bold">Create project</h2>
          <div className="flex flex-wrap gap-2">
            <button type="button" className={`iid-btn ${mode === "new" ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setMode("new")}>
              New business
            </button>
            <button type="button" className={`iid-btn ${mode === "existing" ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setMode("existing")}>
              Existing business
            </button>
          </div>
          <p className="text-xs muted">
            {mode === "existing"
              ? "You will fill organizational memory, then GAUGE — used for research, plan, and agent staffing."
              : "You will answer sell / buyers / goals and connect Drive, Gmail, CRM, etc. as persistent org memory."}
          </p>
          <textarea className="iid-input min-h-28" placeholder="Project idea / topic" value={idea} onChange={(e) => setIdea(e.target.value)} required />
          <div className="grid gap-3 md:grid-cols-2">
            <input className="iid-input" placeholder="Industry" value={industry} onChange={(e) => setIndustry(e.target.value)} required />
            <input className="iid-input" placeholder="Country / market" value={country} onChange={(e) => setCountry(e.target.value)} required />
          </div>
          <input className="iid-input" placeholder="Cities / metro areas (optional)" value={areas} onChange={(e) => setAreas(e.target.value)} />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button className="iid-btn iid-btn-primary" type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create & start onboarding"}
          </button>
        </form>
      )}

      {isDemo && (
        <div className="iid-card text-sm">
          <Link href="/login?mode=register" className="iid-btn iid-btn-primary inline-flex">
            Sign up to create projects
          </Link>
        </div>
      )}

      <section className="iid-card">
        <h2 className="font-display text-xl font-bold">Saved projects</h2>
        {projects.length === 0 ? (
          <p className="mt-3 text-sm text-[var(--iid-muted)]">No saved projects yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-[var(--iid-muted)]">
                <tr>
                  <th className="pb-2">Idea</th>
                  <th className="pb-2">Market</th>
                  <th className="pb-2">Industry</th>
                  <th className="pb-2">Report</th>
                  <th className="pb-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => (
                  <tr key={p.workspace_id} className="border-t border-[var(--iid-line)]">
                    <td className="py-2 pr-4">{p.idea}</td>
                    <td className="py-2 pr-4">{p.country}</td>
                    <td className="py-2 pr-4">{p.industry}</td>
                    <td className="py-2">{p.has_report ? "Yes" : "No"}</td>
                    <td className="py-2 space-x-3">
                      <Link href={`/app/onboarding?project=${p.workspace_id}`} className="text-[var(--iid-blue)] hover:underline">
                        Org memory
                      </Link>
                      <Link href={`/app/mentor?project=${p.workspace_id}`} className="text-[var(--iid-blue)] hover:underline">
                        Mentor
                      </Link>
                      <Link href={`/app/research?project=${p.workspace_id}`} className="text-[var(--iid-blue)] hover:underline">
                        Workspace
                      </Link>
                    </td>
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
