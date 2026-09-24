import type { Metadata } from "next";
import type { ReactNode } from "react";
import { cookies } from "next/headers";

import { ACCESS_COOKIE, apiBaseUrl } from "@/lib/session";

import { Nav } from "./nav";
import styles from "./nav.module.css";
import { PrefsBootstrap } from "./prefs-bootstrap";

export const metadata: Metadata = {
  title: "Dolphin",
};

async function loadA11y(): Promise<{ largerText: boolean; reducedMotion: boolean }> {
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!token) {
    return { largerText: false, reducedMotion: false };
  }
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) {
      return { largerText: false, reducedMotion: false };
    }
    const me = (await response.json()) as {
      profile?: { a11y_prefs?: { larger_text?: boolean; reduced_motion?: boolean } };
    };
    return {
      largerText: Boolean(me.profile?.a11y_prefs?.larger_text),
      reducedMotion: Boolean(me.profile?.a11y_prefs?.reduced_motion),
    };
  } catch {
    return { largerText: false, reducedMotion: false };
  }
}

export default async function AppLayout({ children }: { children: ReactNode }) {
  const a11y = await loadA11y();
  return (
    <div className={styles.frame}>
      <PrefsBootstrap largerText={a11y.largerText} reducedMotion={a11y.reducedMotion} />
      <Nav />
      <div className={styles.main}>{children}</div>
    </div>
  );
}
