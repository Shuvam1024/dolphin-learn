"use client";

import { useEffect } from "react";

/** Apply saved a11y prefs to the document root on authenticated shells. */
export function PrefsBootstrap({
  largerText,
  reducedMotion,
}: {
  largerText: boolean;
  reducedMotion: boolean;
}) {
  useEffect(() => {
    const root = document.documentElement;
    root.dataset.text = largerText ? "large" : "default";
    root.dataset.motion = reducedMotion ? "reduce" : "default";
  }, [largerText, reducedMotion]);
  return null;
}
