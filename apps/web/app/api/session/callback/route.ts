import { ACCESS_COOKIE, apiBaseUrl, redirectToPath } from "@/lib/session";

/**
 * OIDC / magic-link callback for production.
 * Exchanges `code` for tokens at AUTH_TOKEN_URL, stores the access token cookie.
 * Secure; HttpOnly; SameSite=Lax. No password field anywhere.
 */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const error = url.searchParams.get("error");
  if (error || !code) {
    return redirectToPath("/sign-in?error=1");
  }

  const tokenUrl = process.env.AUTH_TOKEN_URL || "";
  const clientId = process.env.AUTH_CLIENT_ID || process.env.NEXT_PUBLIC_AUTH_CLIENT_ID || "";
  const clientSecret = process.env.AUTH_CLIENT_SECRET || "";
  if (!tokenUrl || !clientId) {
    return redirectToPath("/sign-in?error=1");
  }

  const redirectUri = `${url.origin}/api/session/callback`;
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri,
    client_id: clientId,
  });
  if (clientSecret) {
    body.set("client_secret", clientSecret);
  }

  const tokenResponse = await fetch(tokenUrl, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body,
    cache: "no-store",
  });
  if (!tokenResponse.ok) {
    return redirectToPath("/sign-in?error=1");
  }
  const tokens = (await tokenResponse.json()) as { access_token?: string; expires_in?: number };
  if (!tokens.access_token) {
    return redirectToPath("/sign-in?error=1");
  }

  // Touch /me so the API maps the OIDC subject to a local user.
  await fetch(`${apiBaseUrl()}/api/v1/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
    cache: "no-store",
  });

  const response = redirectToPath("/app");
  response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: true,
    maxAge: Math.max(60, Number(tokens.expires_in || 3600)),
  });
  return response;
}
