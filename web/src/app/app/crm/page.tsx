"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, type AdminCrmUser, type CrmLead } from "@/lib/api";

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
  const [grantAmount, setGrantAmount] = useState("1000000");
  const [granting, setGranting] = useState(false);
  const [tab, setTab] = useState<"accounts" | "leads">("accounts");
  const [leads, setLeads] = useState<CrmLead[]>([]);
  const [leadTotals, setLeadTotals] = useState({ leads: 0, visitors: 0, demo: 0, signed_up: 0, imported: 0 });
  const [leadQuery, setLeadQuery] = useState("");
  const [leadStatus, setLeadStatus] = useState("");
  const [selectedLead, setSelectedLead] = useState("");
  const [importing, setImporting] = useState(false);
  const [importNote, setImportNote] = useState("");
  const fileRef = useRef<HTMLInputElement | null>(null);

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

  async function refreshLeads(q = leadQuery, status = leadStatus) {
    try {
      const data = await api.adminLeads(q.trim(), status);
      setLeads(data.leads || []);
      setLeadTotals(data.totals || { leads: 0, visitors: 0, demo: 0, signed_up: 0, imported: 0 });
      if (!selectedLead && data.leads?.[0]?.lead_id) setSelectedLead(data.leads[0].lead_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load leads");
      setLeads([]);
    }
  }

  useEffect(() => {
    refresh("").catch(() => undefined);
    refreshLeads("", "").catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const active = useMemo(() => users.find((u) => u.email === selected) || users[0] || null, [users, selected]);
  const activeLead = useMemo(() => leads.find((l) => l.lead_id === selectedLead) || leads[0] || null, [leads, selectedLead]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    refresh(query).catch(() => undefined);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">CRM</h1>
          <p className="mt-2 muted">
            Registered users stay on Accounts. Website visitors, demo journeys, and sheet imports are on Leads.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" className={`iid-btn ${tab === "accounts" ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setTab("accounts")}>
              Accounts ({totals.users})
            </button>
            <button type="button" className={`iid-btn ${tab === "leads" ? "iid-btn-primary" : "iid-btn-ghost"}`} onClick={() => setTab("leads")}>
              Leads ({leadTotals.leads})
            </button>
            <Link href="/app/analytics" className="iid-btn iid-btn-ghost">
              Analytics
            </Link>
          </div>
        </div>
        {tab === "accounts" ? (
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
        ) : (
        <form
          className="flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            refreshLeads(leadQuery, leadStatus).catch(() => undefined);
          }}
        >
          <input
            className="iid-input min-w-[14rem]"
            placeholder="Search leads"
            value={leadQuery}
            onChange={(e) => setLeadQuery(e.target.value)}
          />
          <select className="iid-input" value={leadStatus} onChange={(e) => setLeadStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="visitor">Website visitors</option>
            <option value="demo">Saw demo</option>
            <option value="signed_up">Signed up</option>
            <option value="imported">Imported</option>
          </select>
          <button type="submit" className="iid-btn iid-btn-primary">Search</button>
        </form>
        )}
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

      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <button type="button" className="iid-card text-left" onClick={() => setTab("accounts")}>
          <p className="text-xs uppercase tracking-wide muted">Accounts</p>
          <p className="mt-1 font-display text-2xl font-bold">{totals.users}</p>
        </button>
        <button type="button" className="iid-card text-left" onClick={() => setTab("leads")}>
          <p className="text-xs uppercase tracking-wide muted">Leads</p>
          <p className="mt-1 font-display text-2xl font-bold">{leadTotals.leads}</p>
        </button>
        <div className="iid-card">
          <p className="text-xs uppercase tracking-wide muted">Saw demo</p>
          <p className="mt-1 font-display text-2xl font-bold">{leadTotals.demo}</p>
        </div>
        <div className="iid-card">
          <p className="text-xs uppercase tracking-wide muted">Signed up</p>
          <p className="mt-1 font-display text-2xl font-bold">{leadTotals.signed_up}</p>
        </div>
        <div className="iid-card">
          <p className="text-xs uppercase tracking-wide muted">Imported</p>
          <p className="mt-1 font-display text-2xl font-bold">{leadTotals.imported}</p>
        </div>
      </div>

      {tab === "leads" ? (
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="iid-card overflow-x-auto">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display text-xl font-bold">Leads</h2>
            <div>
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.tsv,.txt,.xlsx,.xls"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  e.target.value = "";
                  if (!file) return;
                  setImporting(true);
                  setImportNote("");
                  setError("");
                  try {
                    const result = await api.adminImportLeads(file);
                    setImportNote(`Imported ${file.name}: ${result.created} new, ${result.updated} updated, ${result.skipped} skipped.`);
                    await refreshLeads(leadQuery, leadStatus);
                    setTab("leads");
                  } catch (err) {
                    setError(err instanceof Error ? err.message : "Could not import sheet");
                  } finally {
                    setImporting(false);
                  }
                }}
              />
              <button
                type="button"
                className="iid-btn iid-btn-primary"
                disabled={importing}
                onClick={() => fileRef.current?.click()}
              >
                {importing ? "Uploading…" : "Upload sheet"}
              </button>
            </div>
          </div>
          <p className="mt-2 text-xs muted">
            CSV or Excel with headers such as email, name, phone, company, source, city, country, notes.
          </p>
          {importNote ? <p className="mt-2 text-sm text-[var(--iid-blue)]">{importNote}</p> : null}
          {leads.length === 0 ? (
            <p className="mt-3 muted">
              No website leads yet. Registered users are on the Accounts tab
              {totals.users ? ` (${totals.users} already signed up)` : ""}. New visitors are added here as they browse,
              or upload a sheet.
            </p>
          ) : (
            <table className="mt-4 w-full min-w-[720px] text-left text-sm">
              <thead className="text-[var(--iid-muted)]">
                <tr>
                  <th className="pb-2 pr-3">Lead</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3">Source</th>
                  <th className="pb-2 pr-3">Last page</th>
                  <th className="pb-2">Journey</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr
                    key={lead.lead_id}
                    className={`cursor-pointer border-t border-[var(--iid-line)] ${selectedLead === lead.lead_id ? "bg-[var(--iid-panel-2)]" : ""}`}
                    onClick={() => setSelectedLead(lead.lead_id)}
                  >
                    <td className="py-2.5 pr-3">
                      <div className="font-semibold">{lead.name}</div>
                      <div className="text-xs muted">{lead.email || lead.place || lead.lead_id.slice(0, 10)}</div>
                    </td>
                    <td className="py-2.5 pr-3">{lead.status}{lead.saw_demo ? " · demo" : ""}</td>
                    <td className="py-2.5 pr-3">{lead.source || "—"}</td>
                    <td className="py-2.5 pr-3">{lead.last_path || "—"}</td>
                    <td className="py-2.5">{lead.page_count || (lead.journey || []).length} pages</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
        <aside className="iid-card space-y-4">
          <h2 className="font-display text-xl font-bold">Lead journey</h2>
          {!activeLead ? (
            <p className="muted">Select a lead.</p>
          ) : (
            <>
              <div>
                <p className="font-semibold text-lg">{activeLead.name}</p>
                <p className="text-sm muted">{activeLead.email || "Anonymous visitor"}</p>
              </div>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="muted text-xs">Status</dt>
                  <dd>{activeLead.status}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Place</dt>
                  <dd>{activeLead.place || activeLead.city || "—"}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Source</dt>
                  <dd>{[activeLead.source, activeLead.utm_campaign].filter(Boolean).join(" · ") || "direct"}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Company</dt>
                  <dd>{activeLead.company || "—"}</dd>
                </div>
              </dl>
              {activeLead.demo_parts && activeLead.demo_parts.length ? (
                <div>
                  <h3 className="text-sm font-semibold">Demo parts</h3>
                  <p className="mt-1 text-sm">{activeLead.demo_parts.join(" → ")}</p>
                </div>
              ) : null}
              <div>
                <h3 className="text-sm font-semibold">Pages visited</h3>
                {(activeLead.journey || []).length ? (
                  <ol className="mt-2 space-y-1 text-sm">
                    {activeLead.journey!.map((step, idx) => (
                      <li key={`${step}-${idx}`} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                        {idx + 1}. {step}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="mt-2 text-sm muted">No browsing journey stored yet.</p>
                )}
              </div>
              {activeLead.notes ? <p className="text-sm">{activeLead.notes}</p> : null}
            </>
          )}
        </aside>
      </div>
      ) : null}

      {tab === "accounts" ? (
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="iid-card overflow-x-auto">
          <h2 className="font-display text-xl font-bold">Accounts</h2>
          <p className="mt-1 text-xs muted">Everyone who already signed up — plans, credits, and projects. These are not deleted when Leads is empty.</p>
          {loading && users.length === 0 ? (
            <p className="mt-3 muted">Loading users…</p>
          ) : users.length === 0 ? (
            <p className="mt-3 muted">No registered accounts found in the user store.</p>
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
              {active.signup_attribution ? (
                <div className="rounded-lg border border-[var(--iid-line)] px-3 py-2 text-sm">
                  <p className="text-xs muted">Signup source</p>
                  <p>
                    {active.signup_attribution.source || "direct"}
                    {active.signup_attribution.referrer_host ? ` · ${active.signup_attribution.referrer_host}` : ""}
                  </p>
                  <p className="text-xs muted">
                    {[active.signup_attribution.place, active.signup_attribution.landing_path, active.signup_attribution.device]
                      .filter(Boolean)
                      .join(" · ") || "No extra attribution"}
                  </p>
                </div>
              ) : null}
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
                <div className="space-y-2">
                  <label className="block text-xs muted" htmlFor="crm-grant-amount">
                    Grant credits
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <input
                      id="crm-grant-amount"
                      className="iid-input min-w-0 flex-1"
                      type="number"
                      min={1}
                      max={10_000_000}
                      value={grantAmount}
                      onChange={(e) => setGrantAmount(e.target.value)}
                    />
                    <button
                      type="button"
                      className="iid-btn iid-btn-primary"
                      disabled={loading || granting}
                      onClick={async () => {
                        const amount = Math.max(1, Math.min(10_000_000, Number(grantAmount) || 0));
                        if (!amount) {
                          setError("Enter a valid credit amount");
                          return;
                        }
                        try {
                          setGranting(true);
                          setError("");
                          await api.adminGrantCredits(active.email, amount);
                          await refresh(query);
                        } catch (err) {
                          setError(err instanceof Error ? err.message : "Could not grant credits");
                        } finally {
                          setGranting(false);
                        }
                      }}
                    >
                      {granting ? "Granting…" : `Grant +${Number(grantAmount || 0).toLocaleString()}`}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {[100, 1000, 10000, 1_000_000].map((n) => (
                      <button
                        key={n}
                        type="button"
                        className="iid-btn iid-btn-ghost text-xs"
                        onClick={() => setGrantAmount(String(n))}
                      >
                        {n.toLocaleString()}
                      </button>
                    ))}
                  </div>
                </div>
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
                    {active.recent_actions!.map((row, i) => {
                      const amount = typeof row.amount === "number" ? row.amount : 0;
                      const spend = row.direction === "spend" || amount > 0;
                      const label = spend ? `−${Math.abs(amount)}` : `+${Math.abs(amount)}`;
                      return (
                      <li key={`${row.at}-${i}`} className="flex justify-between gap-3 border-b border-[var(--iid-line)] py-1.5">
                        <span>{row.action || "action"}</span>
                        <span className="muted whitespace-nowrap">
                          {label} · {formatDate(row.at)}
                        </span>
                      </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm muted">No credit ledger entries yet.</p>
                )}
              </div>
            </>
          )}
        </aside>
      </div>
      ) : null}
    </div>
  );
}
