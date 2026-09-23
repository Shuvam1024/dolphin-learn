import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

export async function POST(request: Request) {
  const form = await request.formData();
  const email = String(form.get("email") ?? "").trim();
  const signIn = new URL("/sign-in", request.url);

  const issued = await fetch(`${apiBaseUrl()}/api/v1/dev/token`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email }),
    cache: "no-store",
  });

  if (!issued.ok) {
    signIn.searchParams.set("error", "1");
    return NextResponse.redirect(signIn, 303);
  }

  const body = (await issued.json()) as { access_token?: string };
  if (!body.access_token) {
    signIn.searchParams.set("error", "1");
    return NextResponse.redirect(signIn, 303);
  }

  const response = NextResponse.redirect(new URL("/app", request.url), 303);
  response.cookies.set(ACCESS_COOKIE, body.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: 60 * 60,
  });
  return response;
}
