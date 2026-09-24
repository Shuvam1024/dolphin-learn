import Link from "next/link";

import styles from "./auth.module.css";

export default function NotFound() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Not found</p>
        <h1 className={styles.title}>This page is not here</h1>
        <p className={styles.lede}>The link may be old, or the page moved.</p>
        <p className={styles.meta}>
          <Link href="/app">Home</Link>
          {" · "}
          <Link href="/sign-in">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
