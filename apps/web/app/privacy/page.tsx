import styles from "../auth.module.css";

export default function PrivacyPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Privacy</p>
        <h1 className={styles.title}>Privacy summary</h1>
        <p className={styles.lede}>
          Dolphin stores the email you sign in with, your learning profile, and later your goals
          and attempts. That data is private to your account. This version does not upload a
          knowledge vault and does not sell learner data.
        </p>
        <p className={styles.meta}>
          Dolphin is for adults 18+. It is an education product, not medical, legal, or financial
          advice.
        </p>
        <p className={styles.meta}>
          <a href="/sign-in">Back to sign in</a>
        </p>
      </section>
    </main>
  );
}
