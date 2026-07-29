"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api";

const steps = [
  { n: 1, title: "Define idea", detail: "Topic, country, industry", href: "/app/projects" },
  { n: 2, title: "Market research", detail: "Evidence-backed report", href: "/app/research" },
  { n: 3, title: "Business plan", detail: "ICP, GTM, financials", href: "/app/plan" },
  { n: 4, title: "Employee OS", detail: "Run specialist tasks", href: "/app/team" },
  { n: 5, title: "Automation", detail: "Multi-step workflows", href: "/app/automation" },
  { n: 6, title: "Saved deliverables", detail: "Exports and files", href: "/app/saved" },
];

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.projects().then((data) => setProjects(data.projects)).catch(() => setProjects([]));
  }, []);

  const active = projects[0];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">Welcome back</h1>
          <p className="mt-2 muted">Your command center — research, plan, and execute from one IIDA workspace.</p>
        </div>
        <Link href="/app/projects" className="iid-btn iid-btn-primary">New project</Link>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="iid-card"><p className="label">Projects</p><p className="value">{projects.length}</p></div>
        <div className="iid-card"><p className="label">Active idea</p><p className="value">{active?.idea?.slice(0, 32) || "None yet"}</p></div>
        <div className="iid-card"><p className="label">Industry</p><p className="value">{active?.industry?.slice(0, 24) || "-"}</p></div>
        <div className="iid-card"><p className="label">Market</p><p className="value">{active?.country?.slice(0, 24) || "-"}</p></div>
      </div>

      <section className="iid-card">
        <h2 className="font-display text-xl font-bold">IIDA workspace modes</h2>
        <p className="mt-2 text-sm muted">Pick where you want to work — research, planning, team execution, or automation.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <Link href="/app/research" className="rounded-xl border border-[var(--iid-line)] p-4 transition hover:border-[var(--iid-blue)]">
            <p className="font-semibold">Understand your market</p>
            <p className="mt-1 text-xs muted">IIDATECH market research — 3/8/16/25 sections</p>
          </Link>
          <Link href="/app/team" className="rounded-xl border border-[var(--iid-line)] p-4 transition hover:border-[var(--iid-blue)]">
            <p className="font-semibold">Team & Execution</p>
            <p className="mt-1 text-xs muted">Office, tasks, agents, war room, integrations</p>
          </Link>
          <Link href="/app/plan" className="rounded-xl border border-[var(--iid-line)] p-4 transition hover:border-[var(--iid-blue)]">
            <p className="font-semibold">Business Plan</p>
            <p className="mt-1 text-xs muted">New company or existing company (GAUGE)</p>
          </Link>
          <Link href="/app/automation" className="rounded-xl border border-[var(--iid-line)] p-4 transition hover:border-[var(--iid-blue)]">
            <p className="font-semibold">Automations</p>
            <p className="mt-1 text-xs muted">Pick steps, build queue, run with agent team</p>
          </Link>
        </div>
      </section>

      <section className="iid-card">
        <h2 className="font-display text-xl font-bold">Quick actions</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/app/research" className="iid-btn iid-btn-primary">Market research</Link>
          <Link href="/app/plan" className="iid-btn iid-btn-ghost">Business plan</Link>
          <Link href="/app/team" className="iid-btn iid-btn-ghost">Employee OS</Link>
          <Link href="/app/automation" className="iid-btn iid-btn-ghost">Automation</Link>
          <Link href="/app/projects" className="iid-btn iid-btn-ghost">Manage projects</Link>
        </div>
      </section>

      {projects.length > 0 && (
        <section className="iid-card">
          <h2 className="font-display text-xl font-bold">Recent projects</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="muted">
                <tr><th className="pb-2">Idea</th><th className="pb-2">Market</th><th className="pb-2">Report</th><th className="pb-2" /></tr>
              </thead>
              <tbody>
                {projects.slice(0, 5).map((p) => (
                  <tr key={p.workspace_id} className="border-t border-[var(--iid-line)]">
                    <td className="py-2 pr-4">{p.idea}</td>
                    <td className="py-2 pr-4">{p.country}</td>
                    <td className="py-2 pr-4">{p.has_report ? "Ready" : "Pending"}</td>
                    <td className="py-2 text-right">
                      <Link href={`/app/research?project=${p.workspace_id}`} className="text-[var(--iid-blue)] hover:underline">Open</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="iid-card">
        <h2 className="font-display text-xl font-bold">Workspace workflow</h2>
        <div className="mt-4 space-y-2">
          {steps.map((step) => (
            <Link key={step.title} href={step.href} className="flex items-center justify-between rounded-xl border border-[var(--iid-line)] px-4 py-3 transition hover:border-[var(--iid-blue)]">
              <div>
                <p className="font-semibold">{step.n}. {step.title}</p>
                <p className="text-sm muted">{step.detail}</p>
              </div>
              <span className="text-xs text-[var(--iid-blue)]">Open</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
