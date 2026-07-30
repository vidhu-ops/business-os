"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type DashboardData } from "@/lib/api";

function formatDate(value?: string) {
  if (!value) return "Recently joined";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "U";
}

const quickLinksBase = [
  { href: "/app/audit", label: "Free company audit" },
  { href: "/", label: "Homepage" },
  { href: "/partners", label: "Service providers" },
  { href: "/app/research", label: "Market research" },
  { href: "/app/plan", label: "Business plan" },
  { href: "/app/team", label: "Employee OS" },
  { href: "/app/automation", label: "Automation" },
];

const demoQuickLinks = [
  { href: "/app/research?project=demo_readonly", label: "Sample research" },
  { href: "/app/plan?project=demo_readonly", label: "Sample business plan" },
  { href: "/app/audit?project=demo_readonly", label: "Sample GAUGE audit" },
  { href: "/app/automation?project=demo_readonly", label: "Sample automation" },
  { href: "/login?mode=register", label: "Sign up free" },
];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="muted">Loading your dashboard…</p>;
  }

  if (error || !data) {
    return (
      <div className="iid-card space-y-3">
        <p className="text-sm text-red-400">{error || "Dashboard unavailable"}</p>
        <button type="button" className="iid-btn iid-btn-primary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  const { user, plan, stats, projects, recent_files, recent_activity, audit, is_demo: isDemo } = data;
  const creditsLabel = plan.is_unlimited
    ? "Unlimited"
    : `${stats.credits_remaining ?? 0} / ${plan.credits_total ?? 30}`;
  const auditLabel = audit?.free_audit_available ? "Available" : "Used";

  return (
    <div className="dash-page space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">Welcome back, {user.name.split(" ")[0]}</h1>
          <p className="mt-2 muted">Your command center — profile, plan, projects, and recent work in one place.</p>
        </div>
        {!isDemo && (
        <Link href="/app/projects" className="iid-btn iid-btn-primary">
          New project
        </Link>
        )}
        {isDemo ? (
          <Link href="/app/research?project=demo_readonly" className="iid-btn iid-btn-primary">
            View sample report
          </Link>
        ) : (
        <Link href="/app/audit" className="iid-btn iid-btn-ghost">
          Run free audit
        </Link>
        )}
      </div>

      <div className="dash-grid-top">
        <section className="iid-card dash-profile">
          <div className="dash-profile-head">
            <div className="dash-avatar" aria-hidden>
              {initials(user.name)}
            </div>
            <div>
              <p className="label">Your profile</p>
              <h2 className="font-display text-xl font-bold">{user.name}</h2>
              <p className="text-sm muted">{user.email}</p>
            </div>
          </div>
          <dl className="dash-profile-meta">
            <div>
              <dt>Member since</dt>
              <dd>{formatDate(user.member_since)}</dd>
            </div>
            <div>
              <dt>Active projects</dt>
              <dd>{stats.projects}</dd>
            </div>
          </dl>
          <Link href="/app/profile" className="text-sm text-[var(--iid-blue)] hover:underline">
            Edit profile →
          </Link>
        </section>

        <section className="iid-card dash-plan">
          <div className="dash-plan-head">
            <div>
              <p className="label">Current plan</p>
              <h2 className="font-display text-xl font-bold">{plan.name}</h2>
              <p className="text-sm muted">{plan.tagline}</p>
            </div>
            <div className="dash-plan-price">
              <strong>{plan.price_label}</strong>
              {plan.period ? <span>{plan.period}</span> : null}
            </div>
          </div>
          <div className="dash-plan-credits">
            <span>Credits</span>
            <strong>{creditsLabel}</strong>
          </div>
          <div className="dash-plan-credits">
            <span>Free company audit</span>
            <strong>{auditLabel}</strong>
          </div>
          {plan.id === "starter" ? (
            <Link href="/pricing" className="iid-btn iid-btn-primary w-full sm:w-auto">
              Upgrade to Growth
            </Link>
          ) : (
            <Link href="/pricing" className="iid-btn iid-btn-ghost w-full sm:w-auto">
              View pricing
            </Link>
          )}
        </section>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="iid-card dash-stat">
          <p className="label">Projects</p>
          <p className="value">{stats.projects}</p>
        </div>
        <div className="iid-card dash-stat">
          <p className="label">Reports ready</p>
          <p className="value">{stats.reports_ready}</p>
        </div>
        <div className="iid-card dash-stat">
          <p className="label">Plans ready</p>
          <p className="value">{stats.plans_ready}</p>
        </div>
        <div className="iid-card dash-stat">
          <p className="label">Saved files</p>
          <p className="value">{stats.saved_files}</p>
        </div>
      </div>

      <div className="dash-grid-main">
        <section className="iid-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display text-xl font-bold">Your projects</h2>
            <Link href="/app/projects" className="text-sm text-[var(--iid-blue)] hover:underline">
              View all
            </Link>
          </div>
          {projects.length === 0 ? (
            <p className="mt-4 muted">No projects yet. Create one to start research and planning.</p>
          ) : (
            <div className="mt-4 space-y-3">
              {projects.map((project) => (
                <article key={project.workspace_id} className="dash-project-row">
                  <div>
                    <p className="font-semibold">{project.idea || "Untitled project"}</p>
                    <p className="text-sm muted">
                      {project.industry || "Industry"} · {project.country || "Market"}
                    </p>
                  </div>
                  <div className="dash-project-badges">
                    <span className={project.has_report ? "is-on" : ""}>Report</span>
                    <span className={project.has_plan ? "is-on" : ""}>Plan</span>
                  </div>
                  <Link href={`/app/research?project=${project.workspace_id}`} className="dash-project-link">
                    Open
                  </Link>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="iid-card">
          <h2 className="font-display text-xl font-bold">Recent activity</h2>
          {recent_activity.length === 0 ? (
            <p className="mt-4 muted">Activity from research, plans, and saved files will show up here.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {recent_activity.map((item, index) => (
                <li key={`${item.title}-${index}`} className="dash-activity-item">
                  <div>
                    <p className="font-semibold">{item.title}</p>
                    <p className="text-sm muted">{item.detail}</p>
                  </div>
                  <span className="text-xs muted">{formatDate(item.at)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="iid-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-xl font-bold">Previous deliverables</h2>
          <Link href="/app/saved" className="text-sm text-[var(--iid-blue)] hover:underline">
            All saved files
          </Link>
        </div>
        {recent_files.length === 0 ? (
          <p className="mt-4 muted">Exports and reports you generate will appear here.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="muted">
                <tr>
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Type</th>
                  <th className="pb-2">Modified</th>
                </tr>
              </thead>
              <tbody>
                {recent_files.map((file) => (
                  <tr key={String(file.path)} className="border-t border-[var(--iid-line)]">
                    <td className="py-2 pr-4">{file.name}</td>
                    <td className="py-2 pr-4 uppercase">{file.type}</td>
                    <td className="py-2">{file.modified}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="iid-card">
        <h2 className="font-display text-xl font-bold">Quick actions</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          {(isDemo ? demoQuickLinks : quickLinksBase).map((link) => (
            <Link key={link.href} href={link.href} className="iid-btn iid-btn-ghost">
              {link.label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
