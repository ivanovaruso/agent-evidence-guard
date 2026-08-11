# Contributing

Contributions are welcome.

- Keep the core deterministic unless a change clearly requires otherwise.
- Add tests for behavioral changes.
- Do not add network calls or model-provider dependencies to the core without a documented reason.
- Do not weaken fail-closed behavior silently.
- Prefer small pull requests with explicit acceptance criteria.

Run: `python -m unittest discover -s tests -v`.
