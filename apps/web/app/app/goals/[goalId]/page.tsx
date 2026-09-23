import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../../auth.module.css";

type Overview = {
  goal_id: string;
  title: string;
  version_number: number;
  feasibility_note: string;
  why_next: string;
  continue_action: { kind: string; href: string; goal_id: string };
  activities: {
    id: string;
    position: number;
    title: string;
    label: string;
    competency_key: string;
  }[];
  deferred: { competency_key: string; reason_code: string }[];
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
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }
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
        <p className={styles.lede}>{overview.feasibility_note}</p>
        <p className={styles.meta}>{overview.why_next}</p>
        {next.kind === "resume" ? (
          <p className={styles.meta}>
            <Link href={next.href}>Continue</Link>
          </p>
        ) : (
          <form action="/api/sessions" method="post">
            <input type="hidden" name="goal_id" value={next.goal_id} />
            <button className={styles.button} type="submit">
              Continue
            </button>
          </form>
        )}
        <h2 className={styles.meta}>Activities</h2>
        <ol>
          {overview.activities.map((item) => (
            <li key={item.id}>
              {item.title}. {item.label}
            </li>
          ))}
        </ol>
        <h2 className={styles.meta}>Deferred</h2>
        {overview.deferred.length === 0 ? (
          <p className={styles.meta}>Nothing was deferred.</p>
        ) : (
          <ul>
            {overview.deferred.map((item) => (
              <li key={item.competency_key}>
                {item.competency_key}. {item.reason_code}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
