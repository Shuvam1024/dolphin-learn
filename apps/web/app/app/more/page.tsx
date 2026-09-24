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
            <Link className={styles.meta} href="/app/settings" style={{ display: "inline-block", minHeight: 44, padding: "12px 0" }}>
              Settings
            </Link>
          </li>
          <li>
            <Link className={styles.meta} href="/app/help" style={{ display: "inline-block", minHeight: 44, padding: "12px 0" }}>
              Help
            </Link>
          </li>
          <li>
            <Link className={styles.meta} href="/privacy" style={{ display: "inline-block", minHeight: 44, padding: "12px 0" }}>
              Privacy
            </Link>
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
