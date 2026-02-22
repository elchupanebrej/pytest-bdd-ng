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

## Scope Boundary

- In scope: conversion candidate inventory, conversion parity, clear feature docs, retention markers for technical tests.
- Out of scope: Python/pytest version support policy and compatibility matrix logic (tracked in `specs/001-add-py314-pytest39-support/`).
