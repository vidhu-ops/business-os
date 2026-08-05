"use client";

import type { ReactNode } from "react";
import {
  Bell,
  Building2,
  Flame,
  Gauge,
  LayoutGrid,
  ListChecks,
  MessageSquare,
  Network,
  Puzzle,
  Sliders,
  UserPlus,
  Users,
} from "lucide-react";

export type OsTab = { id: string; label: string };
export type TeamChip = { id: string; name: string; role?: string; isLeader?: boolean };

const ICON_BY_TAB: Record<string, typeof LayoutGrid> = {
  office: LayoutGrid,
  hiring: UserPlus,
  organization: Network,
  tasks: ListChecks,
  war_room: Flame,
  command: Gauge,
  agents: Users,
  integrations: Puzzle,
  advanced: Sliders,
};

function shortName(name: string) {
  return name.split("—")[0].split("-")[0].trim();
}

function initials(name: string) {
  const parts = shortName(name).split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (parts[0]?.slice(0, 2) || "?").toUpperCase();
}

type Props = {
  title?: string;
  subtitle?: string;
  tabs: OsTab[];
  activeTab: string;
  onTabChange: (id: string) => void;
  approvalCount?: number;
  onTalkToTaylor?: () => void;
  onOpenApprovals?: () => void;
  ticker?: string[];
  demoReadonly?: boolean;
  projectPicker?: ReactNode;
  team?: TeamChip[];
  activeChatId?: string;
  onChatMember?: (id: string) => void;
  children: ReactNode;
};

export function EmployeeOsChrome({
  title = "Employee OS",
  subtitle,
  tabs,
  activeTab,
  onTabChange,
  approvalCount = 0,
  onTalkToTaylor,
  onOpenApprovals,
  ticker = [],
  demoReadonly = false,
  projectPicker,
  team = [],
  activeChatId,
  onChatMember,
  children,
}: Props) {
  return (
    <div className="rounded-2xl border border-[var(--iid-line)] overflow-hidden bg-[var(--iid-panel)]/50 flex flex-col min-h-[70vh]">
      <header className="border-b border-[var(--iid-line)] bg-[var(--iid-panel)]/90 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-[var(--iid-blue)] flex items-center justify-center shrink-0">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="font-display text-base font-bold leading-tight truncate">{title}</h1>
            {subtitle ? <p className="text-[11px] muted truncate font-mono mt-0.5">{subtitle}</p> : null}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {demoReadonly ? (
            <span className="text-[11px] rounded-full px-2.5 py-1 bg-amber-500/15 text-amber-200 border border-amber-500/30">
              Demo — browse only
            </span>
          ) : null}
          {onTalkToTaylor ? (
            <button type="button" className="iid-btn iid-btn-primary text-xs inline-flex items-center gap-1.5" onClick={onTalkToTaylor}>
              <MessageSquare className="w-3.5 h-3.5" /> Talk to Taylor
            </button>
          ) : null}
          <button
            type="button"
            className="relative iid-btn iid-btn-ghost text-xs px-2.5"
            onClick={onOpenApprovals}
            aria-label="Notifications and approvals"
            title="Approvals"
          >
            <Bell className="w-4 h-4" />
            {approvalCount > 0 ? (
              <span className="absolute -top-1.5 -right-1.5 min-w-5 h-5 px-1 rounded-full bg-red-500 text-[10px] font-bold flex items-center justify-center">
                {approvalCount}
              </span>
            ) : null}
          </button>
        </div>
      </header>

      {projectPicker ? (
        <div className="border-b border-[var(--iid-line)] px-4 py-2 bg-[var(--iid-panel)]/40">{projectPicker}</div>
      ) : null}

      {team.length > 0 && onChatMember ? (
        <div className="border-b border-[var(--iid-line)] px-3 py-2 flex items-center gap-2 overflow-x-auto bg-[var(--iid-panel)]/30">
          <span className="text-[10px] uppercase tracking-wide muted shrink-0 font-semibold">Team</span>
          {team.map((m) => {
            const active = activeChatId === m.id;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => onChatMember(m.id)}
                className={`shrink-0 flex items-center gap-1.5 rounded-full border px-2 py-1 text-[11px] transition-colors ${
                  active
                    ? "border-[var(--iid-blue)] bg-[var(--iid-blue)]/15 text-[var(--iid-text)]"
                    : "border-[var(--iid-line)] text-[var(--iid-muted)] hover:border-[var(--iid-blue)]/50 hover:text-[var(--iid-text)]"
                }`}
                title={`Chat with ${shortName(m.name)}`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold ${
                    m.isLeader ? "bg-violet-500/30 text-violet-200" : "bg-[var(--iid-blue)]/20 text-[var(--iid-sky)]"
                  }`}
                >
                  {initials(m.name)}
                </span>
                {shortName(m.name)}
              </button>
            );
          })}
        </div>
      ) : null}

      <nav className="border-b border-[var(--iid-line)] px-2 flex items-center gap-0.5 overflow-x-auto shrink-0">
        {tabs.map((t) => {
          const Icon = ICON_BY_TAB[t.id] || LayoutGrid;
          const active = activeTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => onTabChange(t.id)}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-semibold border-b-2 whitespace-nowrap transition-colors ${
                active
                  ? "border-[var(--iid-blue)] text-[var(--iid-text)]"
                  : "border-transparent text-[var(--iid-muted)] hover:text-[var(--iid-text)]"
              }`}
            >
              <Icon className="w-3.5 h-3.5" /> {t.label}
            </button>
          );
        })}
      </nav>

      {ticker.length > 0 ? (
        <div className="border-b border-[var(--iid-line)] bg-[var(--iid-panel)]/50 px-4 py-1.5 overflow-hidden shrink-0">
          <div className="flex items-center gap-2 text-[11px] font-mono text-[var(--iid-muted)] whitespace-nowrap overflow-x-auto">
            <span className="text-[var(--iid-blue)] shrink-0 font-semibold">● LIVE</span>
            {ticker.slice(-6).map((line, i) => (
              <span key={`${i}-${line.slice(0, 24)}`} className="shrink-0">
                {line} <span className="opacity-40">·</span>
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="p-4 md:p-5 flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}