import styles from "../../auth.module.css";

export default function LearnPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Learn</p>
        <h1 className={styles.title}>No session yet</h1>
        <p className={styles.lede}>
          Session Studio opens after you have a goal. Create one and Dolphin will fit the work
          to the minutes you actually have.
        </p>
        <p className={styles.meta}>
          <a href="/app/goals/new">Create a goal</a>
        </p>
      </section>
    </main>
  );
}
