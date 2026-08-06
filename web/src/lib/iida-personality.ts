import type { IidaMood } from "@/lib/iida-mascot";
import type { IidaJourney } from "@/lib/iida-session";
import { shouldOfferGame } from "@/lib/iida-session";

export type GameDef = {
  id: string;
  title: string;
  prompt: string;
  choices: Array<{ id: string; label: string; reply: string; mood: IidaMood; href?: string }>;
};

export const IIDA_GAMES: GameDef[] = [
  {
    id: "this_or_that",
    title: "This or that",
    prompt: "Friend check-in: pick one. No overthinking - gut first.",
    choices: [
      {
        id: "audit",
        label: "Stress-test my company",
        reply: "Love that. Audit first means we start from truth, not vibes. I will walk you in.",
        mood: "focused",
        href: "/app/audit",
      },
      {
        id: "research",
        label: "Map the market",
        reply: "Nice. Tight research beats guessing. Scope topic + country, then generate once.",
        mood: "curious",
        href: "/app/research",
      },
      {
        id: "office",
        label: "Staff the office",
        reply: "Bold. Hire lean, then Approvals keep you safe. Want me to open Employee OS?",
        mood: "excited",
        href: "/app/team",
      },
    ],
  },
  {
    id: "one_priority",
    title: "One priority",
    prompt: "Business partner game: if you could only finish ONE thing in the next hour, what wins?",
    choices: [
      {
        id: "clarity",
        label: "Clarity (research/audit)",
        reply: "Clarity it is. Clarity compounds - messy action without it burns credits.",
        mood: "thinking",
        href: "/app/audit",
      },
      {
        id: "plan",
        label: "A plan people can staff",
        reply: "Plan mode. After it is readable, we give Taylor three owners. Deal?",
        mood: "focused",
        href: "/app/plan",
      },
      {
        id: "ship",
        label: "Ship something tiny",
        reply: "Shipping energy. Tiny + done beats perfect + stuck. I am with you.",
        mood: "excited",
        href: "/app/team",
      },
    ],
  },
  {
    id: "energy_check",
    title: "Energy check",
    prompt: "Real talk - how are you showing up right now?",
    choices: [
      {
        id: "tired",
        label: "Tired / foggy",
        reply: "Heard. Then we do the smallest high-signal move only - no marathon. Want a 60-second pick?",
        mood: "love",
      },
      {
        id: "fired",
        label: "Fired up",
        reply: "Yes. Channel that into one scoped run, not five tabs. I will keep you honest.",
        mood: "excited",
      },
      {
        id: "unsure",
        label: "Unsure what matters",
        reply: "Unsure is data. We narrow with This-or-that - I am your co-founder brain for a minute.",
        mood: "curious",
      },
    ],
  },
];

export function pickGame(journey: IidaJourney): GameDef {
  if (journey.vibe === "stuck") return IIDA_GAMES[0];
  if (journey.idleHits >= 2) return IIDA_GAMES[2];
  return IIDA_GAMES[journey.gamesPlayed % IIDA_GAMES.length];
}

export function moodForContext(opts: {
  loading?: boolean;
  open?: boolean;
  vibe: IidaJourney["vibe"];
  justGame?: boolean;
  pulseTip?: boolean;
  userText?: string;
}): IidaMood {
  if (opts.loading) return "thinking";
  if (opts.justGame) return "excited";
  const t = (opts.userText || "").toLowerCase();
  if (/love|thanks|thank you|awesome|great/.test(t)) return "love";
  if (/stuck|confused|lost|overwhelm|idk/.test(t)) return "curious";
  if (/go|build|hire|run|ship|next/.test(t)) return "focused";
  if (/wow|whoa|really|\?!/.test(t)) return "surprised";
  if (opts.vibe === "stuck") return "curious";
  if (opts.vibe === "shipping") return "focused";
  if (opts.vibe === "browsing") return "happy-blink";
  if (opts.pulseTip) return "happy";
  if (opts.open) return "happy";
  return "happy";
}

export function friendStuckNudge(first: string, journey: IidaJourney, pageTitle: string): string {
  if (journey.vibe === "stuck" || journey.idleHits >= 2) {
    return `Hey ${first} - you have been circling ${pageTitle}. I am still here as your partner, not a lecture bot. Want to play a 20-second game to unstick, or tell me what feels heavy?`;
  }
  if (shouldOfferGame(journey)) {
    return `${first}, quick friend interrupt: brains stall under too many tabs. Want a tiny this-or-that game, or a straight next move on ${pageTitle}?`;
  }
  return "";
}

export function friendReplyLocal(opts: {
  message: string;
  first: string;
  path: string;
  tourTitle: string;
  tourHook: string;
  journey: IidaJourney;
}): { reply: string; mood: IidaMood; offerGame?: boolean; href?: string } {
  const text = opts.message.toLowerCase();
  const trail = opts.journey.pathOrder.slice(-3).join(" -> ") || opts.path;

  if (/play|game|unstick|bored|stuck/.test(text)) {
    return {
      reply: `Yes - let's play. Pick This-or-that, One priority, or Energy check. I am your friend first, business partner second when you freeze.`,
      mood: "excited",
      offerGame: true,
    };
  }
  if (/how am i doing|my journey|where was i|session/.test(text)) {
    return {
      reply: `${opts.first}, here is what I noticed: vibe ${opts.journey.vibe}, trail ${trail}, ${opts.journey.chatTurns} chats with me, ${opts.journey.sections.length} sections noticed. On ${opts.tourTitle}: ${opts.tourHook}`,
      mood: "thinking",
    };
  }
  if (/friend|lonely|talk|vent/.test(text)) {
    return {
      reply: `I am here. Building is lonely sometimes. Say what is noisy in your head - then we turn one piece into a next click. No judgment.`,
      mood: "love",
    };
  }
  if (/what is this|where am i|explain/.test(text)) {
    return { reply: `${opts.tourTitle}. ${opts.tourHook}`, mood: "curious" };
  }
  if (/price|pricing|credit|tier/.test(text)) {
    return {
      reply: "Pricing is runway. Free/Starter to validate, Growth when the office runs weekly. Want me to open Pricing?",
      mood: "focused",
      href: "/pricing",
    };
  }
  if (/next|should i|help|start/.test(text)) {
    const game = shouldOfferGame(opts.journey);
    return {
      reply: game
        ? `Honest take on ${opts.tourTitle}: ${opts.tourHook} Or we play a tiny decision game so you stop spinning.`
        : `Partner take: ${opts.tourHook}`,
      mood: game ? "curious" : "focused",
      offerGame: game,
    };
  }
  return {
    reply: `Got you on ${opts.tourTitle}. ${opts.tourHook} Tell me if you want a game, a next step, or just a sanity check.`,
    mood: "happy",
    offerGame: shouldOfferGame(opts.journey),
  };
}