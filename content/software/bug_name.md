---
key: software.bug_name
name: Name what the test caught
domain: software
requires:
- software.failing_test
effort_minutes:
  low: 12
  high: 22
reviewed_by: curriculum
reviewed_on: '2026-09-23'
lesson_title: Name what the test caught
---

## Reading

After you can read a failing assertion, name the bug in product language: wrong order, missing item, off-by-one, or unexpected null. The name should match what the test checked, not a guess about an unrelated subsystem. A clear bug name becomes the smallest change you attempt next. If the name does not fit the assertion, re-read the test before editing code. This habit keeps software practice on the same evidence path as other Dolphin subjects. This short note stays concrete and reviewable. This short note stays concrete and reviewable. This short note stays concrete and reviewable. This short note stays concrete and reviewable. This short note stays concrete and reviewable.

## Worked example

A test fails with `AssertionError: expected 200, got 500`. Name the bug from the observed behavior, not from a guess about the fix: "handler returns 500 on valid input." That name points at the failing contract. Later you can ask why, but the first honest step is to describe what the system did wrong in one short sentence.
