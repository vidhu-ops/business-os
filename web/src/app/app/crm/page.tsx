"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, type AdminCrmUser } from "@/lib/api";

function formatDate(value?: string) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 10) || "—";
  return parsed.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function creditsLabel(user: AdminCrmUser) {
  if (user.is_unlimited) return "Unlimited";
  const rem = user.credits_remaining;
  const total = user.credits_total;
  if (typeof rem === "number" && typeof total === "number") return `${rem} / ${total}`;
  if (typeof rem === "number") return String(rem);
  return "—";
}

export default function CrmPage() {
  const [users, setUsers] = useState<AdminCrmUser[]>([]);
  const [totals, setTotals] = useState({ users: 0, projects: 0, credits_remaining: 0 });
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string>("");

  async function refresh(q = query) {
    setLoading(true);
    setError("");
    try {
      const data = await api.adminUsers(q.trim());
      setUsers(data.users || []);
      setTotals(data.totals || { users: 0, projects: 0, credits_remaining: 0 });
      if (!selected && data.users?.[0]?.email) setSelected(data.users[0].email);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load CRM");
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh("").catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const active = useMemo(() => users.find((u) => u.email === selected) || users[0] || null, [users, selected]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    refresh(query).catch(() => undefined);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">CRM</h1>
          <p className="mt-2 muted">Admin view of every account — usage, credits, and join dates.</p>
        </div>
        <form className="flex flex-wrap gap-2" onSubmit={onSearch}>
          <input
            className="iid-input min-w-[16rem]"
            placeholder="Search name or email"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="iid-btn iid-btn-primary" disabled={loading}>
            {loading ? "Loading…" : "Search"}
          </button>
        </form>
      </div>

      {error ? (
        <div className="iid-card space-y-3">
          <p className="text-sm text-red-400">{error}</p>
          <p className="text-xs muted">
            CRM is only available when you sign in with the admin email set in ADMIN_EMAIL.
          </p>
          <button type="button" className="iid-btn iid-btn-ghost" onClick={() => refresh()}>
            Retry
          </button>
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="iid-card">
          <p className="text-xs uppercase tracking-wide muted">Users</p>
          <p className="mt-1 font-display text-2xl font-bold">{totals.users}</p>
        </div>
        <div className="iid-card">
          <p className="text-xs uppercase tracking-wide muted">Projects</p>
          <p className="mt-1 font-display text-2xl font-bold">{totals.projects}</p>
        </div>
        <div className="iid-card">
          <p className="text-xs uppercase tracking-wide muted">Credits remaining</p>
          <p className="mt-1 font-display text-2xl font-bold">{totals.credits_remaining}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="iid-card overflow-x-auto">
          <h2 className="font-display text-xl font-bold">Accounts</h2>
          {loading && users.length === 0 ? (
            <p className="mt-3 muted">Loading users…</p>
          ) : users.length === 0 ? (
            <p className="mt-3 muted">No users found.</p>
          ) : (
            <table className="mt-4 w-full min-w-[640px] text-left text-sm">
              <thead className="text-[var(--iid-muted)]">
                <tr>
                  <th className="pb-2 pr-3">User</th>
                  <th className="pb-2 pr-3">Joined</th>
                  <th className="pb-2 pr-3">Plan</th>
                  <th className="pb-2 pr-3">Credits</th>
                  <th className="pb-2 pr-3">Used</th>
                  <th className="pb-2">Projects</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr
                    key={user.email}
                    className={`border-t border-[var(--iid-line)] cursor-pointer ${selected === user.email ? "bg-[var(--iid-panel-2)]" : ""}`}
                    onClick={() => setSelected(user.email)}
                  >
                    <td className="py-2.5 pr-3">
                      <div className="font-semibold">{user.name}</div>
                      <div className="text-xs muted">{user.email}</div>
                    </td>
                    <td className="py-2.5 pr-3">{formatDate(user.joined_at)}</td>
                    <td className="py-2.5 pr-3">{user.plan_name || user.plan_id || "—"}</td>
                    <td className="py-2.5 pr-3">{creditsLabel(user)}</td>
                    <td className="py-2.5 pr-3">
                      {user.is_unlimited ? "—" : typeof user.credits_used === "number" ? user.credits_used : "—"}
                    </td>
                    <td className="py-2.5">
                      {user.projects}
                      <span className="muted text-xs"> · {user.reports_ready} reports · {user.plans_ready} plans</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <aside className="iid-card space-y-4">
          <h2 className="font-display text-xl font-bold">User detail</h2>
          {!active ? (
            <p className="muted">Select a user to inspect activity.</p>
          ) : (
            <>
              <div>
                <p className="font-semibold text-lg">{active.name}</p>
                <p className="text-sm muted">{active.email}</p>
              </div>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="muted text-xs">Joined</dt>
                  <dd>{formatDate(active.joined_at)}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Last activity</dt>
                  <dd>{formatDate(active.last_activity_at)}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Credits</dt>
                  <dd>{creditsLabel(active)}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Free audits</dt>
                  <dd>
                    {active.free_audit_used} / {active.free_audit_granted}
                  </dd>
                </div>
              </dl>
              {!active.is_unlimited ? (
                <button
                  type="button"
                  className="iid-btn iid-btn-primary w-full"
                  disabled={loading}
                  onClick={async () => {
                    try {
                      setError("");
                      await api.adminGrantCredits(active.email, 1_000_000);
                      await refresh(query);
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Could not grant credits");
                    }
                  }}
                >
                  Grant +1,000,000 credits
                </button>
              ) : null}
              <div>
                <h3 className="text-sm font-semibold">Projects</h3>
                {(active.project_ideas || []).length ? (
                  <ul className="mt-2 space-y-1 text-sm">
                    {active.project_ideas!.map((idea) => (
                      <li key={idea} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                        {idea}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm muted">No projects yet.</p>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold">Recent credit actions</h3>
                {(active.recent_actions || []).length ? (
                  <ul className="mt-2 space-y-1 text-sm">
                    {active.recent_actions!.map((row, i) => (
                      <li key={`${row.at}-${i}`} className="flex justify-between gap-3 border-b border-[var(--iid-line)] py-1.5">
                        <span>{row.action || "action"}</span>
                        <span className="muted whitespace-nowrap">
                          {typeof row.amount === "number" ? `${row.amount > 0 ? "+" : ""}${row.amount}` : ""} ·{" "}
                          {formatDate(row.at)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm muted">No credit ledger entries yet.</p>
                )}
              </div>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
