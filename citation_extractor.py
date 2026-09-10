#!/usr/bin/env python
"""
M2 — Extraction of Civil Code citations from Uzbek legal text.

Pure functions, no database: `extract(text, ...) -> list[Citation]`.  Run this
module directly to execute its self-tests against real corpus phrasings.

Surface forms this handles, all observed in the corpus:

    Fuqarolik kodeksining 289-moddasi            single article
    Fuqarolik kodeksi 77-moddasi                 no genitive suffix
    ... 10, 24, 39, 40-moddalari                 list
    ... 457 va 458-moddalari                     list with "va"
    ... 299 — 310-moddalari                      range (en/em dash)
    ... 29-moddasining ikkinchi qismida          article + qism (part)
    ... 55-moddasining 12-bandiga                article + band (point)
    ... 30-bobi                                  chapter
    ... 37-bobining 3-paragrafi                  chapter + section
    ... 2591-moddasi                             superscript article 259-1
    FK 14-moddasi                                only where the act defines "FK"
    ushbu Kodeksning 14-moddasi                  only inside the Code itself

Deliberately NOT matched:
    Fuqarolik protsessual kodeksi / Fuqarolik-protsessual kodeksi  (another code)
    1963-yilgi Fuqarolik kodeksi                                   (repealed 1963 Code)
    FK II-IV                                    (a cardiology functional class that
                                                 appears in health regulations)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DOC_GENERAL = -111189
DOC_SPECIAL = -180552
GENERAL_PART_LAST_ARTICLE = 385
CODE_LAST_ARTICLE = 1199

# How far after an anchor we keep looking for reference clauses.
WINDOW = 260

# Uzbek ordinals used for article parts ("qism").
ORDINALS = ("birinchi", "ikkinchi", "uchinchi", "toʻrtinchi", "to'rtinchi", "beshinchi",
            "oltinchi", "yettinchi", "sakkizinchi", "toʻqqizinchi", "to'qqizinchi", "oʻninchi",
            "o'ninchi", "oʻn birinchi", "o'n birinchi", "oʻn ikkinchi", "o'n ikkinchi")

# The Civil Code itself.  "Fuqarolik" and "kodeksi" must be adjacent, which is
# what excludes "Fuqarolik protsessual kodeksi" without a separate rule.
RE_ANCHOR_CC = re.compile(r"Fuqarolik\s+kodeksi\w*", re.IGNORECASE)
RE_OLD_CODE = re.compile(r"19\d\d\s*-\s*yilgi\s*$", re.IGNORECASE)
# "FK" as a standalone token, immediately followed by a number or a reference word.
RE_ANCHOR_FK = re.compile(r"(?<![A-Za-zА-Яа-я0-9ʻʼ'-])FK(?:ning|ga|da|ni)?(?=\s+\d|\s+boshqa|\s+[0-9])")
RE_FK_ALIAS_DEF = re.compile(r"bundan\s+buyon\s+matnda\s+FK\s+deb", re.IGNORECASE)
# "ushbu/shu Kodeks" — only meaningful when the citing act IS the Code.
RE_ANCHOR_SELF = re.compile(r"(?:ushbu|shu|mazkur)\s+Kodeks\w*", re.IGNORECASE)

# A clause of numbers terminated by modda / bob / paragraf.
RE_CLAUSE = re.compile(
    r"(?P<nums>\d+(?:\s*(?:,|va|[–—])\s*\d+)*)\s*[-–—]\s*(?P<unit>modda|bob|paragraf)(?P<suffix>\w*)",
    re.IGNORECASE,
)
# Another act starting: stop scanning, its numbers are not the Code's.
# Case-sensitive bare "Qonun" (capital Q) is deliberately its own, case-sensitive
# alternative rather than folded into the case-insensitive group below: a bare
# lowercase "qonun" is overwhelmingly the generic word ("qonun hujjatlarida",
# "in legislation" — 49484 occurrences in the corpus vs. 3 that precede a modda/bob
# clause), while the corpus capitalizes "Qonun" only when naming a specific Act
# ("ushbu/mazkur Qonun", "...gi Qonun N-moddasi" — 1006 of 12387 capitalized
# occurrences precede a modda/bob clause). Measured 2026-09-05: this bare-nominative
# gap (RE_STOP previously only had the suffixed forms qonuni/qonuniga/qonunining)
# caused 25 real Civil-Code misattributions in the corpus (see DAILY_REVIEW.md).
# The same gap was checked for qaror/farmon/nizom and causes zero actual
# misattributions today — "nizom" bare is already below (case-insensitively, since
# no generic-phrase collision was found for it), and bare Qaror/Farmon never happen
# to sit right before an unstopped modda/bob clause in the current corpus — so they
# are left alone rather than "fixed" against a gap with no measured impact.
RE_STOP = re.compile(
    r"(?i:qonuni|qonuniga|qonunining|kodeksi|kodeksining|farmoni|farmonining|qarori|qarorining|"
    r"nizom|konstitutsiya|buyrugʻi|buyrugi|reglament|"
    # Publication record of the act, e.g. "(Oliy Majlisining Axborotnomasi, 1997-yil,
    # № 2, 56-modda)".  There "56-modda" is item 56 of the gazette issue, not an
    # article of the Code — the single largest false-positive source in the corpus.
    r"axborotnoma|vedomosti|toʻplam|toplam|№|-songa ilova)"
    r"|Qonun\b"
)
# Abbreviation of another code — FPK (Civil Procedure), JPK (Criminal Procedure),
# IPK, MMK and so on.  Case-sensitive on purpose: under IGNORECASE this would match
# any three-letter word ending in "k".  "FK" itself is one letter shorter and so is
# not caught, which is what lets our own alias through.
RE_STOP_ABBR = re.compile(r"\b[A-Z]{2,4}K(?:ning|ga|da|dagi|ni|dan)?\b")
# "XVI va XVII bobi" — a few acts cite chapters in Roman numerals.
RE_ROMAN_CHAPTER = re.compile(
    r"(?<![A-Za-z])(?P<r1>[IVXL]{1,6})(?:\s*(?:,|va)\s*(?P<r2>[IVXL]{1,6}))?\s*bob\w*"
)
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50}
RE_QISM = re.compile(
    r"(?P<num>\d+|" + "|".join(ORDINALS) + r")\s*-?\s*(?P<unit>qism|band)", re.IGNORECASE
)
# A comma or another modda/bob number between a citation and a qism/band match
# means the qism/band belongs to a later item in a list, not to this citation
# (e.g. "185-moddasi, 186-moddasi toʻqqizinchi qismi" — the ninth part is
# 186's, not 185's). Gates the non-"sining" qism/band attachment below.
RE_QISM_BLOCK = re.compile(r",|\d+\s*-\s*(?:modda|bob)", re.IGNORECASE)


@dataclass
class Citation:
    """One resolved reference to a Civil Code provision."""
    target_kind: str            # 'article' | 'chapter' | 'section' | 'act'
    article: str | None         # as written, e.g. '14' or '2591'
    struct_number: int | None   # chapter number for 'chapter'/'section' targets
    section_number: int | None
    qism: str | None            # article part/point, kept for a future finer grain
    anchor: str                 # 'fuqarolik_kodeksi' | 'fk_alias' | 'self_reference'
    listing: str                # 'single' | 'list' | 'range'
    start: int
    end: int
    evidence: str

    @property
    def doc_id(self) -> int | None:
        if self.target_kind == "act" or self.article is None:
            return None
        n = int(self.article)
        # Superscript articles are cited with the suffix digit concatenated onto
        # the base number, matching norm_unit.article_number (e.g. article 173-7
        # is written "1737", 259-1 is "2591" — see build_links.py's norm_by_number
        # lookup, which is keyed on this same literal string). Since no plain
        # article number exceeds CODE_LAST_ARTICLE, anything past it can only be
        # one of these concatenated forms: reclassify by the base article, not
        # the inflated concatenated value. Measured 2026-09-08: without this, the
        # base-then-suffix arithmetic below never ran, so build_links.py's
        # `if dst_doc is None: continue` silently dropped every real citation to
        # a superscript article past 1199 (173-7 and 259-1 in the General Part,
        # 626-1 and 1107-1 in the unmapped Special Part) — see DAILY_REVIEW.md.
        if n > CODE_LAST_ARTICLE:
            n //= 10
        if n <= GENERAL_PART_LAST_ARTICLE:
            return DOC_GENERAL
        return DOC_SPECIAL if n <= CODE_LAST_ARTICLE else None


def _expand(nums: str) -> tuple[list[str], str]:
    """'299 — 310' -> range, '10, 24, 39' -> list, '14' -> single."""
    parts = re.split(r"\s*(,|va|[–—])\s*", nums)
    values = [p for p in parts[::2] if p.strip()]
    seps = [p for p in parts[1::2]]
    if any(s in "–—" for s in seps) and len(values) == 2:
        lo, hi = int(values[0]), int(values[1])
        if 0 < hi - lo <= 200:  # guard against a malformed pair
            return [str(n) for n in range(lo, hi + 1)], "range"
        return values, "list"
    return values, ("list" if len(values) > 1 else "single")


def _roman(s: str) -> int | None:
    total = prev = 0
    for ch in reversed(s.upper()):
        v = ROMAN_VALUES.get(ch)
        if v is None:
            return None
        total += -v if v < prev else v
        prev = max(prev, v)
    return total or None


def _evidence(text: str, start: int, end: int, pad: int = 90) -> str:
    return re.sub(r"\s+", " ", text[max(0, start - pad): end + pad]).strip()


def _anchors(text: str, *, allow_fk_alias: bool, is_the_code: bool) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for m in RE_ANCHOR_CC.finditer(text):
        if RE_OLD_CODE.search(text[max(0, m.start() - 14): m.start()]):
            continue  # "1963-yilgi Fuqarolik kodeksi"
        found.append((m.start(), m.end(), "fuqarolik_kodeksi"))
    if allow_fk_alias:
        for m in RE_ANCHOR_FK.finditer(text):
            found.append((m.start(), m.end(), "fk_alias"))
    if is_the_code:
        for m in RE_ANCHOR_SELF.finditer(text):
            found.append((m.start(), m.end(), "self_reference"))
    return sorted(found)


def extract(text: str | None, *, allow_fk_alias: bool = False,
            is_the_code: bool = False) -> list[Citation]:
    if not text:
        return []
    out: list[Citation] = []
    anchors = _anchors(text, allow_fk_alias=allow_fk_alias, is_the_code=is_the_code)

    for i, (a_start, a_end, kind) in enumerate(anchors):
        # Never scan past the next anchor: its numbers belong to it.
        limit = min(a_end + WINDOW, anchors[i + 1][0] if i + 1 < len(anchors) else len(text))
        window = text[a_end:limit]

        consumed_to = 0
        produced = False
        for m in RE_CLAUSE.finditer(window):
            # A different act named before this clause claims it instead.
            gap = window[consumed_to:m.start()]
            if RE_STOP.search(gap) or RE_STOP_ABBR.search(gap):
                break
            unit = m.group("unit").lower()
            nums, listing = _expand(m.group("nums"))
            abs_start, abs_end = a_end + m.start(), a_end + m.end()

            if unit == "modda":
                tail = window[m.end(): m.end() + 60]
                suffix = m.group("suffix").lower()
                if suffix.startswith("sining"):
                    qm = RE_QISM.search(tail)
                elif len(nums) == 1:
                    # Not the genitive "moddasining" form (e.g. bare "moddasi",
                    # "moddasiga muvofiq") — still attach a qism/band if one
                    # immediately follows, but only when nothing between here
                    # and there suggests it belongs to a different citation.
                    cand = RE_QISM.search(tail)
                    qm = cand if cand and not RE_QISM_BLOCK.search(tail[:cand.start()]) else None
                else:
                    qm = None
                for n in nums:
                    out.append(Citation("article", n, None, None,
                                        qm.group(0).strip() if qm else None,
                                        kind, listing, abs_start, abs_end,
                                        _evidence(text, abs_start, abs_end)))
            elif unit == "bob":
                # "37-bobining 3-paragrafi", or with LexUZ's comma-separated
                # punctuation style, "57-bobi, 4-paragrafi". The optional comma
                # is deliberately followed only by \s* (no wildcard skip): if a
                # second chapter number sits between the comma and "paragraf"
                # (a real list, e.g. "57-bobi, 60-bobi, 4-paragrafi"), the match
                # fails here and the paragraf instead attaches to *that* later
                # bob on its own iteration — never misattributed backwards.
                # Measured 2026-09-10: 3 occurrences corpus-wide, all comma-only
                # (no such list case exists yet). See DAILY_REVIEW.md.
                sec = re.match(r"\s*,?\s*(\d+)\s*-\s*paragraf", window[m.end(): m.end() + 30])
                for n in nums:
                    out.append(Citation("section" if sec else "chapter", None, int(n),
                                        int(sec.group(1)) if sec else None, None,
                                        kind, listing, abs_start, abs_end,
                                        _evidence(text, abs_start, abs_end)))
            else:  # a bare "N-paragrafi" without its chapter is not resolvable
                continue

            produced = True
            consumed_to = m.end()

        if not produced:
            # Chapters cited in Roman numerals; only worth trying when no Arabic
            # clause was found, so "30-bobi" never re-enters here.
            for m in RE_ROMAN_CHAPTER.finditer(window):
                if RE_STOP.search(window[:m.start()]) or RE_STOP_ABBR.search(window[:m.start()]):
                    break
                abs_start, abs_end = a_end + m.start(), a_end + m.end()
                for g in ("r1", "r2"):
                    if (num := _roman(m.group(g) or "")) is not None:
                        out.append(Citation("chapter", None, num, None, None, kind,
                                            "list" if m.group("r2") else "single",
                                            abs_start, abs_end,
                                            _evidence(text, abs_start, abs_end)))
                        produced = True

        if not produced and kind == "fuqarolik_kodeksi":
            # The act is named but no provision is pinned: a real, weaker signal.
            out.append(Citation("act", None, None, None, None, kind, "single",
                                a_start, a_end, _evidence(text, a_start, a_end)))
    return out


# --------------------------------------------------------------------------- tests
def _selftest() -> int:
    cases: list[tuple[str, dict, list[tuple]]] = [
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining 289-moddasi.", {},
         [("article", "289", "single")]),
        ("LexUZ sharhiQarang: Fuqarolik kodeksining 299 — 310-moddalari.", {},
         [("article", str(n), "range") for n in range(299, 311)]),
        ("Fuqarolik kodeksining 10, 24, 39, 40-moddalari", {},
         [("article", n, "list") for n in ("10", "24", "39", "40")]),
        ("Fuqarolik kodeksining 457 va 458-moddalari.", {},
         [("article", "457", "list"), ("article", "458", "list")]),
        ("Fuqarolik kodeksi 29-moddasining ikkinchi qismida koʻrsatilgan", {},
         [("article", "29", "single")]),
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining 30-bobi (“Ayirboshlash”).", {},
         [("chapter", None, "single")]),
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksi 37-bobining 3-paragrafi", {},
         [("section", None, "single")]),
        ("Fuqarolik kodeksining 2591-moddasi", {}, [("article", "2591", "single")]),
        ("shartnoma shartlari bajarilmasa (FK 14-moddasining birinchi qismi)",
         {"allow_fk_alias": True}, [("article", "14", "single")]),
        # negatives
        ("Fuqarolik protsessual kodeksining 105-moddasi", {}, []),
        ("Fuqarolik-protsessual kodeksining 105-moddasi", {}, []),
        ("1963-yilgi Fuqarolik kodeksi normalariga muvofiq hal etiladi", {}, []),
        ("Turgʻun zoʻriqish stenokardiyasi, FK II-IV (oʻtkir miokard infarkti)",
         {"allow_fk_alias": True}, []),
        ("FK 14-moddasi", {}, []),  # alias not enabled for this act
        # the next act's articles must not be attributed to the Code
        ("Fuqarolik kodeksiga muvofiq, “Davlat xaridlari toʻgʻrisida”gi Qonunining 34-moddasi", {},
         [("act", None, "single")]),
        ("ushbu Kodeksning 14-moddasi", {"is_the_code": True}, [("article", "14", "single")]),
        ("ushbu Kodeksning 14-moddasi", {}, []),  # not the Code: refers to its own act
        # the act's own publication record: "56-modda" is a gazette item, not an article
        ("Oʻzbekiston Respublikasining Fuqarolik kodeksi (Oʻzbekiston Respublikasi Oliy "
         "Majlisining Axborotnomasi, 1996-yil, 2-songa ilova, № 11-12; 1997-yil, № 2, "
         "56-modda, № 9, 241-modda)", {}, [("act", None, "single")]),
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining XVI va XVII bobi.", {},
         [("chapter", None, "list"), ("chapter", None, "list")]),
        # a real citation must still survive a gazette reference appearing later
        ("Fuqarolik kodeksining 14-moddasi (Axborotnoma, 1997-yil, № 2, 56-modda)", {},
         [("article", "14", "single")]),
        # another code's abbreviation inside the window must stop the scan
        ("Fuqarolik kodeksiga koʻra javobgar zimmasiga yuklatiladi. FPKning 71-moddasiga muvofiq",
         {}, [("act", None, "single")]),
        ("Fuqarolik kodeksining 14-moddasi, JPKning 22-moddasi", {},
         [("article", "14", "single")]),
    ]
    failures = 0
    for text, kwargs, expected in cases:
        got = [(c.target_kind, c.article, c.listing) for c in extract(text, **kwargs)]
        want = [(k, a, l) for k, a, l in expected]
        if got != want:
            failures += 1
            print(f"FAIL {text[:64]!r}\n     got  {got}\n     want {want}")

    # qism/band attachment for non-"sining" modda suffixes (measured gap, see
    # DAILY_REVIEW.md 2026-09-04): must still attach when unambiguous, and
    # must NOT attach when a comma/another modda intervenes (list continuation).
    qism_cases: list[tuple[str, dict, list[str | None]]] = [
        ("Fuqarolik kodeksining 212-moddasi uchinchi qismiga muvofiq", {}, ["uchinchi qism"]),
        ("Fuqarolik kodeksi 281-moddasi oltinchi qismining 4-bandida", {}, ["oltinchi qism"]),
        ("mazkur Kodeksning 185-moddasi, 186-moddasi toʻqqizinchi qismi",
         {"is_the_code": True}, [None, "toʻqqizinchi qism"]),
        ("FKning 591-moddasi va FPKning 14-moddasining uchinchi qismiga koʻra",
         {"allow_fk_alias": True}, [None]),
    ]
    for text, kwargs, expected in qism_cases:
        got = [c.qism for c in extract(text, **kwargs) if c.target_kind == "article"]
        if got != expected:
            failures += 1
            print(f"FAIL(qism) {text[:64]!r}\n     got  {got}\n     want {expected}")

    # bare-nominative "Qonun" must stop the scan like the suffixed forms already do
    # (measured gap, see DAILY_REVIEW.md 2026-09-05), but the generic lowercase word
    # ("qonun hujjatlarida") must not.
    stop_cases: list[tuple[str, dict, list[tuple]]] = [
        ('Fuqarolik kodeksiga muvofiq, “Davlat boji toʻgʻrisida”gi Qonun 19-moddasining '
         "toʻrtinchi qismi", {}, [("act", None, "single")]),
        ("Fuqarolik kodeksining 14-moddasi qonun hujjatlarida nazarda tutilgan tartibda",
         {}, [("article", "14", "single")]),
    ]
    for text, kwargs, expected in stop_cases:
        got = [(c.target_kind, c.article, c.listing) for c in extract(text, **kwargs)]
        want = [(k, a, l) for k, a, l in expected]
        if got != want:
            failures += 1
            print(f"FAIL(stop) {text[:64]!r}\n     got  {got}\n     want {want}")
    # doc_id must reclassify superscript articles by their base number, not the
    # concatenated citation string (measured gap, see DAILY_REVIEW.md
    # 2026-09-08): a General Part superscript (173-7) and a Special Part one
    # (1107-1, base > GENERAL_PART_LAST_ARTICLE) must resolve to the right doc,
    # not silently become unresolvable the way they did before the fix.
    docid_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining 173 – 1737-moddalari.", {},
         [("173", DOC_GENERAL), ("1737", DOC_GENERAL)]),
        ("Fuqarolik kodeksining 2591-moddasi.", {}, [("2591", DOC_GENERAL)]),
        ("FKning 11071-moddasiga asosan", {"allow_fk_alias": True}, [("11071", DOC_SPECIAL)]),
        ("Fuqarolik kodeksining 700-moddasi.", {}, [("700", DOC_SPECIAL)]),
    ]
    for text, kwargs, expected in docid_cases:
        got = [(c.article, c.doc_id) for c in extract(text, **kwargs) if c.target_kind == "article"]
        if got != expected:
            failures += 1
            print(f"FAIL(doc_id) {text[:64]!r}\n     got  {got}\n     want {expected}")

    # chapter+paragraph attachment must tolerate LexUZ's comma-separated style
    # ("57-bobi, 4-paragrafi", not just the genitive "57-bobining 4-paragrafi"),
    # but must NOT reach across a second, distinct chapter number in a real list
    # (measured gap, see DAILY_REVIEW.md 2026-09-10: 3 real corpus occurrences,
    # all comma-only — no comma-separated-list case exists yet to test against
    # real text, so the list case below is a constructed guard check).
    section_comma_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Fuqarolik kodeksi 57-bobi, 4-paragrafi talablariga koʻra", {},
         [(57, 4)]),
        ("Fuqarolik kodeksining 22-bob, 2-paragrafi.", {}, [(22, 2)]),
        ("Fuqarolik kodeksining 57-bobi, 60-bobi, 4-paragrafi", {},
         [(57, None), (60, 4)]),
    ]
    for text, kwargs, expected in section_comma_cases:
        got = [(c.struct_number, c.section_number) for c in extract(text, **kwargs)
               if c.target_kind in ("chapter", "section")]
        if got != expected:
            failures += 1
            print(f"FAIL(section_comma) {text[:64]!r}\n     got  {got}\n     want {expected}")

    total = (len(cases) + len(qism_cases) + len(stop_cases) + len(docid_cases)
             + len(section_comma_cases))
    print(f"{total - failures}/{total} extractor self-tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(_selftest())
