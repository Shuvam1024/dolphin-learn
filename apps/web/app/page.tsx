import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Clear Depth</p>
        <h1 className={styles.title}>Dolphin</h1>
        <p className={styles.tagline}>Learn anything. Fit the time you have. Prove you can do it.</p>
        <p className={styles.note}>
          Web shell placeholder. Home, goals, and Session Studio arrive in later steps.
        </p>
        <p className={`${styles.monoNote} mono`}>IBM Plex Mono reserved for code and math.</p>
      </section>
    </main>
  );
}
