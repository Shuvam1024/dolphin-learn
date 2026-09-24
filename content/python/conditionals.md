---
key: python.conditionals
name: Choosing with if
domain: python
requires:
- python.names
effort_minutes:
  low: 15
  high: 25
reviewed_by: curriculum
reviewed_on: '2026-09-23'
lesson_title: Choose with if
---

## Reading

A conditional chooses which block runs by evaluating a Boolean expression. In `if n > 2:`, the comparison `n > 2` is the condition; it is not an assignment. When the condition is true, the indented body runs; otherwise Python continues after the block or into an `else`. Conditions use comparison and logical operators rather than `=`. Reading a short `if` carefully means naming the condition in plain words first, then tracing which branch runs for a concrete value of `n`. That habit transfers to longer branches without turning the lesson into a second language tour.

## Worked example

Given `n = 4`, the check `if n > 3:` is true, so the indented block runs and anything under a matching `else:` is skipped. If instead `n = 2`, the condition is false and only the `else` block runs. The condition is evaluated once; exactly one branch is chosen. Nested conditions still pick one path by asking true/false questions in order.
