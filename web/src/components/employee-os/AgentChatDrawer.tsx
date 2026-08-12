"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { Loader2, MessageSquare, Send, Sparkles, X } from "lucide-react";

type Turn = { role: string; content?: string; artifacts?: string[] };

type Props = {
  open: boolean;
  onClose: () => void;
  name: string;
  role?: string;
  subtitle?: string;
  chat: Turn[];
  input: string;
  onInput: (v: string) => void;
  onSend: (message?: string) => void;
  loading?: boolean;
  readOnly?: boolean;
  readOnlyHint?: string;
  starters?: string[];
  footerExtra?: ReactNode;
  renderArtifacts?: (artifacts: string[], content: string) => ReactNode;
};

function initials(name: string) {
  const base = name.split("—")[0].split("-")[0].trim();
  const parts = base.split(/\s+/).filter(Boolean);
  if (!parts.length) return "AI";
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || "")
    .join("");
}

export function AgentChatDrawer({
  open,
  onClose,
  name,
  role,
  subtitle,
  chat,
  input,
  onInput,
  onSend,
  loading,
  readOnly,
  readOnlyHint,
  starters = [],
  footerExtra,
  renderArtifacts,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, open, loading]);

  useEffect(() => {
    if (open && !readOnly) {
      const t = window.setTimeout(() => inputRef.current?.focus(), 80);
      return () => window.clearTimeout(t);
    }
  }, [open, name, readOnly]);

  if (!open) return null;

  const short = name.split("—")[0].split("-")[0].trim().split(" ")[0] || name;
  const avatar = initials(name);
  const meta = role || subtitle || "Team member";

  function submit() {
    if (loading || readOnly) return;
    const value = input.trim();
    if (!value) return;
    onSend(value);
  }

  return (
    <div className="eos-chat-overlay" role="dialog" aria-modal="true" aria-label={`Chat with ${short}`}>
      <button type="button" className="eos-chat-backdrop" aria-label="Close chat" onClick={onClose} />
      <aside className="eos-chat-panel">
        <header className="eos-chat-header">
          <div className="eos-chat-identity">
            <span className="eos-chat-avatar" aria-hidden>
              {avatar}
            </span>
            <div className="min-w-0">
              <p className="eos-chat-name">{name.split("—")[0].trim()}</p>
              <p className="eos-chat-meta">{meta}</p>
            </div>
          </div>
          <button type="button" className="eos-chat-close" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="eos-chat-thread">
          {readOnly ? (
            <div className="eos-chat-empty">
              <MessageSquare className="eos-chat-empty-icon" />
              <p>{readOnlyHint || "Demo mode is browse-only. Sign up to chat with agents."}</p>
            </div>
          ) : chat.length === 0 ? (
            <div className="eos-chat-empty">
              <Sparkles className="eos-chat-empty-icon" />
              <h3>Talk to {short}</h3>
              <p>
                Give a clear deliverable — research, leads, copy, or an SOP. {short} uses this project&apos;s context and
                tools.
              </p>
              {starters.length > 0 ? (
                <div className="eos-chat-starters">
                  {starters.slice(0, 4).map((s) => (
                    <button key={s} type="button" className="eos-chat-starter" disabled={loading} onClick={() => onSend(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : (
            chat.map((turn, i) => {
              const isUser = turn.role === "user";
              return (
                <div key={i} className={`eos-chat-row ${isUser ? "is-user" : "is-agent"}`}>
                  {!isUser ? (
                    <span className="eos-chat-bubble-avatar" aria-hidden>
                      {avatar}
                    </span>
                  ) : null}
                  <div className={`eos-chat-bubble ${isUser ? "is-user" : "is-agent"}`}>
                    {!isUser ? <span className="eos-chat-bubble-label">{short}</span> : null}
                    <div className="eos-chat-bubble-body">{turn.content}</div>
                    {turn.role === "assistant" && renderArtifacts
                      ? renderArtifacts(turn.artifacts || [], String(turn.content || ""))
                      : null}
                  </div>
                </div>
              );
            })
          )}
          {loading ? (
            <div className="eos-chat-row is-agent">
              <span className="eos-chat-bubble-avatar" aria-hidden>
                {avatar}
              </span>
              <div className="eos-chat-bubble is-agent eos-chat-typing">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>{short} is working…</span>
              </div>
            </div>
          ) : null}
          <div ref={endRef} />
        </div>

        {!readOnly ? (
          <footer className="eos-chat-composer">
            {chat.length > 0 && starters.length > 0 ? (
              <div className="eos-chat-starters eos-chat-starters-compact">
                {starters.slice(0, 3).map((s) => (
                  <button key={s} type="button" className="eos-chat-starter" disabled={loading} onClick={() => onSend(s)}>
                    {s}
                  </button>
                ))}
              </div>
            ) : null}
            <div className="eos-chat-input-row">
              <textarea
                ref={inputRef}
                className="eos-chat-input"
                rows={2}
                value={input}
                onChange={(e) => onInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submit();
                  }
                }}
                placeholder={`Message ${short}…`}
                disabled={loading}
              />
              <button
                type="button"
                className="eos-chat-send"
                disabled={loading || !input.trim()}
                onClick={submit}
                aria-label="Send message"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </button>
            </div>
            <p className="eos-chat-hint">Enter to send · Shift+Enter for a new line</p>
            {footerExtra}
          </footer>
        ) : (
          <footer className="eos-chat-composer">
            <a href="/login?mode=register" className="iid-btn iid-btn-primary text-sm w-full justify-center">
              Sign up to run the office
            </a>
          </footer>
        )}
      </aside>
    </div>
  );
}
