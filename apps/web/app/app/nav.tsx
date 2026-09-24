"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./nav.module.css";

const PRIMARY = [
  { href: "/app", label: "Home", match: (path: string) => path === "/app" },
  {
    href: "/app/learn",
    label: "Learn",
    match: (path: string) => path === "/app/learn" || path.startsWith("/app/learn/"),
  },
  { href: "/app/review", label: "Review", match: (path: string) => path.startsWith("/app/review") },
  {
    href: "/app/progress",
    label: "Progress",
    match: (path: string) => path.startsWith("/app/progress"),
  },
  { href: "/app/more", label: "More", match: (path: string) => path.startsWith("/app/more") },
] as const;

const DESKTOP = [
  { href: "/app/learn", label: "Learn" },
  { href: "/app/review", label: "Review" },
  { href: "/app/library", label: "Library" },
  { href: "/app/progress", label: "Progress" },
] as const;

export function Nav() {
  const pathname = usePathname();
  return (
    <>
      <header className={styles.bar}>
        <Link className={styles.brand} href="/app">
          Dolphin
        </Link>
        <nav className={styles.primary} aria-label="Primary">
          {DESKTOP.map((item) => (
            <Link
              key={item.href}
              className={styles.link}
              href={item.href}
              aria-current={pathname === item.href || pathname.startsWith(`${item.href}/`) ? "page" : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <Link className={styles.more} href="/app/more">
          More
        </Link>
      </header>
      <nav className={styles.tabs} aria-label="Primary">
        {PRIMARY.map((item) => {
          const current = item.match(pathname);
          return (
            <Link
              key={item.href}
              className={styles.tab}
              href={item.href}
              aria-current={current ? "page" : undefined}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
