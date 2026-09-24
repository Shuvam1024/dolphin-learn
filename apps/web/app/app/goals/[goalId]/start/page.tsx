import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../../../auth.module.css";

type GoalPayload = {
  title: string;
  time_budget?: { preferred_session_minutes?: number } | null;
};

async function loadGoalSitting(goalId: string): Promise<{ title: string; usual: number }> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/goals/${goalId}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (response.status === 404) {
    redirect("/app");
  }
  if (!response.ok) {
    redirect("/sign-in");
  }
  const goal = (await response.json()) as GoalPayload;
  const usual = goal.time_budget?.preferred_session_minutes ?? 25;
  return { title: goal.title, usual };
}

export default async function SittingChooserPage({
  params,
}: {
  params: Promise<{ goalId: string }>;
}) {
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }
  const { goalId } = await params;
  const { title, usual } = await loadGoalSitting(goalId);
  const choices = [10, 15, 30, 45, 60];

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>How long do you have right now?</p>
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.lede}>
          Pick a sitting length. Dolphin sizes this session to it. Resume never asks again.
        </p>
        <form action="/api/sessions" method="post">
          <input type="hidden" name="goal_id" value={goalId} />
          <fieldset>
            <legend>Minutes for this sitting</legend>
            {choices.map((minutes) => (
              <label key={minutes} style={{ display: "block", marginBottom: "0.5rem" }}>
                <input type="radio" name="target_minutes" value={minutes} required /> {minutes}{" "}
                minutes
              </label>
            ))}
            <label style={{ display: "block", marginBottom: "0.5rem" }}>
              <input type="radio" name="target_minutes" value={usual} /> Use my usual {usual}
            </label>
          </fieldset>
          <button className={styles.button} type="submit">
            Start sitting
          </button>
        </form>
      </section>
    </main>
  );
}
