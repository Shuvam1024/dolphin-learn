import type { ReactNode } from "react";

import styles from "./ui.module.css";

export function PageHeader({
  kicker,
  title,
  subtitle,
}: {
  kicker?: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <header className={styles.header}>
      {kicker ? <p className={styles.kicker}>{kicker}</p> : null}
      <h1 className={styles.title}>{title}</h1>
      {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
    </header>
  );
}

export function Page({ children }: { children: ReactNode }) {
  return <main className={styles.page}>{children}</main>;
}
