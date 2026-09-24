import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  ActionBar,
  ActivityBody,
  AnswerInput,
  AttemptHiddenFields,
  FeedbackNotice,
  StudioHeader,
  TutorPanel,
  type StudioSession,
} from "@/components/studio";
import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "@/components/studio/studio.module.css";

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
  if (!session) {
    return (
      <main className={styles.shell}>
        <h1 className={styles.title}>Session not found</h1>
      </main>
    );
  }

  if (session.status === "finished" && session.summary) {
    const summary = session.summary;
    return (
      <main className={styles.shell}>
        <p className={styles.crumb}>Session summary</p>
        <h1 className={styles.title}>Session finished</h1>
        <p className={styles.metaRow}>{summary.note}</p>
        <h2>Independent attempts</h2>
        <ul>
          {summary.independent_attempts.map((item) => (
            <li key={item.attempt_id}>
              {item.competency_name}: {item.outcome} ({item.choice})
            </li>
          ))}
        </ul>
        <h2>Unresolved</h2>
        {summary.unresolved.length === 0 ? (
          <p>No unresolved questions in this session.</p>
        ) : (
          <ul>
            {summary.unresolved.map((item) => (
              <li key={item.title}>
                {item.title}. {item.reason}
              </li>
            ))}
          </ul>
        )}
        <h2>Suggested review</h2>
        <ul>
          {summary.suggested_review.map((item) => (
            <li key={item.competency_key}>
              {item.competency_name}. {item.reason}
            </li>
          ))}
        </ul>
        <h2>Watch out for</h2>
        {(summary.watch_out_for ?? []).length === 0 ? (
          <p>Nothing flagged from this session.</p>
        ) : (
          <ul>
            {(summary.watch_out_for ?? []).map((item) => (
              <li key={`${item.competency_key}-${item.note}`}>
                {item.competency_name}: {item.note}
              </li>
            ))}
          </ul>
        )}
      </main>
    );
  }

  const activity = session.studio_activity;
  if (!activity) {
    return (
      <main className={styles.shell}>
        <h1 className={styles.title}>Session not found</h1>
      </main>
    );
  }

  const paused = session.status === "paused";
  const needsAttempt = session.actions?.primary === "submit" && !activity.state.recorded;
  const needsSelfRate = Boolean(activity.state.awaiting_self_report);

  return (
    <main className={styles.shell}>
      <StudioHeader
        goalTitle={session.goal?.title ?? ""}
        lessonTitle={session.lesson?.title ?? activity.title}
        activityTitle={activity.title}
        position={session.position}
        total={session.total}
        activeMinutes={session.active_minutes}
        targetMinutes={session.target_minutes ?? 0}
        remainingLow={session.remaining_estimate?.low ?? 0}
        remainingHigh={session.remaining_estimate?.high ?? 0}
        paused={paused}
        sessionId={session.id}
        stopPoint={Boolean(session.actions?.stop_point)}
      />
      <ActivityBody
        bodyMarkdown={activity.body_markdown}
        promptMarkdown={activity.prompt_markdown}
        showBody={
          activity.activity_type === "reading" ||
          activity.activity_type === "worked_example" ||
          (activity.activity_type === "free_recall" && activity.state.recorded)
        }
      />
      {session.activity?.help === "hint" && !activity.state.recorded ? (
        <p>Hint: compare each choice with the note. The letter stays hidden.</p>
      ) : null}
      <FeedbackNotice activity={activity} />
      {needsAttempt ? (
        <form id="studio-attempt-form" action={`/api/sessions/${session.id}/attempts`} method="post">
          <AttemptHiddenFields />
          <AnswerInput activity={activity} sessionId={session.id} />
        </form>
      ) : (
        <AnswerInput activity={activity} sessionId={session.id} disabled />
      )}
      {needsSelfRate ? (
        <form action={`/api/sessions/${session.id}/self-rate`} method="post">
          <fieldset>
            <legend>How did that go?</legend>
            <label>
              <input type="radio" name="rating" value="got_it" required /> Got it
            </label>
            <label>
              <input type="radio" name="rating" value="partly" /> Partly
            </label>
            <label>
              <input type="radio" name="rating" value="not_yet" /> Not yet
            </label>
          </fieldset>
          <button type="submit">Save self-rating</button>
        </form>
      ) : null}
      <TutorPanel session={session} activity={activity} />
      <ActionBar session={session} activity={activity} />
    </main>
  );
}
