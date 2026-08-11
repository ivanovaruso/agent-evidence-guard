# Threat Model

## Assets
- validity of ALLOW/BLOCK decisions
- integrity of evidence references
- explicit authority references
- CI behavior

## Main threats
1. Unsupported completion claim -> required-evidence checks.
2. Missing authority -> fail closed.
3. Narrative evidence -> named evidence keys.
4. Policy bypass through wording -> prohibited-claim checks.
5. Core becomes an execution engine -> no shell execution, network calls, or dynamic code loading.

## Out of scope for v0.1
Semantic truthfulness of evidence, cryptographic provenance, remote attestation, model evaluation, and production authorization.
