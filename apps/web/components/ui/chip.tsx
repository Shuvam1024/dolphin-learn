import styles from "./ui.module.css";

export type ChipTone =
  | "exposed"
  | "practicing"
  | "demonstrated"
  | "retained"
  | "self_reported"
  | "unassessed"
  | "deferred"
  | "ai"
  | "neutral";

export function Chip({
  tone = "neutral",
  children,
}: {
  tone?: ChipTone;
  children?: string;
}) {
  const extra =
    tone === "ai" ? styles.chipAi : tone === "deferred" ? styles.chipDeferred : "";
  return <span className={`${styles.chip} ${extra}`.trim()}>{children}</span>;
}
