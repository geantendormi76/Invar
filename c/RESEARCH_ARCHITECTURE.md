# Invar Research Architecture Grounding

## 1. Authority

This document records the architecture grounding for Invar.

Priority order:

1. Invar static engineering constitution
2. Project HANDOFF / current repository state
3. Zhiniang Peng - "A Year of Hacking with LLMs"
4. Original js_ast implementation as legacy / behavioral ground truth

The original js_ast project is NOT treated as the architectural golden standard.
Its observable algorithms and data behavior may be treated as legacy ground truth when explicitly migrated.

## 2. Research Architecture

The target architecture is:

Deterministic Tools
    ->
Skill
    ->
Agent Reasoning
    ->
Verification
    ->
Evidence
    ->
Knowledge
    ->
Research Loop

## 3. Deterministic Tools

Tools must have deterministic responsibilities.

Examples in Invar:

- JavaScript AST extraction
- Endpoint normalization
- HTTP transport
- Response parsing
- Evidence serialization
- Static risk feature extraction

A deterministic tool must not silently become an Agent planner.

## 4. Skill

Skill defines when and in which order deterministic tools are used.

Skill is the workflow layer.

Skill must not duplicate the implementation of deterministic tools.

## 5. Agent Reasoning

For a high-risk API, reasoning is separated into two questions:

1. Behavior understanding
   - identity
   - parameters
   - required state
   - state transition
   - sensitive action

2. Authorization judgment
   - expected caller authority
   - observed caller authority
   - security boundary
   - whether the operation exceeds that boundary

Risk score is evidence for prioritization, not a substitute for authorization reasoning.

## 6. Verification Loop

A candidate hypothesis is not a finding merely because static analysis produced it.

Verification follows:

Hypothesis
    ->
Probe / PoC
    ->
Observed Result
    ->
Failure Interpretation
    ->
Mutation / Correction
    ->
Retry
    ->
Evidence

The loop is bounded and every iteration is recorded.

## 7. Evidence

Evidence must represent experiment history, not only the final response.

At minimum an experiment record should retain:

- target
- hypothesis
- attempt number
- request
- response
- interpretation
- mutation reason
- final decision

## 8. Knowledge Loop

Research results should be promotable into reusable knowledge:

Knowledge
    ->
Skill
    ->
Research
    ->
Root Cause
    ->
Pattern
    ->
Variant
    ->
Verification
    ->
Knowledge + Skill

## 9. Migration Rule

Legacy js_ast functionality is migrated by semantic role.

Legacy code is categorized as one of:

- deterministic tool
- skill workflow
- agent reasoning
- verification adapter
- evidence component
- knowledge artifact
- compatibility layer

No legacy file name automatically determines the new architectural layer.

## 10. Compatibility

Existing public behavior and TDD expectations should be preserved during migration whenever possible.

The first refactoring stage must be additive.

New abstractions should coexist with the existing implementation before legacy paths are removed.

## 11. Safety Boundary

Research functionality must operate against explicitly authorized targets or controlled fixtures.

Real credentials, embedded bearer tokens, hard-coded private identifiers, and unrestricted brute-force or rate-limit bypass logic must not become part of the reusable Invar core.

Such legacy artifacts may be retained only as historical research evidence and must not be promoted into generic production operators.

## 12. Current Refactoring Target

The first structural refactoring target is:

AdaptiveSandboxExecutor

Current responsibility:

- payload generation
- HTTP transport
- feedback recognition
- mutation
- retry loop
- evidence creation
- concurrency

Target separation:

ExecutionCoordinator
    |
    +-- HttpTransport
    +-- FeedbackInterpreter
    +-- MutationPolicy
    +-- EvidenceLedger
    +-- bounded loop control

The first stage must preserve existing observable behavior while creating these boundaries.

## 13. Grounding

Author source:
Zhiniang Peng, "A Year of Hacking with LLMs"

Relevant concepts:

- deterministic tools
- Skill-controlled tool sequencing
- behavior understanding
- authorization judgment
- execution feedback
- iterative correction
- knowledge and Skill feedback loop

Source:
https://sites.google.com/site/zhiniangpeng/blogs/Hacking-with-LLMs
