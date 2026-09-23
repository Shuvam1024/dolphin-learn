import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

export async function GET() {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json(
      { error: { code: "unauthorized", message: "Sign in required" } },
      { status: 401 },
    );
  }
  const upstream = await fetch(`${apiBaseUrl()}/api/v1/domains`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const payload = await upstream.text();
  return new NextResponse(payload, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
