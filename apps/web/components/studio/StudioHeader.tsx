import { Button } from "@/components/ui";

import styles from "./studio.module.css";

export function StudioHeader({
  goalTitle,
  lessonTitle,
  activityTitle,
  position,
  total,
  activeMinutes,
  paused,
  sessionId,
}: {
  goalTitle: string;
  lessonTitle: string;
  activityTitle: string;
  position: number;
  total: number;
  activeMinutes: number;
  paused: boolean;
  sessionId: string;
}) {
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
        <span>
          Studied in this session: {activeMinutes}{" "}
          {activeMinutes === 1 ? "minute" : "minutes"}
        </span>
        <span>{paused ? "Paused." : "In progress."}</span>
        <span>No countdown</span>
        <span>The clock stops when you pause</span>
      </div>
      <form action={`/api/sessions/${sessionId}/event`} method="post">
        <input type="hidden" name="event_type" value={paused ? "resume" : "pause"} />
        <Button type="submit" variant="quiet">
          {paused ? "Resume" : "Pause"}
        </Button>
      </form>
    </header>
  );
}
