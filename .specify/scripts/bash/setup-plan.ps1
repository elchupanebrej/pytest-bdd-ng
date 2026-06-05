param(
    [switch]$Json
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

# Create directories if they don't exist
$null = New-Item -ItemType Directory -Path (Split-Path $ImplPlan) -Force

# Output based on flags
if ($Json) {
    "{ `"FEATURE_SPEC`": `"$FeatureSpec`", `"IMPL_PLAN`": `"$ImplPlan`", `"SPECS_DIR`": `"$SpecsDir`", `"BRANCH`": `"$BranchName`" }"
} else {
    Write-Output "FEATURE_SPEC: $FeatureSpec"
    Write-Output "IMPL_PLAN: $ImplPlan"
    Write-Output "SPECS_DIR: $SpecsDir"
    Write-Output "BRANCH: $BranchName"
}
