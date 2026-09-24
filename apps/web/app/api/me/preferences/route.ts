import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

export async function PATCH(request: Request) {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const body = await request.json();
  const response = await fetch(`${apiBaseUrl()}/api/v1/me/preferences`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
