# Friction & Exposure Map (v0 draft)

Working document for the Argument Canvas project. Drafts five audience orientation profiles plus the structural commitments list shared across all paths. Designed to be reacted to and corrected — the exposure sets in particular are inferred from the corpus and the *Perspectival Trap* article, and may need adjustment.

**How this document is meant to be used.** It feeds the topology pass that comes next. Each profile names a legitimate entry point into the territory, a natural question that any honest path to that orientation has to be visibly engaging with, a defense mechanism the path has to anticipate, and a small *exposure set* — the claims this audience most needs to be brought into contact with, because their practice insulates them from these claims. The artifact's path-completion criterion is exposure, not assent.

---

## Structural commitments (the territory-floor)

These claims are visited by every legitimate path, regardless of orientation. They are not the destination; they are what every destination rests on. A path that bypasses any of these is incomplete, no matter how coherent it feels locally.

**C1. Acting on the world is mediated by a picture of the world.** Every decision rests on a constructed representation — perception, measurement, model, inference. The world responds to the action, not to the picture. The picture is what the agent has; the world is what the agent affects.

**C2. Relevance requires a frame, and the frame is structurally invisible from inside.** Any reasoning system must decide what matters before reasoning can proceed. The decision is made from a prior vantage point — knowledge, experience, model class. The frame shapes what counts as evidence; what counts as evidence shapes the frame. The loop is closed and cannot be opened from inside the system.

**C3. Specification is finite. What isn't specified is either chosen-not-to-be (aleatory), could-be-reduced (epistemic), or wasn't-considered (ontological).** Real reasoning systems specify finitely. The third category — what the system didn't know to consider — is where most frame failures live, and it's the category least discussed in uncertainty quantification.

**C4. Rigor within a frame and adequacy of the frame are different things.** Internal validity, mathematical soundness, empirical fit — all real, all achievable. Completeness with respect to the world is not. Precision earned within a frame does not transfer to confidence that the frame was right.

**C5. The meta-level no-free-lunch.** No universal procedure can decide when a frame is adequate, because adequacy is relative to a context that the procedure cannot fully anticipate. Any proposed solution to the framing problem is itself a frame and inherits the problem. This forecloses the move "we just need a better methodology" — the methodology is the choice being deferred.

These five commitments are what the artifact treats as non-negotiable. They are visited by every path; they are *what* every path makes visible, even when they're not what the path is *about*.

---

## Orientation profiles

### Engineer

**Legitimate starting point.** Decisions and outcomes. Real consequences in the world. A built thing that performs or fails, a decision that pays off or doesn't, a system in deployment.

**Natural question.** *Why do my predictions or my system underperform in ways I can't always anticipate, and what does the methodological care I'm asked to invest actually buy me?*

**Earned versus asserted ledger.** Grants immediately: predictions are imperfect, robustness matters, decisions have stakes, complex systems surprise their designers. Requires justification: probability as anything other than frequency or "the model's confidence number"; talk of "subjective" anything (sounds like loosening rigor); long detours through formal limits before the practical bite is visible. Will absorb formal material once it's clear what practical problem it solves; will tune out if formal material arrives before its practical motivation.

**Defense mechanism.** *This is academic / philosophical. In practice, we handle it with safety factors, redundancy, conservative design.* The move is to treat frame inadequacy as a known cost already priced into engineering practice — and therefore not in need of further interrogation. The defense is partly right (engineering does handle frame uncertainty heuristically), which is why it works as a defense. The counter-move is not to deny the heuristics work but to show where they predictably fail: at interfaces between models, in regimes outside calibration, in novel-coupling complex systems where the safety factor's basis is itself a frame.

**Practice-implicating exposure set.** The claims most likely to question the engineer's practice:

- *Frame failures live at the interface between models, in the variable that was excluded before analysis began, in the assumption too obvious to state.* This is the claim that safety factors and redundancy do not address, because both presuppose the relevant failure modes were anticipated. The engineer needs to be brought into contact with the failure mode that *was never on the list*.
- *Specification is finite; ontological uncertainty is the category least discussed and most consequential.* Engineering uncertainty quantification typically distinguishes aleatory and epistemic; rarely raises ontological. This is the specific gap.
- *Automation increases throughput of confident outputs and decreases the resource available for evaluating each.* The engineer working in a heavily automated pipeline has practice that systematically erodes the conditions for catching frame failures. This is the practice-implicating claim with the sharpest contemporary edge.
- *Honest communication of a number requires communicating its conditions, assumptions, and failure modes. Otherwise the number is a transfer of responsibility dressed as information.* This is the claim that makes their downstream communication practice questionable to themselves.

**Likely path shape.** Enter at a concrete failure scenario (the lifeboat, or a domain-specific equivalent). Move through *why predictions are inherently imperfect* (finite specification, frame-dependence) as the explanation for the failure. Reach the inference machinery (probability as judgment, total probability as the framing for prediction under uncertainty) as the *toolset for handling what the failure scenario revealed*. End at the disposition and communication claims as *what the engineer should do given what they now see*.

---

### Statistician

**Legitimate starting point.** Tools and their proper use. Probability, inference, modeling, uncertainty quantification — as a craft with right and wrong ways to deploy.

**Natural question.** *What are the actual conditions under which my methods produce reliable conclusions, and where are the conditions silently violated in practice?*

**Earned versus asserted ledger.** Grants immediately: probability requires a frame of reference; model selection involves choices; sensitivity analysis matters; data have provenance. Requires justification: claims that organizations or institutions silence uncertainty (feels like sociology, not statistics); claims that the discipline systematically misuses its own tools (feels like an indictment rather than a methodological observation); the assertion that "every conclusion is necessarily subjective" (tripwire word — sounds like license for arbitrary belief, when the actual claim is structural). Will absorb foundational and meta-methodological material readily; will resist when the conversation moves to deployment-context critique without first establishing it in methodological terms.

**Defense mechanism.** *The methodology is sound. Misuse is a deployment problem, not a methodological one.* The move is to defend the discipline by separating the tools from their misapplication — which works as a defense because it's also partly true. The counter-move is to show that some of the deployment failures are *not* misapplications but *structural consequences of the tool's design assumptions being silently relaxed at the institutional interface*. Robustness analysis bounded by an assumed model class; sensitivity analysis whose perturbations live within the same frame; calibration over a reference class that doesn't include the deployment context.

**Practice-implicating exposure set.**

- *Ontological uncertainty — what isn't in the model because no one thought to put it there — is the category UQ practice underweights.* Statistical UQ has rich machinery for aleatory and epistemic; the third category sits outside the standard apparatus. This is the gap that disciplines like risk analysis sometimes name and statistics-as-such typically does not.
- *Bounded robustness is not the same object as indeterminate framing. Sensitivity within a model class does not address adequacy of the model class.* The statistician's instinct is to bound the residue with elicitation, robustness, and prior-class analysis. The exposure claim is that some residue is not bounded — it's framed, and the frame is the thing the analysis cannot interrogate from inside.
- *In deployment, the conditions under which the tools are sound get systematically relaxed: by automation, by speed, by institutional reward for confident outputs.* This is the deployment claim that needs to be earned through methodological setup, not asserted up front.
- *Probability as judgment-support — distributing over possible worlds given background knowledge — is not the same object as frequency, and conflating them obscures what's actually being claimed in most applied work.* This sits closer to a foundational disagreement than an exposure claim, but it's load-bearing because it determines whether the conversation has shared definitions.

**Likely path shape.** Enter at a methodological framing — probability as judgment-support, total probability as the structure of prediction. Move through the foundational distinctions (deduction/induction, aleatory/epistemic/ontological) as proper craft hygiene. Reach the frame problem and finite specification as the *limit of what the tools can do*. Arrive at the deployment-context claims (automation, institutional pressure, honest communication) as *the place where the discipline's good practices most need active protection*. The disposition claim lands as a craft commitment, not a moral one.

---

### Mathematician

**Legitimate starting point.** Formal objects and their structural properties. Definitions, theorems, limits, impossibility results.

**Natural question.** *What is the structural reason — independent of any particular tool's adequacy — that complete reasoning systems are not available, and what does that imply for what we can prove?*

**Earned versus asserted ledger.** Grants immediately: formal limits, impossibility theorems, the existence of frames in any formal system, dependence of conclusions on definitions and axioms. Requires justification: claims that tools are *practically* inadequate (their domain isn't practical adequacy; will respond *you picked the wrong tool*); claims about deployment or institutional context (not the unit of analysis); claims that the formal apparatus *must* engage with messy real-world judgment (feels like a category error). Will absorb structural arguments deeply; will dismiss claims framed as practical critique of formal tools.

**Defense mechanism.** *The formal object does what it does. Whether it's the right tool for a given purpose is a separate question, not a critique of the object.* This is the cleanest defense of the three because it's *correct* on its own terms. The counter-move is not to attack it but to push *up* the abstraction ladder: the claim is not that any particular formal tool fails its job, it's that *the act of choosing which formal tool to apply* is itself a frame-dependent choice that no formal system can decide for you. The meta-level no-free-lunch is the structural argument the mathematician will actually engage with.

**Practice-implicating exposure set.**

- *The frame problem is not "old AI" or "philosophical." It is a structural property of any reasoning system that must filter relevance from a finite specification, and it survives at the meta-level: choosing the formalization is itself a frame.* This is the claim the mathematician most needs brought into contact with their practice, because the practice involves *choosing formalizations*, and the choice is not formally decidable from inside.
- *Reasoning systems are structurally blind to their own blind spots. The frame cannot audit itself.* This is the structural claim that, taken seriously, applies to the practice of constructing formal theories as much as to applied modeling.
- *Probability is a support tool for judgment, not a quantity grounded in nature. The mathematics is sound; the metaphysical claim that "exact probabilities exist out there" is what gets imported when the formalism is deployed.* The mathematician may not personally hold the metaphysical claim, but their tools are routinely deployed under it.
- *Formal completeness within a frame is not the same object as adequacy of the frame, and the meta-level no-free-lunch says no formalism dissolves this distinction.* This is the claim that questions the practice of *responding to applied critique by formalizing further*.

**Likely path shape.** Enter at the formal frame problem — relevance filtering, finite specification, the structural impossibility of self-audit. Move through the deduction/induction distinction (both modes inherit the frame problem; deduction does not escape it through formality). Reach probability and Bayesian decision theory as *the most refined formal response to the structural problem, and the point at which the structural problem reappears at the meta-level* (prior selection, utility specification, coherence under bounded computation). End at the meta-level no-free-lunch: the practice of formalizing-further does not dissolve the problem; it relocates it.

The mathematician is the audience for whom the article's structural argument lands most directly. The practical and disposition claims come *after* the structural setup, as instantiations of the structural claim, not as independent material.

---

### CS/ML practitioner

**Legitimate starting point.** What the system actually does. Empirical performance, deployed behavior, capability boundaries, what scales and what doesn't.

**Natural question.** *What does the system I'm building actually inherit, and where do its capabilities end in ways the benchmarks don't tell me?*

**Earned versus asserted ledger.** Grants immediately: distribution shift is real; benchmarks aren't deployment; reward specification is hard; ML systems can fail in surprising ways. Requires justification: that the frame problem applies to *modern* ML (the "old AI" dismissal is the load-bearing resistance here); that scale doesn't dissolve the structural problem (intuition runs the other way — more data, more compute, more capability is usually their experience); that "model-free" is a misleading description of what learned representations are doing (these models *do* have implicit frames — training distribution, loss function, architecture — but the practice talks as if they don't).

**Defense mechanism.** *This is old AI thinking. Modern ML is a different paradigm — the frame problem was about symbolic systems; learned representations route around it.* This is the most distinctive defense of the five, and the one that requires the most specific counter-move. The path *must* visibly translate the frame problem into modern ML idiom — distribution shift as frame breakdown, reward specification as utility specification, training-distribution-and-loss-function as the implicit frame the system inherits, deployment context as a frame the system never had access to. Without this translation, the CS/ML practitioner has a legitimate complaint that the argument is using a vocabulary from a paradigm they correctly identify as superseded.

**Practice-implicating exposure set.**

- *Scale does not dissolve the frame problem; it obscures it.* This is the central exposure claim and the one that most directly questions the practice. Their working hypothesis — more capability solves more problems — is partly right, which is why the exposure has to be careful: the claim is not "scale doesn't work," it's "scale doesn't reach the *kind* of problem the frame problem names."
- *Opacity is not neutral. As the production of confident outputs accelerates, the capacity to evaluate whether those outputs rest on adequate frames must be actively protected — because it will not protect itself.* The abstraction ladder that modern ML rests on (silicon, OS, frameworks, learned representations) renders the system's inner workings opaque even to trained practitioners. Their practice is conducted under conditions that systematically erode reflexiveness.
- *Model-free is a misleading description. The frame is in the training distribution, the loss function, the architecture, the dataset curation, the deployment integration. The system has frames; the practice talks as if it doesn't.* This is the claim that questions the rhetorical move of "learning from data" as if it dissolved the inductive bias problem.
- *The drift from "a complex tool operating within a frame" to "an intelligent agent whose capabilities might somehow exceed the limitations that apply to all reasoning" is a perceptual error the field's discourse actively encourages.* This is the claim that questions the field's external communication and self-image, and it's the sharpest-edged of the four.

**Likely path shape.** Enter at a deployment failure or capability boundary the practitioner will recognize (distribution shift, reward hacking, a real failure in a system they know the shape of). Move through *what the system inherited that produced the failure* — training distribution as frame, loss function as utility specification, architecture as inductive bias. Reach the structural frame problem in *modern* idiom: relevance filtering, finite specification, the impossibility of self-audit. Arrive at the opacity-and-reflexiveness claim: the practice operates under conditions where catching frame failure is structurally harder than producing confident output. End at the disposition claim and the field-level claim about external communication.

The CS/ML path is the one for which the contemporary stakes are sharpest, and probably the one most worth getting right.

---

### Layperson

**Legitimate starting point.** Concrete situations with stakes that a non-specialist can hold without specialist machinery. A decision, a choice, a thing that worked out or didn't, a story.

**Natural question.** *Why does this matter to me, and what is the thing I should actually understand?*

**Earned versus asserted ledger.** Grants almost anything concrete. Requires concrete anchoring for almost anything abstract. The challenge is not ideological resistance but attentional collapse — the moment the argument feels like it has left the world of things-they-can-picture, they're gone. They will accept abstractions if and only if those abstractions are visibly doing work on a concrete case they can still see.

**Defense mechanism.** *This is too technical for me, I'm not the audience for this.* The defense is identity-protective (feeling competent rather than lost) rather than ideological. The counter-move is not argument; it's never letting the concrete anchor disappear from view, and ensuring each step lands as a single sentence the layperson can paraphrase. This is more demanding than it sounds: most of the corpus is currently expressed in machinery the layperson doesn't have. The translation work is real.

**Practice-implicating exposure set.** The layperson does not have a "practice" in the same sense the other four do. The exposure question becomes: what should the layperson understand that changes how they receive expert claims they encounter in life?

- *When experts give you a number, the number is conditional on a frame. Asking what the frame is, and what was left out, is not a sign of failing to understand — it is the actual content of intelligent reception of expert advice.*
- *Confidence and reliability are different things. A system that produces confident outputs faster than they can be evaluated is not the same as a system that produces reliable outputs.*
- *Uncertainty is not always a failure of expertise. Sometimes it is the honest description of what is knowable, and the absence of expressed uncertainty is the warning sign.*
- *Some questions are not the kind of question that has an answer in the form being asked, and recognizing that is itself useful knowledge.*

These are less practice-implicating and more *reception-improving*. The layperson's path is the one where the exposure goal is not destabilizing a practice but equipping a stance.

**Likely path shape.** Enter at a concrete recognizable scenario (the lifeboat is good; the turkey is good; a medical decision under uncertainty is good). Move through *why this scenario is harder than it looks*, keeping the scenario in view the whole time. Reach *the general structural reason* — frames, finite specification — only when the concrete case has already made the point and the abstraction is consolidation rather than introduction. End at *how to receive expert claims with this awareness*, anchored back in concrete cases.

The layperson path is the most format-sensitive: visual concreteness matters more than for the other four, and the canvas's spatial-emergence design probably pays off for this audience most directly.

---

## What this document does and doesn't decide

**It decides:**

- The structural floor (C1–C5). These are the commitments every path makes visible.
- Five orientation profiles with their entry points, natural questions, defense mechanisms, and practice-implicating exposure sets.
- The path-completion criterion: a path is complete if it has visited the structural floor and the audience-specific exposure set, regardless of whether it ends at a shared destination.

**It doesn't decide:**

- The bridge-layer claims (probability machinery, expected utility, exploration, deduction/induction). These are the working concepts that connect floor to exposure across paths, and they need their roles assigned by the topology pass.
- The example cards (lifeboat, turkey, triage, ML-specific examples). Their authoring depends on how many references they actually carry.
- The edge declarations. Each pairwise relation between claims gets a type and possibly a precondition; this is topology-pass work.
- The role-per-orientation problem for the schema. Each card needs role information that depends on which orientation is reading it. The schema sketch from earlier (`roles: { engineer_path: ..., statistician_path: ..., ... }`) is provisional and should be validated against real cards.

**Open questions to flag for the topology pass:**

- Whether the "honest communication" claim (the number-with-conditions point) is one claim or several. It plays different roles for the engineer (downstream practice), the statistician (the deployment interface), and the layperson (reception stance), and may need to be split.
- Whether "exploration as a way to discover relevance" is a bridge concept or a fifth structural commitment. It connects to frame-non-self-audit (exploration as the way you sometimes find what your frame omitted) but it has its own complications (exploration is itself frame-dependent; exploration doesn't escape finite specification; exploration has practical limits). I lean toward bridge, but this is a real choice.
- Whether the meta-level no-free-lunch is itself the destination for some paths (especially the mathematician's) or a structural commitment that all paths visit. I've placed it as a commitment, but the mathematician path may want it as a load-bearing destination card rather than a floor card. This is a per-orientation role-assignment question and is exactly the kind of thing the schema's per-orientation roles need to handle.

---

## Notes for the topology pass

A few things to carry forward.

The exposure sets are *small on purpose*. Three to four claims per audience. The temptation will be to add — the corpus has more material that's relevant for each. Resist; the exposure set is "what this audience most needs," not "what's relevant to this audience."

The structural floor is also small on purpose. Five claims. Adding a sixth requires showing it's not derivable from the five.

The five orientation profiles are not exhaustive. Risk professionals, policy analysts, decision-makers in non-engineering contexts, and philosophers of science are real audiences with their own legitimate starting points, and the artifact may eventually want them. They're not in v0 because the corpus is most clearly addressed to the five included here.

The "convergence not required, exposure required" stance has a sharp consequence worth being explicit about: **the artifact can produce paths that are coherent within their orientation but leave the receiver in disagreement with another orientation's path**. That's by design. The territory hosts genuine plurality. The artifact's job is honest exposure within each orientation, not forced reconciliation between them.