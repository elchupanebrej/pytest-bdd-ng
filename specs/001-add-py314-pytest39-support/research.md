<!-- markdownlint-disable MD013 -->

# Research: Python/Pytest Compatibility Matrix

## Decision 1: Compatibility source of truth

- Decision: Use pytest-to-Python compatibility matrix as the canonical rule for valid pairs.
- Rationale: Matches FR-001 and user clarification to follow pytest compatibility matrix directly.
- Alternatives considered:
  - Maintain a project-specific allowlist: rejected because it drifts and can over-restrict supported pairs.
  - Only support latest pytest per Python: rejected because it violates full compatible-pair coverage.

## Decision 2: Matrix coverage strategy

- Decision: Generate and maintain tox environments so every pytest-compatible Python/pytest pair has an explicit runnable job.
- Rationale: Satisfies FR-003 and makes missing coverage detectable.
- Alternatives considered:
  - Sampled pair coverage: rejected by clarification requiring all compatible pairs.
  - Dynamic runtime-only expansion without explicit envs: rejected due to lower auditability.

## Decision 3: Local Python 3.14 provisioning

- Decision: Standardize local Python 3.14 setup through conda-forge environment creation for maintainers.
- Rationale: User explicitly requested conda-forge setup and it provides reproducible access to Python 3.14.
- Alternatives considered:
  - System Python only: rejected because availability is inconsistent.
  - pyenv-only path: rejected as non-standard for current team request.

## Decision 4: Incompatible/unavailable pair handling

- Decision: Fail fast with explicit compatibility reason codes and actionable message text.
- Rationale: Required by FR-006 and reduces troubleshooting time.
- Alternatives considered:
  - Silent skip: rejected because it hides coverage gaps.
  - Raw dependency install errors only: rejected because diagnostics are not user-actionable.

## Decision 5: Feature-scope inclusion policy

- Decision: Treat all currently uncommitted files as in-scope deliverables for this feature.
- Rationale: Direct clarification recorded in spec (FR-008).
- Alternatives considered:
  - Include only matrix-related files: rejected because it conflicts with accepted clarification.

## Decision 6: Commit hygiene enforcement

- Decision: Planning and implementation must respect constitution v1.1.0 (task-ID commit messages, mandatory clean pre-commit before commit).
- Rationale: Constitution is normative and applies to feature delivery gates.
- Alternatives considered:
  - Defer commit policy to post-merge cleanup: rejected because governance requires enforcement before commit.
