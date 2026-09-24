import styles from "../auth.module.css";

export default function PrivacyPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Privacy</p>
        <h1 className={styles.title}>Privacy summary</h1>
        <p className={styles.lede}>
          Dolphin stores the email you sign in with, your learning profile, goals, attempts, and
          AI call metadata (not raw prompts). That data is private to your account. This version
          does not upload a knowledge vault and does not sell learner data.
        </p>
        <p className={styles.lede}>
          From Settings you can download a JSON export of your data (rate limited to 3 per hour)
          or delete your account. After deletion, Dolphin keeps a tombstone for{" "}
          <strong>30 days</strong>, then a purge job removes the account and anonymizes AI audit
          rows.
        </p>
        <p className={styles.meta}>
          Dolphin is for adults 18+. It is an education product, not medical, legal, or financial
          advice.
        </p>
        <p className={styles.meta}>
          <a href="/sign-in">Back to sign in</a>
          {" · "}
          <a href="/app/settings">Settings</a>
        </p>
      </section>
    </main>
  );
}
