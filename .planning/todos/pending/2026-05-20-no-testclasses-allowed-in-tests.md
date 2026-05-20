---
created: 2026-05-20T14:20:53
title: No TestClasses are allowed in tests
area: testing
files:
  - pyproject.toml (ruff config)
  - tests/** (all test files)
---

## Problem

Test classes (unittest.TestCase-style classes) are deprecated and should not be allowed in tests. Currently there is no enforcement — developers could add TestClasses without being blocked.

## Solution

Configure ruff with a rule that bans TestClasses in test files. This must be a hard requirement validated via ruff linting. Add appropriate ruff rule (e.g., PT009 or custom) to pyproject.toml and ensure it blocks any TestClass usage in the test suite.
