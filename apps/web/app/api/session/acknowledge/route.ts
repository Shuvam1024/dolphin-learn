import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

export async function POST(request: Request) {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/sign-in", request.url), 303);
  }
  const recorded = await fetch(`${apiBaseUrl()}/api/v1/me/adult-acknowledgment`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const dest = recorded.ok ? "/app" : "/app";
  return NextResponse.redirect(new URL(dest, request.url), 303);
}
