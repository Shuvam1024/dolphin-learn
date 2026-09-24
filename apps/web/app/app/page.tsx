import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "./home.module.css";
import { Prompt } from "./prompt";

type NextAction = {
  kind: string;
  title: string;
  subtitle?: string;
  minutes_estimate?: number;
  href: string;
  goal_id: string;
};

type GoalCard = {
  id: string;
  title: string;
  subject_name: string;
  next_lesson_title: string;
  remaining_minutes: number;
  usable_minutes: number;
  studied_minutes: number;
  status: string;
};

type HomeSnapshot = {
  next_action: NextAction;
  goals: GoalCard[];
  due_reviews: {
    count: number;
    minutes_estimate: number;
    first_lesson_title: string;
  };
  recent_evidence: {
    competency_key: string;
    competency_name: string;
    facet_label: string;
  }[];
  quick_learn: { href: string; label: string };
};

async function loadHome(): Promise<HomeSnapshot | { error: true }> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/home`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) {
      return { error: true };
    }
    return (await response.json()) as HomeSnapshot;
  } catch {
    return { error: true };
  }
}

function minutesLabel(n: number): string {
  return n === 1 ? "1 minute" : `${n} minutes`;
}

export default async function AppHomePage() {
  const homeOrError = await loadHome();

  if ("error" in homeOrError) {
    return (
      <main className={styles.desk}>
        <h1 className={styles.promptTitle}>Something went wrong</h1>
        <p className={styles.sub}>Home could not load. Try again.</p>
        <p>
          <Link className={styles.quiet} href="/app">
            Retry
          </Link>
        </p>
      </main>
    );
  }

  const home = homeOrError;
  const totalRemaining = home.goals.reduce((sum, goal) => sum + goal.remaining_minutes, 0);
  const showContinue = home.goals.length > 0 && Boolean(home.next_action.href);

  return (
    <main className={styles.desk}>
      <Prompt />

      {showContinue ? (
        <section className={styles.continue} aria-labelledby="home-continue">
          <p className={styles.sectionTitle}>Pick up</p>
          <h2 className={styles.continueLink} id="home-continue">
            <Link href={home.next_action.href}>{home.next_action.title}</Link>
          </h2>
          {home.next_action.subtitle ? <p className={styles.sub}>{home.next_action.subtitle}</p> : null}
          <p className={styles.totals}>Minutes left across goals: {totalRemaining}</p>
        </section>
      ) : null}

      {home.goals.length > 0 ? (
        <section className={styles.section} aria-labelledby="home-goals">
          <h2 className={styles.sectionTitle} id="home-goals">
            Goals
          </h2>
          <ul className={styles.courseList}>
            {home.goals.map((goal) => (
              <li key={goal.id} className={styles.course}>
                <div>
                  <p className={styles.subject}>{goal.subject_name}</p>
                  <Link className={styles.courseTitle} href={`/app/goals/${goal.id}`}>
                    {goal.title}
                  </Link>
                  <p className={styles.meta}>
                    {goal.next_lesson_title ? `next: ${goal.next_lesson_title}` : "No next lesson yet"}
                    {` · ${goal.remaining_minutes} of ${goal.usable_minutes} minutes left`}
                  </p>
                </div>
                <p className={styles.studied}>{minutesLabel(goal.studied_minutes)} studied</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {home.goals.length > 0 ? (
        <>
          <section className={styles.section} aria-labelledby="home-reviews">
            <h2 className={styles.sectionTitle} id="home-reviews">
              Reviews
            </h2>
            {home.due_reviews.count === 0 ? (
              <p className={styles.line}>Nothing is due.</p>
            ) : (
              <p className={styles.line}>
                {home.due_reviews.count} due
                {home.due_reviews.first_lesson_title
                  ? ` · start with ${home.due_reviews.first_lesson_title}`
                  : ""}
                {home.due_reviews.minutes_estimate
                  ? ` · ${minutesLabel(home.due_reviews.minutes_estimate)}`
                  : ""}
                {home.next_action.kind === "review" ? null : (
                  <>
                    {" · "}
                    <Link className={styles.quiet} href="/app/review">
                      Open review
                    </Link>
                  </>
                )}
              </p>
            )}
          </section>
          <section className={styles.section} aria-labelledby="home-evidence">
            <h2 className={styles.sectionTitle} id="home-evidence">
              Recent evidence
            </h2>
            {home.recent_evidence.length === 0 ? (
              <p className={styles.line}>No independent evidence yet.</p>
            ) : (
              <ul className={styles.evidence}>
                {home.recent_evidence.map((item) => (
                  <li key={`${item.competency_name}-${item.facet_label}`}>
                    {item.competency_name}: {item.facet_label}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
