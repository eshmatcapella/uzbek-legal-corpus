#!/usr/bin/env python
"""
M1 — Parse the Civil Code's internal structure into a node tree.

Source: structure/civil_code_structure.md (supplied by the project owner).
This replaces the corpus's own structural metadata, which is unusable for the
Civil Code: `chapter` is empty for every row and `part` is a mangled
concatenation ("I BO'LIMUMUMIY QOIDALAR").

The tree covers the whole Code (Parts I-VI, Articles 1-1199).  Article ranges
are stated on the deepest node that carries them - a chapter with no sections
carries its own range, a chapter split into sections carries none and its
sections do.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STRUCTURE_MD = ROOT / "structure" / "civil_code_structure.md"

# Articles 1-385 are the General Part (lex.uz doc -111189); the rest are the
# Special Part (-180552).  The structure file marks the boundary with "Part Two".
GENERAL_PART_LAST_ARTICLE = 385
DOC_GENERAL = -111189
DOC_SPECIAL = -180552

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}

RE_PART = re.compile(r"^\*\*Part\s+(I{1,3}|IV|V|VI)\.\s*(.+?)\*\*\s*$")
RE_DOC_BREAK = re.compile(r"^\*\*Part\s+Two\*\*\s*$")
RE_SUBSECTION = re.compile(r"^\*\*Subsection\s+(\d+)\.\s*(.+?)\*\*\s*$")
RE_CHAPTER = re.compile(r"^\*\*Chapter\s+(\d+)\.\*\*\s*(.*?)\s*$")
RE_SECTION = re.compile(r"^§\s*(\d+)\.\s*(.+?)\s*$")
# "(Articles 39-57)", "(Article 259)", "(Articles 1102-1107-1)" - the last form
# is a superscript article (1107 with superscript 1) written with a hyphen.
RE_RANGE = re.compile(
    r"\((?:Articles?)\s+(\d+)(?:-(\d+))?\s*(?:[–—-]\s*(\d+)(?:-(\d+))?)?\)\s*$"
)


@dataclass
class Node:
    node_id: str
    kind: str            # part | subsection | chapter | section
    number: str
    label_en: str
    parent_id: str | None
    ordinal: int
    depth: int
    art_from: int | None = None
    art_to: int | None = None
    doc_id: int | None = None
    children: list[str] = field(default_factory=list)


def _strip_range(text: str) -> tuple[str, int | None, int | None]:
    """Split a label into its text and its article range."""
    m = RE_RANGE.search(text)
    if not m:
        return text.strip(), None, None
    lo = int(m.group(1))
    hi = int(m.group(3)) if m.group(3) else lo
    return text[: m.start()].strip(), lo, hi


def parse_structure(path: Path = STRUCTURE_MD) -> list[Node]:
    nodes: list[Node] = []
    by_id: dict[str, Node] = {}
    cur_part = cur_subsection = cur_chapter = None
    counters = {"part": 0, "subsection": 0, "chapter": 0, "section": 0}

    def add(node: Node) -> Node:
        nodes.append(node)
        by_id[node.node_id] = node
        if node.parent_id:
            by_id[node.parent_id].children.append(node.node_id)
        return node

    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":  # YAML front matter from the notes app
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        lines = lines[end + 1:]

    for raw in lines:
        line = raw.strip()
        if not line or line == "---":
            continue

        if RE_DOC_BREAK.match(line):
            # Document boundary between the Code's two published acts, not a
            # structural node: Part III continues across it.
            continue

        if m := RE_PART.match(line):
            counters["part"] += 1
            cur_part = add(Node(f"P{m.group(1)}", "part", m.group(1), m.group(2).strip(),
                                None, counters["part"], 0))
            cur_subsection = cur_chapter = None
            continue

        if m := RE_SUBSECTION.match(line):
            counters["subsection"] += 1
            # Subsection numbering restarts per part, so scope the id by part.
            cur_subsection = add(Node(f"{cur_part.node_id}.SS{m.group(1)}", "subsection",
                                      m.group(1), m.group(2).strip(),
                                      cur_part.node_id, counters["subsection"], 1))
            cur_chapter = None
            continue

        if m := RE_CHAPTER.match(line):
            label, lo, hi = _strip_range(m.group(2))
            parent = cur_subsection or cur_part
            counters["chapter"] += 1
            cur_chapter = add(Node(f"C{m.group(1)}", "chapter", m.group(1), label,
                                   parent.node_id, counters["chapter"],
                                   parent.depth + 1, lo, hi))
            continue

        if m := RE_SECTION.match(line):
            label, lo, hi = _strip_range(m.group(2))
            counters["section"] += 1
            add(Node(f"{cur_chapter.node_id}.S{m.group(1)}", "section", m.group(1), label,
                     cur_chapter.node_id, counters["section"], cur_chapter.depth + 1, lo, hi))
            continue

        raise ValueError(f"unrecognised structure line: {raw!r}")

    for n in nodes:
        if n.art_from is not None:
            n.doc_id = DOC_GENERAL if n.art_from <= GENERAL_PART_LAST_ARTICLE else DOC_SPECIAL
    return nodes


def leaf_ranges(nodes: list[Node]) -> list[Node]:
    """Nodes that actually carry articles (chapters without sections, plus sections)."""
    return [n for n in nodes if n.art_from is not None]


def validate(nodes: list[Node]) -> list[str]:
    """Structural self-consistency: contiguous, non-overlapping, gap-free coverage."""
    problems: list[str] = []
    leaves = sorted(leaf_ranges(nodes), key=lambda n: n.art_from)

    for a, b in zip(leaves, leaves[1:]):
        if b.art_from <= a.art_to:
            problems.append(f"overlap: {a.node_id} ({a.art_from}-{a.art_to}) and "
                            f"{b.node_id} ({b.art_from}-{b.art_to})")
        elif b.art_from != a.art_to + 1:
            problems.append(f"gap: articles {a.art_to + 1}-{b.art_from - 1} between "
                            f"{a.node_id} and {b.node_id}")
    if leaves and leaves[0].art_from != 1:
        problems.append(f"coverage does not start at article 1 (starts at {leaves[0].art_from})")

    # A chapter must either carry a range itself or delegate to sections.
    for n in nodes:
        if n.kind == "chapter" and n.art_from is None and not n.children:
            problems.append(f"{n.node_id} has neither an article range nor sections")
        # A chapter may legitimately carry both: Chapter 22 holds Article 259
        # itself and then splits into §§ 1-6 from Article 260. The overlap/gap
        # checks above already guarantee those ranges stay disjoint.
    return problems


def build_article_index(nodes: list[Node]) -> dict[int, Node]:
    """article number -> the deepest node containing it."""
    index: dict[int, Node] = {}
    for n in leaf_ranges(nodes):
        for art in range(n.art_from, n.art_to + 1):
            index[art] = n
    return index


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    ns = parse_structure()
    leaves = leaf_ranges(ns)
    print(f"parsed {len(ns)} nodes: "
          f"{sum(1 for n in ns if n.kind == 'part')} parts, "
          f"{sum(1 for n in ns if n.kind == 'subsection')} subsections, "
          f"{sum(1 for n in ns if n.kind == 'chapter')} chapters, "
          f"{sum(1 for n in ns if n.kind == 'section')} sections")
    print(f"{len(leaves)} range-carrying nodes covering articles "
          f"{min(n.art_from for n in leaves)}-{max(n.art_to for n in leaves)}")
    problems = validate(ns)
    print(f"validation: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    for p in problems:
        print("  -", p)
