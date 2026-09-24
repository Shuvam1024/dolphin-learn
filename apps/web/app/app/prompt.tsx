"use client";

import { useState } from "react";

import styles from "./home.module.css";

export function Prompt() {
  const [tool, setTool] = useState<"quick" | "plan">("quick");

  return (
    <form className={styles.composer} action="/app/goals/new" method="get">
      <h1 className={styles.promptTitle} id="home-prompt">
        What do you want to learn?
      </h1>
      <textarea
        id="learn-prompt"
        name="q"
        className={styles.prompt}
        aria-labelledby="home-prompt"
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
      <p className={styles.hint}>Quick Learn fits one sitting. Full plan builds a longer path.</p>
    </form>
  );
}
