"use client";

import { FormEvent, useEffect, useState } from "react";

import styles from "./wizard.module.css";

type Mode = "one_off" | "weekly";
type Step = 1 | 2 | 3 | 4 | 5;

type SavedGoal = {
  id: string;
  title: string;
  summary: string;
};

type ProposalItem = {
  competency_key: string;
  name: string;
  competency_name?: string;
  effort_low: number;
  effort_high: number;
  reason_code?: string;
  reason_text?: string;
};

type Proposal = {
  usable_minutes: number;
  estimated_required_low: number;
  estimated_required_high: number;
  included: ProposalItem[];
  deferred: ProposalItem[];
  priority_label?: string;
  priority_effect?: string;
  plan_explanation?: {
    summary: string;
    why_order: string;
    what_is_left_out: string;
    source: string;
  } | null;
};

type DomainOption = { key: string; name: string };

type Draft = {
  step: Step;
  learnText: string;
  title: string;
  domainKey: string;
  outcomes: string[];
  notes: string;
  mode: Mode;
  oneOffMinutes: string;
  weeklyMinutes: string;
  horizonDays: string;
  preferred: string;
  priority: PriorityValue;
  skipKeys: string[];
  suggestedSkips: string[];
  aiSuggested: boolean;
};

const PRIORITY_OPTIONS = [
  { label: "Cover more ground", value: "understand" },
  { label: "Focus one topic", value: "apply" },
  { label: "Leave room for review", value: "make_it_stick" },
] as const;

type PriorityValue = (typeof PRIORITY_OPTIONS)[number]["value"];

const SUBJECT_CHIPS = [
  { key: "python", label: "Python" },
  { key: "math", label: "Foundational math" },
  { key: "software", label: "Software practice" },
  { key: "general", label: "Something else" },
] as const;

const TIME_PRESETS: Array<{
  label: string;
  mode: Mode;
  oneOff?: number;
  weekly?: number;
  days?: number;
  preferred: number;
}> = [
  { label: "10 min", mode: "one_off", oneOff: 10, preferred: 10 },
  { label: "15 min", mode: "one_off", oneOff: 15, preferred: 15 },
  { label: "30 min", mode: "one_off", oneOff: 30, preferred: 30 },
  { label: "60 min", mode: "one_off", oneOff: 60, preferred: 30 },
  { label: "120 min", mode: "one_off", oneOff: 120, preferred: 30 },
  { label: "15 × 7", mode: "weekly", weekly: 15, days: 7, preferred: 15 },
  { label: "30 × 14", mode: "weekly", weekly: 30, days: 14, preferred: 30 },
  { label: "45 × 10", mode: "weekly", weekly: 45, days: 10, preferred: 45 },
];

const DRAFT_KEY = "dolphin.wizard.v2";

function wholeNumber(value: string): number | null {
  if (!/^\d+$/.test(value.trim())) {
    return null;
  }
  return Number(value);
}

function labelFor(value: PriorityValue): string {
  return PRIORITY_OPTIONS.find((item) => item.value === value)?.label ?? value;
}

function hoursSentence(mode: Mode, oneOff: string, weekly: string, days: string): string {
  if (mode === "one_off") {
    const minutes = wholeNumber(oneOff) ?? 0;
    const hours = minutes / 60;
    const hourLabel =
      hours === 1 ? "1 hour" : Number.isInteger(hours) ? `${hours} hours` : `${hours} hours`;
    return `${minutes} minutes = ${hourLabel} of study`;
  }
  const per = wholeNumber(weekly) ?? 0;
  const horizon = wholeNumber(days) ?? 0;
  const total = per * horizon;
  const hours = total / 60;
  const hourLabel =
    hours === 1 ? "1 hour" : Number.isInteger(hours) ? `${hours} hours` : `${hours} hours`;
  return `${per} minutes × ${horizon} sittings = ${hourLabel} of study`;
}

function loadDraft(): Draft | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as Draft;
  } catch {
    return null;
  }
}

export function GoalWizard({
  initialPrompt = "",
  tool = "plan",
}: {
  initialPrompt?: string;
  tool?: "quick" | "plan";
}) {
  const [step, setStep] = useState<Step>(1);
  const [learnText, setLearnText] = useState("");
  const [title, setTitle] = useState("");
  const [outcomes, setOutcomes] = useState<string[]>([""]);
  const [notes, setNotes] = useState("");
  const [domains, setDomains] = useState<DomainOption[]>([]);
  const [domainKey, setDomainKey] = useState("");
  const [mode, setMode] = useState<Mode>("one_off");
  const [oneOffMinutes, setOneOffMinutes] = useState("120");
  const [weeklyMinutes, setWeeklyMinutes] = useState("30");
  const [horizonDays, setHorizonDays] = useState("14");
  const [preferred, setPreferred] = useState("30");
  const [priority, setPriority] = useState<PriorityValue>("apply");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState<SavedGoal | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [ready, setReady] = useState(false);
  const [aiSuggested, setAiSuggested] = useState(false);
  const [suggestedSkips, setSuggestedSkips] = useState<string[]>([]);
  const [skipKeys, setSkipKeys] = useState<string[]>([]);
  const [customTime, setCustomTime] = useState(false);

  useEffect(() => {
    const draft = loadDraft();
    if (draft && !initialPrompt) {
      setStep(draft.step);
      setLearnText(draft.learnText);
      setTitle(draft.title);
      setDomainKey(draft.domainKey);
      setOutcomes(draft.outcomes.length ? draft.outcomes : [""]);
      setNotes(draft.notes);
      setMode(draft.mode);
      setOneOffMinutes(draft.oneOffMinutes);
      setWeeklyMinutes(draft.weeklyMinutes);
      setHorizonDays(draft.horizonDays);
      setPreferred(draft.preferred);
      setPriority(draft.priority);
      setSkipKeys(draft.skipKeys);
      setSuggestedSkips(draft.suggestedSkips);
      setAiSuggested(draft.aiSuggested);
    } else if (initialPrompt) {
      setLearnText(initialPrompt);
      if (tool === "quick") {
        setMode("one_off");
        setOneOffMinutes("120");
        setPreferred("30");
      }
    }
    setReady(true);
  }, [initialPrompt, tool]);

  useEffect(() => {
    if (!ready) {
      return;
    }
    const draft: Draft = {
      step,
      learnText,
      title,
      domainKey,
      outcomes,
      notes,
      mode,
      oneOffMinutes,
      weeklyMinutes,
      horizonDays,
      preferred,
      priority,
      skipKeys,
      suggestedSkips,
      aiSuggested,
    };
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
  }, [
    ready,
    step,
    learnText,
    title,
    domainKey,
    outcomes,
    notes,
    mode,
    oneOffMinutes,
    weeklyMinutes,
    horizonDays,
    preferred,
    priority,
    skipKeys,
    suggestedSkips,
    aiSuggested,
  ]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const response = await fetch("/api/domains");
      if (!response.ok || cancelled) {
        return;
      }
      const body = (await response.json()) as DomainOption[];
      if (!cancelled) {
        setDomains(body);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!saved || accepted) {
      return;
    }
    let cancelled = false;
    void (async () => {
      await fetch(`/api/goals/${saved.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority }),
      });
      if (cancelled) {
        return;
      }
      const response = await fetch(`/api/goals/${saved.id}/plan-proposals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority, skip_competency_keys: skipKeys }),
      });
      if (!response.ok || cancelled) {
        return;
      }
      const body = (await response.json()) as Proposal;
      if (!cancelled) {
        setProposal(body);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [saved, priority, accepted, skipKeys]);

  function budgetPayload() {
    const preferredSession = wholeNumber(preferred);
    if (preferredSession === null) {
      return null;
    }
    if (mode === "one_off") {
      const minutes = wholeNumber(oneOffMinutes);
      if (minutes === null) {
        return null;
      }
      return {
        mode,
        one_off_minutes: minutes,
        preferred_session_minutes: preferredSession,
      };
    }
    const perDay = wholeNumber(weeklyMinutes);
    const days = wholeNumber(horizonDays);
    if (perDay === null || days === null || days <= 0) {
      return null;
    }
    return {
      mode,
      weekly_minutes_per_day: perDay,
      horizon_days: days,
      preferred_session_minutes: preferredSession,
    };
  }

  function summaryFor(payload: NonNullable<ReturnType<typeof budgetPayload>>): string {
    if (payload.mode === "one_off") {
      return `${payload.one_off_minutes} minutes in one sitting`;
    }
    return `${payload.weekly_minutes_per_day} minutes a day for ${payload.horizon_days} days`;
  }

  async function suggestFromText() {
    if (!learnText.trim()) {
      setError("Write what you want to learn.");
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch("/api/goals/normalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: learnText.trim() }),
    });
    setPending(false);
    if (!response.ok) {
      // Manual fields stay available.
      if (!title.trim()) {
        setTitle(learnText.trim().slice(0, 60));
      }
      return;
    }
    const body = (await response.json()) as {
      title: string;
      domain_key: string;
      outcomes: string[];
    };
    setTitle(body.title);
    setDomainKey(body.domain_key);
    setOutcomes(body.outcomes.length ? body.outcomes : [""]);
    setAiSuggested(true);
  }

  function onLearnNext(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !learnText.trim()) {
      setError("Add a title and what you want to learn.");
      return;
    }
    if (!domainKey) {
      setError("Choose a subject.");
      return;
    }
    if (domainKey === "general") {
      const filled = outcomes.map((item) => item.trim()).filter(Boolean);
      if (filled.length < 1 || filled.length > 5) {
        setError("Add one to five outcomes for Something else.");
        return;
      }
      setOutcomes(filled);
    }
    setError(null);
    setStep(2);
  }

  function onTimeNext(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!budgetPayload()) {
      setError("Minutes must be zero or more, and a weekly plan needs at least one day.");
      return;
    }
    setError(null);
    setStep(3);
  }

  function onFocusNext(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (domainKey === "general") {
      void saveAndPreview([]);
      return;
    }
    setStep(4);
  }

  async function saveGoalOnly(): Promise<string | null> {
    const timeBudget = budgetPayload();
    if (!timeBudget) {
      setError("Check the minutes on the previous step.");
      setStep(2);
      return null;
    }
    setPending(true);
    setError(null);
    const payload: Record<string, unknown> = {
      title: title.trim(),
      raw_request: learnText.trim(),
      domain_key: domainKey,
      priority,
      normalized_objective: `Priority: ${labelFor(priority)}`,
      time_budget: timeBudget,
    };
    if (domainKey === "general") {
      payload.general = {
        topic: title.trim(),
        outcomes: outcomes
          .map((item) => item.trim())
          .filter(Boolean)
          .map((statement) => ({ statement })),
        notes_markdown: notes.trim() || undefined,
      };
    }
    const response = await fetch("/api/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = (await response.json()) as {
      id?: string;
      title?: string;
      error?: { message?: string };
    };
    setPending(false);
    if (!response.ok || !body.id || !body.title) {
      setError(body.error?.message ?? "Could not save this goal.");
      return null;
    }
    setSaved({ id: body.id, title: body.title, summary: summaryFor(timeBudget) });
    return body.id;
  }

  async function saveAndPreview(skips: string[]) {
    const id = saved?.id ?? (await saveGoalOnly());
    if (!id) {
      return;
    }
    setSkipKeys(skips);
    setStep(5);
  }

  async function onPlacementSkip() {
    await saveAndPreview([]);
  }

  async function onPlacementStart() {
    const id = saved?.id ?? (await saveGoalOnly());
    if (!id) {
      return;
    }
    setPending(true);
    const started = await fetch(`/api/goals/${id}/diagnostic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "start" }),
    });
    if (!started.ok) {
      setPending(false);
      setError("Placement is not available for this subject.");
      return;
    }
    const items = (await started.json()).items as Array<{ activity_version_id: string }>;
    const submitted = await fetch(`/api/goals/${id}/diagnostic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "submit",
        answers: items.slice(0, 3).map((item) => ({
          activity_version_id: item.activity_version_id,
          choice: "a",
        })),
      }),
    });
    setPending(false);
    if (!submitted.ok) {
      setError("Could not finish placement.");
      return;
    }
    const body = (await submitted.json()) as { suggested_skip_keys: string[] };
    setSuggestedSkips(body.suggested_skip_keys || []);
    setSkipKeys(body.suggested_skip_keys || []);
  }

  async function onPlacementConfirm() {
    await saveAndPreview(skipKeys);
  }

  async function acceptPlan() {
    if (!saved) {
      return;
    }
    setPending(true);
    const response = await fetch(`/api/goals/${saved.id}/plans/accept`, { method: "POST" });
    setPending(false);
    if (!response.ok) {
      setError("Could not accept this plan.");
      return;
    }
    setAccepted(true);
    sessionStorage.removeItem(DRAFT_KEY);
    setError(null);
  }

  const checkedSubject = domainKey !== "general" && domainKey !== "";
  const progress = `Step ${step} of 5`;

  if (step === 5 && saved) {
    const domainName = domains.find((item) => item.key === domainKey)?.name ?? domainKey;
    return (
      <main className={styles.shell} data-hydrated={ready ? "true" : "false"}>
        <section className={styles.card}>
          <p className={styles.kicker}>Goal</p>
          <h1 className={styles.title}>{accepted ? "Plan accepted" : "Your plan"}</h1>
          <p className={styles.step}>{progress}</p>
          <p className={styles.step}>
            {saved.title}. Subject: {domainName}. {saved.summary}. Priority: {labelFor(priority)}.
          </p>
          {proposal ? (
            <>
              <p className={styles.label}>
                Plan uses {proposal.usable_minutes} of your minutes (estimate{" "}
                {proposal.estimated_required_low}–{proposal.estimated_required_high})
              </p>
              <p className={styles.label}>Included</p>
              <ul>
                {proposal.included.map((item) => (
                  <li key={item.competency_key}>
                    {item.competency_name ?? item.name}. ~{item.effort_low}–{item.effort_high} min
                  </li>
                ))}
              </ul>
              <p className={styles.label}>Not in this plan</p>
              {proposal.deferred.length === 0 ? (
                <p className={styles.step}>Nothing is deferred.</p>
              ) : (
                <ul>
                  {proposal.deferred.map((item) => (
                    <li key={item.competency_key}>
                      {item.competency_name ?? item.name}. {item.reason_text ?? item.reason_code}
                    </li>
                  ))}
                </ul>
              )}
              {proposal.plan_explanation ? (
                <div>
                  <p className={styles.label}>
                    Why this plan
                    {proposal.plan_explanation.source === "ai" ? " · AI" : ""}
                  </p>
                  <p className={styles.step}>{proposal.plan_explanation.summary}</p>
                  <p className={styles.meta}>{proposal.plan_explanation.why_order}</p>
                  <p className={styles.meta}>{proposal.plan_explanation.what_is_left_out}</p>
                </div>
              ) : null}
            </>
          ) : (
            <p className={styles.step}>Building your plan…</p>
          )}
          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}
          {accepted ? (
            <p className={styles.step}>Refresh keeps this accepted plan.</p>
          ) : (
            <div className={styles.actions}>
              <button
                className={styles.button}
                type="button"
                onClick={() => void acceptPlan()}
                disabled={pending || !proposal}
              >
                Accept
              </button>
              <button
                className={styles.secondary}
                type="button"
                onClick={() => setStep(2)}
              >
                Change time
              </button>
            </div>
          )}
          <p className={styles.meta}>
            <a href="/app">Back to home</a>
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className={styles.shell} data-hydrated={ready ? "true" : "false"}>
      <section className={styles.card}>
        <p className={styles.kicker}>Goal</p>
        <h1 className={styles.title}>Create a goal</h1>
        <p className={styles.step}>{progress}</p>
        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}

        {step === 1 ? (
          <form className={styles.form} onSubmit={onLearnNext}>
            <label className={styles.label} htmlFor="learn-text">
              What do you want to learn?
            </label>
            <textarea
              id="learn-text"
              className={styles.input}
              value={learnText}
              onChange={(event) => setLearnText(event.target.value)}
              rows={4}
              required
            />
            <div className={styles.actions}>
              <button
                className={styles.secondary}
                type="button"
                onClick={() => void suggestFromText()}
                disabled={pending}
              >
                Suggest with AI
              </button>
            </div>
            <label className={styles.label} htmlFor="goal-title">
              Goal title{aiSuggested ? " · AI" : ""}
            </label>
            <input
              id="goal-title"
              className={styles.input}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              autoComplete="off"
              required
            />
            <p className={styles.label}>Subject</p>
            <div className={styles.chips} role="group" aria-label="Topic chips">
              {SUBJECT_CHIPS.map((chip) => (
                <button
                  key={chip.key}
                  type="button"
                  className={domainKey === chip.key ? styles.chipActive : styles.chip}
                  onClick={() => setDomainKey(chip.key)}
                  aria-pressed={domainKey === chip.key}
                >
                  {chip.label}
                </button>
              ))}
            </div>
            {/* Keep a hidden select for older keyboard/e2e flows */}
            <label className={styles.srOnly} htmlFor="goal-domain">
              Subject
            </label>
            <select
              id="goal-domain"
              className={styles.select}
              value={domainKey}
              onChange={(event) => setDomainKey(event.target.value)}
              required
            >
              <option value="">Choose a subject</option>
              {SUBJECT_CHIPS.map((chip) => (
                <option key={chip.key} value={chip.key}>
                  {chip.label}
                </option>
              ))}
              {domains
                .filter((item) => !SUBJECT_CHIPS.some((chip) => chip.key === item.key))
                .map((item) => (
                  <option key={item.key} value={item.key}>
                    {item.name}
                  </option>
                ))}
            </select>
            {domainKey === "general" ? (
              <>
                <p className={styles.label}>Outcomes (I can …)</p>
                {outcomes.map((item, index) => (
                  <input
                    key={index}
                    className={styles.input}
                    aria-label={`Outcome ${index + 1}`}
                    value={item}
                    onChange={(event) => {
                      const next = [...outcomes];
                      next[index] = event.target.value;
                      setOutcomes(next);
                    }}
                  />
                ))}
                {outcomes.length < 5 ? (
                  <button
                    type="button"
                    className={styles.secondary}
                    onClick={() => setOutcomes([...outcomes, ""])}
                  >
                    Add outcome
                  </button>
                ) : null}
                <label className={styles.label} htmlFor="notes">
                  Notes (optional)
                </label>
                <textarea
                  id="notes"
                  className={styles.input}
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={3}
                />
              </>
            ) : null}
            <div className={styles.actions}>
              <button className={styles.button} type="submit" disabled={!domainKey}>
                Next
              </button>
            </div>
          </form>
        ) : null}

        {step === 2 ? (
          <form className={styles.form} onSubmit={onTimeNext}>
            <p className={styles.label}>How much time do you have?</p>
            <div className={styles.chips} role="group" aria-label="Time presets">
              {TIME_PRESETS.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  className={styles.chip}
                  onClick={() => {
                    setCustomTime(false);
                    setMode(preset.mode);
                    setPreferred(String(preset.preferred));
                    if (preset.mode === "one_off") {
                      setOneOffMinutes(String(preset.oneOff));
                    } else {
                      setWeeklyMinutes(String(preset.weekly));
                      setHorizonDays(String(preset.days));
                    }
                  }}
                >
                  {preset.label}
                </button>
              ))}
              <button
                type="button"
                className={styles.chip}
                onClick={() => setCustomTime(true)}
              >
                Custom
              </button>
            </div>
            <p className={styles.step}>
              {hoursSentence(mode, oneOffMinutes, weeklyMinutes, horizonDays)}
            </p>
            {customTime || mode === "one_off" ? (
              <>
                <label className={styles.label} htmlFor="one-off">
                  Total minutes
                </label>
                <input
                  id="one-off"
                  className={styles.input}
                  value={oneOffMinutes}
                  onChange={(event) => {
                    setMode("one_off");
                    setOneOffMinutes(event.target.value);
                  }}
                  inputMode="numeric"
                />
              </>
            ) : null}
            {customTime || mode === "weekly" ? (
              <>
                <label className={styles.label} htmlFor="weekly">
                  Minutes per sitting
                </label>
                <input
                  id="weekly"
                  className={styles.input}
                  value={weeklyMinutes}
                  onChange={(event) => {
                    setMode("weekly");
                    setWeeklyMinutes(event.target.value);
                  }}
                  inputMode="numeric"
                />
                <label className={styles.label} htmlFor="horizon">
                  Number of sittings
                </label>
                <input
                  id="horizon"
                  className={styles.input}
                  value={horizonDays}
                  onChange={(event) => {
                    setMode("weekly");
                    setHorizonDays(event.target.value);
                  }}
                  inputMode="numeric"
                />
              </>
            ) : null}
            <label className={styles.label} htmlFor="preferred">
              Preferred sitting length
            </label>
            <input
              id="preferred"
              className={styles.input}
              value={preferred}
              onChange={(event) => setPreferred(event.target.value)}
              inputMode="numeric"
            />
            <div className={styles.actions}>
              <button className={styles.secondary} type="button" onClick={() => setStep(1)}>
                Back
              </button>
              <button className={styles.button} type="submit">
                Next
              </button>
            </div>
          </form>
        ) : null}

        {step === 3 ? (
          <form className={styles.form} onSubmit={onFocusNext}>
            <p className={styles.label}>How do you want to focus?</p>
            <div className={styles.choices}>
              {PRIORITY_OPTIONS.map((item) => (
                <label key={item.value} className={styles.choice}>
                  <input
                    type="radio"
                    name="priority"
                    value={item.value}
                    checked={priority === item.value}
                    onChange={() => setPriority(item.value)}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
            <div className={styles.actions}>
              <button className={styles.secondary} type="button" onClick={() => setStep(2)}>
                Back
              </button>
              <button className={styles.button} type="submit" disabled={pending}>
                {domainKey === "general" ? "See plan" : "Next"}
              </button>
            </div>
          </form>
        ) : null}

        {step === 4 && checkedSubject ? (
          <div className={styles.form}>
            <p className={styles.label}>Placement (optional)</p>
            <p className={styles.step}>
              A short sample can suggest lessons to skip. Nothing is skipped until you confirm.
            </p>
            {suggestedSkips.length > 0 ? (
              <>
                <p className={styles.label}>Confirm skips</p>
                {suggestedSkips.map((key) => (
                  <label key={key} className={styles.choice}>
                    <input
                      type="checkbox"
                      checked={skipKeys.includes(key)}
                      onChange={(event) => {
                        if (event.target.checked) {
                          setSkipKeys([...skipKeys, key]);
                        } else {
                          setSkipKeys(skipKeys.filter((item) => item !== key));
                        }
                      }}
                    />
                    <span>{key}</span>
                  </label>
                ))}
                <div className={styles.actions}>
                  <button
                    className={styles.button}
                    type="button"
                    onClick={() => void onPlacementConfirm()}
                    disabled={pending}
                  >
                    Continue with skips
                  </button>
                </div>
              </>
            ) : (
              <div className={styles.actions}>
                <button
                  className={styles.button}
                  type="button"
                  onClick={() => void onPlacementStart()}
                  disabled={pending}
                >
                  Try a short sample
                </button>
                <button
                  className={styles.secondary}
                  type="button"
                  onClick={() => void onPlacementSkip()}
                  disabled={pending}
                >
                  Skip placement
                </button>
              </div>
            )}
            <div className={styles.actions}>
              <button className={styles.secondary} type="button" onClick={() => setStep(3)}>
                Back
              </button>
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
