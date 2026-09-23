import { ACCESS_COOKIE, redirectToPath } from "@/lib/session";

export async function POST() {
  const response = redirectToPath("/sign-in");
  response.cookies.set(ACCESS_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}
