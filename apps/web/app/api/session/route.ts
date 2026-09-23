import { ACCESS_COOKIE, apiBaseUrl, redirectToPath } from "@/lib/session";

export async function POST(request: Request) {
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
  response.cookies.set(ACCESS_COOKIE, body.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: 60 * 60,
  });
  return response;
}
