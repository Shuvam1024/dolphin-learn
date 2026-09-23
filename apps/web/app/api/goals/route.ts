import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

export async function POST(request: Request) {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json(
      { error: { code: "unauthorized", message: "Sign in required" } },
      { status: 401 },
    );
  }
  const body = await request.text();
  const upstream = await fetch(`${apiBaseUrl()}/api/v1/goals`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body,
    cache: "no-store",
  });
  const payload = await upstream.text();
  return new NextResponse(payload, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
