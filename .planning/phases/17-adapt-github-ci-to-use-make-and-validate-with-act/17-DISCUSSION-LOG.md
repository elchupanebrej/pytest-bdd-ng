# Phase 17: Adapt GitHub CI to use make and validate with act - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-27
**Phase:** 17-Adapt GitHub CI to use make and validate with act
**Areas discussed:** CI command boundary, Tox integration, Node/message schema setup, Workflow validation

---

## CI Command Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Replace only duplicated run blocks with `make` targets | Keeps setup actions visible; lowest workflow churn. | ✓ |
| Make CI mostly Makefile-driven | Workflow does setup, then calls Makefile for almost everything. | |
| You decide | Planner picks smallest change preserving local/CI parity. | |

**User's choice:** You decide.
**Notes:** Decision was to keep GitHub Actions runner setup visible and move only project-specific commands into Makefile targets. This reduces drift without hiding CI environment shape.

---

## Tox Integration

| Option | Description | Selected |
|--------|-------------|----------|
| `GITHUB_ACTIONS` branch inside `Makefile` | `TOX` includes `tox-gh-actions` only in GitHub Actions. | ✓ |
| Explicit workflow install | Workflow installs `tox-gh-actions`; Makefile stays environment-agnostic. | |
| You decide | Planner chooses based on least duplication. | |

**User's choice:** You decide.
**Notes:** Decision was to put CI-specific tox plugin selection at tox command construction point. Local `make tox` stays normal; CI `make tox` gets `tox-gh-actions`.

---

## Node/Message Schema Setup

| Option | Description | Selected |
|--------|-------------|----------|
| Move to `make env-install-npm` | CI calls same target local users can run. | ✓ |
| Keep in workflow | Npm install remains visible GitHub Actions step. | |
| You decide | Planner picks based on parity vs clarity. | |

**User's choice:** You decide.
**Notes:** Decision was to add `env-install-npm` because formatter npm packages are project prerequisites. Keep `actions/setup-node@v4` in workflow because Node runner setup belongs to GitHub Actions.

---

## Workflow Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Manual `act --validate` in phase verification only | No Makefile target. | |
| Add `make validate-github-actions` wrapping `act --validate` | Local command becomes discoverable and repeatable. | ✓ |
| You decide | Planner chooses based on project command style. | |

**User's choice:** Add `make validate-github-actions`.
**Notes:** Decision was to make workflow validation a project command. Target must fail clearly when `act` is missing and phase verification must run it.

---

## the agent's Discretion

- Exact Makefile conditional syntax for `GITHUB_ACTIONS`.
- Exact target internals for `tox`, `env-install-npm`, `check-message-schemas`, and `validate-github-actions`.
- Exact workflow step names.

## Deferred Ideas

None.
