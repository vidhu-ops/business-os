export type IidaMood =
  | "happy"
  | "excited"
  | "love"
  | "curious"
  | "thinking"
  | "focused"
  | "surprised"
  | "happy-blink";

export const IIDA_MOOD_SRC: Record<IidaMood, string> = {
  happy: "/iida/moods/happy.png",
  excited: "/iida/moods/excited.png",
  love: "/iida/moods/love.png",
  curious: "/iida/moods/curious.png",
  thinking: "/iida/moods/thinking.png",
  focused: "/iida/moods/focused.png",
  surprised: "/iida/moods/surprised.png",
  "happy-blink": "/iida/moods/happy-blink.png",
};

export const IIDA_MOOD_LABEL: Record<IidaMood, string> = {
  happy: "Happy",
  excited: "Excited",
  love: "Love",
  curious: "Curious",
  thinking: "Thinking",
  focused: "Focused",
  surprised: "Surprised",
  "happy-blink": "Sparkle",
};