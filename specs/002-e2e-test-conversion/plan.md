<!-- markdownlint-disable MD013 -->

# Implementation Plan: E2E Test Conversion to Feature Documentation

**Branch**: `002-e2e-test-conversion` | **Date**: 2026-02-22 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/spec.md`
**Input**: Feature specification from `/specs/002-e2e-test-conversion/spec.md`

## Summary

Convert user-facing E2E pytest scenarios into executable feature documentation under `features/`, keep technical/non-convertible tests under `tests/`, and track parity/audit per conversion commit with follow-up fixes.

## Technical Context

**Language/Version**: Python (project-supported versions)
**Primary Dependencies**: pytest, pytest-bdd, pre-commit, markdownlint
**Testing**: `tests/e2e/test_e2e.py`, converted feature runs, parity audit checks
**Project Type**: Python library with feature-file documentation

## Constitution Check

- Follow-up fixes for conversion parity MUST be separate commits (no history rewrite).
- Pre-commit hooks MUST pass before each commit.
- For non-native platform test environments (except Windows), Docker skill MUST be used.
- Task/commit traceability MUST keep task IDs in commit messages for completed tasks.
- This spec MUST stay scoped to E2E conversion only; Python/pytest compatibility policy remains in spec 001.

**Gate Status**: PASS (enforced by T040-T045 and CI verification)

## Scope Boundary

- In scope: conversion candidate inventory, conversion parity, clear feature docs, retention markers for technical tests.
- Out of scope: Python/pytest version support policy and compatibility matrix logic (tracked in `specs/001-add-py314-pytest39-support/`).
