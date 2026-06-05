#!/usr/bin/env bash

# Script to set up planning phase and return paths

set -euo pipefail

OUTPUT_JSON=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      OUTPUT_JSON=true
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
SPECS_DIR="specs"

# Check if spec file exists
if [[ ! -f "$FEATURE_SPEC" ]]; then
  if [[ "$OUTPUT_JSON" = true ]]; then
    echo "{ \"error\": \"Spec file not found: $FEATURE_SPEC\" }"
  else
    echo "Error: Spec file not found: $FEATURE_SPEC" >&2
  fi
  exit 1
fi

# Create directories if they don't exist
mkdir -p "$(dirname "$IMPL_PLAN")"

# Output based on flags
if [[ "$OUTPUT_JSON" = true ]]; then
  echo "{ \"FEATURE_SPEC\": \"$FEATURE_SPEC\", \"IMPL_PLAN\": \"$IMPL_PLAN\", \"SPECS_DIR\": \"$SPECS_DIR\", \"BRANCH\": \"$BRANCH_NAME\" }"
else
  echo "FEATURE_SPEC: $FEATURE_SPEC"
  echo "IMPL_PLAN: $IMPL_PLAN"
  echo "SPECS_DIR: $SPECS_DIR"
  echo "BRANCH: $BRANCH_NAME"
fi
