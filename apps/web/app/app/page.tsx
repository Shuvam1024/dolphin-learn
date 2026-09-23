import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../auth.module.css";

type Me = {
  id: string;
  auth_subject: string;
  email: string | null;
};

export default async function AppHomePage() {
  const jar = await cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) {
    redirect("/sign-in");
  }

  const response = await fetch(`${apiBaseUrl()}/api/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    redirect("/sign-in");
  }
  const me = (await response.json()) as Me;

  return (
    <main className={styles.shell}>
      <section className={styles.card}>
        <p className={styles.kicker}>Home</p>
        <h1 className={styles.title}>You are in</h1>
        <p className={styles.lede}>
          Signed in as {me.email ?? me.auth_subject}. Goals and Session Studio are not here yet.
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
