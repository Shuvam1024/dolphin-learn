import { NextResponse } from "next/server";

/** Cookie that holds the API access token. HttpOnly; not a password. */
export const ACCESS_COOKIE = "dolphin_access_token";

/** Relative redirect so the browser stays on the host it used (localhost vs 127.0.0.1). */
export function redirectToPath(path: string, status = 303) {
  return new NextResponse(null, {
    status,
    headers: { Location: path },
  });
}

export function apiBaseUrl(): string {
  return (
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://127.0.0.1:8000"
  );
}

/** Anonymous visits to the learning shell go to sign-in. */
export function signInRedirect(pathname: string, hasToken: boolean): string | null {
  const protectedPath = pathname === "/app" || pathname.startsWith("/app/");
  if (protectedPath && !hasToken) {
    return "/sign-in";
  }
  return null;
}
