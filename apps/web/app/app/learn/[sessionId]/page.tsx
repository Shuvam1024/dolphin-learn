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
};

function questionChoices(prompt: string): { value: string; label: string }[] {
  return prompt
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^[a-c]\)/i.test(line))
    .map((line) => ({ value: line[0].toLowerCase(), label: line }));
}

type StudioSession = {
  id: string;
  status: string;
  activity: StudioActivity | null;
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
          Mode: Guided. {paused ? "Paused." : "In progress."} No countdown.
        </p>
        {reading ? (
          <article className={styles.body}>{session.activity.body}</article>
        ) : null}
        <p className={styles.prompt}>{session.activity.prompt}</p>
        {question && recorded ? (
          <p className={styles.meta}>Answer recorded: {recorded}. This does not claim mastery.</p>
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
