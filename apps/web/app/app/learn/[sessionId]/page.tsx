import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "./studio.module.css";

type StudioActivity = {
  activity_type: string;
  title: string;
  prompt: string;
  body: string;
  mode: "guided";
  recorded_choice: string;
  help: string;
  revealed_choice: string;
  outcome: string;
  attempt_assistance: string;
};

function questionChoices(prompt: string): { value: string; label: string }[] {
  return prompt
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^[a-c]\)/i.test(line))
    .map((line) => ({ value: line[0].toLowerCase(), label: line }));
}

type SummaryItem = {
  competency_key: string;
  competency_name: string;
  lesson_title: string;
  title: string;
  reason: string;
  attempt_id: string;
  outcome: string;
  choice: string;
};

type StudioSummary = {
  topics: SummaryItem[];
  independent_attempts: SummaryItem[];
  unresolved: SummaryItem[];
  suggested_review: SummaryItem[];
  note: string;
};

type StudioSession = {
  id: string;
  status: string;
  active_minutes: number;
  activity: StudioActivity | null;
  summary: StudioSummary | null;
};

async function loadSession(sessionId: string): Promise<StudioSession | null> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/sessions/${sessionId}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as StudioSession;
}

export default async function StudioPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }
  const { sessionId } = await params;
  const session = await loadSession(sessionId);
  if (!session || !session.activity) {
    return (
      <main className={styles.shell}>
        <section className={styles.card}>
          <h1 className={styles.title}>Session not found</h1>
        </section>
      </main>
    );
  }

  if (session.status === "finished" && session.summary) {
    const summary = session.summary;
    return (
      <main className={styles.shell}>
        <section className={styles.card}>
          <p className={styles.kicker}>Session summary</p>
          <h1 className={styles.title}>Session finished</h1>
          <p className={styles.meta}>{summary.note}</p>
          <h2 className={styles.meta}>Independent attempts</h2>
          <ul>
            {summary.independent_attempts.map((item) => (
              <li key={item.attempt_id}>
                {item.competency_name}: {item.outcome} ({item.choice})
              </li>
            ))}
          </ul>
          <h2 className={styles.meta}>Unresolved</h2>
          {summary.unresolved.length === 0 ? (
            <p className={styles.meta}>No unresolved questions in this session.</p>
          ) : (
            <ul>
              {summary.unresolved.map((item) => (
                <li key={item.title}>
                  {item.title}. {item.reason}
                </li>
              ))}
            </ul>
          )}
          <h2 className={styles.meta}>Suggested review</h2>
          <ul>
            {summary.suggested_review.map((item) => (
              <li key={item.competency_key}>
                {item.competency_name}. {item.reason}
              </li>
            ))}
          </ul>
        </section>
      </main>
    );
  }

  const paused = session.status === "paused";
  const reading = session.activity.activity_type === "reading";
  const question = session.activity.activity_type === "objective";
  const choices = question ? questionChoices(session.activity.prompt) : [];
  const recorded = session.activity.recorded_choice;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Session Studio</p>
        <h1 className={styles.title}>{session.activity.title}</h1>
        <p className={styles.meta}>
          Mode: Guided. {paused ? "Paused." : "In progress."} Studied in this session:{" "}
          {session.active_minutes} {session.active_minutes === 1 ? "minute" : "minutes"}. The
          clock stops when you pause. No countdown.
        </p>
        {reading ? (
          <article className={styles.body}>{session.activity.body}</article>
        ) : null}
        <p className={styles.prompt}>{session.activity.prompt}</p>
        {question && session.activity.help === "hint" ? (
          <p className={styles.meta}>
            Hint: compare each choice with the note. The letter stays hidden.
          </p>
        ) : null}
        {question && session.activity.revealed_choice ? (
          <p className={styles.meta}>
            You asked for the solution: {session.activity.revealed_choice}. A later answer is
            assisted.
          </p>
        ) : null}
        {question && recorded ? (
          <p className={styles.meta}>
            Answer recorded: {recorded}. Marked {session.activity.attempt_assistance || "independent"}.{" "}
            {session.activity.outcome ? `Outcome: ${session.activity.outcome}.` : ""}
          </p>
        ) : null}
        {question && !recorded ? (
          <form action={`/api/sessions/${session.id}/attempts`} method="post">
            <input type="hidden" name="idempotency_key" value={crypto.randomUUID()} />
            <fieldset className={styles.prompt}>
              <legend>Choose one answer</legend>
              {choices.map((choice) => (
                <label key={choice.value} className={styles.choice}>
                  <input type="radio" name="choice" value={choice.value} required /> {choice.label}
                </label>
              ))}
            </fieldset>
            <button className={styles.button} type="submit">
              Submit answer
            </button>
          </form>
        ) : null}
        {question ? (
          <form action={`/api/sessions/${session.id}/help`} method="post">
            <input type="hidden" name="kind" value="hint" />
            <button className={styles.button} type="submit">
              Show a hint
            </button>
          </form>
        ) : null}
        {question && !session.activity.revealed_choice ? (
          <form action={`/api/sessions/${session.id}/help`} method="post">
            <input type="hidden" name="kind" value="solution" />
            <button className={styles.button} type="submit">
              Show the solution
            </button>
          </form>
        ) : null}
        <form action={`/api/sessions/${session.id}/advance`} method="post">
          <button className={styles.button} type="submit">
            Next activity
          </button>
        </form>
        {question ? (
          <form action={`/api/sessions/${session.id}/independent-check`} method="post">
            <button className={styles.button} type="submit">
              Check a different question
            </button>
          </form>
        ) : null}
        <form action={`/api/sessions/${session.id}/finish`} method="post">
          <button className={styles.button} type="submit">
            Finish session
          </button>
        </form>
        <form action={`/api/sessions/${session.id}/event`} method="post">
          <input type="hidden" name="event_type" value={paused ? "resume" : "pause"} />
          <button className={styles.button} type="submit">
            {paused ? "Resume" : "Pause"}
          </button>
        </form>
      </section>
    </main>
  );
}
