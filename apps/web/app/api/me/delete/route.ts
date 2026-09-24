import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl, redirectToPath } from "@/lib/session";

export async function POST(request: Request) {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const body = await request.json().catch(() => ({ confirm: "DELETE" }));
  const response = await fetch(`${apiBaseUrl()}/api/v1/me`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    return new NextResponse(text, { status: response.status });
  }
  const out = redirectToPath("/sign-in");
  out.cookies.set(ACCESS_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return out;
}
