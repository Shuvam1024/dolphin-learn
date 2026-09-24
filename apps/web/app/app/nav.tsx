"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./nav.module.css";

const SIDEBAR = [
  { href: "/app", label: "Home", match: (path: string) => path === "/app" },
  {
    href: "/app/learn",
    label: "Learn",
    match: (path: string) => path === "/app/learn" || path.startsWith("/app/learn/"),
  },
  { href: "/app/review", label: "Review", match: (path: string) => path.startsWith("/app/review") },
  {
    href: "/app/library",
    label: "Library",
    match: (path: string) => path.startsWith("/app/library"),
  },
  {
    href: "/app/progress",
    label: "Progress",
    match: (path: string) => path.startsWith("/app/progress"),
  },
] as const;

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

export function Nav() {
  const pathname = usePathname();
  return (
    <>
      <aside className={styles.sidebar}>
        <Link className={styles.brand} href="/app">
          Dolphin
        </Link>
        <nav className={styles.primary} aria-label="Primary">
          {SIDEBAR.map((item) => (
            <Link
              key={item.href}
              className={styles.link}
              href={item.href}
              aria-current={item.match(pathname) ? "page" : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <Link
          className={styles.more}
          href="/app/more"
          aria-current={pathname.startsWith("/app/more") ? "page" : undefined}
        >
          More
        </Link>
      </aside>
      <nav className={styles.tabs} aria-label="Primary">
        {PRIMARY.map((item) => (
          <Link
            key={item.href}
            className={styles.tab}
            href={item.href}
            aria-current={item.match(pathname) ? "page" : undefined}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
