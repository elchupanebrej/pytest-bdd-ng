#!/usr/bin/env bash

# Script to create a new feature branch and specification

set -euo pipefail

FEATURE_DESCRIPTION="$1"
SHORT_NAME=""
NUMBER=0
OUTPUT_JSON=false

get_highest_from_specs() {
  local specs_dir="$1"
  local highest=0

  if [[ -d "$specs_dir" ]]; then
    local dir
    for dir in "$specs_dir"/*; do
      [[ -d "$dir" ]] || continue
      local dirname
      dirname=$(basename "$dir")
      if [[ "$dirname" =~ ^([0-9]{3,})- ]] && [[ ! "$dirname" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
        local number=${BASH_REMATCH[1]}
        number=$((10#$number))
        [[ $number -gt $highest ]] && highest=$number
      fi
    done
  fi

  echo "$highest"
}

_extract_highest_number() {
  local highest=0
  local name
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    if [[ "$name" =~ ^([0-9]{3,})- ]] && [[ ! "$name" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
      local number=${BASH_REMATCH[1]}
      number=$((10#$number))
      [[ $number -gt $highest ]] && highest=$number
    fi
  done
  echo "$highest"
}

get_highest_from_branches() {
  git branch -a 2>/dev/null | sed 's/^[* ]*//; s|^remotes/[^/]*/||' | _extract_highest_number
}

get_highest_from_remote_refs() {
  local highest=0
  local remote

  while IFS= read -r remote; do
    [[ -n "$remote" ]] || continue
    local remote_highest
    remote_highest=$(GIT_TERMINAL_PROMPT=0 git ls-remote --heads "$remote" 2>/dev/null | sed 's|.*refs/heads/||' | _extract_highest_number)
    [[ $remote_highest -gt $highest ]] && highest=$remote_highest
  done < <(git remote 2>/dev/null || true)

  echo "$highest"
}

check_existing_branches() {
  local specs_dir="$1"
  local highest_branch=0

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git fetch --all --prune >/dev/null 2>&1 || true
    highest_branch=$(get_highest_from_branches)
    local highest_remote
    highest_remote=$(get_highest_from_remote_refs)
    [[ $highest_remote -gt $highest_branch ]] && highest_branch=$highest_remote
  fi

  local highest_spec
  highest_spec=$(get_highest_from_specs "$specs_dir")
  if [[ $highest_spec -gt $highest_branch ]]; then
    highest_branch=$highest_spec
  fi

  echo $((highest_branch + 1))
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --short-name)
      SHORT_NAME="$2"
      shift 2
      ;;
    --number)
      NUMBER="$2"
      shift 2
      ;;
    --json)
      OUTPUT_JSON=true
      shift
      ;;
    *)
      # Assume it's part of the feature description if not already captured
      if [[ -z "$FEATURE_DESCRIPTION" ]]; then
        FEATURE_DESCRIPTION="$1"
      else
        FEATURE_DESCRIPTION="$FEATURE_DESCRIPTION $1"
      fi
      shift
      ;;
  esac
done

# Trim feature description
FEATURE_DESCRIPTION=$(echo "$FEATURE_DESCRIPTION" | xargs)

if [[ -z "$SHORT_NAME" ]]; then
  echo "Error: --short-name is required" >&2
  exit 1
fi

if [[ $NUMBER -eq 0 ]]; then
  NUMBER=$(check_existing_branches "specs")
fi

# Format number with leading zeros to match existing pattern
FEATURE_NUM=$(printf "%03d" "$NUMBER")
BRANCH_NAME="${FEATURE_NUM}-${SHORT_NAME}"
SPEC_DIR="specs/${BRANCH_NAME}"
SPEC_FILE="${SPEC_DIR}/spec.md"

# Create branch
git checkout -b "$BRANCH_NAME"

# Create spec directory
mkdir -p "$SPEC_DIR"

# Create basic spec structure
cat > "$SPEC_FILE" << EOF
<!-- markdownlint-disable MD013 -->

# Feature Specification: [TO BE FILLED]

**Feature Branch**: \`$BRANCH_NAME\`
**Created**: $(date +%Y-%m-%d)
**Status**: Draft
**Input**: User description: "$FEATURE_DESCRIPTION"

## Clarifications

## User Scenarios & Testing *(mandatory)*

## Requirements *(mandatory)*

### Functional Requirements

### Key Entities *(include if feature involves data)*

### Assumptions

## Success Criteria *(mandatory)*

### Measurable Outcomes

EOF

# Output JSON if requested
if [[ "$OUTPUT_JSON" = true ]]; then
  echo "{ \"BRANCH_NAME\": \"$BRANCH_NAME\", \"FEATURE_NUM\": \"$FEATURE_NUM\", \"SPEC_FILE\": \"$SPEC_FILE\" }"
fi
