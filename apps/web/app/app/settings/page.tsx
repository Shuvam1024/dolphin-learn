import Link from "next/link";

import styles from "../../auth.module.css";

export default function SettingsPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Settings</p>
        <h1 className={styles.title}>Sitting defaults</h1>
        <p className={styles.lede}>
          Full settings (timezone, larger text, AI on/off) arrive before first ship. For now, choose
          sitting length when you start a session, and use Help for how evidence works.
        </p>
        <p className={styles.meta}>
          <Link href="/app/help">Help</Link>
          {" · "}
          <Link href="/app/more">More</Link>
        </p>
      </section>
    </main>
  );
}
