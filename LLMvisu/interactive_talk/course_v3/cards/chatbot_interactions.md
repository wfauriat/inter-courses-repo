---
id: chatbot_interactions
role: example
thesis_role: enriching
prerequisites: [hook]
time_cost:
  short: 0
  standard: 90
faces:
  general: |
    Three examples of the surface.

    *Ask:* "How do I get the disk usage of subdirectories on Linux?"
    *Get:* `du -sh */ | sort -h`, with a clear gloss of what each
    flag does.

    *Ask:* "Walk me through Bayes' theorem with a medical-test
    example." *Get:* a clean derivation with the prior/likelihood/
    posterior labelled.

    *Ask:* "Translate this Korean sign for me." *Get:* a translation,
    a guess at where the sign was photographed, and a caveat about
    the translation's confidence.

    Three domains. Three formats. One machine. And the machine has
    no idea what disk usage is, no idea what Bayes' theorem is, no
    idea what Korean is.

    It is doing exactly one thing.
notes_to_self: |
  Concrete refraction of the hook. Three examples chosen to
  demonstrate range without forcing an academic register: a unix
  one-liner, a stats explainer, a vision/translation task.

  No technical face — the example is identical for both audiences.
  The richness is the heterogeneity, not the framing.

  The closing two lines ("the machine has no idea... it is doing
  exactly one thing") sets up the next card: it is doing exactly
  one thing — predicting the next word.

  Length calibration: ~110 words; OK for a slide.
---

# chatbot_interactions

The lived-experience refraction. Three concrete chatbot
interactions that demonstrate the variety of surface behaviour,
followed by the line that pivots into the predictor claim.
