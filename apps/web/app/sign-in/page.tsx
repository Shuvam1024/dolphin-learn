import {
  Button,
  Field,
  InlineNotice,
  Page,
  PageHeader,
  Stack,
  Surface,
} from "@/components/ui";

function isDevEnvironment() {
  return (process.env.NEXT_PUBLIC_ENVIRONMENT || "development") === "development";
}

function authorizeUrl() {
  const base = process.env.NEXT_PUBLIC_AUTH_AUTHORIZE_URL || process.env.AUTH_AUTHORIZE_URL || "";
  const clientId = process.env.NEXT_PUBLIC_AUTH_CLIENT_ID || process.env.AUTH_CLIENT_ID || "";
  if (!base || !clientId) {
    return "";
  }
  const url = new URL(base);
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid email profile");
  return url.toString();
}

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const dev = isDevEnvironment();
  const managed = authorizeUrl();

  return (
    <Page>
      <Surface>
        <Stack gap="md">
          <PageHeader
            kicker="Sign in"
            title="Dolphin"
            subtitle={
              dev
                ? "Enter your email to open the learning shell. Dolphin does not store a password."
                : "Continue with your email magic link. Dolphin does not store a password."
            }
          />
          {params.error ? (
            <InlineNotice tone="warning">
              Sign-in did not complete. Check the email and that the API is running.
            </InlineNotice>
          ) : null}
          {dev ? (
            <form action="/api/session" method="post">
              <Stack gap="sm">
                <Field
                  id="email"
                  name="email"
                  type="email"
                  label="Email"
                  autoComplete="email"
                  required
                />
                <Button type="submit" variant="primary">
                  Continue
                </Button>
              </Stack>
            </form>
          ) : managed ? (
            <p>
              <a href={managed}>Continue with email</a>
            </p>
          ) : (
            <InlineNotice tone="warning">
              Sign-in is not configured for this environment. Set the managed auth URLs.
            </InlineNotice>
          )}
        </Stack>
      </Surface>
    </Page>
  );
}
