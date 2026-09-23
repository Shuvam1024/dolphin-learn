"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./nav.module.css";

const PRIMARY = [
  { href: "/app/learn", label: "Learn" },
  { href: "/app/review", label: "Review" },
  { href: "/app/library", label: "Library" },
  { href: "/app/progress", label: "Progress" },
] as const;

export function Nav() {
  const pathname = usePathname();
  return (
    <header className={styles.bar}>
      <Link className={styles.brand} href="/app">
        Dolphin
      </Link>
      <nav className={styles.primary} aria-label="Primary">
        {PRIMARY.map((item) => (
          <Link
            key={item.href}
            className={styles.link}
            href={item.href}
            aria-current={pathname === item.href ? "page" : undefined}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <Link className={styles.more} href="/app/more">
        More
      </Link>
    </header>
  );
}
