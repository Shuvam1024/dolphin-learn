import styles from "../auth.module.css";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Sign in</p>
        <h1 className={styles.title}>Dolphin</h1>
        <p className={styles.lede}>
          Enter your email to open the learning shell. Dolphin does not store a password.
          This local sign-in asks the API for a short-lived token.
        </p>
        {params.error ? (
          <p className={styles.error} role="alert">
            Sign-in did not complete. Check the email and that the API is running.
          </p>
        ) : null}
        <form className={styles.form} action="/api/session" method="post">
          <label className={styles.label} htmlFor="email">
            Email
          </label>
          <input
            className={styles.input}
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
          />
          <button className={styles.button} type="submit">
            Continue
          </button>
        </form>
      </section>
    </main>
  );
}
