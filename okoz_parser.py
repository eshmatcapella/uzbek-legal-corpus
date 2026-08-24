#!/usr/bin/env python
"""
M3 — Parse the OKOZ classifier of Uzbek legislation into a node tree.

Source: okoz/okoz_classifier.md (supplied by the project owner; English
translation of the General Classifier of Branches of Legislation).

The classifier is a four-level taxonomy keyed by dotted codes:

    03.00.00.00   sphere        (level 1)  CIVIL LEGISLATION
    03.10.00.00   institution   (level 2)  Law of Obligations
    03.10.02.00   subinstitution(level 3)  Security for Performance
    03.10.02.02   detail        (level 4)  Pledge

The markdown wrapping is inconsistent (`##`, `###`, `**bold**`, plain lines,
and a few truncated codes like "01.14.03."), so the code itself — never the
markdown level — is the source of truth for depth and parentage.

Numbering gaps are legitimate: the official classifier retires codes without
renumbering (e.g. sphere 07 jumps from 07.09 to 07.12).  Cross-references
"(see also NN.NN.NN.NN)" are kept as edges; a few point at codes the supplied
tree does not contain, which is reported as a warning, not an error.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OKOZ_MD = ROOT / "okoz" / "okoz_classifier.md"

# A dotted code at the start of a (de-decorated) line.  The fourth segment is
# optional to accept truncated source lines like "01.14.03. Procedure ..."
RE_CODE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})(?:\.(\d{2}))?\.?\s+(.+)$")
RE_SEE_ALSO = re.compile(r"\s*\(see also ([^)]*\d{2}\.\d{2}\.\d{2}[^)]*)\)", re.IGNORECASE)
RE_SEE_ALSO_CODE = re.compile(r"\d{2}\.\d{2}\.\d{2}(?:\.\d{2})?")

# The document's own title line; everything else must carry a code.
SKIPPABLE = re.compile(r"^#\s*General Classifier", re.IGNORECASE)


@dataclass
class OkozNode:
    code: str                # normalised 'NN.NN.NN.NN'
    level: int               # 1 sphere | 2 institution | 3 subinstitution | 4 detail
    parent_code: str | None
    label_en: str
    see_also: list[str] = field(default_factory=list)
    ordinal: int = 0         # document order, for stable display


def _normalise(code: str) -> str:
    parts = code.split(".")
    while len(parts) < 4:
        parts.append("00")
    return ".".join(parts)


def _level(code: str) -> int:
    s = code.split(".")
    if s[1] == "00":
        return 1
    if s[2] == "00":
        return 2
    if s[3] == "00":
        return 3
    return 4


def _parent(code: str) -> str | None:
    lvl = _level(code)
    if lvl == 1:
        return None
    s = code.split(".")
    s[lvl - 1] = "00"
    return ".".join(s)


def parse_okoz(path: Path = OKOZ_MD) -> list[OkozNode]:
    nodes: list[OkozNode] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":  # YAML front matter from the notes app
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        lines = lines[end + 1:]

    for raw in lines:
        line = raw.strip()
        if not line or line == "---":
            continue
        # Strip markdown decoration: heading hashes and bold markers.
        line = line.lstrip("#").strip().strip("*").strip()
        if not line:
            continue
        if SKIPPABLE.match(raw.strip()):
            continue

        m = RE_CODE.match(line)
        if not m:
            raise ValueError(f"unrecognised OKOZ line: {raw!r}")

        segs = [m.group(i) or "00" for i in range(1, 5)]
        code = ".".join(segs)
        label = m.group(5).strip().strip("*").strip()

        see_also: list[str] = []
        if sa := RE_SEE_ALSO.search(label):
            see_also = [_normalise(c) for c in RE_SEE_ALSO_CODE.findall(sa.group(1))]
            label = RE_SEE_ALSO.sub("", label).strip()

        nodes.append(OkozNode(code, _level(code), _parent(code), label, see_also, len(nodes) + 1))
    return nodes


def validate(nodes: list[OkozNode]) -> tuple[list[str], list[str]]:
    """(errors, warnings): errors break the tree, warnings are source oddities."""
    errors: list[str] = []
    warnings: list[str] = []
    by_code: dict[str, OkozNode] = {}

    for n in nodes:
        if n.code in by_code:
            errors.append(f"duplicate code {n.code}: {by_code[n.code].label_en!r} / {n.label_en!r}")
        by_code[n.code] = n

    for n in nodes:
        if n.parent_code and n.parent_code not in by_code:
            errors.append(f"{n.code} ({n.label_en}): parent {n.parent_code} missing")
        if not n.label_en:
            errors.append(f"{n.code}: empty label")
        for ref in n.see_also:
            if ref not in by_code:
                warnings.append(f"{n.code}: see-also target {ref} not in the supplied tree")
    return errors, warnings


# --------------------------------------------------------------------------- tests
def _selftest() -> int:
    """Parse the real source and assert the invariants the build relies on."""
    nodes = parse_okoz()
    errors, warnings = validate(nodes)
    checks: list[tuple[bool, str]] = [
        (not errors, f"tree validates without errors ({len(errors)} errors)"),
        (len({n.code for n in nodes}) == len(nodes), "codes are unique"),
        (sum(1 for n in nodes if n.level == 1) == 19, "19 spheres (01..19)"),
        # Formatting variants that must all normalise correctly:
        (any(n.code == "01.14.03.00" for n in nodes), "truncated code '01.14.03.' normalised"),
        (any(n.code == "09.14.00.00" and n.level == 2 for n in nodes),
         "bold institution '**09.14.00.00 Agriculture**' parsed"),
        (any(n.code == "04.08.00.00" and n.level == 2 for n in nodes),
         "plain-line institution 04.08 parsed with level from code, not markdown"),
        (any(n.code == "03.10.02.02" and n.label_en == "Pledge" for n in nodes),
         "level-4 detail parsed (03.10.02.02 Pledge)"),
        # see-also handling
        (any("03.11.01.05" in n.see_also for n in nodes if n.code == "09.14.17.01"),
         "see-also cross-reference extracted"),
        (all("see also" not in n.label_en.lower() for n in nodes),
         "see-also stripped from labels"),
        # sphere 03 shape the mapping depends on
        (sum(1 for n in nodes if n.code.startswith("03.") and n.level == 2) == 17,
         "sphere 03 has 17 institutions"),
    ]
    failed = 0
    for ok, label in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        failed += not ok
    for w in warnings[:8]:
        print(f"  [WARN] {w}")
    if len(warnings) > 8:
        print(f"  [WARN] ... and {len(warnings) - 8} more")
    print(f"{len(checks) - failed}/{len(checks)} OKOZ parser self-tests passed; "
          f"{len(nodes)} nodes, {len(warnings)} source warnings")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(_selftest())
