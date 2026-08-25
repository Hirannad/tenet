---
type: decision
created: 2026-01-12
status: accepted
scope: universal
categories:
  - "[[Methods]]"
revisit: If a note keeps needing a second decision to make sense on its own — then the split is cutting through something that is genuinely one choice, and the cap is doing harm
supersedes:
superseded:
related:
  - "[[2026-02-20-ship-behind-a-flag]]"
---

## Decision

One note carries one decision, capped at 400 words with the decision itself under 60. A note that
will not fit is two decisions wearing one filename.

## When to reconsider

If splitting a note repeatedly produces halves that cannot be read alone. That means the cap is
cutting through a single choice rather than separating two, and the rule is costing more than the
searchability it buys.

## Why

A note with two decisions in it can only ever have one status. Accept it and you accept both;
reject it and you lose the good half. The revisit condition has the same problem: two decisions
expire on different triggers, so one of them silently outlives its own reasoning.

The word cap is not about brevity for its own sake. It is the cheapest available detector for the
two-decisions case, and it fails loudly where a style guideline would not.

## Background

The first fifteen notes here were written without a cap. Three of them turned out to carry two
decisions each, and all three were found by hand, months later, when one half needed reversing and
the other did not.

## Options weighed

- **No cap, split on review.** Relies on someone noticing. Nobody did.
- **A cap with a check.** *(this)* The check is mechanical; the judgement stays human.
- **Cap the decision section only.** Catches the obvious cases and misses a long note that buries
  a second choice below the fold.

## The dilemma

A word count is a proxy, and proxies are always slightly wrong. A genuinely intricate decision can
run past 400 words honestly. The cap flags it anyway, and you overrule the flag — which is fine,
as long as overruling stays rare enough to notice.
