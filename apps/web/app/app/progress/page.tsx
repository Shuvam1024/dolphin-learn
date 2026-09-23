import styles from "../../auth.module.css";

export default function ProgressPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Progress</p>
        <h1 className={styles.title}>No evidence yet</h1>
        <p className={styles.lede}>
          Independent checks will be listed here after you try them. Watching a lesson is not
          counted as mastery, and there is no streak score.
        </p>
      </section>
    </main>
  );
}
