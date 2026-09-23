import { cookies } from "next/headers";

import { ACCESS_COOKIE, apiBaseUrl, redirectToPath } from "@/lib/session";

export async function POST() {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return redirectToPath("/sign-in");
  }
  await fetch(`${apiBaseUrl()}/api/v1/me/adult-acknowledgment`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  return redirectToPath("/app");
}
