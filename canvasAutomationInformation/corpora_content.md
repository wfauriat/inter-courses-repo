This document content on the corpora of ideas and claims I want to push and communicate.
There are adjacent articles that make attempt at structuring those claims and idea. I will supply them latter.
Yet this is an inherently difficult exercise as claims and ideas may be :
- connected to one another
- at first hide complexity or proper framing that has to be supplied in sequence, so that the reader/student/audience is not overwhelm
- provocative and trigger defense mechanisms
- dependent on one another : a claim may rest on a formal item or an objet not yet defined
- possibly referencing a particular domain or several : maths, statistics, epistemology, decision making, engineering, computing,...
- the "short description" of an idea may open attacks on "simplification" or "insufficient framing"
- proper ontological arranging of different "types" of statements or remarks may be hard to conceive rigorously

Below are the rather unsorted claims, ideas, remarks :
For some statement , indication are given between brackets [] as to what the "type" of statement is.
Some attempts at classifying statements in domains or "ontological areas" is made.

___

More generic:

- We are focused too much on identifying "what is", we should think in terms of "what could be" [Central claim on disposition]
- Epistemic humility should be encouraged as a disposition [Central claim on disposition]
- Structural (academic, economic,...) incentives tend to punish humility and reward confidence and expertise [Structuring remark on humility issue]
- Psychology resist humility : on identify, on expertise display [Structuring remark on humility issue]
- Scientists have been largely trained to discover "hidden truth": this is often a poor incitation to think the "true answer" is accessible [Claim on inherent lack of humility]

More practical or decision-flavored:

- Why think on limits of reasoning ? Because "how you choose" to process information does shape the "actual" outcomes you get out of your decisions [Explicit display of intent and purpose]
- How to make "proper use" of information for decision making ? [Explicit display of intent and purpose]
- It is better to be vaguely right than precisely wrong [Central claim on disposition toward reasoning]
- The "real world" doesn't care about our anticipations : the world responds to our action, not to our picture of it [Central claim on the specifics of decision making]

Moving into the inference domain:

- Statistics is the "practice" at the intersection between "virtual tools" and "practical problems" [Positionning domain and toolset]
- "Pure maths" have no "direct reach" into the real world [Positionning claim]
- There are two modes to derive conclusions or predictions : deduction from certain rules; induction from possible conditionning [Central theoretical assertion]
- Deduction rests on perfectly described objects or contexts (no exceptions) and necessary conclusions, inductions rests on "sufficiently similar" conditions / observations and generalised patterns or relationships
- Deductive and inductive modes have associated guarantee regimes : for the deductive mode, the guarantee holds if and only if the supporting assumptions hold; for the inductive mode, the guarantee holds if the deployment context is sufficiently similar to the observation context and the observations in that context are sufficiently "solid" [Central theoretical assertion on prediction guarantees]
- This is especially relevant when discussing formal guarantees on predictive uncertainty (ranges, quantiles), notably from the perspective of conformal prediction : either predictive uncertainty holds for distribution-based cases (if and only if the chosen distributional hypothesis holds), or for distribution-free cases (if the predictive uncertainty is correctly calibrated against a "similar" context). Either way the guarantee rests on a framing-level condition the method itself cannot certify
- Probability is a support tool for judgment, not a quantity grounded in nature [Central theoretical assertion, tool definition]
- "Exact" probability is a categorical error, only frequency (of a perfectly repeatable context, thus an inherently limited notion) can be discussed as possibly grounded [Positionning claim]
- Eliciting a probability for a proposition Pr(X) is distributing "possible/alternative state/issues/worlds", given the best of our (backround) knowledge [Framing tool definition]
- Using probability (conditionnal) is the "relevent" approach to answer : what can we conclude, given what we know (Pr(Y|X)) [Tool definition, concept framing]
- The law of total probably is the proper framing of making predictions : Pr(Y) = sum Pr(Y|X)Pr(X) : what can we say about Y is, what does knowing X tell us about Y and how strongly is X supported
- Every conlusion (about the world) is necessarily subjective [Central claim of epistemological inclination]
- Allowing alternatives or "possible worlds", and compute "conclusions" accordingly, is the proper way to navigate inherent uncertainty (irreducible beyond a reasonable point) [General framing of disposition toward reasoning]
- Stripping uncertainty in long or complex reasoning chains (natural tendancy), between component models, is risky and can provoke unreasonable or overly confident predictions
- Displaying uncertainty is often as or more interesting than displaying a point prediction
- It is often good engineering practice (even if it resists formal specification) to consider an uncertainty buffer or to adjust the distribution of possible outcomes by allowing for what might not have been specified — a stress case, an alternative dreary scenario, an "and what if we're missing something" branch. The move cannot be derived from inside the frame, but it is one of the practical answers to the structural problem of ontological uncertainty [Central practical claim on disposition under unspecified outcomes]

Moving close to the frame problem and source of uncertainty:

- The "frame problem" (philosophical) is issue of considering what "actually" matters for a particular prediction problem / instance [Laying out the theoretical framing]
- The "indeterminacy of relevence" is a circular issue : to determine what "does" matter (what would actually "lock-in" a prediction), one has to have an idea of what "could" matter, and sort out between what does and doesn't [Central practical claim]
- When making a prediction of drawing a conclusion, one has to specify what matters : Pr(Y|X1,X2,X3,...) : how to know "in advance" which Xis to select
- Finite specification (necessarily finite in practice) of the context / conditions is what engenders uncertainty
- How "far", how "precisely" to specify before predicting, is the instanciation of the frame problem. It is circular and cannot be exactly determined a priori. [Synthesizing the practice of the frame problem]
- The frame problem applies to both the deductive reasoning mode and the inductive reasoning mode, and thus precludes perfect (exact) prediction structurally
- Authors talk about the limits of "reasonning from a finite position" and about "bounded rationality" (as a consequence for decision-making disposition)
- In uncertainty quantification, one generally functionnaly separates "aleatory uncertainty" : what we choose not specify any further and "leave to chance"; and "epistemic uncertainty" : what could be reduced by acquiring additional information (thus acknowledging the limits of out current knowledge)
- When "deciding" what to specify our predictions build on: what we know will induce variations, both the sources we could possibly reduce but decide not (epistemic) and the sources it would not be practical to reduce (aleatoric), but also what we may not have though about (ontologic)
- In uncertainty quantification, one rarely talks about "ontological uncertainty" : what is relevent, what to consider, what to include in models
- Bertrand Russels's (or Hume's) turkey : prediction confidence grows progressively until Thanksgiving, but the frame is poorly selected

On discovering relevence and connexion with exploration and agency:

- There are essentially two ways to discover relevence : either, someone told you, or, you bumped into it through exploration [Central claim in exploration and relevance]
- Exploration could be a way to expend existing ontlogy or peek behind current frame limits
- Grounding of an agent (human or artificial) into an environnement allows exploration, and possibly discovering relevence
- Exploration does not escape the finite specification issue (choice have to be made about relevence, and limits regarding prediction will follow necessarily)
- Exploration has no built-in guarantee of discovery
- Exploration is not acceptable in various circonstances : damage during exploration, risk, irreversibility of consequences (so exploration has practical limitations, depending on context) [Practical limitations]
- Designing artificial agents locks-in what they can and cannot explore (given capabilites / reach)
- Agents are formal systems and setting the frame of the agent is a choice (of an ontology, what he can and cannot know or do) 
- A reasoning system (human or artificial) reasons from within a frame : it is structurally blind to its own blind spots, it cannot audit the frame from within [Important claim]

On consequences on decision making and reasoning disposition:

- Robustness of decision of outcomes depends on anticipations of possible variations (uncertainty) and adapted choice of a course of action [Framing the decision making analysis]
- Decisions necessarily based on expectations (expected utility), consciously or not
- A rationnal agent would not select an alternative from which he expects lower utility than another available and "better" expectation
- Expected utility relates to a distribution of possible outcomes (necessarily) : the real output of the decision will be a single point / observation / consequence
- Comparing expected utility with actual outcome, a posteriori, can be framed as studying "regret" or "calibration of anticipation"
- In many practical situations, "calibration" of expectations is not possible or relevent
- Example of crossing a sea with or without a lifeboat (or a satelite phone). Incident will not occur X percent of the time, it will either occur or it won't. Probability is how we judge likelihood (given information) it prior to sailing
- Example of crossing a sea : how we eventually act is inherently connected to what we think before acting (practical grounding of subjective probabilities)
- Predictions are inherently (structurally) uncertain: whether we are more or less cautious, or allow alternative issues, or resist overconfidence, is a disposition that will instantiate differently on different practical issues
- There is no "right" balance to strike between carefulness and lack of initiative: it is always problem dependent
- If good practices, or a methodological "solution" to the "uncertainty" issue could be formalized accross practical problems (no-free lunch): this formalization would have occured already (formalizing is a choice, and it is a circular one, choosing just moves the question of which choice to the meta-level of choosing the choice of framework)
- There are no "formal" or "good" solution to the issue of reasoning from a finite position, only dispositions and : some of them are riskier than others, more prone to surprises, and possibly regret, less robust

On the context of decision making:
- Increase in complexity (especially with AI) in problem tends to increase the dificulty to reason with judgement (thus anticipating alternative reasonably): e.g. long reasoning chains, complex systems with many layers, components, abstractions
- Increase in automation (especially with AI) tends to decrease the ability to maintaning reflexivity on the "chosen" treatments and information process: producing opacity
- Increase in automation tend to increase the througput of automated judgements, thus making it harder to evaluate a large pool of produced judgements or conclusions (this is a ressource allocation issue : more tools or more evaluations)
- With more automation in information processing, there is a move from less "model-based" conclusions (deduction inclined with curated hypothesis structured) to more "model free" conclusion (induction inclined, with seemingly agnostic model structure, infered from data)
- The careful and painful practice of model selection and hypothesis critique and reflexive analysis tend to get supperseed with automatic selection, when more computing power is available: this opens risks of less robust conclusions and poor extrapolation performance of information process


Related issue on data-driven reasoning:
- Data-driven prediction have inherent limitations (the context is never exactly similar to observation setting, due to finite description ability): extrapolation may be poor, especially in high dimensionnal space and with large parametric models
- In uncertainty quantification, the issue is often "the data we don't have", not the the data we "do have": data-driven methods can only do so much in this case (but it is paradigmatic of the decision under uncertainty issue)



