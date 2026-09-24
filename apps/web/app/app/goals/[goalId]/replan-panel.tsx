"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import styles from "../../../auth.module.css";

type ProposalItem = {
  competency_key: string;
  name: string;
  competency_name?: string;
  effort_low: number;
  effort_high: number;
  reason_text?: string | null;
};

type Proposal = {
  proposal_hash: string;
  usable_minutes: number;
  remaining_minutes: number;
  studied_minutes: number;
  included: ProposalItem[];
  deferred: ProposalItem[];
  priority_label?: string;
  priority_effect?: string;
};

export function ReplanPanel({ goalId }: { goalId: string }) {
  const router = useRouter();
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function preview() {
    setPending(true);
    setError(null);
    try {
      const response = await fetch(`/api/goals/${goalId}/replan-proposals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as {
          error?: { message?: string };
        } | null;
        setError(body?.error?.message ?? "Could not preview a new plan.");
        setProposal(null);
        return;
      }
      setProposal((await response.json()) as Proposal);
    } finally {
      setPending(false);
    }
  }

  async function accept() {
    if (!proposal) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const response = await fetch(`/api/goals/${goalId}/replan/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proposal_hash: proposal.proposal_hash }),
      });
      if (response.status === 409) {
        setError("This plan preview is out of date. Request a new preview.");
        setProposal(null);
        return;
      }
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as {
          error?: { message?: string };
        } | null;
        setError(body?.error?.message ?? "Could not accept this plan.");
        return;
      }
      setProposal(null);
      router.refresh();
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      {!proposal ? (
        <button className={styles.button} type="button" disabled={pending} onClick={() => void preview()}>
          {pending ? "Working…" : "Update plan"}
        </button>
      ) : (
        <div>
          <h2 className={styles.meta}>Proposed plan</h2>
          <p className={styles.meta}>
            About {proposal.remaining_minutes} minutes left after {proposal.studied_minutes}{" "}
            studied. {proposal.priority_label ? `${proposal.priority_label}.` : ""}{" "}
            {proposal.priority_effect ?? ""}
          </p>
          <h3 className={styles.meta}>Included</h3>
          <ul>
            {proposal.included.map((item) => (
              <li key={item.competency_key}>
                {item.competency_name || item.name}. ~{item.effort_low}–{item.effort_high} min
              </li>
            ))}
          </ul>
          <h3 className={styles.meta}>Not in this plan</h3>
          {proposal.deferred.length === 0 ? (
            <p className={styles.meta}>Nothing was deferred.</p>
          ) : (
            <ul>
              {proposal.deferred.map((item) => (
                <li key={item.competency_key}>
                  {item.competency_name || item.name}. {item.reason_text}
                </li>
              ))}
            </ul>
          )}
          <button className={styles.button} type="button" disabled={pending} onClick={() => void accept()}>
            {pending ? "Working…" : "Accept"}
          </button>
          <button
            className={styles.button}
            type="button"
            disabled={pending}
            onClick={() => setProposal(null)}
            style={{ marginLeft: 8, background: "transparent", color: "inherit", border: "1px solid currentColor" }}
          >
            Cancel
          </button>
        </div>
      )}
      {error ? <p className={styles.meta}>{error}</p> : null}
    </div>
  );
}
