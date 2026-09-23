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

export type { ApiErrorEnvelope } from "./error";
