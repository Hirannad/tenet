---
type: decision
created: 2026-03-04
status: accepted
scope: domain
categories:
  - "[[Tools]]"
revisit: If p95 search latency passes 400 ms on the production index, or a ranking requirement arrives that full-text search cannot express — either one means the cheap answer stopped being the right one
supersedes:
superseded:
related:
---

## Decision

Search runs on Postgres full-text indexes. No separate search service until a measured limit is
hit, not an anticipated one.

## When to reconsider

Either of two observable things: p95 search latency past 400 ms on the production index, or a
ranking requirement that full-text search genuinely cannot express. Both are measurable, which is
the point — "when we outgrow it" is not a condition anyone can recognise on sight.

## Why

The dataset is under a million rows and grows slowly. A dedicated search service would add a
second datastore to keep in sync, and sync bugs are the expensive kind: they are invisible until
someone notices a result that should have been there.

This note is `scope: domain` on purpose. It is a fact about one project, not about how to work,
so it stays out of scope in every unrelated directory — which is what the binding gate is for.

## Background

A search service was proposed during planning on the assumption that Postgres would not keep up.
Nobody had measured it. Measured, it answered in 40 ms.

## Options weighed

- **Postgres full-text.** *(this)* One datastore, no sync.
- **A dedicated search service.** Better ranking, plus an index to keep in step with the database.
- **Client-side filtering.** Works today, falls over the moment the dataset stops fitting in
  memory — which is a condition nobody would notice until it happened.

## The dilemma

Deferring is right until it is late. If the migration is needed under load, it happens under the
worst possible conditions. The two thresholds above exist so the decision to move gets made before
that, on a number rather than a feeling.
