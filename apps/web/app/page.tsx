import { ButtonLink } from "@/components/ui";

import styles from "./page.module.css";

const PROMISES = [
  {
    title: "Learn anything",
    body: "Checked subjects you can prove, or any subject you name.",
  },
  {
    title: "Fit the time you have",
    body: "Plans use real sitting minutes. A date is not study.",
  },
  {
    title: "Prove you can do it",
    body: "Evidence is what you showed without help — not a percent.",
  },
] as const;

export default function Home() {
  return (
    <main className={styles.shell}>
      <section className={styles.hero}>
        <p className={styles.kicker}>Dolphin</p>
        <h1 className={styles.title}>Your learning home.</h1>
        <p className={styles.lede}>
          One place to start a sitting, pick it up later, and keep an honest record of what you
          can do.
        </p>
        <div className={styles.actions}>
          <ButtonLink href="/sign-in">Sign in</ButtonLink>
        </div>
        <ul className={styles.promises}>
          {PROMISES.map((item) => (
            <li key={item.title}>
              <h2>{item.title}</h2>
              <p>{item.body}</p>
            </li>
          ))}
        </ul>
        <p className={styles.note}>The tutor explains. It never grades.</p>
        <p className={styles.note}>Study time is active minutes — never a streak.</p>
      </section>
    </main>
  );
}
