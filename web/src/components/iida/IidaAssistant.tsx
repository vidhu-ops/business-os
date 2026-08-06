"use client";

import { IidaMascot } from "@/components/iida/IidaMascot";
import { api, getToken, type User } from "@/lib/api";
import {
  collectSectionNodes,
  firstNameFrom,
  readScreenSummary,
  sectionCueFromElement,
  tourForPath,
  type SectionCue,
} from "@/lib/iida-guide";
import type { IidaMood } from "@/lib/iida-mascot";
import {
  friendReplyLocal,
  friendStuckNudge,
  moodForContext,
  pickGame,
  type GameDef,
} from "@/lib/iida-personality";
import {
  journeySummary,
  loadJourney,
  recordChat,
  recordGame,
  recordIdle,
  recordPath,
  recordSection,
  saveJourney,
  setMood,
  shouldOfferGame,
  type IidaJourney,
} from "@/lib/iida-session";
import { Send, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
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
  const pathname = usePathname() || "/";
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [tip, setTip] = useState("");
  const [actions, setActions] = useState<Action[]>([]);
  const [chat, setChat] = useState<Turn[]>([]);
  const [sectionTip, setSectionTip] = useState("");
  const [pulse, setPulse] = useState(false);
  const [mood, setMoodState] = useState<IidaMood>("happy");
  const [journey, setJourney] = useState<IidaJourney | null>(null);
  const [activeGame, setActiveGame] = useState<GameDef | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const seenSections = useRef<Set<string>>(new Set());
  const lastSectionId = useRef("");
  const journeyRef = useRef<IidaJourney | null>(null);

  const projectId = useMemo(() => {
    if (typeof window === "undefined") return "";
    try {
      return new URLSearchParams(window.location.search).get("project") || "";
    } catch {
      return "";
    }
  }, [pathname]);
  const authed = Boolean(getToken() || email || user?.email);
  const tour = useMemo(() => tourForPath(pathname), [pathname]);
  const first = firstNameFrom(email || user?.email || "", user?.name);
  const liveTip =
    sectionTip ||
    tip ||
    `Hey ${first} - I am IIDA, your AI business partner on ${tour.title}.`;

  const applyJourney = useCallback((next: IidaJourney) => {
    journeyRef.current = next;
    setJourney(next);
    saveJourney(next);
    setMoodState(next.mood);
  }, []);

  const bumpMood = useCallback(
    (m: IidaMood) => {
      const base = journeyRef.current || loadJourney();
      applyJourney(setMood(base, m));
    },
    [applyJourney],
  );

  useEffect(() => {
    const j = recordPath(loadJourney(), pathname || "/");
    applyJourney(j);
  }, [pathname, applyJourney]);

  useEffect(() => {
    if (!getToken() && !email) {
      setUser(null);
      return;
    }
    api.me().then(setUser).catch(() => setUser(null));
  }, [email, pathname]);

  // Idle / stuck sensing
  useEffect(() => {
    let idleTimer: number | undefined;
    const arm = () => {
      window.clearTimeout(idleTimer);
      idleTimer = window.setTimeout(() => {
        const base = journeyRef.current || loadJourney();
        const next = recordIdle(base, pathname || "/");
        applyJourney(next);
        bumpMood(moodForContext({ vibe: next.vibe, pulseTip: true }));
        const nudge = friendStuckNudge(first, next, tour.title);
          if (nudge) {
          setTip(nudge);
          setSectionTip(nudge);
          setPulse(true);
          window.setTimeout(() => setPulse(false), 700);
          setActions([
            { id: "play_game", label: "Let's play" },
            { id: "what_next", label: "Just next step" },
            { id: "what_is_this", label: "Explain page" },
          ]);
        }
      }, 45_000);
    };
    const onAct = () => arm();
    arm();
    window.addEventListener("pointerdown", onAct);
    window.addEventListener("keydown", onAct);
    window.addEventListener("scroll", onAct, { passive: true });
    return () => {
      window.clearTimeout(idleTimer);
      window.removeEventListener("pointerdown", onAct);
      window.removeEventListener("keydown", onAct);
      window.removeEventListener("scroll", onAct);
    };
  }, [pathname, first, tour.title, applyJourney, bumpMood]);

  // Keep explaining while the panel is closed — nudge, don't go silent.
  useEffect(() => {
    if (open) return;
    const tick = window.setInterval(() => {
      const j = journeyRef.current || loadJourney();
      const line =
        friendStuckNudge(first, j, tour.title) ||
        "Still with you on " + tour.title + ": " + tour.hook + " Tap Explain if you want me to walk this screen.";
      setTip(line);
      setSectionTip(line);
      setPulse(true);
      window.setTimeout(() => setPulse(false), 700);
      bumpMood(moodForContext({ vibe: j.vibe, pulseTip: true }));
      setActions([
        { id: "what_is_this", label: "Explain this" },
        { id: "what_next", label: "What next?" },
        { id: "play_game", label: "Let's play" },
        ...((user?.is_demo || (!authed && !(pathname || "").startsWith("/login")))
          ? [{ id: "go_signup", label: "Sign up free" }]
          : []),
      ]);
    }, 35_000);
    return () => window.clearInterval(tick);
  }, [open, first, tour.title, tour.hook, pathname, bumpMood, user?.is_demo, authed]);

  // Soft-open once per browser session so people notice IIDA is interactable.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const key = "iida_soft_open_session";
    if (sessionStorage.getItem(key)) return;
    const t = window.setTimeout(() => {
      sessionStorage.setItem(key, "1");
      setOpen(true);
      bumpMood("curious");
      const explain =
        "Quick orientation: you are on " + tour.title + ". " + tour.blurb + " " + tour.hook;
      setChat((prev) => {
        if (prev.some((x) => x.role === "iida" && x.text.includes("Quick orientation"))) return prev;
        return [...prev, { role: "iida", text: explain }];
      });
      setActions([
        { id: "what_is_this", label: "Explain more" },
        { id: "what_next", label: "What next?" },
        { id: "play_game", label: "Let's play" },
      ]);
    }, 3500);
    return () => window.clearTimeout(t);
  }, [pathname, bumpMood, tour.title, tour.blurb, tour.hook]);

  const pushIidaNote = useCallback(
    (text: string, intoChat: boolean, nextMood?: IidaMood) => {
      const clean = stripMd(text);
      if (!clean) return;
      setTip(clean);
      setSectionTip(clean);
      setPulse(true);
      window.setTimeout(() => setPulse(false), 700);
      if (nextMood) bumpMood(nextMood);
      if (intoChat) {
        setChat((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "iida" && last.text === clean) return prev;
          return [...prev.slice(-40), { role: "iida", text: clean }];
        });
      }
    },
    [bumpMood],
  );

  const startGame = useCallback(() => {
    const base = journeyRef.current || loadJourney();
    const game = pickGame(base);
    applyJourney(recordGame(base, game.id));
    setActiveGame(game);
    setOpen(true);
    bumpMood("excited");
    setChat((prev) => [
      ...prev,
      { role: "iida", text: `${game.title}: ${game.prompt}` },
    ]);
    setActions(game.choices.map((c) => ({ id: `game_${game.id}__${c.id}`, label: c.label })));
  }, [applyJourney, bumpMood]);

  const refreshTip = useCallback(async () => {
    const j = journeyRef.current || loadJourney();
    const localFallback = () => {
      const nudge = friendStuckNudge(first, j, tour.title);
      const fallback =
        nudge ||
        `Hey ${first} - ${tour.title}. ${tour.hook} I am keeping your session trail so I can talk like a partner, not a stranger.`;
      const base: Action[] = [
        { id: "what_is_this", label: "Explain this" },
        { id: "what_next", label: "What next?" },
      ];
      if (shouldOfferGame(j)) base.unshift({ id: "play_game", label: "Let's play" });
      if (!authed) {
        base.push({ id: "go_signup", label: "Sign up free" });
        base.push({ id: "go_demo", label: "Try demo" });
        if (!(pathname || "").startsWith("/pricing")) base.push({ id: "go_pricing", label: "See pricing" });
      } else if (user?.is_demo || (email || "").includes("demo@")) {
        base.push({ id: "go_signup", label: "Sign up free" });
      } else if ((pathname || "").startsWith("/app/team")) {
        base.push({ id: "brief_taylor", label: "Brief Taylor" });
      }
      setActions(base);
      pushIidaNote(fallback, true, moodForContext({ vibe: j.vibe, open: true }));
    };

    if (!authed) {
      localFallback();
      return;
    }
    try {
      const screen = `${readScreenSummary()} | ${journeySummary(j, first)}`.slice(0, 400);
      const data = await api.iidaTip(pathname || "/app/dashboard", screen);
      const msg = stripMd(String(data.message || ""));
      const acts = (data.actions as Action[]) || [];
      if (shouldOfferGame(j) && !acts.some((a) => a.id === "play_game")) {
        acts.unshift({ id: "play_game", label: "Let's play" });
      }
      setActions(acts);
      pushIidaNote(msg, true, "happy");
    } catch {
      localFallback();
    }
  }, [pathname, first, tour.title, tour.hook, pushIidaNote, authed]);

  useEffect(() => {
    seenSections.current.clear();
    lastSectionId.current = "";
    setChat([]);
    setSectionTip("");
    setActiveGame(null);
    const t = window.setTimeout(() => {
      refreshTip().catch(() => null);
    }, 280);
    return () => window.clearTimeout(t);
  }, [pathname, refreshTip]);

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
          const cue: SectionCue = sectionCueFromElement(top, tour.title, pathname || "");
          if (cue.id === lastSectionId.current) return;
          window.clearTimeout(debounce);
          debounce = window.setTimeout(() => {
            lastSectionId.current = cue.id;
            const firstVisit = !seenSections.current.has(cue.id);
            seenSections.current.add(cue.id);
            const base = journeyRef.current || loadJourney();
            applyJourney(recordSection(base, cue.id, pathname || "/"));
            pushIidaNote(cue.explain, firstVisit, firstVisit ? "curious" : "happy-blink");
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
  }, [pathname, tour.title, pushIidaNote, applyJourney]);

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, open, loading, activeGame]);

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
    const base = journeyRef.current || loadJourney();
    applyJourney(recordChat(base, message, pathname || "/"));
    bumpMood(moodForContext({ userText: message, vibe: (journeyRef.current || base).vibe }));
    setLoading(true);
    try {
      if (!authed) {
        const local = friendReplyLocal({
          message,
          first,
          path: pathname || "/",
          tourTitle: tour.title,
          tourHook: tour.hook,
          journey: journeyRef.current || base,
        });
        setChat((prev) => [...prev, { role: "iida", text: local.reply }]);
        bumpMood(local.mood);
        const acts: Action[] = [
          { id: "what_is_this", label: "What is this?" },
          { id: "what_next", label: "What next?" },
        ];
        if (local.offerGame) acts.unshift({ id: "play_game", label: "Let's play" });
        setActions(acts);
        if (local.offerGame) startGame();
        if (local.href) runHandoff({ type: "navigate", href: local.href });
        return;
      }
      const j = journeyRef.current || base;
      const data = await api.iidaChat({
        message,
        path: pathname || "/app/dashboard",
        screen_summary: `${readScreenSummary()} | ${journeySummary(j, first)} | watching: ${sectionTip || tip}`.slice(0, 480),
        project_id: projectId || undefined,
      });
      setChat((prev) => [...prev, { role: "iida", text: stripMd(String(data.reply || "")) }]);
      bumpMood(moodForContext({ vibe: j.vibe, userText: message }));
      const acts = Array.isArray(data.actions) ? (data.actions as Action[]) : [];
      if (shouldOfferGame(j) && !acts.some((a) => a.id === "play_game")) {
        acts.unshift({ id: "play_game", label: "Let's play" });
      }
      setActions(acts);
      if (data.handoff) runHandoff(data.handoff as Handoff);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "I hit a snag - try again in a moment.";
      setChat((prev) => [...prev, { role: "iida", text: msg }]);
      bumpMood("surprised");
    } finally {
      setLoading(false);
    }
  }

  function onGameChoice(choiceId: string) {
    const game = activeGame;
    const choice = game?.choices.find((c) => c.id === choiceId);
    if (!choice || !game) return;
    setChat((prev) => [
      ...prev,
      { role: "user", text: choice.label },
      { role: "iida", text: choice.reply },
    ]);
    bumpMood(choice.mood);
    setActiveGame(null);
    setActions([
      { id: "what_next", label: "What next?" },
      { id: "play_game", label: "Play again" },
    ]);
    if (choice.href) runHandoff({ type: "navigate", href: choice.href });
  }

  function onAction(id: string) {
    if (id === "play_game") {
      startGame();
      return;
    }
    if (id.startsWith("game_")) {
      const rest = id.slice("game_".length);
      const [, choiceId] = rest.split("__");
      onGameChoice(choiceId);
      return;
    }
    if (id === "brief_taylor" || id === "open_taylor") {
      void sendMessage("Brief Taylor for me");
      return;
    }
    if (id === "go_signup") {
      runHandoff({ type: "navigate", href: "/login?mode=register" });
      return;
    }
    if (id === "go_demo") {
      runHandoff({ type: "navigate", href: "/login" });
      return;
    }
    if (id === "go_pricing") {
      runHandoff({ type: "navigate", href: "/pricing" });
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

  const displayMood = loading ? "thinking" : mood;

  return (
    <div className="iida-popup-root" data-iida-root>
            {!open && liveTip ? (
        <div className={`iida-float-card${pulse ? " iida-float-card-pulse" : ""}`}>
          <button type="button" className="iida-float-card-btn" onClick={() => { setOpen(true); bumpMood("curious"); void sendMessage("Explain this page simply and tell me the best next step."); }}>
            <span className="iida-float-tip-row">
              <IidaMascot mood={displayMood} size={36} bob={false} />
              <span className="min-w-0">
                <span className="iida-float-tip-label">IIDA · tap me · I explain</span>
                <span className="iida-float-tip-text">
                  {liveTip.slice(0, 160)}
                  {liveTip.length > 160 ? "..." : ""}
                </span>
              </span>
            </span>
          </button>
          <div className="iida-float-quick">
            <button type="button" className="iida-chip" onClick={() => { setOpen(true); void sendMessage("Explain this page simply and tell me the best next step."); }}>Explain</button>
            <button type="button" className="iida-chip" onClick={() => { setOpen(true); void sendMessage("What should I do next?"); }}>Next step</button>
            <button type="button" className="iida-chip" onClick={() => startGame()}>Let's play</button>
            {(user?.is_demo || !authed) && !(pathname || "").startsWith("/login") ? (
              <button type="button" className="iida-chip" onClick={() => runHandoff({ type: "navigate", href: "/login?mode=register" })}>Sign up</button>
            ) : null}
          </div>
        </div>
      ) : null}

      {open ? (
        <div className="iida-popup">
          <div className="iida-popup-head">
            <div className="flex items-center gap-2 min-w-0">
              <IidaMascot mood={displayMood} size={44} />
              <div className="min-w-0">
                <p className="font-semibold text-sm">IIDA</p>
                <p className="text-[11px] muted truncate">
                  Friend + business partner · {first} · {tour.title}
                </p>
              </div>
            </div>
            <button type="button" className="iid-btn iid-btn-ghost text-xs px-2" onClick={() => setOpen(false)} aria-label="Close IIDA">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="iida-popup-body">
            {chat.length === 0 ? (
              <p className="text-xs muted">
                I watch your journey, match your energy, and unstick you with a game when you stall.
              </p>
            ) : null}
            {chat.map((t, i) => (
              <div key={i} className={`flex ${t.role === "user" ? "justify-end" : "justify-start"} gap-1.5 items-end`}>
                {t.role === "iida" ? <IidaMascot mood={displayMood} size={22} bob={false} /> : null}
                <div className={`iida-msg ${t.role === "user" ? "iida-msg-user" : "iida-msg-bot"}`}>{t.text}</div>
              </div>
            ))}
            {loading ? (
              <p className="text-xs muted flex items-center gap-2">
                <IidaMascot mood="thinking" size={22} bob={false} /> IIDA is thinking...
              </p>
            ) : null}
            <div ref={endRef} />
          </div>

          {actions.length > 0 ? (
            <div className="iida-popup-chips">
              {actions.slice(0, 5).map((a) => (
                <button key={a.id} type="button" className="iida-chip" disabled={loading} onClick={() => onAction(a.id)}>
                  {a.label}
                </button>
              ))}
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
              placeholder="Talk to IIDA like a partner..."
              disabled={loading}
              aria-label="Message IIDA"
            />
            <button type="submit" className="iida-send" disabled={loading || !input.trim()} aria-label="Send">
              <Send className="w-4 h-4" />
            </button>
          </form>
          {journey ? (
            <p className="iida-journey-foot">
              Session vibe: {journey.vibe} · {journey.pathOrder.slice(-2).join(" -> ") || "just started"}
            </p>
          ) : null}
        </div>
      ) : null}

      <button
        type="button"
        className={`iida-fab iida-fab-mascot${open ? " iida-fab-open" : ""}${pulse ? " iida-fab-pulse" : ""}`}
        onClick={() => {
          setOpen((v) => !v);
          bumpMood(open ? "happy" : "excited");
        }}
        aria-label={open ? "Close IIDA" : "Open IIDA"}
      >
        {open ? (
          <span className="iida-fab-close-x">
            <X className="w-5 h-5" />
          </span>
        ) : (
          <IidaMascot mood={displayMood} size={64} />
        )}
        <span className="iida-fab-label">{open ? "Close" : "IIDA"}</span>
      </button>
    </div>
  );
}