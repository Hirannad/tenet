# Hot cache rules

`_meta/hot.md` is short recent context, restored at the start of a session in a bound directory.

## Why these rules are strict

A widely-used implementation of this same idea shipped a `Stop` hook whose text read, verbatim,
*"It is a cache, not a journal."* Its own `hot.md` had grown to 13 KB of release-engineering
log — commit hashes, branch names, audit findings — and that file was concatenated into the
context at every single session start.

The idea was sound. The discipline failed. These limits exist so the same thing cannot happen
here quietly.

## The rules

1. **500 words maximum.** Check with `wc -w` before writing. If the new content does not fit,
   cut old content — do not raise the limit.
2. **Overwrite completely. Never append.** Appending is how a cache turns into a journal.
3. **Four sections only:** Last updated, Key facts, Recent changes, Active threads.
4. **No commit hashes, branch names, file-by-file change lists, or release detail.** If it looks
   like a changelog entry, it belongs in `_meta/log.md`.
5. **Present state, not history.** "The scoping mechanism is binding-based" belongs here.
   "On the 12th we switched from folders to bindings" belongs in the log.

## The division of labour

| File | Shape | Grows? |
|---|---|---|
| `_meta/hot.md` | Current state, ~500 words | No — overwritten each time |
| `_meta/log.md` | One paragraph per session, newest first | Yes, forever |

When you feel the urge to add detail to the cache, that urge is correct — the detail matters.
It just belongs in the log.

## Self-check

Before writing `hot.md`, ask: *if this were the only thing loaded at the start of the next
session, would it help, or would it be noise?* Anything that fails that test goes to the log.
