import styles from "../../auth.module.css";

export default function LibraryPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Library</p>
        <h1 className={styles.title}>Coming later</h1>
        <p className={styles.lede}>
          The Knowledge Vault is not in this version. This screen does not take files, and it
          does not index or search documents.
        </p>
      </section>
    </main>
  );
}
