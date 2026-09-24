# Funnel events (S94)

Product events are opaque funnels only. No answers, notes, emails, or free-text prompts are stored in `product_events.props`.

## Events

| Event | When |
|---|---|
| `goal_created` | Learner creates a goal |
| `plan_accepted` | First accepted plan version |
| `plan_replanned` | Later accepted plan version |
| `session_started` | Sitting begins |
| `activity_submitted` | Graded attempt stored |
| `hint_requested` | Hint control used |
| `explain_requested` | Explain differently used |
| `independent_check_completed` | Fresh-check advance |
| `review_completed` | Review attempt graded |
| `review_snoozed` | Review snoozed |
| `account_export_requested` | Export requested (S98) |
| `account_deletion_requested` | Delete requested (S99) |

## Honest reading

Counts of these events describe engagement shape, not learning. Do not treat funnel conversion as proof of competence. Evidence facets and review outcomes remain the source of capability claims.
