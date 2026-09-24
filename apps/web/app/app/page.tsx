import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Button, ButtonLink, Chip, Page, PageHeader, Stack, Surface } from "@/components/ui";
import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "./home.module.css";

type NextAction = {
  kind: string;
  title: string;
  subtitle?: string;
  minutes_estimate?: number;
  href: string;
  goal_id: string;
};

type GoalCard = {
  id: string;
  title: string;
  subject_name: string;
  next_lesson_title: string;
  remaining_minutes: number;
  usable_minutes: number;
  studied_minutes: number;
  status: string;
};

type HomeSnapshot = {
  next_action: NextAction;
  goals: GoalCard[];
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

function minutesLabel(n: number): string {
  return n === 1 ? "1 minute" : `${n} minutes`;
}

function GoalRow({ goal }: { goal: GoalCard }) {
  const usable = Math.max(goal.usable_minutes, 0);
  const studied = Math.max(goal.studied_minutes, 0);
  const fill = usable > 0 ? Math.min(100, Math.round((studied / usable) * 100)) : 0;
  return (
    <li className={styles.goal}>
      <div className={styles.goalHead}>
        <Link className={styles.goalTitle} href={`/app/goals/${goal.id}`}>
          {goal.title}
        </Link>
        <Chip>{goal.subject_name}</Chip>
      </div>
      <p className={styles.meta}>
        {goal.next_lesson_title ? `next: ${goal.next_lesson_title}` : "No next lesson yet"}
        {` · ${goal.remaining_minutes} of ${goal.usable_minutes} minutes left`}
        {` · studied ${goal.studied_minutes}`}
      </p>
      <span
        className={styles.meter}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={usable || 0}
        aria-valuenow={studied}
        aria-label={`${studied} of ${usable} minutes studied for ${goal.title}`}
      >
        <span className={styles.meterFill} style={{ width: `${fill}%` }} />
      </span>
    </li>
  );
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
        <section className={styles.error}>
          <p className={styles.kicker}>Home</p>
          <h1 className={styles.title}>Something went wrong</h1>
          <p className={styles.lede}>Home could not load. Try again.</p>
          <Link className={styles.quiet} href="/app">
            Retry
          </Link>
        </section>
      </main>
    );
  }

  const home = homeOrError;
  const empty = home.goals.length === 0;
  const primaryHref = home.next_action.href;
  const totalRemaining = home.goals.reduce((sum, goal) => sum + goal.remaining_minutes, 0);
  const totalStudied = home.goals.reduce((sum, goal) => sum + goal.studied_minutes, 0);

  return (
    <main className={styles.shell}>
      {empty ? (
        <section className={styles.empty}>
          <p className={styles.kicker}>Home</p>
          <h1 className={styles.title}>You are in</h1>
          <p className={styles.lede}>
            Signed in as {me.email ?? me.auth_subject}. You don&apos;t have a goal yet. Create
            one and Dolphin will fit a plan to the minutes you have.
          </p>
          <div className={styles.actions}>
            <ButtonLink href="/app/goals/new">Create a goal</ButtonLink>
            <ButtonLink href={home.quick_learn.href} variant="secondary">
              {home.quick_learn.label}
            </ButtonLink>
          </div>
        </section>
      ) : (
        <>
          <section className={styles.hero}>
            <p className={styles.kicker}>Today</p>
            <h1 className={styles.title}>{home.next_action.title}</h1>
            {home.next_action.subtitle ? (
              <p className={styles.lede}>{home.next_action.subtitle}</p>
            ) : (
              <p className={styles.lede}>
                One sitting. Real minutes. The next honest step is the only one that matters.
              </p>
            )}
            {home.next_action.minutes_estimate ? (
              <p className={styles.meta}>About {home.next_action.minutes_estimate} minutes</p>
            ) : null}
            <div className={styles.actions}>
              {primaryHref ? (
                <ButtonLink href={primaryHref}>{home.next_action.title}</ButtonLink>
              ) : (
                <form action="/api/sessions" method="post">
                  <input type="hidden" name="goal_id" value={home.next_action.goal_id} />
                  <Button type="submit" variant="primary">
                    {home.next_action.title}
                  </Button>
                </form>
              )}
              <ButtonLink href="/app/goals/new" variant="quiet">
                Create a goal
              </ButtonLink>
            </div>
            <div className={styles.stats} aria-label="Study totals">
              <p className={styles.stat}>
                <span className={styles.statValue}>{totalRemaining}</span>
                <span className={styles.statLabel}>minutes left across goals</span>
              </p>
              <p className={styles.stat}>
                <span className={styles.statValue}>{totalStudied}</span>
                <span className={styles.statLabel}>minutes studied</span>
              </p>
              <p className={styles.stat}>
                <span className={styles.statValue}>{home.due_reviews.count}</span>
                <span className={styles.statLabel}>
                  {home.due_reviews.count === 1 ? "review due" : "reviews due"}
                </span>
              </p>
            </div>
          </section>

          <div className={styles.grid}>
            <section className={styles.panel} aria-labelledby="home-goals">
              <h2 className={styles.sectionTitle} id="home-goals">
                Goals
              </h2>
              <ul className={styles.goalList}>
                {home.goals.map((goal) => (
                  <GoalRow key={goal.id} goal={goal} />
                ))}
              </ul>
            </section>

            <div className={styles.stackPanel}>
              <section className={styles.panel} aria-labelledby="home-reviews">
                <h2 className={styles.sectionTitle} id="home-reviews">
                  Due reviews
                </h2>
                {home.due_reviews.count === 0 ? (
                  <p className={styles.meta}>Nothing is due.</p>
                ) : (
                  <>
                    <p className={styles.meta}>
                      {home.due_reviews.count} due
                      {home.due_reviews.first_lesson_title
                        ? ` · start with ${home.due_reviews.first_lesson_title}`
                        : ""}
                      {home.due_reviews.minutes_estimate
                        ? ` (${minutesLabel(home.due_reviews.minutes_estimate)})`
                        : ""}
                    </p>
                    {home.next_action.kind === "review" ? null : (
                      <ButtonLink href="/app/review" variant="secondary">
                        Open review
                      </ButtonLink>
                    )}
                  </>
                )}
              </section>

              <section className={styles.panel} aria-labelledby="home-evidence">
                <h2 className={styles.sectionTitle} id="home-evidence">
                  Recent evidence
                </h2>
                {home.recent_evidence.length === 0 ? (
                  <p className={styles.meta}>No independent evidence yet.</p>
                ) : (
                  <ul className={styles.chips}>
                    {home.recent_evidence.map((item) => (
                      <li key={`${item.competency_name}-${item.facet_label}`}>
                        <Chip>{`${item.competency_name}: ${item.facet_label}`}</Chip>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>
          </div>

          <p className={`${styles.meta} ${styles.follow}`}>
            <Link className={styles.quiet} href={home.quick_learn.href}>
              {home.quick_learn.label}
            </Link>
          </p>
        </>
      )}
    </main>
  );
}
