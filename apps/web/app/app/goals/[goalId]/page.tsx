import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../../auth.module.css";
import { ReplanPanel } from "./replan-panel";

type Overview = {
  goal_id: string;
  title: string;
  version_number: number;
  usable_minutes: number;
  studied_minutes: number;
  remaining_minutes: number;
  feasibility_note: string;
  why_next: string;
  continue_action: { kind: string; href: string; goal_id: string };
  activities: {
    id: string;
    position: number;
    title: string;
    label: string;
    competency_key: string;
    competency_name: string;
    lesson_title: string;
    facet: string;
    facet_label: string;
    effort: { low: number; high: number };
  }[];
  deferred: {
    competency_key: string;
    competency_name: string;
    reason_code: string;
    reason_text: string;
  }[];
  plan_history: {
    version_number: number;
    usable_minutes: number;
    rationale: string;
  }[];
};

async function loadOverview(goalId: string): Promise<Overview | null> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/goals/${goalId}/overview`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as Overview;
}

export default async function GoalPathPage({
  params,
}: {
  params: Promise<{ goalId: string }>;
}) {
  const { goalId } = await params;
  const overview = await loadOverview(goalId);
  if (!overview) {
    return (
      <main className={styles.shell}>
        <section className={styles.card}>
          <h1 className={styles.title}>Goal not found</h1>
        </section>
      </main>
    );
  }
  const next = overview.continue_action;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Goal path</p>
        <h1 className={styles.title}>{overview.title}</h1>
        <p className={styles.meta}>Plan version {overview.version_number}</p>
        <p className={styles.lede}>
          About {overview.remaining_minutes} of{" "}
          {overview.remaining_minutes + overview.studied_minutes} minutes left
        </p>
        <p className={styles.meta}>
          Studied: {overview.studied_minutes}{" "}
          {overview.studied_minutes === 1 ? "minute" : "minutes"}. A date is not study time.
        </p>
        <p className={styles.lede}>{overview.feasibility_note}</p>
        <p className={styles.meta}>{overview.why_next}</p>
        <ReplanPanel goalId={overview.goal_id} />
        {next.kind === "resume" ? (
          <p className={styles.meta}>
            <Link href={next.href}>Continue</Link>
          </p>
        ) : (
          <p className={styles.meta}>
            <Link href={`/app/goals/${overview.goal_id}/start`}>Continue</Link>
          </p>
        )}
        <h2 className={styles.meta}>Lessons</h2>
        <ol>
          {overview.activities.map((item) => (
            <li key={item.id}>
              {item.title}. {item.facet_label}. ~{item.effort.low}–{item.effort.high} min
            </li>
          ))}
        </ol>
        <h2 className={styles.meta}>Not in this plan</h2>
        {overview.deferred.length === 0 ? (
          <p className={styles.meta}>Nothing was deferred.</p>
        ) : (
          <ul>
            {overview.deferred.map((item) => (
              <li key={item.competency_key}>
                {item.competency_name}. {item.reason_text}
              </li>
            ))}
          </ul>
        )}
        {overview.plan_history.length > 0 ? (
          <details>
            <summary className={styles.meta}>Plan history</summary>
            <ul>
              {overview.plan_history.map((row) => (
                <li key={row.version_number}>
                  Version {row.version_number} · {row.usable_minutes} minutes. {row.rationale}
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </section>
    </main>
  );
}
