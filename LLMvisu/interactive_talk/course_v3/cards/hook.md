---
id: hook
role: hook
thesis_role: load_bearing
prerequisites: []
time_cost:
  short: 30
  standard: 90
faces:
  general: |
    You have talked to ChatGPT, Claude, Gemini, or one of their
    siblings. They wrote your code, summarised your meeting, told
    you why your soup is too salty.

    They feel like they understand you.

    None of them does. Underneath, every one of them is a
    probability calculator that emits one word at a time. The rest
    is engineering and scale.

    This talk takes the calculator apart.
  technical: |
    The deployed surface — ChatGPT, Claude, Gemini, Mistral — is a
    thin product layer on top of a single class of artefact: a
    decoder-only transformer pretrained on internet-scale text
    against a next-token-prediction objective, then post-trained
    against a human-preference signal.

    The product layer is not the artefact. This talk specifies the
    artefact, then specifies the product layer, then names the gap
    between them.
notes_to_self: |
  Opens the talk. Sets tone. Commits to demystification register
  before any abstraction. The "they feel like they understand you,
  none of them does" is the thesis-half-1 announced as a line, not
  yet earned. The rest of the talk earns it.

  Length calibration: slide-appropriate, ~80 words on general face.
  Technical face is shorter and more declarative — technical
  audience does not need the warm-up.
---

# hook

The opener. Lands the demystification register before the audience
has had time to build defenses. The promise made here ("this talk
takes the calculator apart") is the contract the rest of the spine
honours.
