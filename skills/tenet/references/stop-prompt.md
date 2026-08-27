<!-- The gate injected at the end of a response, by hooks/on-stop.sh.

     It reaches the model through hookSpecificOutput.additionalContext, which is
     the only channel that works here: a Stop hook's plain stdout on exit 0 goes
     to the debug log and nowhere else. Until 2.1.0 this file was `cat`-ed to
     stdout, so the whole automatic-drafting path never ran once. Measured, both
     directions, 2026-08-27.

     @VAULT@ and @DRAFT_RULES@ are substituted by on-stop.sh. The drafting rules
     are a separate file on purpose — they are needed only when the gate fires,
     which is rare, and this text is paid at the end of every response. -->

TENET CHECK — evaluate this silently, then continue.

Did this session contain any of the following?

**A.** A real decision: at least two genuinely viable paths, where one was chosen for a reason.
**B.** An insight *the user themselves* arrived at and stated — a formulation of theirs worth keeping, not a finding you produced.
**C.** A tool that surprised you and will again: behaviour nobody would predict, not specific to this repository, and with no second viable path. That is a gotcha. Test it against A first — if two viable ways existed and one was picked, it is a decision, not a gotcha.

**If none: do nothing. Output nothing about this check. Stop here.** Most sessions qualify for none, and that is the expected outcome.

If one applies: read @DRAFT_RULES@ and follow it. The vault is @VAULT@. At most one draft per session, then mention in one short sentence that a draft is waiting.
