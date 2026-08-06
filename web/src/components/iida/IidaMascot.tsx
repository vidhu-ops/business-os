"use client";

import { IIDA_MOOD_SRC, type IidaMood } from "@/lib/iida-mascot";
import { useEffect, useState } from "react";

type Props = {
  mood: IidaMood;
  size?: number;
  bob?: boolean;
  className?: string;
  alt?: string;
};

export function IidaMascot({ mood, size = 64, bob = true, className = "", alt = "IIDA" }: Props) {
  const [blink, setBlink] = useState(false);
  const idleBlink = mood === "happy" || mood === "happy-blink";

  useEffect(() => {
    if (!idleBlink) {
      setBlink(false);
      return;
    }
    let timeout: number;
    const loop = () => {
      timeout = window.setTimeout(() => {
        setBlink(true);
        timeout = window.setTimeout(() => {
          setBlink(false);
          loop();
        }, 280);
      }, 3200 + Math.random() * 2400);
    };
    loop();
    return () => window.clearTimeout(timeout);
  }, [idleBlink]);

  const src = IIDA_MOOD_SRC[idleBlink && blink ? "happy-blink" : mood] || IIDA_MOOD_SRC.happy;

  return (
    <span className={`iida-mascot${bob ? " iida-mascot-bob" : ""}${className ? ` ${className}` : ""}`} style={{ width: size, height: size }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} width={size} height={size} draggable={false} className="iida-mascot-img" />
    </span>
  );
}