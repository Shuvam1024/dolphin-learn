"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";

import styles from "../../auth.module.css";

export type SettingsProfile = {
  display_name: string | null;
  timezone: string;
  default_session_minutes: number;
  a11y_prefs: { reduced_motion: boolean; larger_text: boolean };
  use_tutor: boolean;
  ai_opt_out: boolean;
};

function applyDocumentPrefs(profile: SettingsProfile) {
  const root = document.documentElement;
  root.dataset.text = profile.a11y_prefs.larger_text ? "large" : "default";
  root.dataset.motion = profile.a11y_prefs.reduced_motion ? "reduce" : "default";
}

export function SettingsForm({ initial }: { initial: SettingsProfile }) {
  const [displayName, setDisplayName] = useState(initial.display_name ?? "");
  const [timezone, setTimezone] = useState(initial.timezone || "UTC");
  const [minutes, setMinutes] = useState(initial.default_session_minutes || 25);
  const [largerText, setLargerText] = useState(Boolean(initial.a11y_prefs.larger_text));
  const [reducedMotion, setReducedMotion] = useState(
    Boolean(initial.a11y_prefs.reduced_motion),
  );
  const [useTutor, setUseTutor] = useState(initial.use_tutor !== false);
  const [message, setMessage] = useState("");
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    applyDocumentPrefs({
      display_name: displayName || null,
      timezone,
      default_session_minutes: minutes,
      a11y_prefs: { reduced_motion: reducedMotion, larger_text: largerText },
      use_tutor: useTutor,
      ai_opt_out: !useTutor,
    });
  }, [displayName, timezone, minutes, largerText, reducedMotion, useTutor]);

  function save() {
    setMessage("");
    startTransition(async () => {
      const response = await fetch("/api/me/preferences", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          display_name: displayName.trim() || null,
          timezone,
          default_session_minutes: minutes,
          a11y_prefs: { reduced_motion: reducedMotion, larger_text: largerText },
          use_tutor: useTutor,
        }),
      });
      if (!response.ok) {
        setMessage("Could not save. Check the values and try again.");
        return;
      }
      const me = await response.json();
      const profile = me.profile as SettingsProfile;
      setDisplayName(profile.display_name ?? "");
      setTimezone(profile.timezone);
      setMinutes(profile.default_session_minutes);
      setLargerText(Boolean(profile.a11y_prefs?.larger_text));
      setReducedMotion(Boolean(profile.a11y_prefs?.reduced_motion));
      setUseTutor(profile.use_tutor !== false);
      applyDocumentPrefs(profile);
      setMessage("Saved.");
    });
  }

  return (
    <section className={styles.card} style={{ width: "min(560px, 100%)" }}>
      <p className={styles.kicker}>Settings</p>
      <h1 className={styles.title}>Your preferences</h1>
      <p className={styles.lede}>
        Name, timezone, usual sitting length, reading size, motion, and whether the tutor is on.
      </p>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          save();
        }}
      >
        <label className={styles.label} htmlFor="display_name">
          Name
        </label>
        <input
          id="display_name"
          className={styles.input}
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          maxLength={80}
        />

        <label className={styles.label} htmlFor="timezone">
          Timezone
        </label>
        <input
          id="timezone"
          className={styles.input}
          value={timezone}
          onChange={(event) => setTimezone(event.target.value)}
          placeholder="America/New_York"
        />

        <label className={styles.label} htmlFor="sitting">
          Usual sitting length (minutes)
        </label>
        <input
          id="sitting"
          className={styles.input}
          type="number"
          min={5}
          max={180}
          value={minutes}
          onChange={(event) => setMinutes(Number(event.target.value))}
        />

        <label className={styles.label} style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={largerText}
            onChange={(event) => setLargerText(event.target.checked)}
          />
          Larger text
        </label>

        <label className={styles.label} style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={reducedMotion}
            onChange={(event) => setReducedMotion(event.target.checked)}
          />
          Reduced motion
        </label>

        <label className={styles.label} style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={useTutor}
            onChange={(event) => setUseTutor(event.target.checked)}
          />
          Use the tutor
        </label>

        <button className={styles.button} type="submit" disabled={pending}>
          {pending ? "Saving…" : "Save"}
        </button>
        {message ? <p className={styles.meta}>{message}</p> : null}
      </form>

      <div style={{ marginTop: 28 }}>
        <h2 style={{ fontSize: 20, marginBottom: 8 }}>Privacy</h2>
        <p className={styles.lede} style={{ marginBottom: 8 }}>
          Download and delete arrive in the next account steps. Until then, see the privacy notice.
        </p>
        <p className={styles.meta}>
          <Link href="/privacy">Privacy</Link>
          {" · "}
          <span>Download my data (soon)</span>
          {" · "}
          <span>Delete account (soon)</span>
        </p>
      </div>

      <p className={styles.meta} style={{ marginTop: 20 }}>
        <Link href="/app/help">Help</Link>
        {" · "}
        <Link href="/app/more">More</Link>
      </p>
    </section>
  );
}
