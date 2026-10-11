---
id: ntp_summary
role: spine
thesis_role: load_bearing
prerequisites: [next_token_predictor]
time_cost:
  short: 15
  standard: 30
faces:
  general: |
    Half of the thesis, named.

    A modern LLM is a sequential probability calculator. It does
    not understand. It does not plan. It does not revise. It
    samples one word at a time from a distribution it computes
    from the prefix.

    The distribution is the whole game. The next thirty minutes
    are about how that distribution gets computed.
  technical: |
    Beat 2 closes. The artefact under examination is
    $p_\theta(x_{n+1} \mid x_{\le n})$ deployed under
    auto-regressive sampling. The remaining beats specify the
    function class $p_\theta$ belongs to and the procedure that
    fits $\theta$.
notes_to_self: |
  Beat-2 closer. One slide. Names what the audience now believes
  and previews what the rest of the talk addresses (how the
  distribution is computed).

  The line "the distribution is the whole game" is the load-
  bearing setup for the mechanism dive — every mechanism that
  follows is in service of computing this one distribution.
---

# ntp_summary

Beat 2 closer. The audience has accepted the predictor claim;
this card names what they have accepted and points at what comes
next.
