import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../auth.module.css";

type GoalCompetency = {
  name: string;
  facet: string;
  facet_label: string;
  last_independent_at: string | null;
  self_reported: boolean;
};

type GoalProgress = {
  id: string;
  title: string;
  competencies: GoalCompetency[];
  unassessed_count: number;
};

type UpcomingReview = {
  id: string;
  competency_name: string;
  lesson_title: string;
  due_at: string;
  due_now: boolean;
  reason: string;
};

type ProgressSnapshot = {
  goals: GoalProgress[];
  upcoming_reviews: UpcomingReview[];
  facets: { competency_key: string; competency_name: string; facet_label: string }[];
  unassessed: { competency_key: string; competency_name: string; facet_label: string }[];
};

async function loadProgress(): Promise<ProgressSnapshot> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/progress`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as ProgressSnapshot;
}

export default async function ProgressPage() {
  const progress = await loadProgress();
  const empty = progress.goals.length === 0;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Progress</p>
        <h1 className={styles.title}>{empty ? "No evidence yet" : "Evidence by goal"}</h1>
        <p className={styles.lede}>
          Each chip is what you have shown so far. There is no percent and no mastery score.
        </p>
        <details>
          <summary className={styles.meta}>What the chips mean</summary>
          <p className={styles.meta}>
            Exposed means an attempt that was not correct. Practicing means a correct answer after
            help. Independently demonstrated means a correct answer with no help. Retained means a
            later review, already due, was answered with no help. It is not a permanent promise.
            Unassessed means the plan has no stored attempt yet. Full wording lives in{" "}
            <Link href="/app/help">Help</Link>.
          </p>
        </details>
        {progress.goals.map((goal) => (
          <section key={goal.id}>
            <h2 className={styles.meta}>{goal.title}</h2>
            <p className={styles.meta}>
              {goal.unassessed_count}{" "}
              {goal.unassessed_count === 1 ? "topic" : "topics"} not tried yet
            </p>
            <ul>
              {goal.competencies.map((item) => (
                <li key={`${goal.id}-${item.name}`}>
                  {item.name}: {item.facet_label}
                  {item.self_reported ? " · Self-reported" : ""}
                </li>
              ))}
            </ul>
          </section>
        ))}
        <h2 className={styles.meta}>Upcoming reviews</h2>
        {progress.upcoming_reviews.length === 0 ? (
          <p className={styles.meta}>No reviews are scheduled yet.</p>
        ) : (
          <ul>
            {progress.upcoming_reviews.map((item) => (
              <li key={item.id}>
                {item.lesson_title || item.competency_name}
                {item.due_now ? " · due now" : ""}
              </li>
            ))}
          </ul>
        )}
        {empty ? (
          <p className={styles.meta}>
            Competencies you have not tried stay unassessed. A gap is not a zero score.
          </p>
        ) : null}
      </section>
    </main>
  );
}
