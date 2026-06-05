param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks
)

# Get current branch name
try {
    $BranchName = git rev-parse --abbrev-ref HEAD
} catch {
    if ($Json) {
        "{ `"error`": `"Git command failed. Make sure you're in a git repository.`" }"
    } else {
        Write-Error "Git command failed. Make sure you're in a git repository."
    }
    exit 1
}

# Check if we're on a feature branch (pattern: NN-feature-name)
if (-not ($BranchName -match '^[0-9]+-[a-zA-Z0-9_-]+$')) {
    if ($Json) {
        "{ `"error`": `"Not on a feature branch. Current branch: $BranchName`" }"
    } else {
        Write-Error "Not on a feature branch. Current branch: $BranchName"
    }
    exit 1
}

# Extract the feature number and name
if ($BranchName -match '^([0-9]+)-(.+)$') {
    $FeatureNum = $Matches[1]
    $FeatureName = $Matches[2]
} else {
    if ($Json) {
        "{ `"error`": `"Could not parse feature branch name: $BranchName`" }"
    } else {
        Write-Error "Could not parse feature branch name: $BranchName"
    }
    exit 1
}

# Set paths
$FeatureDir = "specs\$BranchName"
$FeatureSpec = Join-Path $FeatureDir "spec.md"
$ImplPlan = Join-Path $FeatureDir "plan.md"
$TasksFile = Join-Path $FeatureDir "tasks.md"
$SpecsDir = "specs"

# Check if spec file exists
if (-not (Test-Path $FeatureSpec)) {
    if ($Json) {
        "{ `"error`": `"Spec file not found: $FeatureSpec`" }"
    } else {
        Write-Error "Spec file not found: $FeatureSpec"
    }
    exit 1
}

# If tasks are required, check if tasks.md exists
if ($RequireTasks) {
    if (-not (Test-Path $TasksFile)) {
        if ($Json) {
            "{ `"error`": `"Tasks file not found: $TasksFile`" }"
        } else {
            Write-Error "Tasks file not found: $TasksFile"
        }
        exit 1
    }
}

# Collect available documentation files if requested
$AvailableDocs = @()
if ($IncludeTasks) {
    # Get all markdown files in the feature directory
    if (Test-Path $FeatureDir) {
        $AvailableDocs = Get-ChildItem -Path $FeatureDir -Filter *.md | Select-Object -ExpandProperty Name
    }
}

# Output based on flags
if ($Json) {
    $result = @{
        "FEATURE_DIR" = $FeatureDir
        "FEATURE_SPEC" = $FeatureSpec
        "IMPL_PLAN" = $ImplPlan
        "TASKS" = if ($RequireTasks) { $TasksFile } else { "" }
        "SPECS_DIR" = $SpecsDir
        "BRANCH" = $BranchName
        "AVAILABLE_DOCS" = $AvailableDocs
    }

    if ($RequireTasks -and (Test-Path $TasksFile)) {
        result["TASKS_CONTENT"] = Get-Content $TasksFile -Raw
    }

    ConvertTo-Json $result
} else {
    Write-Output "FEATURE_DIR: $FeatureDir"
    Write-Output "FEATURE_SPEC: $FeatureSpec"
    Write-Output "IMPL_PLAN: $ImplPlan"
    if ($RequireTasks) { Write-Output "TASKS: $TasksFile" }
    Write-Output "SPECS_DIR: $SpecsDir"
    Write-Output "BRANCH: $BranchName"
    if ($IncludeTasks) { Write-Output "AVAILABLE_DOCS: $($AvailableDocs -join ', ')" }
}
