import Link from "next/link";

import styles from "../../auth.module.css";

export default function MorePage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>More</p>
        <h1 className={styles.title}>Account</h1>
        <ul>
          <li>
            <Link href="/app/settings">Settings</Link>
          </li>
          <li>
            <Link href="/app/help">Help</Link>
          </li>
          <li>
            <Link href="/privacy">Privacy</Link>
          </li>
        </ul>
        <form action="/api/session/logout" method="post">
          <button className={styles.button} type="submit">
            Sign out
          </button>
        </form>
      </section>
    </main>
  );
}
