---
type: decision
created: 2026-02-20
status: accepted
scope: universal
categories:
  - "[[Methods]]"
revisit: If flags outlive their rollouts often enough that reading the code no longer tells you what runs in production — then the flag is the new fork, and it costs more than the branch it replaced
supersedes:
superseded:
related:
  - "[[2026-01-12-one-decision-per-note]]"
---

## Decision

Risky changes ship disabled behind a flag on the main branch, not on a long-lived branch. The flag
is removed in a follow-up within two weeks of full rollout.

## When to reconsider

If removal keeps slipping and stale flags accumulate. Past roughly a dozen, reading the code stops
telling you what actually runs, and the flag has become the long-lived branch it was meant to
replace — with worse tooling.

## Why

A branch that lives for weeks diverges silently: it keeps compiling against an codebase that no
longer exists. A flag on main is exercised by every build, so the divergence surfaces immediately
rather than at merge time.

The two-week removal window is the part that does the work. Without it this decision quietly turns
into permanent configuration, which is the failure mode named in the revisit condition.

## Background

Two rollbacks in one quarter, both traced to merge conflicts in week-old branches rather than to
the change itself.

## Options weighed

- **Long-lived branches.** Familiar, and the source of both rollbacks.
- **Flags on main, removed on a deadline.** *(this)*
- **Flags on main, removed when convenient.** The same as this one minus the only clause that
  keeps it honest.

## The dilemma

Flags are cheap to add and unrewarding to remove, so the deadline is the whole decision. If
nothing enforces it, this note describes an aspiration rather than a practice.
