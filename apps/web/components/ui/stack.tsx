import type { ReactNode } from "react";

import styles from "./ui.module.css";

export function Stack({
  gap = "md",
  children,
}: {
  gap?: "sm" | "md" | "lg";
  children?: ReactNode;
}) {
  const gapClass =
    gap === "sm" ? styles.stackGapSm : gap === "lg" ? styles.stackGapLg : styles.stackGapMd;
  return <div className={`${styles.stack} ${gapClass}`}>{children}</div>;
}
