---
key: software.smallest_fix
name: Smallest fix
domain: software
requires: ['software.bug_name']
effort_minutes:
  low: 40
  high: 60
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Change one thing that matters
---

## Reading

After you can name the bug, look for the smallest fix that removes the failing behavior without rewriting the whole program. A small fix changes one binding, one condition, or one call. Large rewrites hide whether you understood the failure. Prefer a fix you can explain in one sentence tied to the failing test. If the test still fails, the fix was not aimed at the cause. Common mistakes include editing unrelated files, silencing the test, or copying a larger solution without checking the failure mode. Keep the failing test in view while you edit so each change has a clear purpose. Keep practicing by predicting the next state before you check. Write one clear sentence of intent, then compare it to the result. That habit matters more than rushing through every example on the first sitting. Say the idea out loud once before you move to the next item so the model stays audible. If a step surprises you, rewrite the same idea with different numbers and try again.

## Worked example

If a test expects 4 after adding one starting from 3, the smallest fix may be correcting the starting binding rather than rewriting the function.
