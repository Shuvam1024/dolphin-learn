import type { ReactNode } from "react";

import { Button } from "./button";
import styles from "./ui.module.css";

export function Pending({
  label = "Thinking…",
  onCancel,
  children,
}: {
  label?: string;
  onCancel?: () => void;
  children?: ReactNode;
}) {
  return (
    <div className={styles.pending} role="status" aria-live="polite">
      <div className={styles.skeleton} aria-hidden="true" />
      <div className={styles.skeleton} aria-hidden="true" />
      <p>{label}</p>
      {children}
      {onCancel ? (
        <Button type="button" variant="quiet" onClick={onCancel}>
          Cancel
        </Button>
      ) : null}
    </div>
  );
}
