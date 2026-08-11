---
name: agent-evidence-guard
description: Validate whether an AI-agent completion claim is backed by the authority and evidence required by a bounded task contract.
---

# Agent Evidence Guard

Use this skill when a worker says a task is complete, tests passed, a fix is done, or another completion claim should be admitted.

1. Identify the exact completion claim.
2. Identify the authority reference.
3. List required evidence.
4. Compare required with actual evidence.
5. Check prohibited claims/actions.
6. Return `ALLOW` only when all required evidence is present; otherwise `BLOCK` with reasons.

This Skill does not authorize execution, deployment, merge, spending, or promotion.
