# Design Notes

- Detectives run in parallel branches and only emit `Evidence` models.
- `EvidenceAggregator` performs fan-in and error-gates judge execution.
- Judges run in parallel and produce `JudicialOpinion` using structured schema binding.
- `ChiefJusticeNode` is deterministic Python, not LLM-driven.
- Reducers prevent race overwrites across parallel branches.
