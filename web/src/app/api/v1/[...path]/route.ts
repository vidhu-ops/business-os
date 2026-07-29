import { NextRequest, NextResponse } from "next/server";

function apiBase(): string {
  return (process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
}

async function proxy(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const suffix = path?.length ? path.join("/") : "";
  const target = `${apiBase()}/api/v1/${suffix}${req.nextUrl.search}`;

  const headers = new Headers();
  const auth = req.headers.get("authorization");
  const contentType = req.headers.get("content-type");
  if (auth) headers.set("authorization", auth);
  if (contentType) headers.set("content-type", contentType);
  const cookie = req.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  const init: RequestInit = { method: req.method, headers, cache: "no-store" };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  try {
    const upstream = await fetch(target, init);
    const body = await upstream.arrayBuffer();
    const out = new Headers();
    const ct = upstream.headers.get("content-type");
    if (ct) out.set("content-type", ct);
    const setCookie = upstream.headers.get("set-cookie");
    if (setCookie) out.set("set-cookie", setCookie);
    return new NextResponse(body, { status: upstream.status, headers: out });
  } catch (err) {
    const message = err instanceof Error ? err.message : "API unreachable";
    return NextResponse.json(
      { detail: `Cannot reach API at ${apiBase()}: ${message}` },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
