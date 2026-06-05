#!/usr/bin/env bash

# Script to update agent context with new technology from plan

set -euo pipefail

AGENT_TYPE="${1:-codex}"

if [[ -z "$AGENT_TYPE" ]]; then
  echo "Error: Agent type required as first argument" >&2
  exit 1
fi

case "${AGENT_TYPE,,}" in
  codex)
    CONTEXT_FILE="AGENTS.md"
    ;;
  opencode)
    CONTEXT_FILE=".opencode/agentcontext.md"
    ;;
  *)
    CONTEXT_FILE="${AGENT_TYPE}/agentcontext.md"
    ;;
esac

# Create directory if it doesn't exist
CONTEXT_DIR="$(dirname "$CONTEXT_FILE")"
if [[ "$CONTEXT_DIR" != "." ]]; then
  mkdir -p "$CONTEXT_DIR"
fi

# Initialize context file if it doesn't exist
if [[ ! -f "$CONTEXT_FILE" ]]; then
  if [[ "${AGENT_TYPE,,}" == "codex" ]]; then
    echo "# Development Guidelines" > "$CONTEXT_FILE"
    echo "" >> "$CONTEXT_FILE"
  else
    echo "# Agent Context" > "$CONTEXT_FILE"
    echo "" >> "$CONTEXT_FILE"
    echo "## Technologies in Use" >> "$CONTEXT_FILE"
    echo "" >> "$CONTEXT_FILE"
  fi
fi

# Add markers if they don't exist
if ! grep -q "## Technologies Added by Plans" "$CONTEXT_FILE"; then
  echo "" >> "$CONTEXT_FILE"
  echo "## Technologies Added by Plans" >> "$CONTEXT_FILE"
  echo "" >> "$CONTEXT_FILE"
  echo "<!-- PLAN_TECHNOLOGIES_START -->" >> "$CONTEXT_FILE"
  echo "<!-- PLAN_TECHNOLOGIES_END -->" >> "$CONTEXT_FILE"
fi

# For this plan, we're adding:
# - Mermaid diagrams for architecture documentation
# - sphinxcontrib-mermaid extension for Sphinx builds
# - Markdown-based architecture documents

# Check if these are already added
if ! grep -q "Mermaid" "$CONTEXT_FILE"; then
  # Add to the technologies section between markers
  sed -i '/<!-- PLAN_TECHNOLOGIES_START -->/a\
- Mermaid diagrams for architectural visualization\
- sphinxcontrib-mermaid extension for Mermaid support in Sphinx builds\
- Markdown format for architecture documentation with embedded diagrams\
' "$CONTEXT_FILE"
fi

echo "Agent context updated for $AGENT_TYPE at $CONTEXT_FILE"
