import { loadMe } from "@/lib/me";

import styles from "../auth.module.css";

export default async function AppHomePage() {
  const me = await loadMe();
  const acknowledged = Boolean(me.profile.adult_acknowledged_at);

  if (!acknowledged) {
    return (
      <main className={styles.shell}>
        <section className={styles.card}>
          <p className={styles.kicker}>Adults 18+</p>
          <h1 className={styles.title}>Before you start</h1>
          <p className={styles.lede}>
            Dolphin is for adults 18 and older. A child-specific product is not part of this
            version. Learning notes stay private to your account.
          </p>
          <p className={styles.meta}>
            <a href="/privacy">Read the privacy summary</a>
          </p>
          <form action="/api/session/acknowledge" method="post">
            <button className={styles.button} type="submit">
              I am 18 or older and I understand
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Home</p>
        <h1 className={styles.title}>You are in</h1>
        <p className={styles.lede}>
          Signed in as {me.email ?? me.auth_subject}. You don&apos;t have a goal yet. Create one
          and Dolphin will fit a plan to the minutes you have.
        </p>
        <p className={styles.meta}>
          <a href="/app/goals/new">Create a goal</a>
        </p>
        <form action="/api/session/logout" method="post">
          <button className={styles.button} type="submit">
            Log out
          </button>
        </form>
      </section>
    </main>
  );
}
