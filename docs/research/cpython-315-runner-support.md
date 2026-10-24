# CPython 3.15 provisioning on retained GitHub Actions runners

**Checked:** 2026-10-13
**Scope:** Python installer availability and GitHub Actions runner compatibility. This report does not establish product runtime support or change CI.

## Finding

The upstream Python distribution data now contains stable CPython 3.15.0 builds for the OS and architectures in the product's retained runner matrix. The current workflow uses `ubuntu-latest`, `windows-latest`, and `macos-latest`, and invokes `actions/setup-python@v5` in its fast PR, test, and E2E jobs ([workflow on `rewrite-from-2.3.1`](https://github.com/elchupanebrej/pytest-bdd-ng/blob/rewrite-from-2.3.1/.github/workflows/main.yml)). The matrix does not yet contain a 3.15 cell, so this is a provisioning-feasibility result for the planned cells, not evidence from product CI.

The action-version detail needs separate treatment. `setup-python@v5` declares `runs.using: node20`; GitHub began forcing Node 24 by default on June 16, 2026, and removed the Node 20 runtime and opt-out on September 23. That migration means the `node20` declaration alone does **not** establish that v5 fails: current runners may execute the action under the forced Node 24 runtime. It does mean v5 is on the retired runtime path, and the sources reviewed here do not prove this project's v5 action succeeds under that forced runtime. The smallest supported change is to update the workflow's `setup-python` references to `@v6`, whose metadata explicitly declares Node 24. No runner-label change is required for that update or for CPython 3.15 provisioning. [GitHub's Node migration timeline](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/), [Node 20 removal notice](https://github.blog/changelog/2026-09-23-node-20-is-no-longer-available-in-github-actions/), [v5 metadata](https://github.com/actions/setup-python/blob/v5/action.yml#L351-L357), [v6 metadata and release requirements](https://github.com/actions/setup-python/blob/v6/action.yml#L366-L374), [v6.0.0 release notes](https://github.com/actions/setup-python/releases/tag/v6.0.0).

## Provisioning coverage by runner cell

GitHub's current hosted-image table maps the labels as follows on the report date. The `ubuntu-latest` migration to Ubuntu 26.04 is scheduled to begin in November 2026; both Ubuntu 24.04 and 26.04 x64 artifacts are already listed for CPython 3.15.0. The Python 3.15.0 release was added to `actions/python-versions` on October 10, 2026. [Runner image labels](https://github.com/actions/runner-images#available-images), [3.15.0 release](https://github.com/actions/python-versions/releases/tag/3.15.0-38076878863), [current version manifest](https://github.com/actions/python-versions/blob/main/versions-manifest.json).

| Workflow label | Current hosted image and architecture | Matching stable 3.15.0 artifact | Provisioning result |
| --- | --- | --- | --- |
| `ubuntu-latest` | Ubuntu 24.04, x64; migration to Ubuntu 26.04 is upcoming | `linux` / `24.04` / `x64`; the manifest also has `linux` / `26.04` / `x64` | Available for the current image and the announced image migration |
| `windows-latest` | Windows Server 2025, x64 | `win32` / `x64` | Available |
| `macos-latest` | macOS 26, arm64 | `darwin` / `arm64` | Available |

The manifest is consumed dynamically: both the v5 and v6 installer sources point to the `actions/python-versions` `main` manifest, and the setup action downloads the selected release when it is not in the runner's tool cache. The current Ubuntu 24.04 software list caches Python only through 3.14.8, so that cell is expected to exercise the download path today. This is not a missing-build limitation: the manifest has a 3.15.0 Ubuntu 24.04 x64 archive. [v5 installer source](https://github.com/actions/setup-python/blob/v5/src/install-python.ts#L535-L540), [v6 installer source](https://github.com/actions/setup-python/blob/v6/src/install-python.ts#L708-L713), [Ubuntu 24.04 cached Python list](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md#cached-tools).

The Node 24 transition excludes macOS 13.4 and earlier and does not support ARM32. Those restrictions do not apply to the current `macos-latest` macOS 26 arm64 cell or to the x64 Ubuntu and Windows cells. The v6 release notes require runner version 2.327.1 or later; the GitHub-hosted runners manage their runner version, and the required CI run below must confirm the action on the actual hosted image. [Node migration details](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/), [v6.0.0 release notes](https://github.com/actions/setup-python/releases/tag/v6.0.0).

## Recommendation and required CI evidence

1. In the implementation change, update each `actions/setup-python@v5` reference in `main.yml` to `actions/setup-python@v6`. This aligns the action metadata with the Node 24 runtime. Keep the existing runner labels; the Python distribution manifest covers the current architectures and the Ubuntu migration target.
2. Run the planned stable `3.15.0` cell independently on `ubuntu-latest`, `windows-latest`, and `macos-latest`. Record the actual OS and `platform.machine()` so the evidence captures x64 on Ubuntu/Windows and arm64 on macOS.
3. Before the package/test command, assert `sys.version_info[:3] == (3, 15, 0)` and preserve each setup step's outcome and version output. This proves action provisioning on each current runner cell; an upstream manifest entry alone does not.
4. Keep the provisioning result distinct from the product support result. Product support still requires the agreed core behavior and executable-example checks to pass in those cells; this report does not claim those results.

If the implementation wants to retain `@v5`, a CI preflight on all three labels must first show that v5 runs successfully under the forced Node 24 runtime and sets up exactly 3.15.0. Updating to `@v6` removes that runtime uncertainty and is the recommended path.

## Sources

- [Product workflow at `rewrite-from-2.3.1`](https://github.com/elchupanebrej/pytest-bdd-ng/blob/rewrite-from-2.3.1/.github/workflows/main.yml)
- [GitHub Actions Node 20 deprecation and forced-Node-24 timeline](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/)
- [GitHub Actions Node 20 removal notice](https://github.blog/changelog/2026-09-23-node-20-is-no-longer-available-in-github-actions/)
- [`actions/setup-python@v5` metadata](https://github.com/actions/setup-python/blob/v5/action.yml)
- [`actions/setup-python@v6` metadata](https://github.com/actions/setup-python/blob/v6/action.yml)
- [`actions/setup-python@v6` release notes](https://github.com/actions/setup-python/releases/tag/v6.0.0)
- [`actions/setup-python@v5` installer source](https://github.com/actions/setup-python/blob/v5/src/install-python.ts)
- [`actions/setup-python@v6` installer source](https://github.com/actions/setup-python/blob/v6/src/install-python.ts)
- [`actions/python-versions` CPython 3.15.0 release](https://github.com/actions/python-versions/releases/tag/3.15.0-38076878863)
- [`actions/python-versions` current release manifest](https://github.com/actions/python-versions/blob/main/versions-manifest.json)
- [`actions/runner-images` available image labels](https://github.com/actions/runner-images#available-images)
- [`actions/runner-images` Ubuntu 24.04 software list](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md)
