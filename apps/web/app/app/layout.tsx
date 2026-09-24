import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Nav } from "./nav";
import styles from "./nav.module.css";

export const metadata: Metadata = {
  title: "Dolphin",
};

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className={styles.frame}>
      <Nav />
      {children}
    </div>
  );
}
