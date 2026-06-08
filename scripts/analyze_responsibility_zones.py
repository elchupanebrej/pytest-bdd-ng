"""Aggregate weak responsibility-contract zones from architecture object data."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

OBJECT_MAP_JSON = Path(".planning/tmp/object-map.json")
GAPS_JSON = Path(".planning/tmp/responsibility-gaps.json")
GAPS_MD = Path("docs/architecture/RESPONSIBILITY_GAPS.md")


def load_entries() -> list[dict[str, Any]]:
    if not OBJECT_MAP_JSON.exists():
        from collect_arch_scores import collect_entries, write_json

        entries = collect_entries(Path("src/pytest_bdd"))
        write_json(entries)
    return json.loads(OBJECT_MAP_JSON.read_text(encoding="utf-8"))


def package_key(module: str) -> str:
    parts = module.split(".")
    return module if len(parts) <= 2 else ".".join(parts[:3])


def parent_qualname(entry: dict[str, Any]) -> str:
    qualname = entry["qualname"]
    return qualname.rsplit(".", 1)[0] if "." in qualname else qualname


def recommendations(entry: dict[str, Any], signals: list[str]) -> list[str]:
    recs: list[str] = []
    if "too many responsibilities" in signals:
        recs.append("split entity by delegated responsibility and add tests before refactor")
    if "duplicate or vague peer boundary" in signals:
        recs.append("merge duplicate same-kind entities or rename for responsibility clarity")
    if "no main consumers" in signals:
        recs.append("verify whether entity is dead code, dynamic API, or missing test coverage")
    if "weak state/side effects" in signals:
        recs.append("extract state owner or document stash/cache/file mutation invariant")
    if entry["kind"] == "module" and "many weak children" in signals:
        recs.append("introduce facade or move low-score children to better-focused modules")
    if entry["kind"] == "class" and "broad class surface" in signals:
        recs.append("extract collaborator class or keep as-is with explicit cohesion rationale")
    if "missing cohesion/separation rationale" in signals:
        recs.append("complete Cohesion and Separation sections before structural refactor")
    if not recs:
        recs.append("keep as-is with rationale and monitor score trend")
    return recs


def entity_signals(entry: dict[str, Any], child_counts: Counter[str], low_child_counts: Counter[str]) -> list[str]:
    signals: list[str] = []
    missing = set(entry.get("missing_sections", []))
    scores = entry.get("scores", {})
    if entry.get("average", 0) < 3:
        signals.append("low average score")
    if "Cohesion" in missing or "Separation" in missing:
        signals.append("missing cohesion/separation rationale")
    if not entry.get("consumers") or entry.get("consumers") == "None found":
        signals.append("no main consumers")
    if scores.get("state_invariants", 0) < 3 or "State and side effects" in missing:
        signals.append("weak state/side effects")
    if scores.get("owned_responsibility", 0) < 3 and scores.get("delegation_boundary", 0) < 3:
        signals.append("too many responsibilities")
    if scores.get("separation", 0) < 3:
        signals.append("duplicate or vague peer boundary")
    if entry["kind"] == "module" and low_child_counts[entry["qualname"]] >= 4:
        signals.append("many weak children")
    if entry["kind"] == "class" and child_counts[entry["qualname"]] >= 10 and scores.get("owned_responsibility", 0) < 4:
        signals.append("broad class surface")
    if entry["kind"] in {"function", "method", "async function", "async method"}:
        if scores.get("delegation_boundary", 0) < 3 and scores.get("owned_responsibility", 0) >= 4:
            signals.append("broad orchestration without delegates")
    return signals


def build_zones(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    child_counts: Counter[str] = Counter()
    low_child_counts: Counter[str] = Counter()
    for entry in entries:
        parent = parent_qualname(entry)
        if parent != entry["qualname"]:
            child_counts[parent] += 1
            if entry.get("average", 0) < 3:
                low_child_counts[parent] += 1
    zones = []
    for entry in entries:
        signals = entity_signals(entry, child_counts, low_child_counts)
        if not signals:
            continue
        zones.append(
            {
                "entity": entry["qualname"],
                "kind": entry["kind"],
                "file": entry["file"],
                "line": entry["line"],
                "package": package_key(entry["module"]),
                "average": entry.get("average", 0),
                "signals": signals,
                "recommendations": recommendations(entry, signals),
            },
        )
    return sorted(zones, key=lambda item: (-len(item["signals"]), item["average"], item["entity"]))


def package_summary(entries: list[dict[str, Any]], zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_package: dict[str, list[dict[str, Any]]] = defaultdict(list)
    zone_counts = Counter(zone["package"] for zone in zones)
    for entry in entries:
        by_package[package_key(entry["module"])].append(entry)
    return sorted(
        [
            {
                "package": package,
                "entities": len(package_entries),
                "average": round(
                    sum(float(entry.get("average", 0)) for entry in package_entries) / len(package_entries),
                    2,
                ),
                "problem_zones": zone_counts[package],
            }
            for package, package_entries in by_package.items()
        ],
        key=lambda item: (-item["problem_zones"], item["average"], item["package"]),
    )


def write_outputs(entries: list[dict[str, Any]], zones: list[dict[str, Any]]) -> None:
    summary = package_summary(entries, zones)
    payload = {"summary": summary, "zones": zones}
    GAPS_JSON.parent.mkdir(parents=True, exist_ok=True)
    GAPS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# pytest-bdd Responsibility Gaps",
        "",
        "Generated by `scripts/analyze_responsibility_zones.py` from responsibility docstring contracts.",
        "",
        "## Package Risk Summary",
        "",
        "| Package | Entities | Average | Problem Zones |",
        "|---|---:|---:|---:|",
    ]
    for item in summary:
        lines.append(f"| `{item['package']}` | {item['entities']} | {item['average']:.2f} | {item['problem_zones']} |")
    lines.extend(["", "## Highest Priority Zones", ""])
    for zone in zones[:50]:
        lines.extend(
            [
                f"### `{zone['entity']}`",
                "",
                f"- Kind: {zone['kind']}",
                f"- Location: `{zone['file']}:{zone['line']}`",
                f"- Average score: {zone['average']:.2f}",
                f"- Signals: {', '.join(zone['signals'])}",
                "- Recommendations:",
            ],
        )
        for rec in zone["recommendations"]:
            lines.append(f"  - {rec}")
        lines.append("")
    GAPS_MD.parent.mkdir(parents=True, exist_ok=True)
    GAPS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    entries = load_entries()
    zones = build_zones(entries)
    write_outputs(entries, zones)
    print(f"Analyzed {len(entries)} entities.")
    print(f"Problem zones: {len(zones)}.")
    print(f"Output: {GAPS_MD}")
    print(f"JSON: {GAPS_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
