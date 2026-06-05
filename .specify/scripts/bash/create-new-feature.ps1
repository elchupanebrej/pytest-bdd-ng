param(
    [string]$FeatureDescription = "",
    [string]$ShortName = "",
    [int]$Number = 0,
    [switch]$Json
)

if (-not $ShortName) {
    Write-Error "Error: --short-name is required"
    exit 1
}

if ($Number -eq 0) {
    # Find the highest existing number for this short name
    $highest = 0

    # Check local branches
    git branch --list | ForEach-Object {
        if ($_ -match '^\s*[0-9]+-' + [regex]::Escape($ShortName) + '$') {
            $num = [int]($Matches[0].Trim().Split('-')[0])
            if ($num -gt $highest) { $highest = $num }
        }
    }

    # Check remote branches (if accessible)
    try {
        git ls-remote --heads origin | ForEach-Object {
            if ($_ -match 'refs/heads/([0-9]+)-' + [regex]::Escape($ShortName) + '$') {
                $num = [int]$Matches[1]
                if ($num -gt $highest) { $highest = $num }
            }
        }
    } catch {
        # Ignore remote errors
    }

    # Check specs directories
    if (Test-Path "specs") {
        Get-ChildItem -Path "specs" -Directory | Where-Object {
            $_ -match '^([0-9]+)-' + [regex]::Escape($ShortName) + '$'
        } | ForEach-Object {
            $num = [int]$Matches[1]
            if ($num -gt $highest) { $highest = $num }
        }
    }

    $Number = $highest + 1
}

# Format number with leading zeros to match existing pattern
$BranchNum = "{0:D2}" -f $Number
$BranchName = "$BranchNum-$ShortName"
$SpecDir = "specs\$BranchName"
$SpecFile = Join-Path $SpecDir "spec.md"

# Create branch
git checkout -b $BranchName

# Create spec directory
New-Item -ItemType Directory -Path $SpecDir -Force | Out-Null

# Create basic spec structure
@"
<!-- markdownlint-disable MD013 -->

# Feature Specification: [TO BE FILLED]

**Feature Branch**: `$BranchName`
**Created**: $(Get-Date -Format yyyy-MM-dd)
**Status**: Draft
**Input**: User description: "$FeatureDescription"

## Clarifications

## User Scenarios & Testing *(mandatory)*

## Requirements *(mandatory)*

### Functional Requirements

### Key Entities *(include if feature involves data)*

### Assumptions

## Success Criteria *(mandatory)*

### Measurable Outcomes

"@ | Set-Content -Path $SpecFile -Encoding UTF8

# Output JSON if requested
if ($Json) {
    "{ `"BRANCH_NAME`": `"$BranchName`", `"SPEC_FILE`": `"$SpecFile`" }"
}
