"use client";

import { IidaAssistant } from "@/components/iida/IidaAssistant";

/** Always mounted from the root layout — every page, signed-in or not. */
export function IidaAssistantHost() {
  return <IidaAssistant />;
}
