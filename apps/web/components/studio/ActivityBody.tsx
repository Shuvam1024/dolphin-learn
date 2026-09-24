import { Markdown } from "@/components/ui";

import styles from "./studio.module.css";

export function ActivityBody({
  bodyMarkdown,
  promptMarkdown,
  showBody,
}: {
  bodyMarkdown: string;
  promptMarkdown: string;
  showBody: boolean;
}) {
  return (
    <div className={styles.body}>
      {showBody && bodyMarkdown ? <Markdown>{bodyMarkdown}</Markdown> : null}
      {promptMarkdown ? (
        <div className={styles.prompt}>
          <Markdown>{promptMarkdown}</Markdown>
        </div>
      ) : null}
    </div>
  );
}
