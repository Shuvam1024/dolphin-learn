import { Chip, InlineNotice } from "@/components/ui";

import type { StudioActivity } from "./types";

export function FeedbackNotice({ activity }: { activity: StudioActivity }) {
  const { state } = activity;
  if (!state.recorded && !state.revealed_answer) {
    return null;
  }

  const assisted = state.assistance === "assisted";
  const tone =
    state.outcome === "correct" || state.outcome === "independently_demonstrated"
      ? "success"
      : state.outcome
        ? "warning"
        : "info";

  return (
    <InlineNotice tone={tone}>
      {state.recorded ? (
        <p>
          Answer recorded: {state.response}. Marked {state.assistance || "independent"}.
          {state.outcome ? ` Outcome: ${state.outcome}.` : ""}
        </p>
      ) : null}
      {assisted ? <Chip tone="neutral">Assisted</Chip> : null}
      {state.revealed_answer ? (
        <p>
          You asked for the solution: {state.revealed_answer}. A later answer is assisted.
        </p>
      ) : null}
      {state.explanation ? <p>{state.explanation}</p> : null}
      {state.misconception_note ? (
        <p>
          {state.misconception_source === "ai" ? <Chip tone="ai">AI</Chip> : null}{" "}
          {state.misconception_note}
        </p>
      ) : null}
      {state.hint_text ? (
        <p>
          {state.hint_source === "ai" ? <Chip tone="ai">AI</Chip> : null} Hint: {state.hint_text}
        </p>
      ) : null}
    </InlineNotice>
  );
}
