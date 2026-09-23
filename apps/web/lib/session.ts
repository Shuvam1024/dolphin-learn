/** Cookie that holds the API access token. HttpOnly; not a password. */
export const ACCESS_COOKIE = "dolphin_access_token";

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
