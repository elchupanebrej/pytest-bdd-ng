"""Fix files that have incomplete architecture score sections (missing criteria)."""

import re
from pathlib import Path

FULL_SCORE_BLOCK = """\
    #arch-eval:reason_for_existence={rfe}
    #arch-eval:owned_responsibility={or_}
    #arch-eval:delegation_boundary={db}
    #arch-eval:cohesion={coh}
    #arch-eval:separation={sep}
    #arch-eval:consumer_clarity={cc}
    #arch-eval:state_invariants={si}
    #arch-eval:entity_fullness={ef}
    #arch-eval:locational_stability={ls}"""


def fix_file(path: Path, defaults: dict[str, int]) -> int:
    source = path.read_text(encoding="utf-8")
    # Find architecture score blocks with fewer than 9 tags
    pattern = re.compile(
        r"(Architecture score:\n)((?:\s+#arch-eval:\w+=\S+\n)+)",
        re.MULTILINE,
    )
    replacements = 0

    def replacer(m: re.Match) -> str:
        nonlocal replacements
        header = m.group(1)
        existing_block = m.group(2)
        # Parse existing tags
        existing = {}
        for line in existing_block.splitlines():
            tm = re.match(r"\s+#arch-eval:(\w+)=(\S+)", line)
            if tm:
                existing[tm.group(1)] = tm.group(2)
        # Build full block, using existing values where present
        scores = {}
        for k, v in defaults.items():
            scores[k] = existing.get(k, str(v))
        new_block = "\n".join(f"    #arch-eval:{k}={v}" for k, v in scores.items()) + "\n"
        if new_block.rstrip() != existing_block.rstrip():
            replacements += 1
        return header + new_block

    new_source = pattern.sub(replacer, source)
    if replacements:
        path.write_text(new_source, encoding="utf-8")
    return replacements


def main() -> int:
    fixes = {
        Path("src/pytest_bdd/script/_feature_tree.py"): {
            "reason_for_existence": 4,
            "owned_responsibility": 3,
            "delegation_boundary": 3,
            "cohesion": 4,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4,
            "entity_fullness": 2,
            "locational_stability": 4,
        },
        Path("src/pytest_bdd/script/validate_feature_headings.py"): {
            "reason_for_existence": 3,
            "owned_responsibility": 3,
            "delegation_boundary": 3,
            "cohesion": 4,
            "separation": 3,
            "consumer_clarity": 3,
            "state_invariants": 4,
            "entity_fullness": 2,
            "locational_stability": 4,
        },
    }
    total = 0
    for path, defaults in fixes.items():
        n = fix_file(path, defaults)
        print(f"  {path}: {n} blocks fixed")
        total += n
    print(f"Total: {total} blocks fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
