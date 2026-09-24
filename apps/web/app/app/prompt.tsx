"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import styles from "./home.module.css";

export function Prompt() {
  const router = useRouter();
  const [tool, setTool] = useState<"quick" | "plan">("quick");
  const [text, setText] = useState("");

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = encodeURIComponent(text.trim());
    router.push(`/app/goals/new?tool=${tool}&q=${q}`);
  }

  return (
    <form className={styles.composer} onSubmit={onSubmit}>
      <h1 className={styles.promptTitle} id="home-prompt">
        What do you want to learn?
      </h1>
      <textarea
        id="learn-prompt"
        className={styles.prompt}
        aria-labelledby="home-prompt"
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={3}
        placeholder="A topic, a skill, or the next thing you want to be able to do."
        required
      />
      <div className={styles.composerBar}>
        <div className={styles.tools} role="radiogroup" aria-label="Tool">
          <label className={tool === "quick" ? styles.toolOn : styles.tool}>
            <input
              type="radio"
              name="tool"
              value="quick"
              checked={tool === "quick"}
              onChange={() => setTool("quick")}
            />
            Quick Learn
          </label>
          <label className={tool === "plan" ? styles.toolOn : styles.tool}>
            <input
              type="radio"
              name="tool"
              value="plan"
              checked={tool === "plan"}
              onChange={() => setTool("plan")}
            />
            Full plan
          </label>
        </div>
        <button className={styles.start} type="submit">
          Start
        </button>
      </div>
      <p className={styles.hint}>
        Quick Learn fits one sitting. Full plan builds a longer path.{" "}
        <a href="/app/goals/new">Create a goal</a>
      </p>
    </form>
  );
}
