import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";

import styles from "../../../auth.module.css";

export default async function NewGoalPage() {
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Goal</p>
        <h1 className={styles.title}>Create a goal</h1>
        <p className={styles.lede}>
          The goal wizard is not built yet. This page only opens after the adult acknowledgment
          is on your profile.
        </p>
        <p className={styles.meta}>
          <a href="/app">Back to home</a>
        </p>
      </section>
    </main>
  );
}
