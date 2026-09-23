import type { ReactNode } from "react";

import styles from "./ui.module.css";

type Tone = "info" | "success" | "warning" | "pending";

const map: Record<Tone, string> = {
  info: styles.noticeInfo,
  success: styles.noticeSuccess,
  warning: styles.noticeWarning,
  pending: styles.noticePending,
};

export function InlineNotice({
  tone = "info",
  children,
}: {
  tone?: Tone;
  children?: ReactNode;
}) {
  return <div className={`${styles.notice} ${map[tone]}`.trim()}>{children}</div>;
}
