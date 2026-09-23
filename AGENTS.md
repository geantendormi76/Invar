LLM Collaboration Rules

- Local LLM is a bounded action selector, never a global architect.
- Every LLM stage must have a deterministic terminal condition.
- Every task has a hard LLM invocation budget.
- Identical target + stage must not invoke LLM repeatedly within one run.
- LLM output must use finite typed actions.
- Natural-language continuation such as "continue analyzing" is not a valid control action.
- ResearchLoop owns 403/405 denial research only.
- Secret findings must use an independent verification pipeline.
- REPORT_READY requires explicit evidence completeness.
- LLM inference is never physical evidence.
- Scanner findings are never equivalent to confirmed vulnerabilities.