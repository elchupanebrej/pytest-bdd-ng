#!/usr/bin/env bash

# Script to check prerequisites and return feature paths

set -euo pipefail

OUTPUT_JSON=false
PATHS_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      OUTPUT_JSON=true
      shift
      ;;
    --paths-only)
      PATHS_ONLY=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Get current branch name
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

# Check if we're on a feature branch (pattern: NN-feature-name)
if [[ ! $BRANCH_NAME =~ ^[0-9]+-[a-zA-Z0-9_-]+$ ]]; then
  if [[ "$OUTPUT_JSON" = true ]]; then
    echo "{ \"error\": \"Not on a feature branch. Current branch: $BRANCH_NAME\" }"
  else
    echo "Error: Not on a feature branch. Current branch: $BRANCH_NAME" >&2
  fi
  exit 1
fi

# Extract the feature number and name
if [[ $BRANCH_NAME =~ ^([0-9]+)-(.+)$ ]]; then
  FEATURE_NUM=${BASH_REMATCH[1]}
  FEATURE_NAME=${BASH_REMATCH[2]}
else
  if [[ "$OUTPUT_JSON" = true ]]; then
    echo "{ \"error\": \"Could not parse feature branch name: $BRANCH_NAME\" }"
  else
    echo "Error: Could not parse feature branch name: $BRANCH_NAME" >&2
  fi
  exit 1
fi

# Set paths
FEATURE_DIR="specs/${BRANCH_NAME}"
FEATURE_SPEC="${FEATURE_DIR}/spec.md"
IMPL_PLAN="${FEATURE_DIR}/plan.md"
TASKS_FILE="${FEATURE_DIR}/tasks.md"

# Check if spec file exists
if [[ ! -f "$FEATURE_SPEC" ]]; then
  if [[ "$OUTPUT_JSON" = true ]]; then
    echo "{ \"error\": \"Spec file not found: $FEATURE_SPEC\" }"
  else
    echo "Error: Spec file not found: $FEATURE_SPEC" >&2
  fi
  exit 1
fi

# Output based on flags
if [[ "$OUTPUT_JSON" = true ]]; then
  if [[ "$PATHS_ONLY" = true ]]; then
    echo "{ \"FEATURE_DIR\": \"$FEATURE_DIR\", \"FEATURE_SPEC\": \"$FEATURE_SPEC\" }"
  else
    echo "{ \"FEATURE_DIR\": \"$FEATURE_DIR\", \"FEATURE_SPEC\": \"$FEATURE_SPEC\", \"IMPL_PLAN\": \"$IMPL_PLAN\", \"TASKS\": \"$TASKS_FILE\" }"
  fi
else
  echo "FEATURE_DIR: $FEATURE_DIR"
  echo "FEATURE_SPEC: $FEATURE_SPEC"
  if [[ "$PATHS_ONLY" = false ]]; then
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "TASKS: $TASKS_FILE"
  fi
fi
