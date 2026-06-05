param(
    [string]$AgentType = "codex"
)

switch ($AgentType.ToLowerInvariant()) {
    "codex" { $ContextFile = "AGENTS.md" }
    "opencode" { $ContextFile = ".opencode\agentcontext.md" }
    default { $ContextFile = "$AgentType\agentcontext.md" }
}

# Create directory if it doesn't exist
$ContextDir = Split-Path $ContextFile
if ($ContextDir) {
    $null = New-Item -ItemType Directory -Path $ContextDir -Force
}

# Initialize context file if it doesn't exist
if (-not (Test-Path $ContextFile)) {
    if ($AgentType.ToLowerInvariant() -eq "codex") {
        "# Development Guidelines" | Out-File $ContextFile -Encoding UTF8
        "" | Out-File $ContextFile -Append -Encoding UTF8
    } else {
        "# Agent Context" | Out-File $ContextFile -Encoding UTF8
        "" | Out-File $ContextFile -Append -Encoding UTF8
        "## Technologies in Use" | Out-File $ContextFile -Append -Encoding UTF8
        "" | Out-File $ContextFile -Append -Encoding UTF8
    }
}

# Add markers if they don't exist
if ((Select-String -Path $ContextFile -Pattern "## Technologies Added by Plans" -SimpleMatch -ErrorAction SilentlyContinue) -eq $null) {
    "" | Out-File $ContextFile -Append -Encoding UTF8
    "## Technologies Added by Plans" | Out-File $ContextFile -Append -Encoding UTF8
    "" | Out-File $ContextFile -Append -Encoding UTF8
    "<!-- PLAN_TECHNOLOGIES_START -->" | Out-File $ContextFile -Append -Encoding UTF8
    "<!-- PLAN_TECHNOLOGIES_END -->" | Out-File $ContextFile -Append -Encoding UTF8
}

# For this plan, we're adding:
# - Mermaid diagrams for architecture documentation
# - sphinxcontrib-mermaid extension for Sphinx builds
# - Markdown-based architecture documents

# Check if these are already added
if ((Select-String -Path $ContextFile -Pattern "Mermaid" -SimpleMatch) -eq $null) {
    # Add to the technologies section between markers
    (Get-Content $ContextFile) |
        ForEach-Object {
            $_
            if ($_ -eq "<!-- PLAN_TECHNOLOGIES_START -->") {
                "- Mermaid diagrams for architectural visualization"
                "- sphinxcontrib-mermaid extension for Mermaid support in Sphinx builds"
                "- Markdown format for architecture documentation with embedded diagrams"
            }
        } | Set-Content $ContextFile -Encoding UTF8
}

Write-Host "Agent context updated for $AgentType at $ContextFile"
