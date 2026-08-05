"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { Loader2, Send, X } from "lucide-react";

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
  onSend: () => void;
  loading?: boolean;
  readOnly?: boolean;
  readOnlyHint?: string;
  starters?: string[];
  footerExtra?: ReactNode;
  renderArtifacts?: (artifacts: string[], content: string) => ReactNode;
};

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
  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, open, loading]);

  if (!open) return null;
  const short = name.split("—")[0].split("-")[0].trim().split(" ")[0] || name;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button type="button" className="absolute inset-0 bg-black/50" aria-label="Close chat" onClick={onClose} />
      <div className="relative w-full max-w-md bg-[var(--iid-panel)] border-l border-[var(--iid-line)] flex flex-col shadow-2xl">
        <div className="px-4 py-3 border-b border-[var(--iid-line)] flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">{name}</p>
            <p className="text-xs muted truncate">{role || subtitle}</p>
          </div>
          <button type="button" className="text-[var(--iid-muted)] hover:text-[var(--iid-text)]" onClick={onClose}>
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {readOnly ? (
            <p className="text-xs muted">{readOnlyHint || "Demo mode is browse-only. Sign up to chat with agents."}</p>
          ) : chat.length === 0 ? (
            <p className="text-xs muted">Start a conversation with {short}. They know their tasks and team context.</p>
          ) : null}
          {chat.map((turn, i) => (
            <div key={i} className={`flex ${turn.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[88%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap ${
                  turn.role === "user" ? "bg-[var(--iid-blue)] text-white" : "bg-[var(--iid-panel-2)] text-[var(--iid-text)]"
                }`}
              >
                {turn.content}
                {turn.role === "assistant" && renderArtifacts
                  ? renderArtifacts(turn.artifacts || [], String(turn.content || ""))
                  : null}
              </div>
            </div>
          ))}
          {loading ? (
            <div className="flex justify-start">
              <div className="bg-[var(--iid-panel-2)] rounded-2xl px-3 py-2 flex items-center gap-1.5 text-xs muted">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> typing…
              </div>
            </div>
          ) : null}
          <div ref={endRef} />
        </div>
        {!readOnly ? (
          <div className="p-3 border-t border-[var(--iid-line)] space-y-2">
            {starters.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {starters.slice(0, 3).map((s) => (
                  <button key={s} type="button" className="iid-btn iid-btn-ghost text-[10px]" disabled={loading} onClick={() => onSend()}>
                    {s}
                  </button>
                ))}
              </div>
            ) : null}
            <div className="flex items-center gap-2">
              <input
                className="iid-input flex-1 text-sm"
                value={input}
                onChange={(e) => onInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSend()}
                placeholder={`Message ${short}…`}
                disabled={loading}
              />
              <button
                type="button"
                className="w-10 h-10 rounded-lg bg-[var(--iid-blue)] text-white flex items-center justify-center disabled:opacity-40"
                disabled={loading || !input.trim()}
                onClick={onSend}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            {footerExtra}
          </div>
        ) : (
          <div className="p-3 border-t border-[var(--iid-line)]">
            <a href="/login?mode=register" className="iid-btn iid-btn-primary text-sm w-full justify-center">
              Sign up to run the office
            </a>
          </div>
        )}
      </div>
    </div>
  );
}