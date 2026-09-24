import { Button, Field, InlineNotice } from "@/components/ui";

import styles from "./sign-in.module.css";

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
    <main className={styles.shell}>
      <div className={styles.column}>
        <h1 className={styles.wordmark}>Dolphin</h1>
        {params.error ? (
          <InlineNotice tone="warning">
            Sign-in did not complete. Check the email and that the API is running.
          </InlineNotice>
        ) : null}
        {dev ? (
          <form className={styles.form} action="/api/session" method="post">
            <Field
              id="email"
              name="email"
              type="email"
              label="Email"
              autoComplete="email"
              autoFocus
              required
            />
            <Button className={styles.submit} type="submit" variant="primary">
              Continue
            </Button>
          </form>
        ) : managed ? (
          <a className={styles.managed} href={managed}>
            Continue with email
          </a>
        ) : (
          <InlineNotice tone="warning">
            Sign-in is not configured for this environment. Set the managed auth URLs.
          </InlineNotice>
        )}
      </div>
    </main>
  );
}
