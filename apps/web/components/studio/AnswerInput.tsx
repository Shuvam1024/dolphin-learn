import { Field } from "@/components/ui";

import styles from "./studio.module.css";
import type { StudioActivity } from "./types";

export function AnswerInput({
  activity,
  disabled,
}: {
  activity: StudioActivity;
  sessionId: string;
  disabled?: boolean;
}) {
  const { input_kind: kind, choices, state } = activity;
  if (kind === "none" || state.recorded || disabled) {
    return null;
  }

  if (kind === "choice") {
    return (
      <fieldset className={styles.choices}>
        <legend>Choose one answer</legend>
        {choices.map((choice) => (
          <label key={choice.id} className={styles.choice}>
            <input type="radio" name="choice" value={choice.id} required />
            {choice.id}) {choice.label}
          </label>
        ))}
      </fieldset>
    );
  }

  if (kind === "text") {
    return (
      <Field id="studio-text" label="Your answer" name="text" required autoComplete="off" />
    );
  }

  if (kind === "number") {
    return (
      <Field
        id="studio-number"
        label="Your number"
        name="value"
        inputMode="decimal"
        required
        autoComplete="off"
      />
    );
  }

  if (kind === "recall") {
    return (
      <Field id="studio-recall" label="Write from memory">
        <textarea
          id="studio-recall"
          className={styles.recallInput}
          name="text"
          required
          rows={5}
        />
      </Field>
    );
  }

  return null;
}

export function AttemptHiddenFields() {
  return <input type="hidden" name="idempotency_key" value={crypto.randomUUID()} />;
}
