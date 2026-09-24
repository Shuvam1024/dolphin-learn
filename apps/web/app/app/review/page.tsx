import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../auth.module.css";

type ReviewItem = {
  id: string;
  competency_key: string;
  competency_name: string;
  lesson_title: string;
  due_at: string;
  interval_days: number;
  reason: string;
  title: string;
  prompt: string;
  revealed_choice: string;
  estimated_minutes: number;
};

type ReviewQueue = {
  due: ReviewItem[];
  scheduled: ReviewItem[];
  preferred_session_minutes: number;
  fits: { count: number; minutes: number };
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
  const dueCount = queue.due.length;
  const fitCount = queue.fits?.count ?? 0;
  const fitMinutes = queue.fits?.minutes ?? 0;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Review</p>
        {current ? (
          <>
            <h1 className={styles.title}>Due now</h1>
            <p className={styles.lede}>
              {dueCount} due · start with {fitCount} (about {fitMinutes}{" "}
              {fitMinutes === 1 ? "minute" : "minutes"})
            </p>
            <p className={styles.meta}>{current.reason}</p>
            <p className={styles.meta}>
              {current.competency_name}. {current.lesson_title || current.title}. About{" "}
              {current.estimated_minutes} min. Interval {current.interval_days} day
              {current.interval_days === 1 ? "" : "s"}.
            </p>
            <p className={styles.meta}>{current.prompt}</p>
            {current.revealed_choice ? (
              <p className={styles.meta}>
                You asked for the solution: {current.revealed_choice}. This answer is assisted and
                does not lengthen the interval. After you answer, the tutor can explain differently
                when AI is on.
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
            <p className={styles.meta}>Not now</p>
            {[3, 24, 72].map((hours) => (
              <form
                key={hours}
                action={`/api/reviews/${current.id}/snooze`}
                method="post"
                style={{ display: "inline-block", marginRight: 8 }}
              >
                <input type="hidden" name="hours" value={String(hours)} />
                <button className={styles.button} type="submit">
                  {hours}h
                </button>
              </form>
            ))}
            <p className={styles.meta}>
              Snooze waits 3, 24, or 72 hours. Skipping is not study and does not count as
              remembering.
            </p>
          </>
        ) : (
          <>
            <h1 className={styles.title}>Nothing is due</h1>
            <p className={styles.lede}>
              Reviews show up after you practice. There is nothing to catch up on today.
            </p>
            {queue.scheduled.map((item) => (
              <p key={item.id} className={styles.meta}>
                {item.competency_name}. About {item.estimated_minutes} min. {item.reason}
              </p>
            ))}
          </>
        )}
      </section>
    </main>
  );
}
