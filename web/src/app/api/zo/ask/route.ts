import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const zoKey =
      (process.env.ZO_API_KEY || "").trim() ||
      (process.env.VITE_ZO_API_KEY || "").trim() ||
      (process.env.NEXT_PUBLIC_ZO_API_KEY || "").trim();

    if (!zoKey) {
      return NextResponse.json({ error: "Missing Zo API key (set ZO_API_KEY)" }, { status: 400 });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120_000);

    const response = await fetch("https://api.zo.computer/zo/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${zoKey}`,
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
