import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import styles from "./ui.module.css";

type Variant = "primary" | "secondary" | "quiet";

const variantClass: Record<Variant, string> = {
  primary: styles.buttonPrimary,
  secondary: styles.buttonSecondary,
  quiet: styles.buttonQuiet,
};

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children?: ReactNode;
}) {
  return (
    <button
      className={`${styles.button} ${variantClass[variant]} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  );
}

export function ButtonLink({
  href,
  variant = "primary",
  className = "",
  children,
}: {
  href: string;
  variant?: Variant;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <Link
      className={`${styles.button} ${variantClass[variant]} ${className}`.trim()}
      href={href}
    >
      {children}
    </Link>
  );
}
