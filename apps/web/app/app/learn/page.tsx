import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../auth.module.css";

type GoalCard = {
  id: string;
  title: string;
  status: string;
  subject_name: string;
  next_lesson_title: string;
  remaining_minutes: number;
  usable_minutes: number;
};

async function loadGoals(): Promise<GoalCard[]> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/goals`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as GoalCard[];
}

function Section({
  title,
  goals,
  open,
}: {
  title: string;
  goals: GoalCard[];
  open?: boolean;
}) {
  if (goals.length === 0) {
    return null;
  }
  return (
    <details open={open}>
      <summary className={styles.meta}>
        {title} ({goals.length})
      </summary>
      <ul>
        {goals.map((goal) => (
          <li key={goal.id}>
            <Link href={`/app/goals/${goal.id}`}>{goal.title}</Link>
            {goal.subject_name ? ` · ${goal.subject_name}` : ""}
            {goal.next_lesson_title ? ` · ${goal.next_lesson_title}` : ""}
            {goal.status === "active" ? (
              <>
                {" · "}
                <Link href={`/app/goals/${goal.id}/start`}>Continue</Link>
                <form
                  action={`/api/goals/${goal.id}/status`}
                  method="post"
                  style={{ display: "inline", marginLeft: "0.5rem" }}
                >
                  <input type="hidden" name="status" value="paused" />
                  <button type="submit" className={styles.button}>
                    Pause
                  </button>
                </form>
                <form
                  action={`/api/goals/${goal.id}/status`}
                  method="post"
                  style={{ display: "inline", marginLeft: "0.5rem" }}
                >
                  <input type="hidden" name="status" value="archived" />
                  <button type="submit" className={styles.button}>
                    Archive
                  </button>
                </form>
              </>
            ) : null}
            {goal.status === "paused" ? (
              <form
                action={`/api/goals/${goal.id}/status`}
                method="post"
                style={{ display: "inline", marginLeft: "0.5rem" }}
              >
                <input type="hidden" name="status" value="active" />
                <button type="submit" className={styles.button}>
                  Resume
                </button>
              </form>
            ) : null}
          </li>
        ))}
      </ul>
    </details>
  );
}

export default async function LearnPage() {
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }
  const goals = await loadGoals();
  const active = goals.filter((goal) => goal.status === "active");
  const paused = goals.filter((goal) => goal.status === "paused");
  const archived = goals.filter((goal) => goal.status === "archived");

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Learn</p>
        <h1 className={styles.title}>Your goals</h1>
        {goals.length === 0 ? (
          <>
            <p className={styles.lede}>
              No goals yet. Create one and Dolphin will fit the work to the minutes you have.
            </p>
            <p className={styles.meta}>
              <Link href="/app/goals/new">Create a goal</Link>
            </p>
          </>
        ) : (
          <>
            <Section title="Active" goals={active} open />
            <Section title="Paused" goals={paused} />
            <Section title="Archived" goals={archived} />
            <p className={styles.meta}>
              <Link href="/app/goals/new">Create a goal</Link>
            </p>
          </>
        )}
      </section>
    </main>
  );
}
