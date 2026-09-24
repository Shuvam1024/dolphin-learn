/** Learner-facing display fields paired with machine keys (S53). */
export type NamedCompetency = {
  competency_key: string;
  competency_name: string;
};

export type FacetChip = NamedCompetency & {
  status_facet: string;
  facet_label: string;
};

export type DeferredTopic = NamedCompetency & {
  reason_code: string;
  reason_text: string;
};

/** Session Studio actions and tutor slots (S57). */
export type StudioActions = {
  primary: "submit" | "continue" | "fresh_check" | "finish";
  can_hint: boolean;
  can_reveal: boolean;
  can_fresh_check: boolean;
  can_pause: boolean;
  can_explain_differently: boolean;
  stop_point: boolean;
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
};

export type { ApiErrorEnvelope } from "./error";
