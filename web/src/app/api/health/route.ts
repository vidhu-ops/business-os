import { NextResponse } from "next/server";

/** Lightweight health for Render — confirms Next.js is serving (not the Python API). */
export async function GET() {
  return NextResponse.json({ status: "ok", service: "iidatech-web" });
}

export async function HEAD() {
  return new NextResponse(null, { status: 200 });
}