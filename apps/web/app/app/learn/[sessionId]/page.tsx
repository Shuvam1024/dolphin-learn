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
        <p className={styles.metaRow}>
          Minutes studied: {summary.minutes_studied ?? session.active_minutes}
        </p>
        <h2>What you showed on your own</h2>
        {(summary.showed_on_your_own ?? summary.independent_attempts).length === 0 ? (
          <p>Nothing independent in this session.</p>
        ) : (
          <ul>
            {(summary.showed_on_your_own ?? summary.independent_attempts).map((item) => (
              <li key={item.attempt_id || `${item.competency_key}-${item.choice}`}>
                {item.competency_name}: {item.outcome} ({item.choice})
              </li>
            ))}
          </ul>
        )}
        <h2>Practiced with help</h2>
        {(summary.practiced_with_help ?? []).length === 0 ? (
          <p>No assisted practice in this session.</p>
        ) : (
          <ul>
            {(summary.practiced_with_help ?? []).map((item) => (
              <li key={item.attempt_id || `${item.competency_key}-helped`}>
                {item.competency_name}: {item.outcome}
              </li>
            ))}
          </ul>
        )}
        <h2>Self-reported</h2>
        {(summary.self_reported ?? []).length === 0 ? (
          <p>No self-reported recall in this session.</p>
        ) : (
          <ul>
            {(summary.self_reported ?? []).map((item) => (
              <li key={item.attempt_id || `${item.competency_key}-self`}>
                {item.competency_name}: {item.rating || "self-reported"}
              </li>
            ))}
          </ul>
        )}
        <h2>Watch out for</h2>
        {(summary.watch_out_for ?? []).length === 0 ? (
          <p>Nothing flagged from this session.</p>
        ) : (
          <ul>
            {(summary.watch_out_for ?? []).map((item) => (
              <li key={`${item.competency_key}-${item.note}`}>
                {item.competency_name}: {item.note}
                {item.source === "ai" ? " (AI)" : ""}
              </li>
            ))}
          </ul>
        )}
        {summary.next_review ? (
          <>
            <h2>Next review</h2>
            <p>
              {String(summary.next_review.lesson)} in{" "}
              {String(summary.next_review.in_days)} days
            </p>
          </>
        ) : null}
        {summary.next_step ? (
          <p>
            <a href={summary.next_step.href}>{summary.next_step.label}</a>
          </p>
        ) : null}
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
