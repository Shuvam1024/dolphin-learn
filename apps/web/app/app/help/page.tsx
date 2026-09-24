import Link from "next/link";

import styles from "../../auth.module.css";

export default function HelpPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Help</p>
        <h1 className={styles.title}>How Dolphin talks about learning</h1>

        <h2 className={styles.meta}>Evidence words</h2>
        <ul>
          <li>Seen — you opened the lesson.</li>
          <li>Practicing — you tried with help or a self-check.</li>
          <li>Shown on your own — an independent correct answer.</li>
          <li>Remembered later — a due review answered independently.</li>
          <li>Self-reported — free recall you rated yourself; never higher than practicing.</li>
        </ul>

        <h2 className={styles.meta}>How minutes are counted</h2>
        <p className={styles.lede}>
          Study time is active minutes in a session. Pause stops the clock. Time away is not study.
          There is no countdown and no streak.
        </p>

        <h2 className={styles.meta}>Reviews</h2>
        <p className={styles.lede}>
          After an independent success, Dolphin schedules a later check. Passing that check can mark
          Remembered later. It is not a promise of permanent mastery.
        </p>

        <h2 className={styles.meta}>What the tutor does and does not do</h2>
        <p className={styles.lede}>
          The tutor can explain differently, offer a validated hint, draft a misconception note, and
          compare free-recall writing. It never grades and never writes an evidence row. Seeded
          lessons work with the tutor off.
        </p>

        <p className={styles.meta}>
          <Link href="/app">Back to Home</Link>
        </p>
      </section>
    </main>
  );
}
