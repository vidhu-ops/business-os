export type IidaMood =
  | "happy"
  | "excited"
  | "love"
  | "curious"
  | "thinking"
  | "focused"
  | "surprised"
  | "happy-blink";

/** Cache-bust so redeployed transparent cutouts replace old opaque plates. */
const V = "v2";

export const IIDA_MOOD_SRC: Record<IidaMood, string> = {
  happy: `/iida/moods/happy.png?${V}`,
  excited: `/iida/moods/excited.png?${V}`,
  love: `/iida/moods/love.png?${V}`,
  curious: `/iida/moods/curious.png?${V}`,
  thinking: `/iida/moods/thinking.png?${V}`,
  focused: `/iida/moods/focused.png?${V}`,
  surprised: `/iida/moods/surprised.png?${V}`,
  "happy-blink": `/iida/moods/happy-blink.png?${V}`,
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