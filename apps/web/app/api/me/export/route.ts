import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

export async function GET() {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/me/export`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition": 'attachment; filename="dolphin-export.json"',
    },
  });
}
