import styles from "../../auth.module.css";

export default function MorePage() {
  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>More</p>
        <h1 className={styles.title}>Account</h1>
        <p className={styles.lede}>
          Settings beyond the basics are not here yet. Privacy notes and sign-out are.
        </p>
        <p className={styles.meta}>
          <a href="/privacy">Privacy summary</a>
        </p>
        <form action="/api/session/logout" method="post">
          <button className={styles.button} type="submit">
            Log out
          </button>
        </form>
      </section>
    </main>
  );
}
