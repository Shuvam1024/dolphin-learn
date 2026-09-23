import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Button, Page, PageHeader, Stack, Surface } from "@/components/ui";
import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../auth.module.css";

type NextAction = {
  kind: string;
  title: string;
  href: string;
  goal_id: string;
};

type HomeSnapshot = {
  next_action: NextAction;
  goals: {
    id: string;
    title: string;
    feasibility_note: string;
    usable_minutes: number;
    studied_minutes: number;
  }[];
  due_reviews: { competency_key: string; reason: string }[];
  recent_evidence: { competency_key: string; status_facet: string }[];
  quick_learn: { href: string; label: string };
};

async function loadHome(): Promise<HomeSnapshot> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  const response = await fetch(`${apiBaseUrl()}/api/v1/home`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  return (await response.json()) as HomeSnapshot;
}

export default async function AppHomePage() {
  const me = await loadMe();
  const acknowledged = Boolean(me.profile.adult_acknowledged_at);

  if (!acknowledged) {
    return (
      <Page>
        <Surface>
          <Stack gap="md">
            <PageHeader
              kicker="Adults 18+"
              title="Before you start"
              subtitle="Dolphin is for adults 18 and older. A child-specific product is not part of this version. Learning notes stay private to your account."
            />
            <p>
              <Link href="/privacy">Read the privacy summary</Link>
            </p>
            <form action="/api/session/acknowledge" method="post">
              <Button type="submit" variant="primary">
                I am 18 or older and I understand
              </Button>
            </form>
          </Stack>
        </Surface>
      </Page>
    );
  }

  const home = await loadHome();
  const empty = home.goals.length === 0;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Home</p>
        {empty ? (
          <>
            <h1 className={styles.title}>You are in</h1>
            <p className={styles.lede}>
              Signed in as {me.email ?? me.auth_subject}. You don&apos;t have a goal yet. Create
              one and Dolphin will fit a plan to the minutes you have.
            </p>
            <p className={styles.meta}>
              <Link href="/app/goals/new">Create a goal</Link>
            </p>
          </>
        ) : (
          <>
            <h1 className={styles.title}>What now?</h1>
            <p className={styles.lede}>{home.next_action.title}</p>
            {home.next_action.href ? (
              <p className={styles.meta}>
                <Link href={home.next_action.href}>{home.next_action.title}</Link>
              </p>
            ) : (
              <form action="/api/sessions" method="post">
                <input type="hidden" name="goal_id" value={home.next_action.goal_id} />
                <button className={styles.button} type="submit">
                  {home.next_action.title}
                </button>
              </form>
            )}
            <h2 className={styles.meta}>Goals</h2>
            <ul>
              {home.goals.map((goal) => (
                <li key={goal.id}>
                  <Link href={`/app/goals/${goal.id}`}>{goal.title}</Link>. Usable minutes:{" "}
                  {goal.usable_minutes}. Studied: {goal.studied_minutes}. {goal.feasibility_note}
                </li>
              ))}
            </ul>
            <h2 className={styles.meta}>Due reviews</h2>
            {home.due_reviews.length === 0 ? (
              <p className={styles.meta}>Nothing is due.</p>
            ) : (
              <ul>
                {home.due_reviews.map((item) => (
                  <li key={item.competency_key}>
                    {item.competency_key}. {item.reason}
                  </li>
                ))}
              </ul>
            )}
            <h2 className={styles.meta}>Independent evidence</h2>
            {home.recent_evidence.length === 0 ? (
              <p className={styles.meta}>No independent evidence yet.</p>
            ) : (
              <ul>
                {home.recent_evidence.map((item) => (
                  <li key={item.competency_key}>
                    {item.competency_key}: {item.status_facet}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
        <p className={styles.meta}>
          <Link href={home.quick_learn.href}>{home.quick_learn.label}</Link>
        </p>
        <form action="/api/session/logout" method="post">
          <button className={styles.button} type="submit">
            Log out
          </button>
        </form>
      </section>
    </main>
  );
}
