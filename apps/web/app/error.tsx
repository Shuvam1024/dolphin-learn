"use client";

import Link from "next/link";

import styles from "./auth.module.css";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Error</p>
        <h1 className={styles.title}>Something went wrong</h1>
        <p className={styles.lede}>
          Dolphin hit an unexpected problem. You can try again, or return home.
        </p>
        <p className={styles.meta}>{error.message || "Please try again."}</p>
        <button className={styles.button} type="button" onClick={() => reset()}>
          Try again
        </button>
        <p className={styles.meta} style={{ marginTop: 16 }}>
          <Link href="/app">Home</Link>
        </p>
      </section>
    </main>
  );
}
