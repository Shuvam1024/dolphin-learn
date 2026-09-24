export type StudioActions = {
  primary: "submit" | "continue" | "fresh_check" | "finish";
  can_hint: boolean;
  can_reveal: boolean;
  can_fresh_check: boolean;
  can_pause: boolean;
  can_explain_differently: boolean;
  stop_point: boolean;
  awaiting_self_report?: boolean;
  can_keep_going?: boolean;
};

export type StudioTutor = {
  enabled: boolean;
  pending_request_id: string;
};

export type StudioActivityState = {
  recorded: boolean;
  response: string;
  outcome: string;
  assistance: string;
  hint_text: string;
  hint_source: "seed" | "ai";
  revealed_answer: string;
  explanation: string;
  misconception_note: string;
  misconception_source: "seed" | "ai";
  alt_explanation: string;
  repeat: boolean;
  self_rating?: string;
  awaiting_self_report?: boolean;
  recall_covered?: string[];
  recall_missing?: string[];
  recall_feedback?: string;
};

export type StudioChoice = { id: string; label: string };

export type StudioActivity = {
  activity_type: string;
  item_id: string;
  title: string;
  prompt_markdown: string;
  body_markdown: string;
  input_kind: "choice" | "text" | "number" | "recall" | "none";
  choices: StudioChoice[];
  provisional: boolean;
  state: StudioActivityState;
};

export type SummaryItem = {
  competency_key: string;
  competency_name: string;
  lesson_title: string;
  title: string;
  reason: string;
  attempt_id: string;
  outcome: string;
  choice: string;
  note?: string;
  source?: string;
  rating?: string;
};

export type StudioSession = {
  id: string;
  status: string;
  active_minutes: number;
  target_minutes: number;
  goal: { id: string; title: string } | null;
  lesson: { title: string; competency_name: string } | null;
  position: number;
  total: number;
  remaining_estimate: { low: number; high: number } | null;
  studio_activity: StudioActivity | null;
  activity: {
    activity_type: string;
    title: string;
    prompt: string;
    body: string;
    mode: "guided";
    recorded_choice: string;
    help: string;
    revealed_choice: string;
    outcome: string;
    attempt_assistance: string;
  } | null;
  actions: StudioActions | null;
  tutor: StudioTutor | null;
  summary: {
    topics: SummaryItem[];
    independent_attempts: SummaryItem[];
    unresolved: SummaryItem[];
    suggested_review: SummaryItem[];
    watch_out_for?: SummaryItem[];
    showed_on_your_own?: SummaryItem[];
    practiced_with_help?: SummaryItem[];
    self_reported?: SummaryItem[];
    next_review?: { lesson: string; in_days: number } | null;
    minutes_studied?: number;
    next_step?: { kind: string; href: string; label: string } | null;
    note: string;
  } | null;
};

export function primaryLabel(
  primary: StudioActions["primary"],
  activityType: string,
): string {
  if (primary === "submit") return "Submit answer";
  if (primary === "fresh_check") return "Try a fresh question";
  if (primary === "finish") return "Finish session";
  if (activityType === "worked_example") return "Now you try";
  return "Next activity";
}
