---
id: attention_disambig
role: example
thesis_role: load_bearing
prerequisites: [attention]
time_cost:
  short: 30
  standard: 60
faces:
  general: |
    Concretely. Two sentences:

    > *I sat on the **bank** of the river and watched the fish.*
    >
    > *I went to the **bank** to deposit a cheque.*

    The token "bank" is the same. After embedding, the vector for
    "bank" is identical in both sentences.

    After one or two attention layers, it is not.

    In the first sentence, attention has pulled in information
    from "river" and "fish." The "bank" vector has shifted toward
    the part of the embedding space where geographical features
    live. In the second sentence, attention has pulled in
    information from "deposit" and "cheque," and "bank" has
    shifted toward the financial-institution region.

    Same input. Same starting vector. Different neighbours.
    Different output. *That* is what attention does.

    Run this same trick across twelve layers, on every token,
    looking at every other token, and you have a representation
    that is deeply context-aware. You also have a reason to
    believe that the word "understand," when applied to the
    machine, is doing some work — even if it is not the work the
    audience instinctively assumed.
notes_to_self: |
  The attention example. Bank disambiguation is the canonical
  pedagogical case for attention because it is concrete (the
  audience can imagine running each sentence themselves) and
  ambiguous in a way the audience already understands (they have
  felt the word "bank" mean different things).

  Single face — the example is identical for both audiences. The
  technical audience knows what disambiguation means; the general
  audience just needs the demonstration.

  This is the strongest single beat in the whole talk for the
  general audience. Belief-trajectory waypoint W3 lands here; if
  the audience holds bank-disambig, beat 3 has succeeded.

  Length is on the longer side (~150 words on slide); calibrate
  in delivery — speaker can pause on the figure-of-speech "bank"
  line and let the audience laugh / recognise.
---

# attention_disambig

The bank-disambiguation example. Same word, different neighbours,
different meaning. The strongest single layman beat in the talk.
