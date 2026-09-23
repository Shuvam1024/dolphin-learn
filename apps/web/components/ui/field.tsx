import type { InputHTMLAttributes, ReactNode } from "react";

import styles from "./ui.module.css";

export function Field({
  id,
  label,
  help,
  error,
  children,
  ...input
}: {
  id: string;
  label: string;
  help?: string;
  error?: string;
  children?: ReactNode;
} & InputHTMLAttributes<HTMLInputElement>) {
  const helpId = help ? `${id}-help` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className={styles.field}>
      <label className={styles.fieldLabel} htmlFor={id}>
        {label}
      </label>
      {children ?? (
        <input
          className={styles.fieldControl}
          id={id}
          aria-describedby={describedBy}
          aria-invalid={error ? true : undefined}
          {...input}
        />
      )}
      {help ? (
        <p className={styles.fieldHelp} id={helpId}>
          {help}
        </p>
      ) : null}
      {error ? (
        <p className={styles.fieldError} id={errorId} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
