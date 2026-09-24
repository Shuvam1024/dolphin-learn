import { Button } from "@/components/ui";

import styles from "./studio.module.css";

export function StudioHeader({
  goalTitle,
  lessonTitle,
  activityTitle,
  position,
  total,
  activeMinutes,
  targetMinutes,
  remainingLow,
  remainingHigh,
  paused,
  sessionId,
  stopPoint,
}: {
  goalTitle: string;
  lessonTitle: string;
  activityTitle: string;
  position: number;
  total: number;
  activeMinutes: number;
  targetMinutes: number;
  remainingLow: number;
  remainingHigh: number;
  paused: boolean;
  sessionId: string;
  stopPoint?: boolean;
}) {
  const remainingLabel =
    remainingLow === remainingHigh
      ? `About ${remainingLow} minutes left in this sitting`
      : `About ${remainingLow}–${remainingHigh} minutes left in this sitting`;

  return (
    <header className={styles.header}>
      <p className={styles.crumb}>
        {goalTitle || "Goal"} › {lessonTitle || activityTitle}
      </p>
      <h1 className={styles.title}>{activityTitle}</h1>
      <div className={styles.metaRow}>
        <span>Mode: Guided</span>
        <span>
          Activity {position} of {total}
        </span>
        {targetMinutes > 0 ? <span>About {targetMinutes} minutes</span> : null}
        <span>{remainingLabel}</span>
        <span>
          Studied in this session: {activeMinutes}{" "}
          {activeMinutes === 1 ? "minute" : "minutes"}
        </span>
        <span>{paused ? "Paused." : "In progress."}</span>
        <span>The clock stops when you pause</span>
      </div>
      {stopPoint ? (
        <p className={styles.metaRow}>Good place to stop</p>
      ) : null}
      <form action={`/api/sessions/${sessionId}/event`} method="post">
        <input type="hidden" name="event_type" value={paused ? "resume" : "pause"} />
        <Button type="submit" variant="quiet">
          {paused ? "Resume" : "Pause"}
        </Button>
      </form>
    </header>
  );
}
