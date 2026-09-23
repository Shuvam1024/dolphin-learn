import type { ReactNode } from "react";

import { Nav } from "./nav";
import styles from "./nav.module.css";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className={styles.frame}>
      <Nav />
      {children}
    </div>
  );
}
