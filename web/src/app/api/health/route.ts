import { NextResponse } from "next/server";

const NO_STORE = {
  "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
  Pragma: "no-cache",
};

/** Lightweight health for Render / keep-warm — must hit origin (not CDN cache). */
export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "iidatech-web",
      ts: Date.now(),
      git: process.env.RENDER_GIT_COMMIT || process.env.RENDER_GIT_COMMIT_SHA || "",
      repo: process.env.RENDER_GIT_REPO_SLUG || "",
    },
    { headers: NO_STORE },
  );
}

export async function HEAD() {
  return new NextResponse(null, { status: 200, headers: NO_STORE });
}
