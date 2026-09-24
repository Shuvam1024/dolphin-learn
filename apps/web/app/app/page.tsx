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
  subtitle?: string;
  minutes_estimate?: number;
  href: string;
  goal_id: string;
};

type HomeSnapshot = {
  next_action: NextAction;
  goals: {
    id: string;
    title: string;
    subject_name: string;
    next_lesson_title: string;
    remaining_minutes: number;
    usable_minutes: number;
    studied_minutes: number;
    status: string;
  }[];
  due_reviews: {
    count: number;
    minutes_estimate: number;
    first_lesson_title: string;
  };
  recent_evidence: {
    competency_key: string;
    competency_name: string;
    facet_label: string;
  }[];
  quick_learn: { href: string; label: string };
};

async function loadHome(): Promise<HomeSnapshot | { error: true }> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/home`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) {
      return { error: true };
    }
    return (await response.json()) as HomeSnapshot;
  } catch {
    return { error: true };
  }
}

export default async function AppHomePage() {
  const [me, homeOrError] = await Promise.all([loadMe(), loadHome()]);
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

  if ("error" in homeOrError) {
    return (
      <main className={styles.shell}>
        <section className={styles.card}>
          <p className={styles.kicker}>Home</p>
          <h1 className={styles.title}>Something went wrong</h1>
          <p className={styles.lede}>Home could not load. Try again.</p>
          <p className={styles.meta}>
            <Link href="/app">Retry</Link>
          </p>
        </section>
      </main>
    );
  }

  const home = homeOrError;
  const empty = home.goals.length === 0;
  const primaryHref = home.next_action.href;

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
            <h1 className={styles.title}>{home.next_action.title}</h1>
            {home.next_action.subtitle ? (
              <p className={styles.lede}>{home.next_action.subtitle}</p>
            ) : null}
            {home.next_action.minutes_estimate ? (
              <p className={styles.meta}>About {home.next_action.minutes_estimate} minutes</p>
            ) : null}
            {primaryHref ? (
              <p className={styles.meta}>
                <Link href={primaryHref}>{home.next_action.title}</Link>
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
                  <Link href={`/app/goals/${goal.id}`}>{goal.title}</Link>
                  {" · "}
                  {goal.subject_name}
                  {goal.next_lesson_title ? ` · next: ${goal.next_lesson_title}` : ""}
                  {` · ${goal.remaining_minutes} of ${goal.usable_minutes} minutes left`}
                  {` · studied ${goal.studied_minutes}`}
                </li>
              ))}
            </ul>
            <h2 className={styles.meta}>Due reviews</h2>
            {home.due_reviews.count === 0 ? (
              <p className={styles.meta}>Nothing is due.</p>
            ) : (
              <p className={styles.meta}>
                {home.due_reviews.count} due
                {home.due_reviews.first_lesson_title
                  ? ` · start with ${home.due_reviews.first_lesson_title}`
                  : ""}
                {home.due_reviews.minutes_estimate
                  ? ` (about ${home.due_reviews.minutes_estimate} minutes)`
                  : ""}
              </p>
            )}
            <h2 className={styles.meta}>Recent evidence</h2>
            {home.recent_evidence.length === 0 ? (
              <p className={styles.meta}>No independent evidence yet.</p>
            ) : (
              <ul>
                {home.recent_evidence.map((item) => (
                  <li key={item.competency_key}>
                    {item.competency_name}: {item.facet_label}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
        <p className={styles.meta}>
          <Link href={home.quick_learn.href}>{home.quick_learn.label}</Link>
        </p>
      </section>
    </main>
  );
}
