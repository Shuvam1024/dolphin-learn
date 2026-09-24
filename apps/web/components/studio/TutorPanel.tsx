"use client";

import { useState } from "react";

import { Button, Chip, Pending } from "@/components/ui";

import styles from "./studio.module.css";
import type { StudioActivity, StudioSession } from "./types";

export function TutorPanel({
  session,
  activity,
}: {
  session: Pick<StudioSession, "id" | "tutor" | "actions">;
  activity: StudioActivity;
}) {
  const [open, setOpen] = useState(false);
  const tutor = session.tutor;
  if (!tutor?.enabled) {
    return null;
  }

  const pending = Boolean(tutor.pending_request_id);
  const canExplain = Boolean(session.actions?.can_explain_differently);
  const canHint = Boolean(session.actions?.can_hint);
  const alt = activity.state.alt_explanation;
  const hint = activity.state.hint_text;
  const hintAi = activity.state.hint_source === "ai";

  return (
    <details
      className={styles.tutor}
      open={open}
      onToggle={(event) => setOpen((event.target as HTMLDetailsElement).open)}
    >
      <summary className={styles.tutorSummary}>Tutor help</summary>
      <div className={styles.tutorBody}>
        {pending ? <Pending label="Pending" /> : null}
        {alt ? (
          <div className={styles.tutorText}>
            <Chip tone="ai">AI</Chip>
            <p>{alt}</p>
          </div>
        ) : null}
        {hint ? (
          <div className={styles.tutorText}>
            {hintAi ? <Chip tone="ai">AI</Chip> : null}
            <p>{hint}</p>
          </div>
        ) : null}
        {canExplain ? (
          <form action={`/api/sessions/${session.id}/help`} method="post">
            <input type="hidden" name="kind" value="explain" />
            <Button type="submit" variant="secondary">
              Explain this differently
            </Button>
          </form>
        ) : null}
        {canHint ? (
          <form action={`/api/sessions/${session.id}/help`} method="post">
            <input type="hidden" name="kind" value="hint" />
            <Button type="submit" variant="secondary">
              Give me a hint
            </Button>
          </form>
        ) : null}
      </div>
    </details>
  );
}
