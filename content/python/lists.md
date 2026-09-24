---
key: python.lists
name: Lists
domain: python
requires: ['python.names']
effort_minutes:
  low: 45
  high: 70
reviewed_by: curriculum
reviewed_on: '2026-09-24'
lesson_title: Ordered collections
---

## Reading

A list is an ordered sequence of values. You write it with square brackets, as in `nums = [3, 1, 4]`. Indexing with `nums[0]` looks up the first value; assignment like `nums[1] = 9` replaces the value at that index. Appending with `nums.append(5)` grows the list at the end. Lists are mutable: the same list object can change over time while names that point at it keep pointing at that same object. Slicing with `nums[1:3]` builds a new list of selected elements without changing the original. Length comes from `len(nums)`. Mixing indexing, append, and iteration is how most early programs process collections. Confusing a list with a single value, or assuming indexing starts at 1, are common early mistakes. Keep this model in mind when you write small programs: names, conditions, and collections work together. Practice by predicting the next state before you run anything, then compare your prediction to what Python actually does. That habit matters more than memorizing every keyword on the first pass through the path. Write one more sentence of intent before you change the code.

## Worked example

Start with `nums = [3, 1, 4]`. Then `nums[1] = 9` yields `[3, 9, 4]`. Next `nums.append(5)` yields `[3, 9, 4, 5]`.
