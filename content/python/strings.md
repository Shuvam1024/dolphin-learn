---
key: python.strings
name: Strings
domain: python
requires: ['python.names']
effort_minutes:
  low: 45
  high: 70
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Text as sequences
---

## Reading

A string is an immutable sequence of characters. You write it in quotes, as in `word = "hi"`. Indexing `word[0]` looks up a character. Concatenation with `+` builds a new string. Methods like `word.upper()` return a new string rather than changing the old one, because strings cannot be mutated in place. Length uses `len(word)`. Formatting with f-strings embeds values into a new string without changing the originals. Treating strings as mutable, or assuming indexing starts at 1, leads to confusion. Reading a string operation means asking whether a new string was created and which name points at it afterward. Keep this model in mind when you write small programs: names, conditions, and collections work together. Practice by predicting the next state before you run anything, then compare your prediction to what Python actually does. That habit matters more than memorizing every keyword on the first pass through the path. Write one more sentence of intent before you change the code.

## Worked example

Start with `word = "hi"`. Then `word.upper()` returns `"HI"` while `word` still points at `"hi"`.
