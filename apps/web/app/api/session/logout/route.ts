import { cookies } from "next/headers";

import { ACCESS_COOKIE, apiBaseUrl, redirectToPath } from "@/lib/session";

export async function POST() {
  const jar = await cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (token) {
    try {
      await fetch(`${apiBaseUrl()}/api/v1/auth/revoke`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
    } catch {
      // Cookie clear still happens below.
    }
  }
  const response = redirectToPath("/sign-in");
  response.cookies.set(ACCESS_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: 0,
  });
  return response;
}
