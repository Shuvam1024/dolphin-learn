# Content review checklist

Use this before seeding graded items for a checked subject.

## Always

1. Reading is 80–400 words and matches the competency name.
2. Worked example is present for checked subjects.
3. At least three graded items mix types where possible.
4. Every graded item has `explanation`, `difficulty` (1–3), and realistic effort.
5. Prompt stem does not leak the answer.
6. Frontmatter has `reviewed_by` and `reviewed_on`.

## AI-drafted items

1. Drafts land in `*.drafts.yaml` with `provisional: true`. Never seed drafts directly.
2. Reviewer edits the prompt, choices, explanation, and misconceptions.
3. Reject near-duplicates (token Jaccard ≥ 0.8 against existing prompts).
4. Move an approved item into the competency `.items.yaml`.
5. Keep or set `reviewed_by` / `reviewed_on` on the competency frontmatter.
6. Seed marks approved AI items as `provisional=false`, `source='ai'`, with `reviewed_at`.
7. Nothing provisional is ever selected for grading (`pick_unseen(graded=True)` excludes it).
