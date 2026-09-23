"use client";

import { FormEvent, useEffect, useState } from "react";

import styles from "./wizard.module.css";

type Mode = "one_off" | "weekly";

type SavedGoal = {
  id: string;
  title: string;
  summary: string;
};

type Proposal = {
  included: { competency_key: string; name: string }[];
  deferred: { competency_key: string; name: string; reason_code: string }[];
};

type DomainOption = {
  key: string;
  name: string;
};

const PRIORITIES = ["Focus one topic", "Cover more ground", "Leave room for review"] as const;

function wholeNumber(value: string): number | null {
  if (!/^\d+$/.test(value.trim())) {
    return null;
  }
  return Number(value);
}

export function GoalWizard() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [title, setTitle] = useState("");
  const [rawRequest, setRawRequest] = useState("");
  const [domains, setDomains] = useState<DomainOption[]>([]);
  const [domainKey, setDomainKey] = useState("");
  const [mode, setMode] = useState<Mode>("one_off");
  const [oneOffMinutes, setOneOffMinutes] = useState("120");
  const [weeklyMinutes, setWeeklyMinutes] = useState("30");
  const [horizonDays, setHorizonDays] = useState("14");
  const [preferred, setPreferred] = useState("30");
  const [priority, setPriority] = useState<(typeof PRIORITIES)[number]>("Focus one topic");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState<SavedGoal | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const response = await fetch("/api/domains");
      if (!response.ok || cancelled) {
        return;
      }
      const body = (await response.json()) as DomainOption[];
      if (cancelled) {
        return;
      }
      setDomains(body);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!saved) {
      return;
    }
    let cancelled = false;
    void (async () => {
      const response = await fetch(`/api/goals/${saved.id}/plan-proposals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
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
  }, [saved]);

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
    setError(null);
  }

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

  function onGoalText(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !rawRequest.trim()) {
      setError("Add a title and what you want to learn.");
      return;
    }
    if (!domainKey) {
      setError("Choose a subject we can check today.");
      return;
    }
    setError(null);
    setStep(2);
  }

  function onAvailability(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!budgetPayload()) {
      setError("Minutes must be zero or more, and a weekly plan needs at least one day.");
      return;
    }
    setError(null);
    setStep(3);
  }

  async function onPriority(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const timeBudget = budgetPayload();
    if (!timeBudget) {
      setError("Check the minutes on the previous step.");
      setStep(2);
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch("/api/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title.trim(),
        raw_request: rawRequest.trim(),
        domain_key: domainKey,
        normalized_objective: `Priority: ${priority}`,
        time_budget: timeBudget,
      }),
    });
    const body = (await response.json()) as {
      id?: string;
      title?: string;
      error?: { message?: string };
    };
    setPending(false);
    if (!response.ok || !body.id || !body.title) {
      setError(body.error?.message ?? "Could not save this goal.");
      return;
    }
    setSaved({ id: body.id, title: body.title, summary: summaryFor(timeBudget) });
  }

  if (saved) {
    return (
      <main className={styles.shell}>
        <section className={styles.card}>
          <p className={styles.kicker}>Goal</p>
          <h1 className={styles.title}>{accepted ? "Plan accepted" : "Goal saved"}</h1>
          <p className={styles.step}>
            {saved.title}. Subject: {domainKey}. {saved.summary}. Priority: {priority}.
          </p>
          {proposal ? (
            <>
              <p className={styles.label}>Included</p>
              <ul>
                {proposal.included.map((item) => (
                  <li key={item.competency_key}>{item.competency_key}</li>
                ))}
              </ul>
              <p className={styles.label}>Deferred</p>
              {proposal.deferred.length === 0 ? (
                <p className={styles.step}>Nothing is deferred.</p>
              ) : (
                <ul>
                  {proposal.deferred.map((item) => (
                    <li key={item.competency_key}>
                      {item.competency_key} ({item.reason_code})
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <p className={styles.step}>This preview is not an active plan yet.</p>
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
                Accept plan
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
        <p className={styles.step}>Step {step} of 3</p>
        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}

        {step === 1 ? (
          <form className={styles.form} onSubmit={onGoalText}>
            <label className={styles.label} htmlFor="goal-title">
              Goal title
            </label>
            <input
              id="goal-title"
              className={styles.input}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              autoComplete="off"
              required
            />
            <label className={styles.label} htmlFor="goal-request">
              What do you want to learn?
            </label>
            <textarea
              id="goal-request"
              className={styles.input}
              value={rawRequest}
              onChange={(event) => setRawRequest(event.target.value)}
              rows={4}
              required
            />
            <label className={styles.label} htmlFor="goal-domain">
              Subject
            </label>
            <select
              id="goal-domain"
              className={styles.select}
              value={domainKey}
              onChange={(event) => setDomainKey(event.target.value)}
              required
            >
              {domains.length === 0 ? (
                <option value="">Loading subjects…</option>
              ) : (
                <option value="">Choose a subject</option>
              )}
              {domains.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.name}
                </option>
              ))}
            </select>
            <p className={styles.meta}>
              These are subjects we can check today. More come later on the same platform.
            </p>
            <div className={styles.actions}>
              <button className={styles.button} type="submit" disabled={!domainKey}>
                Next
              </button>
            </div>
          </form>
        ) : null}

        {step === 2 ? (
          <form className={styles.form} onSubmit={onAvailability}>
            <fieldset className={styles.choices}>
              <legend className={styles.label}>How much time do you have?</legend>
              <label className={styles.choice}>
                <input
                  type="radio"
                  name="budget-mode"
                  value="one_off"
                  checked={mode === "one_off"}
                  onChange={() => setMode("one_off")}
                />
                One block of minutes
              </label>
              <label className={styles.choice}>
                <input
                  type="radio"
                  name="budget-mode"
                  value="weekly"
                  checked={mode === "weekly"}
                  onChange={() => setMode("weekly")}
                />
                Minutes each day for a set number of days
              </label>
            </fieldset>
            {mode === "one_off" ? (
              <>
                <label className={styles.label} htmlFor="one-off-minutes">
                  Total minutes
                </label>
                <input
                  id="one-off-minutes"
                  className={styles.input}
                  inputMode="numeric"
                  value={oneOffMinutes}
                  onChange={(event) => setOneOffMinutes(event.target.value)}
                  required
                />
              </>
            ) : (
              <>
                <label className={styles.label} htmlFor="weekly-minutes">
                  Minutes per day
                </label>
                <input
                  id="weekly-minutes"
                  className={styles.input}
                  inputMode="numeric"
                  value={weeklyMinutes}
                  onChange={(event) => setWeeklyMinutes(event.target.value)}
                  required
                />
                <label className={styles.label} htmlFor="horizon-days">
                  Number of days
                </label>
                <input
                  id="horizon-days"
                  className={styles.input}
                  inputMode="numeric"
                  value={horizonDays}
                  onChange={(event) => setHorizonDays(event.target.value)}
                  required
                />
              </>
            )}
            <label className={styles.label} htmlFor="preferred-session">
              Preferred session length (minutes)
            </label>
            <input
              id="preferred-session"
              className={styles.input}
              inputMode="numeric"
              value={preferred}
              onChange={(event) => setPreferred(event.target.value)}
              required
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
          <form className={styles.form} onSubmit={onPriority}>
            <label className={styles.label} htmlFor="priority">
              Priority
            </label>
            <select
              id="priority"
              className={styles.select}
              value={priority}
              onChange={(event) =>
                setPriority(event.target.value as (typeof PRIORITIES)[number])
              }
            >
              {PRIORITIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <div className={styles.actions}>
              <button className={styles.secondary} type="button" onClick={() => setStep(2)}>
                Back
              </button>
              <button className={styles.button} type="submit" disabled={pending}>
                {pending ? "Saving…" : "Save goal"}
              </button>
            </div>
          </form>
        ) : null}
      </section>
    </main>
  );
}

