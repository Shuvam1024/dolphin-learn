import styles from "../../auth.module.css";

export default function ReviewPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Review</p>
        <h1 className={styles.title}>Nothing is due</h1>
        <p className={styles.lede}>
          Reviews show up after you practice. There is no streak to protect and nothing to catch
          up on today.
        </p>
      </section>
    </main>
  );
}
