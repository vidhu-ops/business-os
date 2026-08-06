"use client";

import { api, type User } from "@/lib/api";
import {
  collectSectionNodes,
  firstNameFrom,
  readScreenSummary,
  sectionCueFromElement,
  tourForPath,
  type SectionCue,
} from "@/lib/iida-guide";
import { MessageCircle, Send, Sparkles, X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Turn = { role: "iida" | "user"; text: string };
type Action = { id: string; label: string };
type Handoff = { type?: string; href?: string } | null;

type Props = {
  email?: string;
};

function stripMd(s: string) {
  return s.replace(/\*\*/g, "");
}

export function IidaAssistant({ email = "" }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [tip, setTip] = useState("");
  const [actions, setActions] = useState<Action[]>([]);
  const [chat, setChat] = useState<Turn[]>([]);
  const [sectionTip, setSectionTip] = useState("");
  const [pulse, setPulse] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const seenSections = useRef<Set<string>>(new Set());
  const lastSectionId = useRef("");
  const projectId = searchParams.get("project") || "";

  const tour = useMemo(() => tourForPath(pathname), [pathname]);
  const first = firstNameFrom(email || user?.email || "", user?.name);
  const liveTip = sectionTip || tip;

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, [email]);

  const pushIidaNote = useCallback((text: string, intoChat: boolean) => {
    const clean = stripMd(text);
    if (!clean) return;
    setTip(clean);
    setSectionTip(clean);
    setPulse(true);
    window.setTimeout(() => setPulse(false), 700);
    if (intoChat) {
      setChat((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === "iida" && last.text === clean) return prev;
        return [...prev.slice(-40), { role: "iida", text: clean }];
      });
    }
  }, []);

  const refreshTip = useCallback(async () => {
    const screen = readScreenSummary();
    try {
      const data = await api.iidaTip(pathname || "/app/dashboard", screen);
      const msg = stripMd(String(data.message || ""));
      setActions((data.actions as Action[]) || []);
      pushIidaNote(msg, true);
    } catch {
      const fallback = `Hey ${first} — you are on ${tour.title}. ${tour.blurb} ${tour.hook}`;
      setActions([
        { id: "what_is_this", label: "What is this?" },
        { id: "what_next", label: "What next?" },
      ]);
      pushIidaNote(fallback, true);
    }
  }, [pathname, first, tour.title, tour.blurb, tour.hook, pushIidaNote]);

  useEffect(() => {
    seenSections.current.clear();
    lastSectionId.current = "";
    setChat([]);
    setSectionTip("");
    const t = window.setTimeout(() => {
      refreshTip().catch(() => null);
    }, 280);
    return () => window.clearTimeout(t);
  }, [pathname, refreshTip]);

  // Auto-narrate sections as the user scrolls
  useEffect(() => {
    let cancelled = false;
    let observer: IntersectionObserver | null = null;
    let debounce: number | undefined;

    const attach = () => {
      if (cancelled) return;
      observer?.disconnect();
      const nodes = collectSectionNodes();
      if (!nodes.length) return;

      observer = new IntersectionObserver(
        (entries) => {
          const visible = entries
            .filter((e) => e.isIntersecting && e.intersectionRatio >= 0.35)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
          const top = visible[0]?.target as HTMLElement | undefined;
          if (!top) return;
          const cue: SectionCue = sectionCueFromElement(top, tour.title);
          if (cue.id === lastSectionId.current) return;
          window.clearTimeout(debounce);
          debounce = window.setTimeout(() => {
            lastSectionId.current = cue.id;
            const firstVisit = !seenSections.current.has(cue.id);
            seenSections.current.add(cue.id);
            // Always update the popup tip quickly; add to chat on first visit of a section
            pushIidaNote(cue.explain, firstVisit);
          }, 120);
        },
        { root: null, rootMargin: "-12% 0px -42% 0px", threshold: [0.35, 0.55, 0.75] },
      );
      nodes.forEach((n) => observer?.observe(n));
    };

    const boot = window.setTimeout(attach, 400);
    const onResize = () => {
      window.clearTimeout(debounce);
      attach();
    };
    window.addEventListener("resize", onResize);
    return () => {
      cancelled = true;
      window.clearTimeout(boot);
      window.clearTimeout(debounce);
      window.removeEventListener("resize", onResize);
      observer?.disconnect();
    };
  }, [pathname, tour.title, pushIidaNote]);

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, open, loading]);

  function runHandoff(handoff: Handoff) {
    if (!handoff?.href) return;
    let href = handoff.href;
    if (projectId && href.startsWith("/app/team") && !href.includes("project=")) {
      href += (href.includes("?") ? "&" : "?") + `project=${encodeURIComponent(projectId)}`;
    }
    router.push(href);
    if (handoff.type === "taylor") setOpen(true);
  }

  async function sendMessage(raw: string) {
    const message = raw.trim();
    if (!message || loading) return;
    setInput("");
    setOpen(true);
    setChat((prev) => [...prev, { role: "user", text: message }]);
    setLoading(true);
    try {
      const data = await api.iidaChat({
        message,
        path: pathname || "/app/dashboard",
        screen_summary: `${readScreenSummary()} | watching: ${sectionTip || tip}`.slice(0, 400),
        project_id: projectId || undefined,
      });
      setChat((prev) => [...prev, { role: "iida", text: stripMd(String(data.reply || "")) }]);
      if (Array.isArray(data.actions)) setActions(data.actions as Action[]);
      if (data.handoff) runHandoff(data.handoff as Handoff);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "I hit a snag — try again in a moment.";
      setChat((prev) => [...prev, { role: "iida", text: msg }]);
    } finally {
      setLoading(false);
    }
  }

  function onAction(id: string) {
    if (id === "brief_taylor" || id === "open_taylor") {
      void sendMessage("Brief Taylor for me");
      return;
    }
    if (id === "open_hiring") {
      runHandoff({ type: "navigate", href: "/app/team?tab=hiring" });
      return;
    }
    if (id === "open_approvals") {
      runHandoff({ type: "navigate", href: "/app/team?tab=tasks" });
      return;
    }
    if (id === "go_team") {
      runHandoff({ type: "navigate", href: "/app/team" });
      return;
    }
    if (id === "go_audit") {
      runHandoff({ type: "navigate", href: "/app/audit" });
      return;
    }
    if (id === "what_is_this") void sendMessage("What is this page? Read the screen for me.");
    else if (id === "what_next") void sendMessage("What should I do next?");
    else void sendMessage(id.replace(/_/g, " "));
  }

  return (
    <div className="iida-popup-root" data-iida-root>
      {!open && liveTip ? (
        <button
          type="button"
          className={`iida-float-tip${pulse ? " iida-float-tip-pulse" : ""}`}
          onClick={() => setOpen(true)}
        >
          <span className="iida-float-tip-label">Your assistant</span>
          <span className="iida-float-tip-text">
            {liveTip.slice(0, 150)}
            {liveTip.length > 150 ? "…" : ""}
          </span>
        </button>
      ) : null}

      {open ? (
        <div className="iida-popup">
          <div className="iida-popup-head">
            <div className="min-w-0">
              <p className="font-semibold text-sm flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[var(--iid-sky)]" /> Your assistant
              </p>
              <p className="text-[11px] muted truncate">
                IIDA · {first} · narrating {tour.title}
              </p>
            </div>
            <button type="button" className="iid-btn iid-btn-ghost text-xs px-2" onClick={() => setOpen(false)} aria-label="Close assistant">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="iida-popup-body">
            {chat.length === 0 ? (
              <p className="text-xs muted">I explain each section as you scroll. Ask anything anytime.</p>
            ) : null}
            {chat.map((t, i) => (
              <div key={i} className={`flex ${t.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`iida-msg ${t.role === "user" ? "iida-msg-user" : "iida-msg-bot"}`}>{t.text}</div>
              </div>
            ))}
            {loading ? <p className="text-xs muted">IIDA is thinking…</p> : null}
            <div ref={endRef} />
          </div>

          {actions.length > 0 ? (
            <div className="iida-popup-chips">
              {actions.slice(0, 3).map((a) => (
                <button key={a.id} type="button" className="iida-chip" disabled={loading} onClick={() => onAction(a.id)}>
                  {a.label}
                </button>
              ))}
              {pathname?.startsWith("/app/team") ? (
                <button type="button" className="iida-chip iida-chip-accent" disabled={loading} onClick={() => onAction("brief_taylor")}>
                  Brief Taylor
                </button>
              ) : null}
            </div>
          ) : null}

          <form
            className="iida-popup-input"
            onSubmit={(e) => {
              e.preventDefault();
              void sendMessage(input);
            }}
          >
            <input
              className="iida-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask your assistant…"
              disabled={loading}
              aria-label="Message your assistant"
            />
            <button type="submit" className="iida-send" disabled={loading || !input.trim()} aria-label="Send">
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      ) : null}

      <button
        type="button"
        className={`iida-fab${open ? " iida-fab-open" : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close your assistant" : "Open your assistant"}
      >
        {open ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
        <span className="iida-fab-label">{open ? "Close" : "Your assistant"}</span>
      </button>
    </div>
  );
}