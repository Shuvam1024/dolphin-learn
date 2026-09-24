---
key: python.errors
name: Errors
domain: python
requires: ['python.names']
effort_minutes:
  low: 45
  high: 70
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Read and respond to errors
---

## Reading

When Python cannot finish an operation, it raises an error with a type and a message. A `NameError` means a name has no binding. An `IndexError` means an index is out of range for a sequence. A `TypeError` means an operation was given the wrong kind of value. Reading the traceback from the bottom up shows the line that failed. Fixing the cause is better than catching every error blindly. Beginners often ignore the message and guess. Instead, match the error type to the model you already know: bindings, indexes, and types. Small experiments in the studio help confirm the fix before you move on. Keep this model in mind when you write small programs: names, conditions, and collections work together. Practice by predicting the next state before you run anything, then compare your prediction to what Python actually does. That habit matters more than memorizing every keyword on the first pass through the path. Write one more sentence of intent before you change the code.

## Worked example

Evaluating `print(missing)` raises `NameError` because `missing` has no binding. Evaluating `[1, 2][5]` raises `IndexError`.
