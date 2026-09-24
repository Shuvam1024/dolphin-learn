import { Chip, InlineNotice } from "@/components/ui";

import type { StudioActivity } from "./types";

export function FeedbackNotice({ activity }: { activity: StudioActivity }) {
  const { state } = activity;
  if (!state.recorded && !state.revealed_answer && !state.explanation) {
    return null;
  }

  const assisted = state.assistance === "assisted";
  const incorrect = Boolean(state.recorded && state.outcome && state.outcome !== "correct");
  const tone = state.outcome === "correct" ? "success" : incorrect ? "warning" : "info";

  return (
    <InlineNotice tone={tone}>
      {state.recorded ? (
        <p>
          Answer recorded: {state.response}. Marked {state.assistance || "independent"}.
          {state.outcome ? ` Outcome: ${state.outcome}.` : ""}
        </p>
      ) : null}
      {assisted ? <Chip tone="neutral">Assisted</Chip> : null}
      {state.outcome === "self_reported" ? <Chip tone="neutral">Self-reported</Chip> : null}
      {state.revealed_answer ? (
        <p>
          You asked for the solution: {state.revealed_answer}. A later answer is assisted.
        </p>
      ) : null}
      {state.explanation ? <p>{state.explanation}</p> : null}
      {state.misconception_note ? (
        <p>
          {state.misconception_source === "ai" ? <Chip tone="ai">AI</Chip> : null}
          {state.misconception_note}
        </p>
      ) : null}
      {state.recall_feedback ? (
        <p>
          <Chip tone="ai">AI</Chip> {state.recall_feedback}
        </p>
      ) : null}
      {(state.recall_covered?.length || state.recall_missing?.length) ? (
        <div>
          {state.recall_covered && state.recall_covered.length > 0 ? (
            <p>Covered: {state.recall_covered.join("; ")}</p>
          ) : null}
          {state.recall_missing && state.recall_missing.length > 0 ? (
            <p>Missed: {state.recall_missing.join("; ")}</p>
          ) : null}
        </div>
      ) : null}
      {state.hint_text ? (
        <p>
          {state.hint_source === "ai" ? <Chip tone="ai">AI</Chip> : null} Hint: {state.hint_text}
        </p>
      ) : null}
    </InlineNotice>
  );
}
