---
key: python.calls
name: Calling a function
domain: python
requires:
- python.names
effort_minutes:
  low: 25
  high: 50
reviewed_by: curriculum
reviewed_on: '2026-09-23'
lesson_title: Call a function by name
---

## Reading

A function call looks up a callable by name and runs it with the arguments you pass. `print(n)` looks up `print`, evaluates `n` to its current value, and passes that value in. The call itself does not bind a new name unless you write an assignment such as `result = len(items)`. Arguments are expressions evaluated before the call begins. Distinguishing lookup, evaluation, and binding helps you read stack traces and failing tests: the name in the call is how Python finds the function, while any assignment on the left-hand side is a separate binding step that happens only when you write `=`.

## Worked example

Define `def greet(name): return "hi " + name`. Calling `greet("Ada")` does not invent a new kind of assignment. It temporarily binds the parameter `name` to the argument `"Ada"`, runs the body, and returns the resulting string. After the call finishes, that parameter binding goes away. The important move is: a call evaluates arguments, binds them to parameters for the body, then discards those bindings.
