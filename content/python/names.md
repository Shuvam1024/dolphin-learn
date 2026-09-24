---
key: python.names
name: Names and values
domain: python
requires: []
effort_minutes:
  low: 10
  high: 20
reviewed_by: curriculum
reviewed_on: '2026-09-23'
lesson_title: Names point at values
---

## Reading

In Python, a name is a label that points at a value. The statement `n = 3` does not create a permanent box that can only hold three. It binds the name `n` to the integer value `3`. Later, when you write `n = n + 1`, Python looks up the current value of `n`, adds one, and rebinds the name to the new result. Reading a name, as in `print(n)`, looks up the binding without creating a new one. Assignment is the operation that creates or replaces a binding. Keeping this model clear prevents the common myth that variables are little boxes that forever own their first value, and it is the foundation for understanding calls and reassignment in larger programs.

## Worked example

Start with `n = 3`. The name `n` now points at the integer `3`. Next evaluate `n = n + 1`: look up the current value of `n` (which is 3), add one to get 4, and rebind `n` to that new value. After those two lines, reading `n` yields 4. The first assignment created the binding; the second replaced it. Nothing about the first binding permanently limited what `n` could point at later.
