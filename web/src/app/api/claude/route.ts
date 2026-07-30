import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const apiKey =
      (req.headers.get("x-api-key") || "").trim() ||
      (process.env.ANTHROPIC_API_KEY || "").trim() ||
      (process.env.VITE_CLAUDE_API_KEY || "").trim() ||
      (process.env.CLAUDE_API_KEY || "").trim();

    if (!apiKey) {
      return NextResponse.json(
        { error: "Missing Claude API key (set ANTHROPIC_API_KEY on the server)" },
        { status: 400 },
      );
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120_000);

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") || "application/json",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Proxy error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
