#!/usr/bin/env bash

# Common Bash helpers for Spec Kit scripts.

find_specify_root() {
    local start_dir="${1:-$(pwd)}"
    local current
    current="$(cd "$start_dir" 2>/dev/null && pwd -P)" || return 1

    while [ -n "$current" ] && [ "$current" != "/" ]; do
        if [ -d "$current/.specify" ]; then
            printf '%s\n' "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done

    if [ "$current" = "/" ] && [ -d "/.specify" ]; then
        printf '/\n'
        return 0
    fi
    return 1
}

get_repo_root() {
    local specify_root
    specify_root="$(find_specify_root 2>/dev/null)" && {
        printf '%s\n' "$specify_root"
        return 0
    }

    if command -v git >/dev/null 2>&1; then
        git rev-parse --show-toplevel 2>/dev/null && return 0
    fi

    pwd -P
}

has_git() {
    local repo_root="${1:-$(get_repo_root)}"
    command -v git >/dev/null 2>&1 &&
        { [ -d "$repo_root/.git" ] || [ -f "$repo_root/.git" ]; } &&
        git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="${2:-true}"

    if [ "$has_git_repo" != "true" ]; then
        printf '[specify] Warning: Git repository not detected; skipped branch validation\n' >&2
        return 0
    fi

    if [[ "$branch" =~ ^[0-9]{7}-[0-9]{6} ]] || [[ "$branch" =~ ^[0-9]{8}-[0-9]{6}$ ]]; then
        printf 'ERROR: Not on a feature branch. Current branch: %s\n' "$branch" >&2
        printf 'Feature branches should be named like: 001-feature-name or 20260319-143022-feature-name\n' >&2
        return 1
    fi

    if [[ "$branch" =~ ^[0-9]{3,}- ]] || [[ "$branch" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
        return 0
    fi

    printf 'ERROR: Not on a feature branch. Current branch: %s\n' "$branch" >&2
    printf 'Feature branches should be named like: 001-feature-name or 20260319-143022-feature-name\n' >&2
    return 1
}

find_feature_dir_by_prefix() {
    local prefix="$1"
    local repo_root="${2:-$(get_repo_root)}"
    local specs_dir="$repo_root/specs"

    [ -d "$specs_dir" ] || return 1

    local matches=()
    local path
    while IFS= read -r path; do
        [ -n "$path" ] && matches+=("$path")
    done < <(find "$specs_dir" -maxdepth 1 -mindepth 1 -type d \( -name "${prefix}-*" -o -name "${prefix}" \) | sort)

    case "${#matches[@]}" in
        0) return 1 ;;
        1) printf '%s\n' "${matches[0]}" ;;
        *) printf '%s\n' "${matches[-1]}" ;;
    esac
}

json_escape() {
    local value="${1:-}"
    python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$value"
}
