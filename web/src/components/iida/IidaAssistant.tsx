"use client";

import { api, type User } from "@/lib/api";
import { firstNameFrom, readScreenSummary, tourForPath } from "@/lib/iida-guide";
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
  const [minimized, setMinimized] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const projectId = searchParams.get("project") || "";

  const tour = useMemo(() => tourForPath(pathname), [pathname]);
  const first = firstNameFrom(email || user?.email || "", user?.name);

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, [email]);

  const refreshTip = useCallback(async () => {
    const screen = readScreenSummary();
    try {
      const data = await api.iidaTip(pathname || "/app/dashboard", screen);
      setTip(String(data.message || ""));
      setActions((data.actions as Action[]) || []);
      setChat((prev) => {
        if (prev.length > 0) return prev;
        return [{ role: "iida", text: stripMd(String(data.message || "")) }];
      });
    } catch {
      const fallback = `Hey ${first} — you are on ${tour.title}. ${tour.blurb} ${tour.hook}`;
      setTip(fallback);
      setActions([
        { id: "what_is_this", label: "What is this page?" },
        { id: "what_next", label: "What should I do next?" },
      ]);
      setChat((prev) => (prev.length ? prev : [{ role: "iida", text: fallback }]));
    }
  }, [pathname, first, tour.title, tour.blurb, tour.hook]);

  useEffect(() => {
    setChat([]);
    const t = window.setTimeout(() => {
      refreshTip().catch(() => null);
    }, 350);
    return () => window.clearTimeout(t);
  }, [pathname, refreshTip]);

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
        screen_summary: readScreenSummary(),
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

  if (minimized) {
    return (
      <button
        type="button"
        className="iida-fab"
        onClick={() => setMinimized(false)}
        aria-label="Open IIDA assistant"
      >
        <Sparkles className="w-4 h-4" />
        <span>IIDA</span>
      </button>
    );
  }

  return (
    <div className="iida-dock" data-iida-root>
      {!open && tip ? (
        <button type="button" className="iida-bubble" onClick={() => setOpen(true)}>
          <span className="iida-bubble-label">IIDA</span>
          <span className="iida-bubble-text">{stripMd(tip).slice(0, 140)}{stripMd(tip).length > 140 ? "…" : ""}</span>
        </button>
      ) : null}

      {open ? (
        <div className="iida-panel">
          <div className="iida-panel-head">
            <div className="min-w-0">
              <p className="font-semibold text-sm flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[var(--iid-sky)]" /> IIDA
                <span className="text-[10px] muted font-normal">your guide · {tour.title}</span>
              </p>
              <p className="text-[11px] muted truncate">Personal aide for {first} — I read the screen and can brief Taylor</p>
            </div>
            <button type="button" className="iid-btn iid-btn-ghost text-xs px-2" onClick={() => setOpen(false)} aria-label="Collapse chat">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="iida-panel-body">
            {chat.map((t, i) => (
              <div key={i} className={`flex ${t.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`iida-msg ${t.role === "user" ? "iida-msg-user" : "iida-msg-bot"}`}>{t.text}</div>
              </div>
            ))}
            {loading ? <p className="text-xs muted">IIDA is thinking…</p> : null}
            <div ref={endRef} />
          </div>
        </div>
      ) : null}

      <div className="iida-bar">
        <button type="button" className="iida-avatar" onClick={() => setOpen((v) => !v)} title="Toggle IIDA">
          <MessageCircle className="w-4 h-4" />
        </button>
        <div className="iida-bar-meta hidden sm:block">
          <p className="text-[11px] font-semibold leading-tight">IIDA</p>
          <p className="text-[10px] muted truncate max-w-[9rem]">{tour.title}</p>
        </div>
        <div className="iida-chips">
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
        <form
          className="iida-input-wrap"
          onSubmit={(e) => {
            e.preventDefault();
            void sendMessage(input);
          }}
        >
          <input
            className="iida-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask IIDA anything about this screen…`}
            disabled={loading}
            aria-label="Message IIDA"
          />
          <button type="submit" className="iida-send" disabled={loading || !input.trim()} aria-label="Send">
            <Send className="w-4 h-4" />
          </button>
        </form>
        <button type="button" className="iid-btn iid-btn-ghost text-[10px] px-2 hidden md:inline-flex" onClick={() => setMinimized(true)}>
          Hide
        </button>
      </div>
    </div>
  );
}