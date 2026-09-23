import {
  Button,
  Field,
  InlineNotice,
  Page,
  PageHeader,
  Stack,
  Surface,
} from "@/components/ui";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  return (
    <Page>
      <Surface>
        <Stack gap="md">
          <PageHeader
            kicker="Sign in"
            title="Dolphin"
            subtitle="Enter your email to open the learning shell. Dolphin does not store a password."
          />
          {params.error ? (
            <InlineNotice tone="warning">
              Sign-in did not complete. Check the email and that the API is running.
            </InlineNotice>
          ) : null}
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
        </Stack>
      </Surface>
    </Page>
  );
}
