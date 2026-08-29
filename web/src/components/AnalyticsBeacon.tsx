"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";
import { getToken } from "@/lib/api";
import {
  collectClientContext,
  getSessionId,
  getVisitorId,
  parseClickIds,
  parseUtms,
  scrollPercent,
} from "@/lib/visitor";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

type CollectPayload = {
  visitor_id: string;
  session_id: string;
  type: "pageview" | "heartbeat" | "event" | "identify";
  path: string;
  title?: string;
  href?: string;
  referrer?: string;
  pageview_id?: string;
  duration_ms?: number;
  scroll_pct?: number;
  event_name?: string;
  utm?: Record<string, string>;
  click_ids?: Record<string, string>;
  client?: Record<string, unknown>;
  props?: Record<string, unknown>;
};

function send(payload: CollectPayload, keepalive = false) {
  const body = JSON.stringify(payload);
  const url = `${API_BASE}/api/v1/analytics/collect`;
  if (keepalive && typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
    try {
      const blob = new Blob([body], { type: "application/json" });
      if (navigator.sendBeacon(url, blob)) return;
    } catch {
      /* fall through */
    }
  }
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token && payload.type === "identify") headers.Authorization = `Bearer ${token}`;
  void fetch(url, {
    method: "POST",
    headers,
    body,
    credentials: "include",
    keepalive,
  }).catch(() => undefined);
}

function AnalyticsBeaconInner() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const pageviewId = useRef("");
  const startedAt = useRef(0);
  const maxScroll = useRef(0);
  const identifiedSession = useRef("");
  const landingSearch = useRef("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!landingSearch.current) landingSearch.current = window.location.search || "";
    getVisitorId();
    getSessionId();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const path = pathname || window.location.pathname || "/";
    if (path.startsWith("/api/")) return;
    const visitorId = getVisitorId();
    const sessionId = getSessionId();
    const search = searchParams?.toString() ? `?${searchParams.toString()}` : window.location.search;
    const href = `${window.location.origin}${path}${search}`;
    const utm = parseUtms(search || landingSearch.current);
    const clickIds = parseClickIds(search || landingSearch.current);
    startedAt.current = Date.now();
    maxScroll.current = scrollPercent();
    pageviewId.current = "";

    const payload: CollectPayload = {
      visitor_id: visitorId,
      session_id: sessionId,
      type: "pageview",
      path,
      title: document.title || "",
      href,
      referrer: document.referrer || "",
      utm,
      click_ids: clickIds,
      client: collectClientContext(),
    };

    const url = `${API_BASE}/api/v1/analytics/collect`;
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    })
      .then((res) => res.json().catch(() => ({})))
      .then((data: { pageview_id?: string }) => {
        if (data?.pageview_id) pageviewId.current = data.pageview_id;
      })
      .catch(() => undefined);

    const token = getToken();
    if (token && identifiedSession.current !== sessionId) {
      identifiedSession.current = sessionId;
      send({
        visitor_id: visitorId,
        session_id: sessionId,
        type: "identify",
        event_name: "identify",
        path,
        href,
        client: collectClientContext(),
      });
    }

    const onScroll = () => {
      maxScroll.current = Math.max(maxScroll.current, scrollPercent());
    };
    const heartbeat = () => {
      if (document.visibilityState === "hidden") return;
      send({
        visitor_id: visitorId,
        session_id: sessionId,
        type: "heartbeat",
        path,
        href,
        pageview_id: pageviewId.current,
        duration_ms: Date.now() - startedAt.current,
        scroll_pct: maxScroll.current,
      });
    };
    const flush = () => {
      send(
        {
          visitor_id: visitorId,
          session_id: sessionId,
          type: "heartbeat",
          path,
          href,
          pageview_id: pageviewId.current,
          duration_ms: Date.now() - startedAt.current,
          scroll_pct: Math.max(maxScroll.current, scrollPercent()),
        },
        true,
      );
    };
    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const link = target?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!link) return;
      const next = link.href || "";
      if (!next) return;
      let outbound = false;
      try {
        const parsed = new URL(next, window.location.origin);
        outbound = parsed.origin !== window.location.origin;
        const destPath = parsed.pathname || "";
        const name = outbound ? "outbound_click" : destPath.startsWith("/login") || destPath.startsWith("/pricing") || destPath.startsWith("/app") ? "cta_click" : "";
        if (!name) return;
        send({
          visitor_id: visitorId,
          session_id: sessionId,
          type: "event",
          event_name: name,
          path,
          href: parsed.toString(),
          props: { text: (link.textContent || "").trim().slice(0, 80), dest: destPath },
        });
      } catch {
        /* ignore */
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("click", onClick, true);
    window.addEventListener("pagehide", flush);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") flush();
    });
    const timer = window.setInterval(heartbeat, 15000);
    return () => {
      flush();
      window.clearInterval(timer);
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("click", onClick, true);
      window.removeEventListener("pagehide", flush);
    };
  }, [pathname, searchParams]);

  return null;
}

export function AnalyticsBeacon() {
  return (
    <Suspense fallback={null}>
      <AnalyticsBeaconInner />
    </Suspense>
  );
}
