---
key: software.describe_test
name: Describe a test
domain: software
requires: ['software.failing_test']
effort_minutes:
  low: 40
  high: 60
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Say what should happen
---

## Reading

A useful test description says the situation, the action, and the expected result in plain words. It does not narrate implementation details. Good descriptions help you choose the next failing check and explain a fix later. Write the expectation before you change code so you are not inventing success after the fact. Common mistakes include vague titles like 'works', mixing many behaviors in one test, or asserting nothing observable. Keep one behavior per test when you can, and name the outcome you care about. Keep practicing by predicting the next state before you check. Write one clear sentence of intent, then compare it to the result. That habit matters more than rushing through every example on the first sitting. Say the idea out loud once before you move to the next item so the model stays audible. If a step surprises you, rewrite the same idea with different numbers and try again.

## Worked example

Instead of 'test1', write 'when n starts at 3 and we add one, the result should be 4'. That states situation, action, and result.
