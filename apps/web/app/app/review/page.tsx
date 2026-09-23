import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../auth.module.css";

type ReviewItem = {
  id: string;
  competency_key: string;
  due_at: string;
  interval_days: number;
  reason: string;
  title: string;
  prompt: string;
  revealed_choice: string;
};

type ReviewQueue = {
  due: ReviewItem[];
  scheduled: ReviewItem[];
};

function questionChoices(prompt: string): { value: string; label: string }[] {
  return prompt
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^[a-c]\)/i.test(line))
    .map((line) => ({ value: line[0].toLowerCase(), label: line }));
}

async function loadQueue(): Promise<ReviewQueue> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/reviews/due`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as ReviewQueue;
}

export default async function ReviewPage() {
  const queue = await loadQueue();
  const current = queue.due[0];

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Review</p>
        {current ? (
          <>
            <h1 className={styles.title}>Due now</h1>
            <p className={styles.lede}>{current.reason}</p>
            <p className={styles.meta}>
              {current.competency_key}. {current.title}. Interval {current.interval_days} day
              {current.interval_days === 1 ? "" : "s"}.
            </p>
            <p className={styles.meta}>{current.prompt}</p>
            {current.revealed_choice ? (
              <p className={styles.meta}>
                You asked for the solution: {current.revealed_choice}. This answer is assisted and
                does not lengthen the interval.
              </p>
            ) : (
              <form action={`/api/reviews/${current.id}/solution`} method="post">
                <button className={styles.button} type="submit">
                  Show the solution
                </button>
              </form>
            )}
            <form action={`/api/reviews/${current.id}/attempts`} method="post">
              <fieldset className={styles.meta}>
                <legend>Choose one answer</legend>
                {questionChoices(current.prompt).map((choice) => (
                  <label key={choice.value} className={styles.meta}>
                    <input type="radio" name="choice" value={choice.value} required /> {choice.label}
                  </label>
                ))}
              </fieldset>
              <button className={styles.button} type="submit">
                Submit review
              </button>
            </form>
          </>
        ) : (
          <>
            <h1 className={styles.title}>Nothing is due</h1>
            <p className={styles.lede}>
              Reviews show up after you practice. There is no streak to protect and nothing to
              catch up on today.
            </p>
            {queue.scheduled.map((item) => (
              <p key={item.id} className={styles.meta}>
                {item.competency_key}. {item.reason}
              </p>
            ))}
          </>
        )}
      </section>
    </main>
  );
}
