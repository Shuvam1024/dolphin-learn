import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Button, ButtonLink } from "@/components/ui";
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
  return (
    <li className={styles.course}>
      <div>
        <p className={styles.subject}>{goal.subject_name}</p>
        <Link className={styles.courseTitle} href={`/app/goals/${goal.id}`}>
          {goal.title}
        </Link>
        <p className={styles.meta}>
          {goal.next_lesson_title ? `next: ${goal.next_lesson_title}` : "No next lesson yet"}
          {` · ${goal.remaining_minutes} of ${goal.usable_minutes} minutes left`}
        </p>
      </div>
      <p className={styles.studied}>{minutesLabel(goal.studied_minutes)} studied</p>
    </li>
  );
}

export default async function AppHomePage() {
  const [me, homeOrError] = await Promise.all([loadMe(), loadHome()]);
  const acknowledged = Boolean(me.profile.adult_acknowledged_at);

  if (!acknowledged) {
    return (
      <main className={styles.desk}>
        <section className={styles.gate}>
          <h1 className={styles.title}>Before you start</h1>
          <p className={styles.lede}>
            Dolphin is for adults 18 and older. A child-specific product is not part of this
            version. Learning notes stay private to your account.
          </p>
          <p className={styles.privacy}>
            <Link href="/privacy">Read the privacy summary</Link>
          </p>
          <form className={styles.actions} action="/api/session/acknowledge" method="post">
            <Button type="submit" variant="primary">
              I am 18 or older and I understand
            </Button>
          </form>
        </section>
      </main>
    );
  }

  if ("error" in homeOrError) {
    return (
      <main className={styles.desk}>
        <section className={styles.error}>
          <h1 className={styles.title}>Something went wrong</h1>
          <p className={styles.lede}>Home could not load. Try again.</p>
          <p className={styles.follow}>
            <Link className={styles.quiet} href="/app">
              Retry
            </Link>
          </p>
        </section>
      </main>
    );
  }

  const home = homeOrError;
  const empty = home.goals.length === 0;
  const primaryHref = home.next_action.href;
  const totalRemaining = home.goals.reduce((sum, goal) => sum + goal.remaining_minutes, 0);

  if (empty) {
    return (
      <main className={styles.desk}>
        <section className={styles.empty}>
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
      </main>
    );
  }

  const estimate = home.next_action.minutes_estimate ?? 0;

  return (
    <main className={styles.desk}>
      <section className={styles.continue} aria-labelledby="home-continue">
        <p className={styles.eyebrow} id="home-continue">
          Continue
        </p>
        <div className={styles.continueTop}>
          <h1 className={styles.title}>
            {primaryHref ? (
              <Link href={primaryHref}>{home.next_action.title}</Link>
            ) : (
              home.next_action.title
            )}
          </h1>
          {estimate > 0 ? (
            <p className={styles.estimate}>About {minutesLabel(estimate)}</p>
          ) : null}
        </div>
        {home.next_action.subtitle ? <p className={styles.sub}>{home.next_action.subtitle}</p> : null}
        {primaryHref ? null : (
          <form className={styles.actions} action="/api/sessions" method="post">
            <input type="hidden" name="goal_id" value={home.next_action.goal_id} />
            <Button type="submit" variant="primary">
              {home.next_action.title}
            </Button>
          </form>
        )}
        <p className={styles.totals}>Minutes left across goals: {totalRemaining}</p>
      </section>

      <section className={styles.section} aria-labelledby="home-goals">
        <h2 className={styles.sectionTitle} id="home-goals">
          Goals
        </h2>
        <ul className={styles.courseList}>
          {home.goals.map((goal) => (
            <GoalRow key={goal.id} goal={goal} />
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="home-reviews">
        <h2 className={styles.sectionTitle} id="home-reviews">
          Reviews
        </h2>
        {home.due_reviews.count === 0 ? (
          <p className={styles.line}>Nothing is due.</p>
        ) : (
          <p className={styles.line}>
            {home.due_reviews.count} due
            {home.due_reviews.first_lesson_title
              ? ` · start with ${home.due_reviews.first_lesson_title}`
              : ""}
            {home.due_reviews.minutes_estimate
              ? ` · ${minutesLabel(home.due_reviews.minutes_estimate)}`
              : ""}
            {home.next_action.kind === "review" ? null : (
              <>
                {" · "}
                <Link className={styles.quiet} href="/app/review">
                  Open review
                </Link>
              </>
            )}
          </p>
        )}
      </section>

      <section className={styles.section} aria-labelledby="home-evidence">
        <h2 className={styles.sectionTitle} id="home-evidence">
          Recent evidence
        </h2>
        {home.recent_evidence.length === 0 ? (
          <p className={styles.line}>No independent evidence yet.</p>
        ) : (
          <ul className={styles.evidence}>
            {home.recent_evidence.map((item) => (
              <li key={`${item.competency_name}-${item.facet_label}`}>
                {item.competency_name}: {item.facet_label}
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className={styles.follow}>
        <Link className={styles.quiet} href="/app/goals/new">
          Create a goal
        </Link>
        <Link className={styles.quiet} href={home.quick_learn.href}>
          {home.quick_learn.label}
        </Link>
      </p>
    </main>
  );
}
