import { ACCESS_COOKIE, apiBaseUrl, redirectToPath } from "@/lib/session";

function isDevEnvironment() {
  return (process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || "development") === "development";
}

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge,
  };
}

/** Dev-only email sign-in. Production uses the managed OIDC callback. */
export async function POST(request: Request) {
  if (!isDevEnvironment()) {
    return redirectToPath("/sign-in?error=1");
  }
  const form = await request.formData();
  const email = String(form.get("email") ?? "").trim();

  const issued = await fetch(`${apiBaseUrl()}/api/v1/dev/token`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email }),
    cache: "no-store",
  });

  if (!issued.ok) {
    return redirectToPath("/sign-in?error=1");
  }

  const body = (await issued.json()) as { access_token?: string };
  if (!body.access_token) {
    return redirectToPath("/sign-in?error=1");
  }

  const response = redirectToPath("/app");
  response.cookies.set(ACCESS_COOKIE, body.access_token, cookieOptions(60 * 60));
  return response;
}
