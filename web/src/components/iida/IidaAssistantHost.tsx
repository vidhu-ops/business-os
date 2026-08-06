"use client";

import { Suspense } from "react";
import { IidaAssistant } from "@/components/iida/IidaAssistant";

/** Site-wide host so Your assistant appears on marketing + signed-in pages. */
export function IidaAssistantHost() {
  return (
    <Suspense fallback={null}>
      <IidaAssistant />
    </Suspense>
  );
}
