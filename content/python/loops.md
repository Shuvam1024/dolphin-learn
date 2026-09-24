---
key: python.loops
name: Loops
domain: python
requires: ['python.conditionals']
effort_minutes:
  low: 45
  high: 70
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Repeat with for and while
---

## Reading

A loop repeats a block of statements while a condition holds or while there are items left to visit. In Python, `for item in items:` walks a sequence once per element. The name `item` is rebound on each pass. A `while condition:` loop keeps running as long as the condition is true, so you must change something inside the body or the loop never ends. Loops do not invent new binding rules: each iteration reuses ordinary assignment and lookup. Choosing `for` when you already have a collection, and `while` when you must wait for a condition, keeps intent clear. Common mistakes include mutating a list while iterating it in a `for` loop, or forgetting to update the condition in a `while` loop. Reading a loop means simulating each pass in order, not guessing the final state from the first line. Keep this model in mind when you write small programs: names, conditions, and collections work together. Practice by predicting the next state before you run anything, then compare your prediction to what Python actually does. That habit matters more than memorizing every keyword on the first pass through the path. Write one more sentence of intent before you change the code.

## Worked example

Given `nums = [1, 2, 3]` and `total = 0`, the loop `for n in nums: total = total + n` binds `n` to 1, then 2, then 3. After three passes, `total` is 6.
