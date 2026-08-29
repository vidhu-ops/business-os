"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type AnalyticsOverview,
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
            First-party traffic for every visitor — pages, time on site, source, device, and location.
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

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard label="Unique visitors" value={totals?.visitors} loading={loading} />
        <StatCard label="Sessions" value={totals?.sessions} loading={loading} />
        <StatCard label="Page views" value={totals?.pageviews} loading={loading} />
        <StatCard label="Signups" value={totals?.signups} loading={loading} />
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
          <div className="mt-4 h-64">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--iid-line)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} stroke="var(--iid-muted)" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="var(--iid-muted)" width={32} />
                  <Tooltip />
                  <Area type="monotone" dataKey="visitors" name="Visitors" stroke="#0b5fff" fill="#0b5fff33" />
                  <Area type="monotone" dataKey="pageviews" name="Page views" stroke="#22c55e" fill="#22c55e22" />
                  <Area type="monotone" dataKey="signups" name="Signups" stroke="#f59e0b" fill="#f59e0b22" />
                </AreaChart>
              </ResponsiveContainer>
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
        <ListCard title="Pages" rows={(overview?.top_pages || []).map((row) => ({
          label: row.path,
          detail: `${row.views} views · ${formatDuration(row.avg_duration_ms)} avg · ${row.avg_scroll_pct}% scroll`,
        }))} />
        <ListCard title="Where they came from" rows={(overview?.top_referrers || []).map((row) => ({
          label: row.label || "direct",
          detail: `${row.count} sessions`,
        }))} />
        <ListCard title="Location" rows={(overview?.top_cities || overview?.top_countries || []).map((row) => ({
          label: row.label || "Unknown",
          detail: `${row.count} sessions`,
        }))} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="iid-card">
          <h2 className="font-display text-lg font-bold">Channels</h2>
          <div className="mt-4 h-48">
            {(overview?.top_sources || []).length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={overview?.top_sources || []} layout="vertical" margin={{ left: 8, right: 8 }}>
                  <XAxis type="number" allowDecimals={false} hide />
                  <YAxis type="category" dataKey="label" width={80} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#0b5fff" radius={4} />
                </BarChart>
              </ResponsiveContainer>
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
                          <span className="font-medium">{page.path}</span>
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
