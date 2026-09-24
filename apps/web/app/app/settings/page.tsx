import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { loadMe } from "@/lib/me";
import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import styles from "../../auth.module.css";
import { SettingsForm, type SettingsProfile } from "./settings-form";

async function loadProfile(): Promise<SettingsProfile> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
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
  const me = (await response.json()) as { profile: SettingsProfile };
  return {
    display_name: me.profile.display_name ?? null,
    timezone: me.profile.timezone || "UTC",
    default_session_minutes: me.profile.default_session_minutes || 25,
    a11y_prefs: {
      reduced_motion: Boolean(me.profile.a11y_prefs?.reduced_motion),
      larger_text: Boolean(me.profile.a11y_prefs?.larger_text),
    },
    use_tutor: me.profile.use_tutor !== false,
    ai_opt_out: Boolean(me.profile.ai_opt_out),
  };
}

export default async function SettingsPage() {
  const me = await loadMe();
  if (!me.profile.adult_acknowledged_at) {
    redirect("/app");
  }
  const profile = await loadProfile();
  return (
    <main className={styles.shell}>
      <SettingsForm initial={profile} />
    </main>
  );
}
