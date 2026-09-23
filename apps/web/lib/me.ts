import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "./session";

export type Me = {
  id: string;
  auth_subject: string;
  email: string | null;
  profile: {
    adult_acknowledged_at: string | null;
  };
};

export async function loadMe(): Promise<Me> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as Me;
}
