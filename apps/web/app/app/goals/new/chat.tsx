"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import styles from "./wizard.module.css";

type Tool = "quick" | "plan";
type Role = "dolphin" | "you";

type Message = { id: string; role: Role; text: string };

type Budget =
  | { mode: "one_off"; minutes: number; preferred: number }
  | { mode: "weekly"; per: number; days: number; preferred: number };

type ProposalItem = {
  competency_key: string;
  name: string;
  competency_name?: string;
  reason_text?: string;
};

type Proposal = {
  usable_minutes: number;
  included: ProposalItem[];
  deferred: ProposalItem[];
};

const SUBJECTS = [
  { key: "python", label: "Python" },
  { key: "math", label: "Foundational math" },
  { key: "software", label: "Software practice" },
  { key: "general", label: "Something else" },
] as const;

function inferSubject(text: string): string | null {
  const value = text.toLowerCase();
  if (/\bpython\b|names and calls/.test(value)) return "python";
  if (/fraction|denominator|\bmath\b|algebra/.test(value)) return "math";
  if (/failing test|\bsoftware\b|\bbug\b|debug/.test(value)) return "software";
  if (/something else|spanish|greeting|travel/.test(value)) return "general";
  const chip = SUBJECTS.find((item) => value === item.label.toLowerCase());
  return chip?.key ?? null;
}

function inferBudget(text: string): Budget | null {
  const weekly =
    text.match(/(\d+)\s*minutes?\s*(?:a|per)\s*day\s*for\s*(\d+)\s*days/i) ||
    text.match(/(\d+)\s*min(?:utes)?\s*[×x]\s*(\d+)/i);
  if (weekly) {
    const per = Number(weekly[1]);
    return { mode: "weekly", per, days: Number(weekly[2]), preferred: Math.min(30, per) };
  }
  const one = text.match(/(\d+)\s*min(?:utes)?\b/i);
  if (one) {
    const minutes = Number(one[1]);
    return { mode: "one_off", minutes, preferred: Math.min(30, minutes) };
  }
  return null;
}

function titleFrom(text: string): string {
  const line = text.split(/[.\n]/)[0]?.trim() || text.trim();
  return line.slice(0, 80);
}

function budgetSummary(budget: Budget): string {
  if (budget.mode === "one_off") return `${budget.minutes} minutes in one sitting`;
  return `${budget.per} minutes a day for ${budget.days} days`;
}

let messageId = 0;
function nextId(): string {
  messageId += 1;
  return `m${messageId}`;
}

export function GoalChat({
  initialPrompt = "",
  tool = "plan",
}: {
  initialPrompt?: string;
  tool?: Tool;
}) {
  const [ready, setReady] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [request, setRequest] = useState("");
  const [subject, setSubject] = useState<string | null>(null);
  const [outcome, setOutcome] = useState("");
  const [budget, setBudget] = useState<Budget | null>(tool === "quick" ? { mode: "one_off", minutes: 120, preferred: 30 } : null);
  const [asking, setAsking] = useState<"request" | "subject" | "outcome" | "time" | "plan" | "done">("request");
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [goalId, setGoalId] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const creating = useRef(false);

  function say(role: Role, text: string) {
    setMessages((current) => [...current, { id: nextId(), role, text }]);
  }

  useEffect(() => {
    if (started) return;
    setStarted(true);
    const params = new URLSearchParams(window.location.search);
    const text = (initialPrompt || params.get("q") || "").trim();
    const chosen: Tool = params.get("tool") === "quick" || tool === "quick" ? "quick" : "plan";
    if (chosen === "quick") {
      setBudget({ mode: "one_off", minutes: 120, preferred: 30 });
    }
    if (text) {
      setMessages([{ id: nextId(), role: "you", text }]);
      setRequest(text);
      const found = inferSubject(text);
      const timed = inferBudget(text);
      if (found) setSubject(found);
      if (timed) setBudget(timed);
      if (!found) {
        say("dolphin", "Which subject is this?");
        setAsking("subject");
      } else if (found === "general") {
        say("dolphin", "What should you be able to do when this is done? One sentence is enough.");
        setAsking("outcome");
      } else if (!timed && chosen !== "quick") {
        say("dolphin", "How much time do you have?");
        setAsking("time");
      } else {
        setAsking("plan");
      }
    } else {
      say("dolphin", "What do you want to learn?");
      setAsking("request");
    }
    setReady(true);
  }, [initialPrompt, started, tool]);

  useEffect(() => {
    if (asking !== "plan" || goalId || pending) return;
    if (!request || !subject || !budget) return;
    if (subject === "general" && !outcome) return;
    void createPlan();
    // createPlan is stable enough for this one-shot step.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asking, goalId, pending, request, subject, budget, outcome]);

  async function createPlan() {
    if (!subject || !budget || creating.current) return;
    creating.current = true;
    setPending(true);
    setError(null);
    const title = titleFrom(subject === "general" && outcome ? outcome : request);
    const payload: Record<string, unknown> = {
      title,
      raw_request: request,
      domain_key: subject,
      priority: "understand",
      time_budget:
        budget.mode === "one_off"
          ? {
              mode: "one_off",
              one_off_minutes: budget.minutes,
              preferred_session_minutes: budget.preferred,
            }
          : {
              mode: "weekly",
              weekly_minutes_per_day: budget.per,
              horizon_days: budget.days,
              preferred_session_minutes: budget.preferred,
            },
    };
    if (subject === "general") {
      payload.general = {
        topic: title,
        outcomes: [{ statement: outcome }],
      };
    }
    const created = await fetch("/api/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const goal = (await created.json()) as { id?: string; error?: { message?: string } };
    if (!created.ok || !goal.id) {
      setPending(false);
      setError(goal.error?.message ?? "Could not start this plan.");
      return;
    }
    const proposed = await fetch(`/api/goals/${goal.id}/plan-proposals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ priority: "understand", skip_competency_keys: [] }),
    });
    setPending(false);
    if (!proposed.ok) {
      setError("Could not build a plan from that.");
      return;
    }
    const body = (await proposed.json()) as Proposal;
    setGoalId(goal.id);
    setProposal(body);
    const subjectName = SUBJECTS.find((item) => item.key === subject)?.label ?? subject;
    say(
      "dolphin",
      `Here is a plan for ${title}. ${subjectName}. ${budgetSummary(budget)}. It uses ${body.usable_minutes} of your minutes.`,
    );
  }

  function onReply(text: string) {
    const cleaned = text.trim();
    if (!cleaned || pending || asking === "done" || asking === "plan") return;
    say("you", cleaned);
    if (asking === "request") {
      setRequest(cleaned);
      const found = inferSubject(cleaned);
      const timed = inferBudget(cleaned);
      if (found) setSubject(found);
      if (timed) setBudget(timed);
      if (!found) {
        say("dolphin", "Which subject is this?");
        setAsking("subject");
        return;
      }
      if (found === "general") {
        say("dolphin", "What should you be able to do when this is done? One sentence is enough.");
        setAsking("outcome");
        return;
      }
      if (!timed && tool !== "quick" && !budget) {
        say("dolphin", "How much time do you have?");
        setAsking("time");
        return;
      }
      setAsking("plan");
      return;
    }
    if (asking === "subject") {
      const found = inferSubject(cleaned);
      if (!found) {
        say("dolphin", "Pick Python, foundational math, software practice, or something else.");
        return;
      }
      setSubject(found);
      const timed = inferBudget(`${request} ${cleaned}`);
      if (timed) setBudget(timed);
      if (found === "general") {
        say("dolphin", "What should you be able to do when this is done? One sentence is enough.");
        setAsking("outcome");
        return;
      }
      if (!budget && !timed && tool !== "quick") {
        say("dolphin", "How much time do you have?");
        setAsking("time");
        return;
      }
      setAsking("plan");
      return;
    }
    if (asking === "outcome") {
      setOutcome(cleaned);
      const timed = inferBudget(`${request} ${cleaned}`);
      if (timed) setBudget(timed);
      if (!budget && !timed && tool !== "quick") {
        say("dolphin", "How much time do you have?");
        setAsking("time");
        return;
      }
      setAsking("plan");
      return;
    }
    if (asking === "time") {
      const timed = inferBudget(cleaned);
      if (!timed) {
        say("dolphin", "Tell me a sitting, like 120 minutes, or 30 minutes a day for 14 days.");
        return;
      }
      setBudget(timed);
      setAsking("plan");
    }
  }

  async function acceptPlan() {
    if (!goalId) return;
    setPending(true);
    const response = await fetch(`/api/goals/${goalId}/plans/accept`, { method: "POST" });
    setPending(false);
    if (!response.ok) {
      setError("Could not accept this plan.");
      return;
    }
    setAsking("done");
    say("dolphin", "Plan accepted. You can start a sitting whenever you are ready.");
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onReply(draft);
    setDraft("");
  }

  const choices =
    asking === "subject"
      ? SUBJECTS.map((item) => item.label)
      : asking === "time"
        ? ["30 min", "120 min", "30 min × 14 days"]
        : [];

  return (
    <main className={styles.shell} data-hydrated={ready ? "true" : "false"}>
      <section className={styles.card}>
        <h1 className={styles.title}>{asking === "done" ? "Plan accepted" : "What do you want to learn?"}</h1>
        <div role="log" aria-live="polite" aria-label="Conversation">
          {messages.map((message) => (
            <p key={message.id} className={styles.step}>
              <strong>{message.role === "dolphin" ? "Dolphin" : "You"}: </strong>
              {message.text}
            </p>
          ))}
        </div>
        {proposal ? (
          <>
            <p className={styles.label}>Included</p>
            <ul>
              {proposal.included.map((item) => (
                <li key={item.competency_key}>{item.competency_name ?? item.name}</li>
              ))}
            </ul>
            <p className={styles.label}>Not in this plan</p>
            {proposal.deferred.length === 0 ? (
              <p className={styles.step}>Nothing is deferred.</p>
            ) : (
              <ul>
                {proposal.deferred.map((item) => (
                  <li key={item.competency_key}>
                    {item.competency_name ?? item.name}. {item.reason_text}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : null}
        {error ? (
          <p className={styles.error} role="alert">
            {error}
          </p>
        ) : null}
        {asking === "plan" && proposal ? (
          <button className={styles.button} type="button" onClick={() => void acceptPlan()} disabled={pending}>
            Accept
          </button>
        ) : null}
        {asking === "done" ? (
          <p className={styles.meta}>
            <a href="/app">Back to home</a>
          </p>
        ) : null}
        {asking !== "plan" && asking !== "done" ? (
          <form className={styles.form} onSubmit={onSubmit}>
            <label className={styles.label} htmlFor="chat-reply">
              Message
            </label>
            <input
              id="chat-reply"
              className={styles.input}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              autoComplete="off"
            />
            <div className={styles.actions}>
              {choices.map((choice) => (
                <button key={choice} className={styles.secondary} type="button" onClick={() => onReply(choice)}>
                  {choice}
                </button>
              ))}
              <button className={styles.button} type="submit">
                Send
              </button>
            </div>
          </form>
        ) : null}
      </section>
    </main>
  );
}
