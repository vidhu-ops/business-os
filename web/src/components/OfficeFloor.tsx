"use client";

import { useMemo } from "react";

type FloorMember = {
  id: string;
  name: string;
  role?: string;
  department?: string;
  is_leader?: boolean;
};

type BoardRow = {
  assignee?: string;
  title?: string;
  status?: string;
  mentor_note?: string;
  harness_id?: string;
};

type ActivityRow = { from?: string; text?: string; when?: string };

type Props = {
  members: FloorMember[];
  phase?: string;
  board?: BoardRow[];
  activity?: ActivityRow[];
  lastMentor?: string;
  activeAgentId?: string;
  chatLoading?: boolean;
  liveChatSnippet?: string;
  officeRunning?: boolean;
  onSelectMember?: (id: string) => void;
};

const PHASE_LABELS: Record<string, string> = {
  arrival: "Opening the office",
  standup: "Morning standup",
  execution: "Team executing tasks",
  agent_cycle: "Team sync and debate",
  delivery: "Wrapping up deliverables",
  closed: "Day complete",
};

const ACTIVE_STATUS = /in progress|assigned|qc review|working/i;

function shortName(name: string) {
  return name.split("—")[0].split("-")[0].trim();
}

function initials(name: string) {
  const parts = shortName(name).split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (parts[0]?.slice(0, 2) || "?").toUpperCase();
}

function matchMember(members: FloorMember[], label: string) {
  const needle = label.toLowerCase();
  return members.find((m) => {
    const n = shortName(m.name).toLowerCase();
    return n === needle || needle.includes(n) || n.includes(needle) || String(m.role || "").toLowerCase() === needle;
  });
}

function memberStatus(row: BoardRow | undefined, talking: boolean, running: boolean) {
  if (talking || running) return "talking";
  if (!row) return "idle";
  const status = String(row.status || "");
  if (ACTIVE_STATUS.test(status)) return "working";
  if (/delivered|completed/i.test(status)) return "done";
  return "idle";
}

export function OfficeFloor({
  members,
  phase = "arrival",
  board = [],
  activity = [],
  lastMentor = "",
  activeAgentId = "",
  chatLoading = false,
  liveChatSnippet = "",
  officeRunning = false,
  onSelectMember,
}: Props) {
  const bubbles = useMemo(() => {
    const map = new Map<string, string>();
    if (lastMentor && (phase === "standup" || phase === "execution" || phase === "arrival")) {
      map.set("taylor", lastMentor.slice(0, 140));
    }
    for (const row of board) {
      const status = String(row.status || "");
      if (!ACTIVE_STATUS.test(status)) continue;
      const hid = String(row.harness_id || "");
      const member = hid ? members.find((m) => m.id === hid) : matchMember(members, String(row.assignee || ""));
      const id = member?.id || hid || String(row.assignee || "");
      if (!id) continue;
      map.set(id, String(row.mentor_note || row.title || "Working on this task...").slice(0, 140));
    }
    for (const act of activity.slice(0, 6)) {
      const member = matchMember(members, String(act.from || ""));
      if (member && act.text) map.set(member.id, String(act.text).slice(0, 140));
    }
    if (chatLoading && activeAgentId) map.set(activeAgentId, "Typing...");
    else if (activeAgentId && liveChatSnippet) map.set(activeAgentId, liveChatSnippet.slice(0, 140));
    return map;
  }, [activity, activeAgentId, board, chatLoading, lastMentor, liveChatSnippet, members, phase]);

  const taskByMember = useMemo(() => {
    const map = new Map<string, BoardRow>();
    for (const row of board) {
      const hid = String(row.harness_id || "");
      const member = hid ? members.find((m) => m.id === hid) : matchMember(members, String(row.assignee || ""));
      if (member) map.set(member.id, row);
    }
    return map;
  }, [board, members]);

  if (members.length <= 1) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--iid-line)] bg-[var(--iid-panel)]/60 p-6 text-center">
        <p className="text-sm font-semibold">Your office is empty</p>
        <p className="text-xs muted mt-2">Hire at least one department above. Only hired teammates appear on the floor.</p>
      </div>
    );
  }

  const phaseLabel = PHASE_LABELS[phase] || phase;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--iid-blue)]">{phaseLabel}</p>
        <p className="text-xs muted">{members.length - 1} hired | {bubbles.size} active now</p>
      </div>
      <div
        className="relative rounded-2xl border border-[var(--iid-line)] p-4 md:p-6 overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(11,95,255,0.12), transparent 55%), linear-gradient(180deg, #0f1728 0%, #0a1020 100%)",
        }}
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-5">
          {members.map((member) => {
            const bubble = bubbles.get(member.id);
            const task = taskByMember.get(member.id);
            const talking = Boolean(bubble);
            const running = officeRunning && talking;
            const status = memberStatus(task, talking, running);
            const isLeader = member.is_leader || member.id === "taylor";
            return (
              <button
                key={member.id}
                type="button"
                onClick={() => onSelectMember?.(member.id)}
                className="group relative flex flex-col items-center text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--iid-blue)] rounded-xl"
              >
                {bubble ? (
                  <div className="absolute -top-2 left-1/2 z-20 w-[min(220px,92vw)] -translate-x-1/2 rounded-xl border border-[var(--iid-blue)]/40 bg-[var(--iid-panel-2)] px-3 py-2 text-[11px] leading-snug shadow-lg">
                    <span className="line-clamp-3 text-[var(--iid-text)]">{bubble}</span>
                  </div>
                ) : null}
                <div
                  className={`relative mt-6 flex h-16 w-16 items-center justify-center rounded-2xl border-2 text-sm font-bold transition-transform group-hover:scale-105 ${
                    isLeader
                      ? "border-violet-400 bg-gradient-to-br from-violet-600/40 to-indigo-700/40"
                      : status === "working" || status === "talking"
                        ? "border-[var(--iid-blue)] bg-[var(--iid-blue)]/20"
                        : status === "done"
                          ? "border-emerald-500/50 bg-emerald-500/10"
                          : "border-[var(--iid-line)] bg-[var(--iid-panel)]"
                  }`}
                >
                  {initials(member.name)}
                  {(status === "working" || status === "talking") && (
                    <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-[var(--iid-blue)] animate-pulse" />
                  )}
                </div>
                <p className="mt-2 text-center text-xs font-semibold leading-tight">{shortName(member.name)}</p>
                <p className="text-[10px] muted text-center">{member.department || member.role}</p>
                {task ? (
                  <p className="mt-1 text-[10px] text-center text-[var(--iid-muted)] line-clamp-2 px-1">
                    {String(task.title || "")}
                    <span className="block opacity-70">({String(task.status || "queued")})</span>
                  </p>
                ) : (
                  <p className="mt-1 text-[10px] text-center muted">Ready</p>
                )}
              </button>
            );
          })}
        </div>
      </div>
      <p className="text-[11px] muted">Click a teammate to chat. Bubbles show who is talking or working right now.</p>
    </div>
  );
}
