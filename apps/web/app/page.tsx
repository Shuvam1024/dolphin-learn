import Link from "next/link";

import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Clear Depth</p>
        <h1 className={styles.title}>Dolphin</h1>
        <p className={styles.tagline}>Learn anything.</p>
        <p className={styles.tagline}>Fit the time you have.</p>
        <p className={styles.tagline}>Prove you can do it.</p>
        <p className={styles.tagline}>The tutor explains. It never grades.</p>
        <p className={styles.tagline}>Study time is active minutes — never a streak.</p>
        <p className={styles.note}>
          <Link href="/sign-in">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
