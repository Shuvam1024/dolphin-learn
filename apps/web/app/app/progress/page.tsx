import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../auth.module.css";

type Facet = {
  competency_key: string;
  status_facet: string;
};

type ProgressSnapshot = {
  facets: Facet[];
  unassessed: Facet[];
};

async function loadProgress(): Promise<ProgressSnapshot> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/progress`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as ProgressSnapshot;
}

export default async function ProgressPage() {
  const progress = await loadProgress();
  const empty = progress.facets.length === 0 && progress.unassessed.length === 0;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Progress</p>
        <h1 className={styles.title}>{empty ? "No evidence yet" : "Evidence"}</h1>
        <p className={styles.lede}>
          Exposed means an attempt that was not correct. Practicing means a correct answer after
          help. Independently demonstrated means a correct answer with no help. Unassessed means
          the plan has no stored attempt yet. There is no global mastery score.
        </p>
        {progress.facets.length > 0 ? (
          <ul>
            {progress.facets.map((item) => (
              <li key={item.competency_key}>
                {item.competency_key}: {item.status_facet}
              </li>
            ))}
          </ul>
        ) : null}
        {progress.unassessed.length > 0 ? (
          <>
            <h2 className={styles.meta}>Unassessed</h2>
            <ul>
              {progress.unassessed.map((item) => (
                <li key={item.competency_key}>
                  {item.competency_key}: unassessed
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className={styles.meta}>
            Competencies you have not tried stay unassessed. A gap is not a zero score.
          </p>
        )}
      </section>
    </main>
  );
}
