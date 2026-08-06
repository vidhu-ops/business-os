import type { IidaMood } from "@/lib/iida-mascot";

const KEY = "iida_journey_v1";

export type JourneyEvent = {
  t: number;
  kind: "path" | "section" | "chat" | "idle" | "game" | "mood" | "note";
  path?: string;
  detail?: string;
};

export type IidaJourney = {
  startedAt: number;
  lastActiveAt: number;
  pathCounts: Record<string, number>;
  pathOrder: string[];
  sections: string[];
  chatTurns: number;
  idleHits: number;
  stuckHits: number;
  gamesPlayed: number;
  lastGameAt: number;
  mood: IidaMood;
  events: JourneyEvent[];
  vibe: "curious" | "rushing" | "stuck" | "shipping" | "browsing";
};

function blank(): IidaJourney {
  const now = Date.now();
  return {
    startedAt: now,
    lastActiveAt: now,
    pathCounts: {},
    pathOrder: [],
    sections: [],
    chatTurns: 0,
    idleHits: 0,
    stuckHits: 0,
    gamesPlayed: 0,
    lastGameAt: 0,
    mood: "happy",
    events: [],
    vibe: "curious",
  };
}

export function loadJourney(): IidaJourney {
  if (typeof window === "undefined") return blank();
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return blank();
    const parsed = JSON.parse(raw) as IidaJourney;
    if (!parsed?.startedAt) return blank();
    return { ...blank(), ...parsed, events: (parsed.events || []).slice(-80) };
  } catch {
    return blank();
  }
}

export function saveJourney(j: IidaJourney) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify({ ...j, events: j.events.slice(-80) }));
  } catch {
    /* ignore quota */
  }
}

function pushEvent(j: IidaJourney, ev: JourneyEvent): IidaJourney {
  return { ...j, lastActiveAt: Date.now(), events: [...j.events.slice(-79), ev] };
}

export function recordPath(j: IidaJourney, path: string): IidaJourney {
  const pathCounts = { ...j.pathCounts, [path]: (j.pathCounts[path] || 0) + 1 };
  const pathOrder = j.pathOrder[j.pathOrder.length - 1] === path ? j.pathOrder : [...j.pathOrder.slice(-19), path];
  let vibe = j.vibe;
  if (pathCounts[path] >= 3) vibe = "stuck";
  else if (pathOrder.length >= 5 && new Set(pathOrder.slice(-5)).size >= 4) vibe = "browsing";
  else if (/\/app\/(research|plan|team|audit)/.test(path)) vibe = "shipping";
  return pushEvent(
    { ...j, pathCounts, pathOrder, vibe },
    { t: Date.now(), kind: "path", path, detail: `visit#${pathCounts[path]}` },
  );
}

export function recordSection(j: IidaJourney, sectionId: string, path: string): IidaJourney {
  const sections = j.sections.includes(sectionId) ? j.sections : [...j.sections.slice(-39), sectionId];
  return pushEvent({ ...j, sections }, { t: Date.now(), kind: "section", path, detail: sectionId.slice(0, 80) });
}

export function recordChat(j: IidaJourney, text: string, path: string): IidaJourney {
  const stuck = /stuck|confused|lost|help|idk|don't know|dont know|overwhelm/i.test(text);
  return pushEvent(
    {
      ...j,
      chatTurns: j.chatTurns + 1,
      stuckHits: j.stuckHits + (stuck ? 1 : 0),
      vibe: stuck ? "stuck" : j.vibe === "stuck" ? "curious" : j.vibe,
    },
    { t: Date.now(), kind: "chat", path, detail: text.slice(0, 120) },
  );
}

export function recordIdle(j: IidaJourney, path: string): IidaJourney {
  const idleHits = j.idleHits + 1;
  const stuckHits = idleHits >= 2 ? j.stuckHits + 1 : j.stuckHits;
  return pushEvent(
    { ...j, idleHits, stuckHits, vibe: idleHits >= 2 ? "stuck" : j.vibe },
    { t: Date.now(), kind: "idle", path, detail: `idle#${idleHits}` },
  );
}

export function recordGame(j: IidaJourney, name: string): IidaJourney {
  return pushEvent(
    {
      ...j,
      gamesPlayed: j.gamesPlayed + 1,
      lastGameAt: Date.now(),
      vibe: "curious",
      mood: "excited",
    },
    { t: Date.now(), kind: "game", detail: name },
  );
}

export function setMood(j: IidaJourney, mood: IidaMood): IidaJourney {
  if (j.mood === mood) return j;
  return pushEvent({ ...j, mood }, { t: Date.now(), kind: "mood", detail: mood });
}

export function journeySummary(j: IidaJourney, firstName: string): string {
  const mins = Math.max(1, Math.round((Date.now() - j.startedAt) / 60000));
  const topPath = Object.entries(j.pathCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "home";
  const recent = j.pathOrder.slice(-3).join(" -> ") || topPath;
  return [
    `${firstName} session ~${mins}m`,
    `vibe:${j.vibe}`,
    `path trail: ${recent}`,
    `chats:${j.chatTurns} sections:${j.sections.length} stuckSignals:${j.stuckHits}`,
  ].join(" | ");
}

export function shouldOfferGame(j: IidaJourney): boolean {
  if (Date.now() - j.lastGameAt < 8 * 60 * 1000) return false;
  return j.stuckHits >= 1 || j.idleHits >= 2 || j.vibe === "stuck" || (j.chatTurns >= 2 && j.pathOrder.length <= 2);
}