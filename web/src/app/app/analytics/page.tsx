"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  api,
  type AnalyticsOverview,
  type AnalyticsPagePerson,
  type AnalyticsSessionDetail,
  type AnalyticsSessionRow,
} from "@/lib/api";

const RANGES = [
  { days: 1, label: "24h" },
  { days: 7, label: "7d" },
  { days: 30, label: "30d" },
  { days: 90, label: "90d" },
];

function formatDateTime(value?: string) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 16) || "—";
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(ms?: number) {
  const n = Math.max(0, Number(ms) || 0);
  if (n < 1000) return `${n}ms`;
  const sec = Math.round(n / 1000);
  if (sec < 60) return `${sec}s`;
  const min = Math.floor(sec / 60);
  const rem = sec % 60;
  if (min < 60) return rem ? `${min}m ${rem}s` : `${min}m`;
  const hr = Math.floor(min / 60);
  return `${hr}h ${min % 60}m`;
}

function formatDay(value: string) {
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return value.slice(5);
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function placeLabel(row: AnalyticsSessionRow) {
  return row.place || row.city || row.country_name || row.country || "Unknown";
}

function sourceLabel(row: AnalyticsSessionRow) {
  const utm = [row.utm_source, row.utm_medium, row.utm_campaign].filter(Boolean).join(" / ");
  if (utm) return utm;
  if (row.referrer_host) return row.referrer_host;
  return row.source || "direct";
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(7);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [sessions, setSessions] = useState<AnalyticsSessionRow[]>([]);
  const [totalSessions, setTotalSessions] = useState(0);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState<AnalyticsSessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [pagePath, setPagePath] = useState("");
  const [pagePeople, setPagePeople] = useState<AnalyticsPagePerson[]>([]);
  const [pagePeopleMeta, setPagePeopleMeta] = useState({ views: 0, unique_visitors: 0 });

  async function refresh(nextDays = days, q = query) {
    setLoading(true);
    setError("");
    try {
      const [over, list] = await Promise.all([
        api.adminAnalyticsOverview(nextDays),
        api.adminAnalyticsSessions(nextDays, q, 80, 0),
      ]);
      setOverview(over);
      setSessions(list.sessions || []);
      setTotalSessions(list.total || 0);
      const first = list.sessions?.[0]?.session_id || over.recent_sessions?.[0]?.session_id || "";
      if (first && (!selected || !list.sessions.some((row) => row.session_id === selected))) {
        setSelected(first);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load analytics");
      setOverview(null);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh(days, "").catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  useEffect(() => {
    if (!pagePath) {
      setPagePeople([]);
      return;
    }
    let cancelled = false;
    api
      .adminAnalyticsPagePeople(pagePath, days)
      .then((data) => {
        if (cancelled) return;
        setPagePeople(data.people || []);
        setPagePeopleMeta({ views: data.views || 0, unique_visitors: data.unique_visitors || 0 });
      })
      .catch(() => {
        if (!cancelled) setPagePeople([]);
      });
    return () => {
      cancelled = true;
    };
  }, [pagePath, days]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setDetailLoading(true);
    api
      .adminAnalyticsSession(selected)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selected]);

  const totals = overview?.totals;
  const chartData = useMemo(
    () =>
      (overview?.series || []).map((row) => ({
        ...row,
        label: formatDay(row.date),
      })),
    [overview],
  );
  const funnelMax = Math.max(1, overview?.funnel.landed || 1);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    refresh(days, query).catch(() => undefined);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold">Analytics</h1>
          <p className="mt-2 muted">
            First-party traffic at <code className="text-[var(--iid-ink)]">/app/analytics</code> — pages, time on site,
            source, device, and location. Registered users remain in{" "}
            <Link href="/app/crm" className="text-[var(--iid-blue)] hover:underline">
              CRM → Accounts
            </Link>
            .
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {RANGES.map((range) => (
            <button
              key={range.days}
              type="button"
              className={`iid-btn ${days === range.days ? "iid-btn-primary" : "iid-btn-ghost"}`}
              onClick={() => setDays(range.days)}
            >
              {range.label}
            </button>
          ))}
          <Link href="/app/crm" className="iid-btn iid-btn-ghost">
            CRM
          </Link>
        </div>
      </div>

      {error ? (
        <div className="iid-card space-y-3">
          <p className="text-sm text-red-400">{error}</p>
          <p className="text-xs muted">Analytics is only available when you sign in with the admin email set in ADMIN_EMAIL.</p>
          <button type="button" className="iid-btn iid-btn-ghost" onClick={() => refresh()}>
            Retry
          </button>
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Unique visitors" value={totals?.visitors} loading={loading} />
        <StatCard label="Sessions" value={totals?.sessions} loading={loading} />
        <StatCard label="Page views" value={totals?.pageviews} loading={loading} />
        <StatCard label="Signups (range)" value={totals?.signups} loading={loading} />
        <StatCard label="Registered accounts" value={totals?.registered_users} loading={loading} />
        <StatCard label="Demo starts" value={totals?.demo_starts ?? overview?.demo?.started} loading={loading} />
        <StatCard
          label="Signup rate"
          value={totals ? `${totals.signup_rate_pct}%` : undefined}
          loading={loading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="iid-card">
          <h2 className="font-display text-xl font-bold">Traffic</h2>
          <p className="mt-1 text-xs muted">Visitors, sessions, and page views by day.</p>
          <div className="mt-4">
            {chartData.length ? (
              <TrafficBars rows={chartData} />
            ) : (
              <p className="muted text-sm">No traffic in this range yet. Visit the public site to generate data.</p>
            )}
          </div>
        </section>
        <section className="iid-card space-y-3">
          <h2 className="font-display text-xl font-bold">Funnel</h2>
          <p className="text-xs muted">Share of sessions that reached each step.</p>
          {(["landed", "pricing", "login", "signup", "app"] as const).map((key) => {
            const count = overview?.funnel[key] || 0;
            const pct = Math.round((count / funnelMax) * 100);
            const labels: Record<typeof key, string> = {
              landed: "Visited site",
              pricing: "Viewed pricing",
              login: "Opened login",
              signup: "Signed up / identified",
              app: "Entered workspace",
            };
            return (
              <div key={key}>
                <div className="flex justify-between text-sm">
                  <span>{labels[key]}</span>
                  <span className="muted">
                    {count} · {pct}%
                  </span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-[var(--iid-panel-2)]">
                  <div className="h-full rounded-full bg-[var(--iid-blue)]" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="iid-card">
          <h2 className="font-display text-lg font-bold">Pages — who visited</h2>
          <p className="mt-1 text-xs muted">Click a page to see every visitor on it.</p>
          {(overview?.top_pages || []).length ? (
            <ul className="mt-3 space-y-2 text-sm">
              {(overview?.top_pages || []).slice(0, 12).map((row) => (
                <li key={row.path}>
                  <button
                    type="button"
                    className={`flex w-full justify-between gap-3 border-b border-[var(--iid-line)] py-1.5 text-left ${pagePath === row.path ? "font-semibold text-[var(--iid-blue)]" : ""}`}
                    onClick={() => setPagePath(row.path)}
                  >
                    <span className="truncate">{row.path}</span>
                    <span className="muted whitespace-nowrap">
                      {row.unique_visitors} people · {row.views} views
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm muted">No pages yet.</p>
          )}
          {pagePath ? (
            <div className="mt-4 rounded-lg border border-[var(--iid-line)] p-3">
              <p className="text-sm font-semibold">{pagePath}</p>
              <p className="text-xs muted">
                {pagePeopleMeta.unique_visitors} people · {pagePeopleMeta.views} views
              </p>
              <ul className="mt-2 max-h-56 space-y-1 overflow-auto text-sm">
                {pagePeople.map((person) => (
                  <li key={person.visitor_id} className="flex justify-between gap-2">
                    <span className="truncate">{person.email || person.name || person.visitor_id.slice(0, 10)}</span>
                    <span className="muted whitespace-nowrap">
                      {person.place || person.source || "—"} · {person.views}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
        <ListCard title="Where they came from" rows={(overview?.top_referrers || []).map((row) => ({
          label: row.label || "direct",
          detail: `${row.count} sessions`,
        }))} />
        <ListCard
          title="Demo parts viewed"
          rows={(overview?.demo?.parts || []).map((row) => ({
            label: row.label,
            detail: `${row.count} sessions`,
          }))}
          empty="No demo sessions yet. “See demo” and demo_readonly workspace pages will show here."
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="iid-card">
          <h2 className="font-display text-lg font-bold">Channels</h2>
          <div className="mt-4 space-y-2">
            {(overview?.top_sources || []).length ? (
              (overview?.top_sources || []).slice(0, 8).map((row) => {
                const max = Math.max(1, ...(overview?.top_sources || []).map((item) => item.count));
                const pct = Math.round((row.count / max) * 100);
                return (
                  <div key={row.label}>
                    <div className="flex justify-between text-sm">
                      <span className="truncate">{row.label}</span>
                      <span className="muted">{row.count}</span>
                    </div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-[var(--iid-panel-2)]">
                      <div className="h-full rounded-full bg-[var(--iid-blue)]" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-sm muted">No source data yet.</p>
            )}
          </div>
        </section>
        <ListCard title="Devices" rows={(overview?.top_devices || []).map((row) => ({
          label: row.label,
          detail: `${row.count} sessions`,
        }))} />
        <ListCard title="Campaigns / UTM" rows={(overview?.top_campaigns || []).map((row) => ({
          label: row.label,
          detail: `${row.count} sessions`,
        }))} empty="No UTM campaigns captured yet." />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="iid-card overflow-x-auto">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-xl font-bold">Visitors</h2>
              <p className="mt-1 text-xs muted">{totalSessions} sessions in range</p>
            </div>
            <form className="flex flex-wrap gap-2" onSubmit={onSearch}>
              <input
                className="iid-input min-w-[14rem]"
                placeholder="Search email, city, source, page"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button type="submit" className="iid-btn iid-btn-primary" disabled={loading}>
                {loading ? "Loading…" : "Search"}
              </button>
            </form>
          </div>
          {loading && sessions.length === 0 ? (
            <p className="mt-3 muted">Loading sessions…</p>
          ) : sessions.length === 0 ? (
            <p className="mt-3 muted">No visitors recorded yet.</p>
          ) : (
            <table className="mt-4 w-full min-w-[720px] text-left text-sm">
              <thead className="text-[var(--iid-muted)]">
                <tr>
                  <th className="pb-2 pr-3">When</th>
                  <th className="pb-2 pr-3">Place</th>
                  <th className="pb-2 pr-3">Source</th>
                  <th className="pb-2 pr-3">Pages</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((row) => (
                  <tr
                    key={row.session_id}
                    className={`cursor-pointer border-t border-[var(--iid-line)] ${selected === row.session_id ? "bg-[var(--iid-panel-2)]" : ""}`}
                    onClick={() => setSelected(row.session_id)}
                  >
                    <td className="py-2.5 pr-3">
                      <div className="font-semibold">{formatDateTime(row.last_seen_at)}</div>
                      <div className="text-xs muted">{row.user_email || row.visitor_id.slice(0, 10)}</div>
                    </td>
                    <td className="py-2.5 pr-3">
                      <div>{placeLabel(row)}</div>
                      <div className="text-xs muted">
                        {row.device || "—"} · {row.browser || "—"}
                      </div>
                    </td>
                    <td className="py-2.5 pr-3">
                      <div>{sourceLabel(row)}</div>
                      <div className="text-xs muted">{row.landing_path || "/"}</div>
                    </td>
                    <td className="py-2.5 pr-3">{row.page_count}</td>
                    <td className="py-2.5">{formatDuration(row.duration_ms)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <aside className="iid-card space-y-4">
          <h2 className="font-display text-xl font-bold">Session detail</h2>
          {detailLoading ? (
            <p className="muted text-sm">Loading journey…</p>
          ) : !detail ? (
            <p className="muted text-sm">Select a visitor to inspect their path.</p>
          ) : (
            <>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="muted text-xs">Location</dt>
                  <dd>{String(detail.session.place || detail.visitor.place || placeLabel(detail.session))}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Timezone</dt>
                  <dd>{String(detail.session.timezone || detail.visitor.timezone || "—")}</dd>
                </div>
                <div>
                  <dt className="muted text-xs">Device</dt>
                  <dd>
                    {detail.session.device || "—"} · {detail.session.os || "—"} · {detail.session.browser || "—"}
                  </dd>
                </div>
                <div>
                  <dt className="muted text-xs">Identity</dt>
                  <dd>{detail.session.user_email || String(detail.visitor.user_email || "Anonymous")}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="muted text-xs">Landed from</dt>
                  <dd className="break-all">
                    {sourceLabel(detail.session)}
                    {detail.session.referrer ? ` · ${detail.session.referrer}` : ""}
                  </dd>
                </div>
              </dl>
              <div>
                <h3 className="text-sm font-semibold">Pages visited</h3>
                {detail.pages.length ? (
                  <ol className="mt-2 space-y-1 text-sm">
                    {detail.pages.map((page) => (
                      <li key={page.id} className="rounded-lg border border-[var(--iid-line)] px-3 py-2">
                        <div className="flex justify-between gap-3">
                          <span className="font-medium">{page.label || page.path}</span>
                          <span className="muted whitespace-nowrap">{formatDuration(page.duration_ms)}</span>
                        </div>
                        <div className="text-xs muted">
                          {formatDateTime(page.at)} · {page.scroll_pct}% scrolled
                          {page.title ? ` · ${page.title}` : ""}
                        </div>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="mt-2 text-sm muted">No page timeline yet.</p>
                )}
              </div>
              {detail.events.length ? (
                <div>
                  <h3 className="text-sm font-semibold">Events</h3>
                  <ul className="mt-2 space-y-1 text-sm">
                    {detail.events.map((event) => (
                      <li key={event.id} className="flex justify-between gap-3 border-b border-[var(--iid-line)] py-1.5">
                        <span>
                          {event.name}
                          {event.path ? ` · ${event.path}` : ""}
                        </span>
                        <span className="muted whitespace-nowrap">{formatDateTime(event.at)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

function TrafficBars({
  rows,
}: {
  rows: Array<{ label: string; visitors: number; pageviews: number; signups: number }>;
}) {
  const max = Math.max(1, ...rows.map((row) => Math.max(row.visitors, row.pageviews, row.signups)));
  const shown = rows.length > 31 ? rows.slice(-31) : rows;
  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-3 text-xs muted">
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm bg-[var(--iid-blue)]" /> Visitors
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm bg-emerald-500" /> Page views
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm bg-amber-500" /> Signups
        </span>
      </div>
      <div className="flex h-64 items-end gap-1 overflow-x-auto">
        {shown.map((row) => (
          <div key={row.label} className="flex min-w-[1.75rem] flex-1 flex-col items-center justify-end gap-1">
            <div className="flex h-52 w-full items-end justify-center gap-0.5">
              <div
                className="w-1/3 rounded-t bg-[var(--iid-blue)]"
                style={{ height: `${Math.max(2, (row.visitors / max) * 100)}%` }}
                title={`${row.visitors} visitors`}
              />
              <div
                className="w-1/3 rounded-t bg-emerald-500/80"
                style={{ height: `${Math.max(2, (row.pageviews / max) * 100)}%` }}
                title={`${row.pageviews} page views`}
              />
              <div
                className="w-1/3 rounded-t bg-amber-500/80"
                style={{ height: `${Math.max(2, (row.signups / max) * 100)}%` }}
                title={`${row.signups} signups`}
              />
            </div>
            <span className="text-[10px] muted">{row.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, loading }: { label: string; value?: string | number; loading?: boolean }) {
  return (
    <div className="iid-card">
      <p className="text-xs uppercase tracking-wide muted">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold">{loading && value == null ? "…" : value ?? 0}</p>
    </div>
  );
}

function ListCard({
  title,
  rows,
  empty = "Nothing recorded yet.",
}: {
  title: string;
  rows: Array<{ label: string; detail: string }>;
  empty?: string;
}) {
  return (
    <section className="iid-card">
      <h2 className="font-display text-lg font-bold">{title}</h2>
      {rows.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {rows.slice(0, 8).map((row) => (
            <li key={`${row.label}-${row.detail}`} className="flex justify-between gap-3 border-b border-[var(--iid-line)] py-1.5">
              <span className="truncate font-medium">{row.label}</span>
              <span className="muted whitespace-nowrap">{row.detail}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm muted">{empty}</p>
      )}
    </section>
  );
}
