---
key: python.functions
name: Functions
domain: python
requires: ['python.calls']
effort_minutes:
  low: 45
  high: 70
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Define and return
---

## Reading

A function packages a named block of work. You define it with `def`, parameters in parentheses, and a body indented underneath. Calling the function binds arguments to those parameters for that call. A `return` statement ends the call and hands a value back to the caller. Without `return`, the call finishes with `None`. Local names inside the function do not replace bindings outside it unless you intentionally share an object. Writing small functions with clear names makes later loops and conditionals easier to test. Common mistakes include forgetting `return`, confusing printing with returning, and mutating a shared list unexpectedly through a parameter. Keep this model in mind when you write small programs: names, conditions, and collections work together. Practice by predicting the next state before you run anything, then compare your prediction to what Python actually does. That habit matters more than memorizing every keyword on the first pass through the path. Write one more sentence of intent before you change the code.

## Worked example

Define `def double(n): return n * 2`. Calling `double(3)` binds `n` to 3 and returns 6.
