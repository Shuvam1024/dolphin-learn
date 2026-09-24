import { Button } from "@/components/ui";

import styles from "./studio.module.css";
import { primaryLabel, type StudioActivity, type StudioSession } from "./types";

export function ActionBar({
  session,
  activity,
}: {
  session: Pick<StudioSession, "id" | "actions">;
  activity: StudioActivity;
}) {
  const actions = session.actions;
  if (!actions) {
    return null;
  }

  const label = primaryLabel(actions.primary, activity.activity_type);
  const primaryAction =
    actions.primary === "submit"
      ? null
      : actions.primary === "continue"
        ? "advance"
        : actions.primary === "fresh_check"
          ? "independent-check"
          : "finish";

  return (
    <div className={styles.actionBar} data-studio-action-bar="">
      {actions.awaiting_self_report ? null : actions.primary === "submit" ? (
        <Button type="submit" variant="primary" form="studio-attempt-form">
          {label}
        </Button>
      ) : (
        <form action={`/api/sessions/${session.id}/${primaryAction}`} method="post">
          <Button type="submit" variant="primary">
            {label}
          </Button>
        </form>
      )}
      <div className={styles.actionBarSecondary}>
        {actions.can_hint && !activity.state.recorded ? (
          <form action={`/api/sessions/${session.id}/help`} method="post">
            <input type="hidden" name="kind" value="hint" />
            <Button type="submit" variant="secondary">
              Show a hint
            </Button>
          </form>
        ) : null}
        {actions.can_reveal && !activity.state.revealed_answer ? (
          <form action={`/api/sessions/${session.id}/help`} method="post">
            <input type="hidden" name="kind" value="solution" />
            <Button type="submit" variant="secondary">
              Show the solution
            </Button>
          </form>
        ) : null}
        {actions.can_fresh_check && actions.primary !== "fresh_check" ? (
          <form action={`/api/sessions/${session.id}/independent-check`} method="post">
            <Button type="submit" variant="secondary">
              Check a different question
            </Button>
          </form>
        ) : null}
        {activity.state.recorded &&
        ["objective", "short_answer", "numeric"].includes(activity.activity_type) &&
        actions.primary !== "fresh_check" &&
        !actions.can_fresh_check ? (
          <form action={`/api/sessions/${session.id}/independent-check`} method="post">
            <Button type="submit" variant="secondary">
              Check a different question
            </Button>
          </form>
        ) : null}
        {actions.primary !== "finish" ? (
          <form action={`/api/sessions/${session.id}/finish`} method="post">
            <Button type="submit" variant="quiet">
              Finish session
            </Button>
          </form>
        ) : null}
      </div>
    </div>
  );
}
