---
phase: 17
slug: adapt-github-ci-to-use-make-and-validate-with-act
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-28
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| developer shell -> Makefile | local commands execute static Makefile recipes | user command / none |
| GitHub runner -> Makefile | CI will execute Makefile recipes in hosted runners | runner context / high |
| Makefile -> npm/PyPI tools | recipe invokes external package managers and CLI tools | external dependencies / high |
| GitHub event -> hosted runner | untrusted PR/push metadata triggers workflow | event metadata / medium |
| workflow -> Makefile | workflow delegates project commands to repository-controlled Makefile | execution delegation / high |
| workflow -> secrets | build step reads secrets.PYPI_TOKEN on existing condition | PyPI token / high |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-17-01 | Tampering | `TOX` command construction | mitigate | Static command selection branching on `GITHUB_ACTIONS=true`; verified in `test_makefile_test_api.py`. | closed |
| T-17-02 | Tampering | `env-install-npm` packages | mitigate | Installs `@cucumber/html-formatter` and `cucumber-html-reporter` with `--no-save`; verified in `test_makefile_test_api.py`. | closed |
| T-17-03 | Denial of Service | `validate-github-actions` missing tool | mitigate | Guards `act` with `command -v act` and prints actionable install hint; verified in `test_makefile_test_api.py`. | closed |
| T-17-04 | Information Disclosure | `act` workflow validation | mitigate | Executes `act --validate` only; verified in `test_makefile_test_api.py`. | closed |
| T-17-05 | Information Disclosure | Build checking step secrets | mitigate | Preserves `TWINE_PASSWORD` scope only on Python 3.14 build step; verified in `main.yml`. | closed |
| T-17-06 | Tampering | GitHub Actions setup action supply chain | mitigate | Uses official setup actions and `astral-sh/setup-uv@v6`; verified in `main.yml`. | closed |
| T-17-07 | Tampering | workflow -> Makefile target mapping | mitigate | Explicit Makefile target calls, syntax validation, and contract check; verified in `test_template_packaging.py`. | closed |
| T-17-08 | Denial of Service | tox matrix fanout | accept | Accepted risk; tox matrix unchanged and out of scope. | closed |
| T-17-SC | Tampering | npm/PyPI installs | mitigate | Scoped packages are locked and contract-tested by exact name; verified in `test_makefile_test_api.py`. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-17-01 | T-17-08 | Matrix fanout is kept unchanged to preserve broad platform coverage matrix. | gsd-security-auditor | 2026-05-28 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-28 | 9 | 9 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-28
