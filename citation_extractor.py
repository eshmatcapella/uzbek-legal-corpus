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
    ... V boʻlimi / V-boʻlimi                    part (roman numeral)
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
# The "kodeksning" alternative (genitive without the "-i-" thematic vowel,
# same gap class as "qonunning" below) is needed here too, not just as a
# RE_STOP entry: unlike "kodeksning" naming some OTHER code by role (already
# handled by RE_STOP so the scan stops on it), "Fuqarolik kodeksning" is a
# real, if rare, way LexUZ names the Civil Code itself, and without this the
# anchor never fires at all (not merely a coarser match — the whole citation,
# including every article listed after it, is invisible). Measured
# 2026-09-17 (see DAILY_REVIEW.md): 3 rows / 4 occurrences corpus-wide, all
# genuine, all previously producing zero citations.
#
# The suffix group below is deliberately NOT bare `\w*`: LexUZ occasionally
# omits the space before the following number entirely ("kodeksining202 va
# 203-moddalari"), and `\w*` is greedy over *all* word characters, digits
# included — it would consume "202" as part of the anchor match itself,
# before RE_CLAUSE ever gets a chance to see it, silently dropping the first
# item of the list. Found 2026-10-30 via the signature-stratified gold
# sampler (batch 16, row 34219): `a_end` landed after "202", not before it,
# so the per-anchor window started at " va 203-moddalari" and only "203"
# survived. `[^\W0-9]*` matches the same real Uzbek suffixes (letters and
# the ʻ/ʼ okina marks, all Unicode word characters) while excluding ASCII
# digits, so a glued genitive suffix still matches in full but a glued
# number no longer does. Measured corpus-wide: this exact shape (the anchor
# regex's own match ending on a digit) occurs 2 times (rows 34219, 38589);
# row 34219 is a genuine, confirmed recall loss (article 202 never appears
# anywhere in that field's extract() output); row 38589's swallowed "190" is
# coincidentally recovered by an unrelated, separate mention of article 190
# elsewhere in the same field, so it wasn't visible in the headline recall
# number, but was still a latent per-anchor precision bug waiting to recur
# without the coincidence. See DAILY_REVIEW.md 2026-10-30.
RE_ANCHOR_CC = re.compile(r"Fuqarolik\s+kodeks(?:i[^\W0-9]*|ning)", re.IGNORECASE)
RE_OLD_CODE = re.compile(r"19\d\d\s*-\s*yilgi\s*$", re.IGNORECASE)
# A self-naming "(... deb yuritiladi/ataladi)" parenthetical ("hereinafter
# referred to as ...") routinely repeats, inside its own parens, the exact
# name it is defining an abbreviation FOR -- e.g. "...Fuqarolik kodeksi
# (keyingi oʻrinlarda Fuqarolik kodeksi deb yuritiladi) 327-moddasiga...".
# The second, parenthesized "Fuqarolik kodeksi" is pure definitional noise,
# not a second real anchor, but RE_ANCHOR_CC matches it anyway, creating a
# spurious anchor immediately after the real one. Per `_anchors()`'s own
# "never scan past the next anchor" rule, the REAL anchor's window then gets
# truncated right at the spurious one's start, before ever reaching the
# citation that follows the closing paren -- and the spurious anchor's own
# window starts mid-clause ("... deb yuritiladi) <citation>"), which
# RE_LEADING_PUB_PAREN can't recognize as a publication parenthetical (it
# isn't one, and isn't even at the window's start). Found 2026-11-09 via gold
# batch 19 (gold_id 763, row 30003): article 327 dropped entirely because
# this row chains a SECOND, genuine publication parenthetical right after
# the naming one, so `RE_STOP`'s whole-window break (fired on "Axborotnomasi"
# inside that second paren) discards the real citation too. Measured
# corpus-wide 2026-11-18 (every row containing the literal "Fuqarolik kodeksi
# deb yuritiladi/ataladi" naming clause): 8 rows, 9 raw occurrences
# (5291, 18091, 25971, 30003, 30057, 30344 x2, 30762, 30789).
#
# First fix attempted (reverted, same session): just drop any anchor match
# that falls entirely inside such a parenthetical, so the spurious anchor
# never forms. That's necessary but NOT sufficient -- 5 of the other 7 rows
# were already recovering the real citation today only BECAUSE the spurious
# anchor's own (separately-windowed) scan started right after "kodeksi",
# never seeing that word as a gap at all. Drop the spurious anchor alone and
# the REAL anchor's own (now-unbounded) window reaches the citation directly
# -- but the literal word "kodeksi", still sitting unconsumed inside the
# naming parenthetical, is itself one of RE_STOP's own trigger words (see
# RE_STOP's `kodeksi|kodeksining|kodeksning` alternative above): the gap
# before the real citation's RE_CLAUSE match now contains "kodeksi" in plain
# text, so RE_STOP fires and the whole-window `break` discards the citation
# all over again -- a regression (5291, 30057, 30344, 30762, 30789 all lost
# their real citation), and 30003 itself stayed broken.
#
# Real fix: blank the whole naming parenthetical out (same length-preserving
# space-fill RE_LEADING_PUB_PAREN already uses, just computed once up front
# over the whole text rather than per-window) BEFORE anchor-finding and
# clause-scanning -- see `_blank_naming_parens()`. This removes the spurious
# anchor (nothing inside the blanked span can match RE_ANCHOR_CC) AND removes
# "kodeksi" from the gap RE_STOP searches (it's now blank spaces), so the
# real anchor's own window runs straight through the (now-invisible) naming
# clause to the real citation, exactly as if it had never repeated the
# Code's name at all. `_evidence()` still slices the UNBLANKED original
# text, so the displayed citation context still shows the real naming
# clause verbatim. Re-measured after this fix (see DAILY_REVIEW.md
# 2026-11-18): article 327 recovered at row 30003 (the one documented
# recall miss); the 5 redundant `act`-kind edges the spurious anchor
# produced at 18091/25971/30057/30344/30762/30789 are gone, with no loss --
# every real citation those 6 rows already had stays exactly as it was; and
# 5291's own previously-"coincidentally-recovered" article 549 is now found
# the SAME way (via the real anchor directly), not lost. Zero rows anywhere
# else in the corpus change at all.
RE_NAMING_PAREN = re.compile(r"\([^()]*\bdeb\s+(?:yuritiladi|ataladi)\b[^()]*\)", re.IGNORECASE)
# "FK" as a standalone token, immediately followed by a number or a reference word.
RE_ANCHOR_FK = re.compile(r"(?<![A-Za-zА-Яа-я0-9ʻʼ'-])FK(?:ning|ga|da|ni)?(?=\s+\d|\s+boshqa|\s+[0-9])")
# "ushbu/shu Kodeks" — only meaningful when the citing act IS the Code.
# Same digit-glomming risk as RE_ANCHOR_CC above, same fix (see 2026-10-30
# note there) — no measured corpus occurrence inside a real self_reference
# anchor today (the only two matches with a trailing digit, rows 48522 and
# 53096, are both is_the_code=False documents where this pattern isn't even
# used as an anchor), but there is no reason this regex should behave
# differently from RE_ANCHOR_CC on the exact same input shape.
RE_ANCHOR_SELF = re.compile(r"(?:ushbu|shu|mazkur)\s+Kodeks[^\W0-9]*", re.IGNORECASE)

# A clause of numbers terminated by modda / bob / paragraf. The separator
# before the unit word is usually a hyphen/dash, but LexUZ sometimes just
# leaves a plain space ("Fuqarolik kodeksining 49 moddasi", no hyphen at all —
# confirmed by reading raw corpus text, not assumed). Accept either: a
# dash with optional surrounding whitespace, or bare whitespace with no dash
# at all (never *zero* separator, so this can't start matching some unrelated
# digit run glued directly onto another word). Measured 2026-09-15 (see
# DAILY_REVIEW.md): 21 real citations corpus-wide used only the space form and
# were silently invisible to the old dash-only pattern — not unresolved, not
# dangling, the anchor's window just never produced a RE_CLAUSE match for them
# at all.
#
# The inner list separator (between numbers WITHIN nums) also accepts a bare
# ASCII hyphen now, not just comma/va/en-dash/em-dash — LexUZ sometimes packs
# a sub-range into a list with an ordinary "-" ("393-395, 399, 402, 408,
# 412-moddalarida"). No ambiguity with the outer unit separator above: that
# one needs "modda/bob/paragraf" (letters) right after the dash, this one
# needs a digit, so the regex engine never confuses the two. _expand() below
# does the actual sub-range recognition/expansion. Measured 2026-09-15: 11
# such clauses corpus-wide (see DAILY_REVIEW.md).
#
# The dash class itself is "+", not a single character, because LexUZ
# sometimes doubles it ("744 –– 748-moddalari", two literal en-dashes back
# to back with no space between them — an export artifact, not a different
# separator). A single-dash class silently fails to extend "nums" past the
# first number when it hits the second dash character where a digit was
# expected, so the whole range collapsed to just its own trailing endpoint
# (matched as an unrelated single citation, the range's low end dropped
# entirely with no edge, dangling or otherwise). Measured 2026-09-17 (see
# DAILY_REVIEW.md): 16 clauses corpus-wide.
# Each item of the list may carry its own short parenthetical title right
# after its number, before the next separator ("43 (“Bank omonati”) va 44
# (“Bank hisobvaragʻi”) boblari") -- LexUZ names chapters/articles this way
# often enough in multi-item lists that the parenthetical otherwise breaks
# "nums" entirely (the old pattern required a contiguous digit/separator
# run with nothing else interposed, so the whole clause fell through to a
# bare act/chapter citation, dropping every listed item but the last).
# Bounded to 100 chars and excludes further parens so it can't accidentally
# swallow past its own closing ")" into unrelated text. Measured 2026-10-27
# (see DAILY_REVIEW.md): re-measuring the ALREADY-recorded known_gap
# (gold_id 548, 2026-10-24) with a regex that also allows the paren after
# the SECOND item -- the original measurement required the paren only on
# the first -- found the true corpus-wide in-scope footprint is 5 occurrences,
# not 1 as originally measured, crossing this project's own single-occurrence
# deferral threshold. _expand() below strips the parenthetical text itself
# before splitting on comma/va, since a title can contain the literal word
# "va" ("Majburiyat tushunchasi va taraflari") which would otherwise be
# misread as a second list separator.
#
# "hamda" ("as well as") is accepted as a third list conjunction alongside
# comma/va: found 2026-09-15 (row 24219, "11-12 hamda 14-moddalari"), measured
# at exactly 1 genuine in-scope occurrence corpus-wide (2 more raw matches
# are inside Fuqarolik protsessual kodeksi text, already excluded by
# RE_STOP_ABBR before the anchor ever fires), recorded as known_gap gold_id
# 140 and deferred at that single-occurrence scope for two months. Swept
# 2026-11-15 alongside the other known_gap items: "hamda" only ever sits
# between two numbers inside an already-anchored `nums` clause (same as "va"
# above), so this can't collide with the word's far more common standalone
# use elsewhere in the corpus (e.g. plain "...hamda shuningdek..." prose,
# nowhere near a digit).
RE_CLAUSE = re.compile(
    r"(?P<nums>\d+(?:\s*\([^()]{0,100}\))?(?:\s*(?:,|va|hamda|[-–—]+)\s*\d+(?:\s*\([^()]{0,100}\))?)*)"
    r"(?:\s*[-–—]\s*|\s+)(?P<unit>modda|bob|paragraf)(?P<suffix>\w*)",
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
#
# "qonunning" (genitive WITHOUT the "-i-" thematic vowel: qonun+ning, as opposed
# to qonuni+ning already covered by "qonunining") is a distinct surface form
# that isn't a substring of any alternative above, and IS folded into the
# case-insensitive group rather than kept case-sensitive like bare "Qonun":
# unlike bare "qonun" (ambiguous generic noun, "legislation"), "qonunning" only
# ever means "of [a specific, previously-named] law" — the Civil Code itself is
# never referred to as "qonun" in this corpus, so there is no generic-phrase
# collision to guard against, and LexUZ often leaves it lowercase even when it
# heads a genuinely specific "X toʻgʻrisida"gi qonunning N-moddasi" citation.
# Measured 2026-09-12 (see DAILY_REVIEW.md): 131 real Civil-Code misattributions
# (118 capitalized "Qonunning" + 13 more lowercase "qonunning") corpus-wide, 0
# collateral loss of genuine Code citations sharing the same anchor window.
#
# "kodeksning" is the same genitive-without-"-i-" gap as "qonunning" above, for
# "kodeks" instead of "qonun": "kodeksi"/"kodeksining" (already in this group)
# don't match it as a substring (the "i" that "kodeksi" needs sits one letter
# later than where "kodeksning" puts its "n"). Two real surface forms hit this:
# another code named by role ("Maʼmuriy javobgarlik toʻgʻrisidagi kodeksning
# 60-moddasi") and, far more often, "mazkur/ushbu/shu Kodeksning" *inside some
# other code's own text* pointing at itself, not the Civil Code — RE_ANCHOR_SELF
# only treats that phrase as a self-reference anchor when the citing act IS the
# Civil Code (`is_the_code`), so in every other code's text it's just inert
# words the scan should stop at, same as any other act name. Measured
# 2026-09-15 (see DAILY_REVIEW.md): 32 clauses misattributed to the Civil Code
# across 21 rows, all confirmed by reading the citing text — every one names or
# means a different code (Administrative Liability, and 20 rows of some other
# code's "mazkur Kodeksning" self-reference). Zero collateral loss: inside the
# Civil Code's own text, "ushbu/mazkur/shu Kodeksning" is always itself the
# self_reference anchor match (RE_ANCHOR_SELF consumes the whole word,
# including "-ning"), so this stop-word never fires there.
#
# BUT bare "Kodeksning" (or "ushbu/mazkur/shu Kodeksning" with nothing else
# naming a different act in front of it) directly after -- or, in a longer
# window, still clearly continuing -- the Civil Code's own mention is a THIRD
# surface form this single substring match can't tell apart from the two
# above: "Oʻzbekiston Respublikasining Fuqarolik kodeksi Kodeksning
# 53-moddasi" is LexUZ redundantly restating the Civil Code's own name one
# word after naming it, not announcing a different code (`gold_id` 587, row
# 19636, found 2026-10-27). Moved the bare "kodeksning" alternative out to its
# own `RE_STOP_KODEKSNING` below, checked by `extract()`'s `_is_stop` helper
# at every stop-check call site.
#
# First attempt (2026-11-21): gate purely on `doc_type` -- stop only when the
# citing act genuinely has "its own code" (`doc_type == "code"`) or `doc_type`
# isn't known at all (`None`, the conservative default every caller gets
# unless it explicitly threads `doc_type` through). A full corpus-wide
# before/after `extract()` diff (same discipline as every prior fix here, not
# just the 2 occurrences the original narrow measurement found) caught this
# alone as WRONG before shipping: row 29029 ("Fuqarolik kodeksining
# 166-moddasi, Oʻzbekiston Respublikasi Maʼmuriy javobgarlik toʻgʻrisidagi
# kodeksning 60, 61-moddalari...") has `doc_type='law'`, same as the bug, but
# here "kodeksning" genuinely IS naming a different code -- the Code on
# Administrative Liability, named immediately before it by its own
# "<subject> toʻgʻrisidagi" qualifier phrase -- and a doc_type-only gate would
# have wrongly attributed its 60/61 to the Civil Code. The real second signal
# is local, not document-level: is "kodeksning" preceded, anywhere in the same
# stop-check span, by a "toʻgʻrisida(gi)" act-naming qualifier? If so it always
# stops, regardless of `doc_type` -- `RE_ACT_QUALIFIER` below checks exactly
# this, scanned over the same span before deferring to `doc_type` at all.
#
# Measured corpus-wide before shipping (every anchor-window stop-check span
# anywhere in the corpus whose own text contains bare "kodeksning", cross-
# checked against each row's actual text and `doc_type`, not just the 2 the
# original narrow single-regex measurement found): 4 occurrences total.
# Row 19636 (`doc_type='law'`, no qualifier before it) -- the known bug,
# fixed, recovers article 53. Row 29029 (`doc_type='law'`, preceded by
# "toʻgʻrisidagi") -- correctly still stops via `RE_ACT_QUALIFIER`, zero
# change. Two more, not previously found by the narrower 2026-10-27
# measurement because it only looked within 20 chars of a bare digit+modda
# clause: row 11208 (`doc_type='constitution'`, "...Ushbu Kodeksning
# 197-moddasiga muvofiq..." continuing a Civil Code citation 166 moddasi
# started two sentences earlier) and row 41405 (`doc_type='law'`,
# "...ushbu Kodeksning 57-bobi ("Zarar yetkazishdan kelib chiqadigan
# majburiyatlar")..." continuing a Civil Code article-725 citation) -- both
# genuine additional recall fixes under the same doc_type+qualifier logic,
# recovering article 197 and chapter 57 respectively. See DAILY_REVIEW.md
# 2026-11-21 for the full trace and the `link_edge` before/after count.
RE_STOP = re.compile(
    r"(?i:qonuni|qonuniga|qonunining|qonunning|kodeksi|kodeksining|"
    r"farmoni|farmonining|qarori|qarorining|"
    r"nizom|konstitutsiya|buyrugʻi|buyrugi|reglament|"
    # A "yoʻriqnoma" (instruction/guideline) being named is the same "a
    # different act is speaking now" signal as qonun/farmon/qaror/nizom
    # above: its own numbered parts (including, since 2026-10-02, a
    # roman-numeral "boʻlim") aren't the Code's. Found while building
    # part-level ("boʻlim") citation support: row 42566's "...yoʻriqnoma"ning
    # (roʻyxat raqami 697, 08.04.1999-y.) IV boʻlimi" was being misattributed
    # to the Civil Code (the window's actual Code citation is an earlier,
    # separate "22-bobining 5 paragrafi" clause; the new part-scan ran past
    # it unconditionally and reached the yoʻriqnoma's own Part IV). Measured
    # corpus-wide 2026-10-02: 11 anchor windows mention "yoʻriqnoma" at all,
    # and row 42566 (twice, V and IV boʻlimi) is the ONLY one where a modda/
    # bob/paragraf/boʻlim clause of any kind follows it within the window —
    # the other 10 only ever reach an "ilova" (annex) or "band" (point), units
    # this extractor never matches anyway. Zero collateral loss: no other
    # window loses any citation by adding this.
    r"yo[ʻʼ']?riqnoma|"
    # Publication record of the act, e.g. "(Oliy Majlisining Axborotnomasi, 1997-yil,
    # № 2, 56-modda)".  There "56-modda" is item 56 of the gazette issue, not an
    # article of the Code — the single largest false-positive source in the corpus.
    r"axborotnoma|vedomosti|toʻplam|toplam|№|-songa ilova|"
    # Bare "qonun" immediately followed by an open parenthesis: LexUZ
    # sometimes parenthetically cites another act's own provision right
    # inside a Civil Code anchor's window — "...toʻgʻrisida"gi qonun
    # (35-modda) asosida" means article 35 of THAT law, not the Code.
    # Deliberately narrower than the general bare-lowercase-"qonun" gap
    # already measured and left alone (2026-09-05: 49484 generic occurrences
    # vs. only 3 immediately before a modda/bob clause, too high a
    # false-negative risk to stop on unconditionally): requiring the
    # immediate "(" is a much rarer, unambiguous shape (this alternative
    # sits inside the case-insensitive group, so it also covers capitalized
    # "Qonun(" — harmlessly redundant with "Qonun\b" below, which already
    # stops there too). Measured 2026-09-25 (see DAILY_REVIEW.md): exactly 6
    # bare "qonun(" occurrences (any case) exist corpus-wide at all, every
    # one a parenthetical aside naming some OTHER act/provision, never a
    # continuation of the Code's own citation — and only 1 of the 6
    # (row 6071) sits inside any Civil-Code/FK anchor's window in the first
    # place, where it was already live as a wrong `link_edge` row (article
    # "35" misattributed to DOC_GENERAL) before this fix.
    r"qonun\s*\()"
    r"|Qonun\b"
)
# Bare "kodeksning" (genitive without "-i-"), split out from RE_STOP above so it
# can be gated on `doc_type` instead of firing unconditionally — see the long
# comment above RE_STOP's own definition for the full reasoning and the
# gold_id 587 fix it's for.
RE_STOP_KODEKSNING = re.compile(r"kodeksning", re.IGNORECASE)
# A "<subject> toʻgʻrisidagi" qualifier (any okina spelling) immediately in
# front of "kodeksning" names a SPECIFIC different code by its own subject
# matter ("Maʼmuriy javobgarlik toʻgʻrisidagi kodeksning" — "of the Code on
# Administrative Liability"), unlike bare/"ushbu/mazkur/shu" "kodeksning" on
# its own. When this qualifier is present, "kodeksning" always stops the scan
# regardless of `doc_type` — see RE_STOP_KODEKSNING's own comment, row 29029.
RE_ACT_QUALIFIER = re.compile(r"to[ʻʼ']?g[ʻʼ']?risida", re.IGNORECASE)
# Abbreviation of another code — FPK (Civil Procedure), JPK (Criminal Procedure),
# IPK, MMK and so on.  Case-sensitive on purpose: under IGNORECASE this would match
# any three-letter word ending in "k".  "FK" itself is one letter shorter and so is
# not caught, which is what lets our own alias through.
RE_STOP_ABBR = re.compile(r"\b[A-Z]{2,4}K(?:ning|ga|da|dagi|ni|dan)?\b")
# "XVI va XVII bobi" — a few acts cite chapters in Roman numerals.
RE_ROMAN_CHAPTER = re.compile(
    r"(?<![A-Za-z])(?P<r1>[IVXL]{1,6})(?:\s*(?:,|va)\s*(?P<r2>[IVXL]{1,6}))?\s*bob\w*"
)
# "Fuqarolik kodeksining V boʻlimi" — Part, the structural tier above chapter
# (struct_node has 6 real 'part' nodes, PI..PVI). Always a single roman
# numeral in the corpus today, never a list/range. Like modda/bob/paragraf
# above, LexUZ sometimes writes a bare space instead of a hyphen before the
# unit word, and the apostrophe-like letter in "boʻlim" itself varies (okina
# ʻ, a plain "'", or dropped entirely). Previously unrecognized entirely —
# no target_kind existed for it — so every occurrence fell through to either
# the coarse bare-`act` fallback (when nothing else in the window matched) or
# was silently dropped outright (when an earlier modda/bob clause in the same
# window already set `produced`, e.g. "23-bobi ... hamda V boʻlimiga").
# Measured 2026-09-17: 6 corpus-wide occurrences, all using the hyphen form
# only — that was an undercount of the methodology's own regex, not the real
# count: measured again 2026-10-02 with the hyphen made optional, 20
# corpus-wide (14 more via the bare-space form), same single-occurrence-per-
# window shape throughout. See DAILY_REVIEW.md.
RE_ROMAN_PART = re.compile(
    r"(?<![A-Za-z])(?P<r1>[IVXL]{1,6})(?:\s*-\s*|\s+)bo[ʻʼ']?lim\w*", re.IGNORECASE
)
# An Arabic-DIGIT "boʻlim" is a different unit from the roman-numeral Part
# above: the Code's own 6 structural Parts (PI..PVI) are only ever written
# with a roman numeral in this corpus (see RE_ROMAN_PART's own comment), so a
# bare digit before "boʻlim" can't be naming one of them -- it's LexUZ using
# "boʻlim" as a loose synonym for "bob" (chapter) instead. Found 2026-10-30
# (gold_id 618, row 32903): "Fuqarolik kodeksining 40-boʻlimi ("Transport
# ekspeditsiyasi")" names Chapter 40 (confirmed via struct_node: C40 =
# "Transport ekspeditsiyasi"), not a 40th Part (the Code has only 6).
# Deferred over two weeks at its then-measured single-occurrence scope, swept
# 2026-11-15 alongside the other known_gap items: re-measured against every
# real Civil-Code/FK/self-reference anchor window corpus-wide (not a blind
# text-wide regex grep -- "boʻlim" is an ordinary word, "department/unit",
# that appears far more often outside any citation context) and confirmed
# the in-window footprint is still exactly 1 occurrence, zero collateral.
# Scanned independently, same convention as RE_ROMAN_PART, so it can't be
# silently skipped by an earlier modda/bob clause already setting `produced`.
RE_ARABIC_BOLIM = re.compile(r"(?<!\d)(?P<num>\d+)(?:\s*-\s*|\s+)bo[ʻʼ']?lim\w*", re.IGNORECASE)
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50}
RE_QISM = re.compile(
    r"(?P<num>\d+|" + "|".join(ORDINALS) + r")\s*-?\s*(?P<unit>qism|band)", re.IGNORECASE
)
# A comma or another modda/bob number between a citation and a qism/band match
# means the qism/band belongs to a later item in a list, not to this citation
# (e.g. "185-moddasi, 186-moddasi toʻqqizinchi qismi" — the ninth part is
# 186's, not 185's). Gates the non-"sining" qism/band attachment below.
RE_QISM_BLOCK = re.compile(r",|\d+\s*-\s*(?:modda|bob)", re.IGNORECASE)
# A single modda can itself carry SEVERAL qism/band references at once --
# "497-moddasi birinchi, ikkinchi qismlari" (parts one AND two of article
# 497, not a list of different articles), or with "va" instead of a comma,
# "377-moddasining oltinchi va yettinchi qismlarida" (parts six and seven).
# RE_QISM alone only ever grabs the ONE ordinal immediately adjacent to the
# unit word -- for "birinchi, ikkinchi qismlari" that's "ikkinchi", and
# RE_QISM_BLOCK's own comma check (correctly tuned for the *different-article*
# list case above) then discards even that, so today's code silently drops
# every qism but at most the last one. Measured 2026-10-18 (see
# DAILY_REVIEW.md): 63 real in-scope citations corpus-wide carry 2+ qism/band
# ordinals this way. This pattern is anchored at the START of the post-modda
# tail (optionally through one leading comma, same position RE_QISM_BLOCK's
# gate already inspects) specifically so it can never fire on the
# different-article shape: a bare digit token is excluded via lookahead
# whenever it's itself the START of another "N-modda/bob" citation (e.g.
# "186-moddasi" in the example above), so that shape still falls through to
# the existing single-match/gate logic below, unchanged.
RE_QISM_MULTI = re.compile(
    r"^\s*,?\s*(?P<list>"
    r"(?:\d+(?!\s*-?\s*(?:modda|bob))|" + "|".join(ORDINALS) + r")"
    r"(?:\s*,\s*(?:\d+(?!\s*-?\s*(?:modda|bob))|" + "|".join(ORDINALS) + r"))*"
    r"(?:\s+va\s+(?:\d+(?!\s*-?\s*(?:modda|bob))|" + "|".join(ORDINALS) + r"))?"
    r")\s*-?\s*(?P<unit>qism|band)",
    re.IGNORECASE,
)
RE_QISM_TOKEN = re.compile(r"\d+|" + "|".join(ORDINALS), re.IGNORECASE)


def _qism_list(tail: str) -> list[str] | None:
    """Multiple qism/band ordinals attached to ONE modda (see RE_QISM_MULTI).
    Returns None (defer to the single-match path, unchanged) unless at least
    two ordinals are found -- a single-ordinal match here would just
    duplicate what the existing RE_QISM/RE_QISM_BLOCK logic already does."""
    m = RE_QISM_MULTI.match(tail)
    if not m:
        return None
    unit = m.group("unit").lower()
    tokens = RE_QISM_TOKEN.findall(m.group("list"))
    if len(tokens) < 2:
        return None
    return [f"{t} {unit}" for t in tokens]


# Canonical spellings of ORDINALS, one entry per distinct ordinal (ORDINALS
# itself carries two spellings each for "toʻrtinchi"/"toʻqqizinchi"/
# "oʻninchi"/"oʻn birinchi"/"oʻn ikkinchi" -- the apostrophe-letter ʻ vs the
# plain ASCII "'" -- so it can't be indexed directly for a range).
_ORDINAL_CANON = ("birinchi", "ikkinchi", "uchinchi", "toʻrtinchi", "beshinchi",
                   "oltinchi", "yettinchi", "sakkizinchi", "toʻqqizinchi",
                   "oʻninchi", "oʻn birinchi", "oʻn ikkinchi")


def _ordinal_index(word: str) -> int | None:
    """0-based position of an ordinal word in _ORDINAL_CANON, normalizing
    away the apostrophe-letter spelling variants (ʻ/ʼ/plain ') so either
    spelling of a dash-range endpoint resolves to the same index."""
    norm = word.lower().replace("ʼ", "ʻ").replace("'", "ʻ")
    try:
        return _ORDINAL_CANON.index(norm)
    except ValueError:
        return None


# "ikkinchi — toʻrtinchi qismlarida" (parts two through four) -- the dash-
# RANGE sub-form of the same gap RE_QISM_MULTI's list form above fixed
# (see its own comment); a genuinely different shape, not reachable by
# extending that regex's comma/"va" alternation. Anchored the same way, at
# the start of the post-modda tail through one optional leading comma, so
# it can never fire on the different-article list shape RE_QISM_BLOCK
# guards against. Measured 2026-10-21 against real anchor-window output
# (mirroring extract()'s own scan, not a raw corpus-wide regex grep, which
# overcounts wildly -- "qism"/"band" are ordinary Uzbek words, e.g. "harbiy
# qism" (military unit) or a resolution's own numbered "band" list items):
# exactly 7 in-scope citations corpus-wide (rows 21303, 25801, 26169, 41003,
# 43296, 46794, 46898 -- precisely the 7 the 2026-10-18 entry scoped and
# deferred; two of them only resolve once the "FK" alias anchor is in play,
# not just "Fuqarolik kodeksi"). Only ordinal endpoints are handled -- no
# digit-range form ("3 — 5-qismlari") appears in-scope anywhere in the
# corpus, so none is built here.
RE_QISM_RANGE = re.compile(
    r"^\s*,?\s*(?P<lo>" + "|".join(ORDINALS) + r")"
    r"\s*[-–—]\s*"
    r"(?P<hi>" + "|".join(ORDINALS) + r")"
    r"\s*-?\s*(?P<unit>qism|band)",
    re.IGNORECASE,
)


def _qism_range(tail: str) -> list[str] | None:
    """Ordinal RANGE sub-form (see RE_QISM_RANGE). Expands via each
    ordinal's position in _ORDINAL_CANON, the same way _expand() expands a
    numeric article range -- a lookup, not a new numbering scheme. Returns
    None (defer to the single-match path, unchanged) when the range is
    reversed or either endpoint doesn't resolve to a known ordinal."""
    m = RE_QISM_RANGE.match(tail)
    if not m:
        return None
    lo, hi = _ordinal_index(m.group("lo")), _ordinal_index(m.group("hi"))
    if lo is None or hi is None or lo > hi:
        return None
    unit = m.group("unit").lower()
    return [f"{_ORDINAL_CANON[i]} {unit}" for i in range(lo, hi + 1)]
# The Code's OWN bibliographic/publication-record parenthetical, when it sits
# immediately after the anchor -- e.g. "Fuqarolik kodeksi (Oʻzbekiston
# Respublikasi Oliy Majlisining Axborotnomasi, 1996-yil, 2-songa ilova; ...
# 1997-yil, № 2, 56-modda, № 9, 241-modda) 292-moddasiga muvofiq". The
# parenthetical's own gazette-item locators ("56-modda") are themselves
# RE_CLAUSE matches, and the very first one's gap contains "Axborotnomasi" --
# RE_STOP's deliberately whole-window `break` (see the "break-vs-continue"
# backlog note) then discards the REAL citation that follows the closing
# paren too, not just the gazette-locator false match. Measured 2026-09-29:
# 9 rows corpus-wide lose their Code citation entirely this way. Deliberately
# scoped to ONLY a parenthetical that starts right at the anchor (mirroring
# exactly the measured shape) and that is itself balanced (no nested parens,
# so a clause match starting inside an unclosed paren is never exposed) --
# an "axborotnoma"/"№" mention anywhere else in the window still triggers the
# full, conservative break, since that's different, unmeasured territory
# (the citing act's own gazette record vs. some other act just being named).
RE_LEADING_PUB_PAREN = re.compile(
    r"^\s*\((?P<body>[^()]*(?:[Aa]xborotnoma|[Vv]edomosti|to[ʻ']?plam|№)[^()]*)\)"
)

# "<N>-bobining 1 (“title”), 7-paragraflari (“title”)" -- a LIST of paragraf
# numbers after a single chapter, each optionally carrying its own short
# parenthetical title, same as RE_CLAUSE's own top-level `nums` group already
# allows for modda/bob/paragraf lists (see its own comment above) -- this is
# the identical grammar one level deeper: the chapter+section lookahead below
# used to accept only ONE bare digit immediately before "paragraf" ("3-paragrafi"),
# so a list of two-or-more paragraf numbers for the same chapter silently
# downgraded to a bare chapter citation, losing every section in the list, not
# just the grain of a single one (same failure class as the already-recorded
# "paragrif"/Roman-chapter-lookahead/section-mark known_gaps, but affecting a
# LIST rather than a single item). Found 2026-11-09 via the signature-stratified
# gold sampler (batch 19, gold_id 23/row 41009): "Fuqarolik kodeksi 29-bobining
# 1 (“Oldi-sotdi toʻgʻrisida umumiy qoidalar”), 7-paragraflari (“Koʻchmas mulkni
# sotish”), 30 (“Ayirboshlash”) va 31-boblari (“Hadya”)" -- chapter 29's own
# paragraf 1 and paragraf 7 both vanished entirely (not even downgraded to one
# bare chapter-29 citation per paragraf -- a single bare chapter 29 total),
# while chapters 30/31 (plain list items, not a paragraf list) were already
# handled correctly by the existing list support. Measured corpus-wide: the
# widened lookahead (100 chars, not 30, to fit a title) changes the match/
# no-match outcome in exactly 4 rows (41009, plus a second distinct citation
# duplicated across 41010/41012, plus a third, 25634) -- re-ran the OLD
# 30-char/single-digit lookahead against every "bob" match corpus-wide and
# diffed against this new one: zero other rows change at all, so widening is
# purely additive, not a new false-positive source. Reuses _expand() for the
# actual list/range parsing (strips the parenthetical, splits on comma/va,
# expands a dash range) -- the exact same proven logic RE_CLAUSE's own `nums`
# group already relies on, not a new parsing path.
#
# The separator before "paragraf"/"paragrif" accepts a bare space, not just a
# hyphen, same space-vs-hyphen tolerance RE_CLAUSE's own unit separator has
# had since 2026-09-15 -- this lookahead was never updated to match. Found
# 2026-09-15 (row 42566, "22-bobining 2 paragrafi"), left as a known_gap for
# over two months (single-occurrence scope) and swept 2026-11-15: still
# exactly 1 corpus-wide occurrence (gold_id 341), fixed alongside the other
# known_gap items below since all are the same class of additive separator/
# notation tolerance with no shared code path to collide on.
RE_SECTION_LIST = re.compile(
    r"\s*,?\s*(?P<nums>\d+(?:\s*\([^()]{0,100}\))?"
    r"(?:\s*(?:,|va)\s*\d+(?:\s*\([^()]{0,100}\))?)*)"
    r"(?:\s*-\s*|\s+)paragr[ai]f"
)
# "9-bobi § 2" -- a "§ N" section-mark notation, semantically identical to
# "9-bobining 2-paragrafi" but naming the section with the symbol instead of
# the word "paragraf" entirely, so RE_SECTION_LIST's own literal match never
# fires. Found 2026-10-04 (row 41858), recorded as known_gap gold_id 324 at a
# measured single in-scope occurrence (one other raw "§" match, row 35993,
# belongs to a different document's own internal Rules, never inside a Civil
# Code anchor window). Swept 2026-11-15 as its own narrow regex rather than
# folded into RE_SECTION_LIST: the surface grammar has no list/parenthetical
# form in the corpus today (unlike the word form), so a single bare digit
# after "§" is all that's needed -- deliberately not sharing RE_SECTION_LIST's
# richer list grammar until a real "§ N va M" occurrence is ever found.
RE_SECTION_MARK = re.compile(r"\s*,?\s*§\s*(?P<num>\d+)")


@dataclass
class Citation:
    """One resolved reference to a Civil Code provision."""
    target_kind: str            # 'article' | 'chapter' | 'section' | 'part' | 'act'
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


RE_RANGE_PAIR = re.compile(r"^(\d+)\s*[-–—]+\s*(\d+)$")


def _expand(nums: str) -> tuple[list[str], str]:
    """'299 — 310' -> range, '10, 24, 39' -> list, '14' -> single.

    A top-level comma/va-separated item can itself be a dash-joined sub-range
    ('393-395' inside '393-395, 399, 402, 408, 412') — a compact list style
    LexUZ uses alongside the plain whole-clause range ('299 — 310'). Each such
    item is expanded on its own, same 200-wide malformed-range guard as the
    whole-clause case; a comma/va list is otherwise unaffected. Measured
    2026-09-15 (see DAILY_REVIEW.md): 11 clauses corpus-wide had at least one
    such sub-range, previously silently truncated to just its two endpoints
    (or, when the sub-range came first, losing the rest of the list too — the
    fixed unit separator couldn't even be reached).
    """
    nums_bare = re.sub(r"\s*\([^()]{0,100}\)", "", nums)
    # "hamda" splits the same as "va"/"," -- see RE_CLAUSE's own comment on
    # the "hamda" conjunction above (gold_id 140).
    top_items = [p for p in re.split(r"\s*(?:,|va|hamda)\s*", nums_bare) if p.strip()]
    values: list[str] = []
    single_range = False
    for item in top_items:
        m = RE_RANGE_PAIR.match(item)
        if not m:
            values.append(item)
            continue
        lo, hi = int(m.group(1)), int(m.group(2))
        if 0 < hi - lo <= 200:  # guard against a malformed pair
            values.extend(str(n) for n in range(lo, hi + 1))
            single_range = len(top_items) == 1
        else:
            values.extend((m.group(1), m.group(2)))
    return values, ("range" if single_range else "list" if len(values) > 1 else "single")


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


def _blank_naming_parens(text: str) -> str:
    """Replace every self-naming '(... deb yuritiladi/ataladi)' parenthetical
    with spaces of the same length, so neither a spurious anchor nor a
    RE_STOP trigger word can be read out of its body, while every later
    offset into the result still lines up with the untouched original text
    (same length-preserving-blank technique RE_LEADING_PUB_PAREN already
    uses on a single leading paren, applied corpus-wide up front instead of
    per-window). The ORIGINAL `text` -- not this blanked copy -- is still
    what `_evidence()` slices, so the naming clause remains visible,
    verbatim, in the evidence snippet shown to a reader; only the SCANNING
    (anchor-finding, RE_CLAUSE/RE_STOP matching) is done against the blanked
    copy. See RE_NAMING_PAREN's own comment for why a naive "just drop the
    spurious anchor" fix (tried first, reverted 2026-11-18) isn't enough:
    blanking the anchor's match alone still leaves "kodeksi" sitting in the
    real anchor's own window gap, which RE_STOP's bare "kodeksi" alternative
    then reads as a different-code announcement and wrongly discards the
    rest of the window.
    """
    out = text
    for m in RE_NAMING_PAREN.finditer(text):
        out = out[:m.start()] + " " * len(m.group(0)) + out[m.end():]
    return out


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
            is_the_code: bool = False, doc_type: str | None = None) -> list[Citation]:
    if not text:
        return []
    out: list[Citation] = []

    def _is_stop(s: str) -> bool:
        # Bare/"ushbu/mazkur/shu" "kodeksning" only means "a different code is
        # being named" when the citing act genuinely has a code of its own
        # (`doc_type == "code"`) or the caller hasn't told us `doc_type` at
        # all (`None`, the conservative old-behavior default) -- UNLESS a
        # "<subject> toʻgʻrisidagi" qualifier right before it already names a
        # specific different code explicitly, which always stops regardless
        # of `doc_type`. See RE_STOP_KODEKSNING's own comment for the full
        # reasoning and the corpus-wide measurement.
        if RE_STOP.search(s) or RE_STOP_ABBR.search(s):
            return True
        m = RE_STOP_KODEKSNING.search(s)
        if not m:
            return False
        if RE_ACT_QUALIFIER.search(s[:m.start()]):
            return True
        return doc_type is None or doc_type == "code"

    # Scan against a naming-paren-blanked copy (see _blank_naming_parens);
    # `text` itself stays untouched so `_evidence()` can still show the
    # genuine, unblanked source text to a reader.
    scan_text = _blank_naming_parens(text)
    anchors = _anchors(scan_text, allow_fk_alias=allow_fk_alias, is_the_code=is_the_code)

    for i, (a_start, a_end, kind) in enumerate(anchors):
        # Never scan past the next anchor: its numbers belong to it.
        hard_limit = anchors[i + 1][0] if i + 1 < len(anchors) else len(text)
        limit = min(a_end + WINDOW, hard_limit)
        window = scan_text[a_end:limit]

        pub_paren = RE_LEADING_PUB_PAREN.match(window)
        if pub_paren:
            # Blank it out in place (same length) so every later offset into
            # `window` -- and hence abs_start/abs_end into the untouched
            # `text` -- stays correct.
            window = window[:pub_paren.start()] + " " * len(pub_paren.group(0)) + window[pub_paren.end():]

        consumed_to = 0
        produced = False
        for m in RE_CLAUSE.finditer(window):
            # A different act named before this clause claims it instead.
            gap = window[consumed_to:m.start()]
            if _is_stop(gap):
                break
            unit = m.group("unit").lower()
            nums, listing = _expand(m.group("nums"))
            abs_start, abs_end = a_end + m.start(), a_end + m.end()

            if unit == "modda":
                # Qism/band tail-window truncation (found 2026-09-04, see
                # DAILY_REVIEW.md Backlog): `window` is itself already capped
                # at `limit` (a_end+WINDOW, or the next anchor -- whichever
                # comes first), so re-slicing `window[m.end():m.end()+60]`
                # silently shortens to fewer than 60 chars whenever a modda
                # match lands close to that cap, dropping a qism/band clause
                # that sits just past it even though it's well within 60 raw
                # chars of the match and still before the next anchor. Slice
                # from `text` directly instead, bounded by `hard_limit` (the
                # next anchor's own start, never WINDOW) -- the same fix this
                # project's own backlog note proposed. Measured corpus-wide
                # before shipping: 8 real qism/band attachments recovered,
                # zero collateral change (see DAILY_REVIEW.md).
                tail = scan_text[abs_end: min(abs_end + 60, hard_limit)]
                suffix = m.group("suffix").lower()
                if suffix.startswith("sining"):
                    qms = _qism_list(tail) or _qism_range(tail)
                    if qms is None:
                        qm = RE_QISM.search(tail)
                        qms = [qm.group(0).strip() if qm else None]
                elif len(nums) == 1:
                    # Not the genitive "moddasining" form (e.g. bare "moddasi",
                    # "moddasiga muvofiq") — still attach a qism/band if one
                    # immediately follows, but only when nothing between here
                    # and there suggests it belongs to a different citation.
                    qms = _qism_list(tail) or _qism_range(tail)
                    if qms is None:
                        cand = RE_QISM.search(tail)
                        qm = cand if cand and not RE_QISM_BLOCK.search(tail[:cand.start()]) else None
                        qms = [qm.group(0).strip() if qm else None]
                else:
                    qms = [None]
                for n in nums:
                    for q in qms:
                        out.append(Citation("article", n, None, None, q,
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
                #
                # "paragr[ai]f" (not a bare "paragraf" literal): row 46605 spells
                # it "paragrifi" twice ("65-bobining 1-paragrifi", "65-bobi
                # 1-paragrifi") -- a genuine LexUZ spelling variant, not a typo
                # unique to this row's own two occurrences (measured 2026-11-02,
                # see DAILY_REVIEW.md: gold batch 17, gold_id 25). Without this,
                # the match below fails, the citation silently downgrades from
                # "chapter 65, section 1" to just "chapter 65", losing the
                # paragraph. The only other corpus-wide "paragrif" occurrence
                # (row 25664) cites a Nizom, not the Code or itself, so it's
                # outside any anchor's scan window regardless.
                sec = RE_SECTION_LIST.match(window[m.end(): m.end() + 150])
                # The "§ N" notation (see RE_SECTION_MARK above) is tried only
                # when the word form didn't match -- the two surface forms
                # never co-occur on the same citation, so this is a pure
                # fallback, not a competing match.
                mark = None if sec else RE_SECTION_MARK.match(window[m.end(): m.end() + 150])
                # When the paragraf lookahead itself is a list/range ("1 va
                # 2-paragraflari"), the resulting citations' own `listing`
                # must describe THAT list, not the (usually single) chapter
                # number in front of it -- gold_id 148 (row 25634) expects
                # listing="list" for both sections, not the chapter's own
                # "single". Only overridden when sec actually matched; the
                # bare-chapter fallback keeps the chapter-level `listing`
                # exactly as before.
                if sec:
                    secs, sec_listing = _expand(sec.group("nums"))
                elif mark:
                    secs, sec_listing = [mark.group("num")], listing
                else:
                    secs, sec_listing = [None], listing
                for n in nums:
                    for s in secs:
                        out.append(Citation("section" if (sec or mark) else "chapter", None, int(n),
                                            int(s) if s is not None else None, None,
                                            kind, sec_listing, abs_start, abs_end,
                                            _evidence(text, abs_start, abs_end)))
            else:  # a bare "N-paragrafi" without its chapter is not resolvable
                continue

            produced = True
            consumed_to = m.end()

        found_arabic = produced  # snapshot before the independent part-scan below

        # Part-level ("V boʻlimi") citations, scanned independently of the
        # Arabic modda/bob/paragraf loop above rather than gated on `produced`
        # the way the Roman-chapter fallback below is: unlike a roman chapter
        # (only ever tried as a fallback when nothing else matched), a part
        # citation can sit BEFORE an already-matched clause in the same window
        # ("Fuqarolik kodeksi III-boʻlimining ... va 927-moddasi") as well as
        # after one ("23-bobi ... hamda V boʻlimiga") — so this always scans
        # the whole window from its own start, same convention as the
        # Roman-chapter fallback uses for its own stop-word gate.
        for m in RE_ROMAN_PART.finditer(window):
            if _is_stop(window[:m.start()]):
                break
            if (num := _roman(m.group("r1"))) is not None:
                abs_start, abs_end = a_end + m.start(), a_end + m.end()
                out.append(Citation("part", None, num, None, None, kind, "single",
                                    abs_start, abs_end, _evidence(text, abs_start, abs_end)))
                produced = True

        # Arabic-digit "boʻlim" (see RE_ARABIC_BOLIM above) -- a chapter, not
        # a Part, despite sharing the unit word with RE_ROMAN_PART just
        # above. Same unconditional-scan convention as that loop, for the
        # same reason (a chapter citation can sit on either side of an
        # already-matched clause in the same window).
        for m in RE_ARABIC_BOLIM.finditer(window):
            if _is_stop(window[:m.start()]):
                break
            abs_start, abs_end = a_end + m.start(), a_end + m.end()
            out.append(Citation("chapter", None, int(m.group("num")), None, None, kind, "single",
                                abs_start, abs_end, _evidence(text, abs_start, abs_end)))
            produced = True

        if not found_arabic:
            # Chapters cited in Roman numerals; only worth trying when no Arabic
            # clause was found, so "30-bobi" never re-enters here.
            for m in RE_ROMAN_CHAPTER.finditer(window):
                if RE_STOP.search(window[:m.start()]) or RE_STOP_ABBR.search(window[:m.start()]):
                    break
                abs_start, abs_end = a_end + m.start(), a_end + m.end()
                # Roman-numeral chapters never got the paragraf/section
                # lookahead the Arabic "bob" branch above has had all along
                # (gold_id 123, "Fuqarolik kodeksi IV bobining 2 paragrafi" --
                # found 2026-09-25, swept 2026-11-15, same 1-occurrence scope
                # as the other items swept alongside it). Only tried for a
                # single roman numeral (no `r2`): a section lookahead after a
                # TWO-chapter roman list has no measured corpus occurrence to
                # confirm which chapter the section would even belong to, so
                # the list form is left exactly as before.
                sec = mark = None
                if not m.group("r2"):
                    sec = RE_SECTION_LIST.match(window[m.end(): m.end() + 150])
                    if not sec:
                        mark = RE_SECTION_MARK.match(window[m.end(): m.end() + 150])
                if sec:
                    secs, sec_listing = _expand(sec.group("nums"))
                elif mark:
                    secs, sec_listing = [mark.group("num")], "single"
                else:
                    secs = None
                for g in ("r1", "r2"):
                    if (num := _roman(m.group(g) or "")) is not None:
                        if secs is not None and g == "r1":
                            for s in secs:
                                out.append(Citation("section", None, num,
                                                    int(s) if s is not None else None, None,
                                                    kind, sec_listing, abs_start, abs_end,
                                                    _evidence(text, abs_start, abs_end)))
                        else:
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
        # a LIST of paragraf numbers for one chapter, each carrying its own
        # short parenthetical title (real corpus phrasing, row 41009,
        # 2026-11-09 -- see DAILY_REVIEW.md): both paragraf 1 and paragraf 7
        # of chapter 29 must be found, not just one bare chapter-29 citation
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksi 29-bobining 1 "
         "(“Oldi-sotdi toʻgʻrisida umumiy qoidalar”), 7-paragraflari "
         "(“Koʻchmas mulkni sotish”) va 31-boblari (“Hadya”).", {},
         [("section", None, "list"), ("section", None, "list"), ("chapter", None, "single")]),
        # Part-level ("boʻlim") citations, both the hyphen and the bare-space
        # forms, and both apostrophe-like spellings LexUZ uses for the vowel
        # (real corpus phrasings, 2026-10-02 — see DAILY_REVIEW.md)
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining V-boʻlimi.", {},
         [("part", None, "single")]),
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining IV boʻlimi.", {},
         [("part", None, "single")]),
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining VI bo'limi.", {},
         [("part", None, "single")]),
        # a part citation appearing AFTER an already-matched chapter clause in
        # the same window (real corpus phrasing, row 38614) must still be
        # found, not silently skipped because the modda/bob loop already
        # set `produced`
        ("Fuqarolik kodeksining 50-moddasi, 23-bobi hamda V boʻlimiga qarang.", {},
         [("article", "50", "single"), ("chapter", None, "single"), ("part", None, "single")]),
        # a part citation appearing BEFORE a later article clause in the same
        # window (real corpus phrasing, row 32449) must also still be found
        ("Fuqarolik kodeksi III-boʻlimining 2-kichik boʻlimi va 927-moddasi.", {},
         [("article", "927", "single"), ("part", None, "single")]),
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
        # "kodeksning" (genitive without "-i-") naming a different code by role
        # must stop the scan just like "kodeksining" already does (2026-09-15)
        ("Fuqarolik kodeksining 166-moddasi, Maʼmuriy javobgarlik toʻgʻrisidagi "
         "kodeksning 60, 61-moddalari.", {}, [("article", "166", "single")]),
        # "mazkur Kodeksning" inside some OTHER code's own text means that code,
        # not the Civil Code — is_the_code=False here, so it must stop the scan
        # rather than being read as a self-reference to the Code just cited
        ("Fuqarolik kodeksining 31, 32-moddalari, mazkur Kodeksning 36-moddasi.",
         {}, [("article", "31", "list"), ("article", "32", "list")]),
        # control: "mazkur Kodeksning" still resolves as a real self-reference
        # anchor (not stopped) when the citing act genuinely IS the Code
        ("Fuqarolik kodeksining 14-moddasi. mazkur Kodeksning 20-moddasi.",
         {"is_the_code": True},
         [("article", "14", "single"), ("article", "20", "single")]),
        # gold_id 587 (row 19636): bare "Kodeksning" directly after the Code's
        # own name, with no other code named and no demonstrative, is LexUZ
        # redundantly restating the Civil Code, not announcing a different
        # one -- but only when the CITING act has no code of its own to mean
        # ("doc_type='law'"). Must NOT stop the scan here.
        ("Oʻzbekiston Respublikasining Fuqarolik kodeksi Kodeksning 53-moddasi.",
         {"doc_type": "law"}, [("article", "53", "single")]),
        # control: the exact same bare "Kodeksning" shape still stops the scan
        # when the citing act genuinely IS some other code (doc_type='code',
        # row 21291) -- matches the already-tested "mazkur Kodeksning" design
        # above, and the conservative no-doc_type default (old behavior) below.
        ("Oʻzbekiston Respublikasining Fuqarolik kodeksi Kodeksning 53-moddasi.",
         {"doc_type": "code"}, [("act", None, "single")]),
        ("Oʻzbekiston Respublikasining Fuqarolik kodeksi Kodeksning 53-moddasi.",
         {}, [("act", None, "single")]),
        # row 29029: a "<subject> toʻgʻrisidagi kodeksning" qualifier names a
        # SPECIFIC other code (Administrative Liability) right before bare
        # "kodeksning" -- must still stop unconditionally, even with the same
        # doc_type='law' as the gold_id 587 bug above. Caught by the full
        # corpus-wide diff before shipping the doc_type-only first attempt.
        ("Fuqarolik kodeksining 166-moddasi, Oʻzbekiston Respublikasi Maʼmuriy "
         "javobgarlik toʻgʻrisidagi kodeksning 60, 61-moddalari.",
         {"doc_type": "law"}, [("article", "166", "single")]),
        # row 11208/41405: "ushbu Kodeksning" continuing an EARLIER Civil Code
        # citation in the same window, with ordinary prose (no act qualifier)
        # in between, must also NOT stop when doc_type has no code of its own
        # -- found via the same corpus-wide diff, not previously in the gold
        # set (a bonus recall fix alongside gold_id 587).
        ("Fuqarolik kodeksining 166-moddasiga koʻra ham mulkdorning huquqi cheklanadi. "
         "Ushbu Kodeksning 197-moddasiga muvofiq mulk huquqi toʻxtatiladi.",
         {"doc_type": "constitution"},
         [("article", "166", "single"), ("article", "197", "single")]),
        # a plain space instead of a hyphen before modda/bob/paragraf, real
        # corpus phrasings (2026-09-15)
        ("Fuqarolik kodeksining 49 moddasi.", {}, [("article", "49", "single")]),
        # "hamda" ("as well as") is a recognized list conjunction alongside
        # comma/va, same class as the space-vs-hyphen separator above (gold_id
        # 140, found 2026-09-15, fixed 2026-11-15 -- see DAILY_REVIEW.md): all
        # three articles must survive, not just the one touching "moddalari".
        ("Fuqarolik kodeksining 11-12 hamda 14 moddalari.", {},
         [("article", n, "list") for n in ("11", "12", "14")]),
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksi 40 bobi.", {},
         [("chapter", None, "single")]),
        # an ASCII-hyphen sub-range packed into a list, real corpus phrasing
        # (2026-09-15): "393-395" must expand, not collapse to two endpoints
        # or (worse) block the rest of the list from ever being reached
        ("ushbu Kodeksning 393-395, 399, 402, 408, 412-moddalarida", {"is_the_code": True},
         [("article", str(n), "list") for n in (393, 394, 395, 399, 402, 408, 412)]),
        # the malformed-range guard still rejects a too-wide sub-range, same
        # as the whole-clause case (row 1390's documented residual)
        ("Fuqarolik kodeksining 173 – 1737-moddalari", {},
         [("article", "173", "list"), ("article", "1737", "list")]),
        # a doubled en-dash ("744 –– 748", two literal en-dashes, no space
        # between them) must still expand the full range, not just its
        # trailing endpoint (real corpus phrasing, 2026-09-17)
        ("Oʻzbekiston Respublikasi Fuqarolik kodeksining 744 –– 748-moddalari.", {},
         [("article", str(n), "range") for n in range(744, 749)]),
        # "Fuqarolik kodeksning" (missing the "-i-" thematic vowel: kodeks+ning,
        # as opposed to kodeksi+ning) must still anchor as the Civil Code
        # itself, not be dropped entirely (real corpus phrasing, 2026-09-17)
        ("Oʻzbekiston Respublikasi Fuqarolik Kodeksning 260 –– 263-moddalari.", {},
         [("article", str(n), "range") for n in range(260, 264)]),
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
        # ONE modda carrying several qism/band ordinals at once -- comma-
        # separated ("birinchi, ikkinchi qismlari") and "va"-separated
        # ("oltinchi va yettinchi qismlarida") both mean every listed part
        # belongs to THIS article, not a list of different articles (measured
        # 2026-10-18, see DAILY_REVIEW.md: 63 real corpus-wide citations).
        ("Fuqarolik kodeksining 497-moddasi birinchi, ikkinchi qismlari", {},
         ["birinchi qism", "ikkinchi qism"]),
        ("ushbu Kodeksning 377-moddasining oltinchi va yettinchi qismlarida",
         {"is_the_code": True}, ["oltinchi qism", "yettinchi qism"]),
        ("Fuqarolik kodeksi 175-moddasining birinchi, ikkinchi, uchinchi, "
         "beshinchi va oltinchi qismlarida", {},
         ["birinchi qism", "ikkinchi qism", "uchinchi qism", "beshinchi qism",
          "oltinchi qism"]),
        # the different-article shape must still resolve exactly as before:
        # a real "N-moddasi" between the first number and the trailing qism
        # blocks the multi-qism read, falling through to the old single/gate
        # logic unchanged (regression guard for the new regex).
        ("mazkur Kodeksning 185-moddasi, 186-moddasi toʻqqizinchi qismi",
         {"is_the_code": True}, [None, "toʻqqizinchi qism"]),
        # The dash-RANGE sub-form of the same gap -- "ikkinchi -- toʻrtinchi
        # qismlarida" means parts two THROUGH four, not just the two named
        # endpoints (measured 2026-10-21, see DAILY_REVIEW.md: 7 real
        # corpus-wide citations, all three dash spellings below). Covers
        # both the "-sining" genitive path and the bare "-moddasi" path
        # (len(nums) == 1) that share this logic.
        ("Fuqarolik kodeksining 476-moddasining uchinchi-beshinchi qismlari", {},
         ["uchinchi qism", "toʻrtinchi qism", "beshinchi qism"]),
        ("Fuqarolik kodeksining 216-moddasining birinchi — uchinchi qismlari", {},
         ["birinchi qism", "ikkinchi qism", "uchinchi qism"]),
        ("Fuqarolik kodeksi 382-moddasi ikkinchi – toʻrtinchi qismlari", {},
         ["ikkinchi qism", "uchinchi qism", "toʻrtinchi qism"]),
        # a reversed range (hi before lo) isn't a valid range -- falls
        # through to the old single-match behavior unchanged, same as any
        # other text RE_QISM_RANGE doesn't recognize.
        ("Fuqarolik kodeksining 1-moddasining beshinchi — uchinchi qismlari", {},
         ["uchinchi qism"]),
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
        # "qonunning" (genitive without the "-i-" vowel, e.g. "...gi Qonunning
        # N-moddasi") is a distinct surface form from "qonunining", not caught
        # by the bare case-sensitive "Qonun" rule above either — measured gap,
        # see DAILY_REVIEW.md 2026-09-12 (131 real misattributions corpus-wide,
        # both this capitalized form and the lowercase one right below).
        ('Fuqarolik kodeksiga muvofiq, “Sudlar toʻgʻrisida”gi Qonunning 47-moddasiga asosan',
         {}, [("act", None, "single")]),
        # LexUZ often leaves it lowercase even for a specific, quoted act title;
        # the real Code citation earlier in the same window must still survive.
        ('Fuqarolik kodeksining 1048-moddasi, “Mualliflik huquqi toʻgʻrisida”gi '
         "qonunning 13-moddasi bilan tartibga solinadi", {},
         [("article", "1048", "single")]),
        # bare lowercase "qonun" immediately followed by a "(N-modda)" shorthand
        # names that OTHER act's own article, not the Code's — real corpus
        # phrasing (2026-09-25, row 6071): must stop before the parenthetical
        # number, distinct from (and much narrower than) the already-rejected
        # blanket bare-lowercase-"qonun" stop.
        ("FKning 60-bobi, “Mualliflik huquqi toʻgʻrisida”gi qonun (35-modda) asosida",
         {"allow_fk_alias": True}, [("chapter", None, "single")]),
        # a "yoʻriqnoma" (instruction/guideline) named later in the window
        # owns its own roman-numeral "boʻlim" — must not be misattributed to
        # the Code as a part-level citation (real corpus phrasing, row 42566,
        # found 2026-10-02 while building part-level support; see
        # DAILY_REVIEW.md). The "22-bobining 5 paragrafi" clause itself is
        # the exact space-separator shape gold_id 341 recorded as a known_gap
        # (found 2026-09-15, the real row 42566 text reads "...2 paragrafi",
        # not "5" — this case predates that discovery and never got updated
        # to use the real number) and swept 2026-11-15: now correctly
        # resolves to chapter 22 section 5, not a bare chapter.
        ("Fuqarolik kodeksi 22-bobining 5 paragrafi va “Bojxona toʻlovlarini "
         "toʻlash muddatlarini uzaytirish”ning yoʻriqnomaning IV boʻlimi.", {},
         [("section", None, "single")]),
    ]
    for text, kwargs, expected in stop_cases:
        got = [(c.target_kind, c.article, c.listing) for c in extract(text, **kwargs)]
        want = [(k, a, l) for k, a, l in expected]
        if got != want:
            failures += 1
            print(f"FAIL(stop) {text[:64]!r}\n     got  {got}\n     want {want}")
    # A publication-record parenthetical right after the anchor is the
    # Code's OWN bibliographic citation, not another act being named -- must
    # NOT trigger RE_STOP's whole-window break, real corpus phrasing
    # (2026-09-29, 9 rows corpus-wide): the real article after the closing
    # paren must still be found, even when the parenthetical itself contains
    # several gazette-item "N-modda" locators that would otherwise look like
    # (and, before this fix, break scanning as) real clauses.
    pub_paren_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Fuqarolik kodeksining (Oʻzbekiston Respublikasi Oliy Majlisining "
         "Axborotnomasi, 1996-y., 2-songa ilova) 292-moddasiga muvofiq", {},
         [("article", "292", "single")]),
        ("Fuqarolik kodeksi (Oʻzbekiston Respublikasi Oliy Majlisining "
         "Axborotnomasi, 1996-yil, 2-songa ilova; № 11-12; 1997-yil, № 2, "
         "56-modda, № 9, 241-modda) 1015-moddasining uchinchi qismidagi",
         {}, [("article", "1015", "single")]),
        # a leading paren that's the "bundan buyon matnda FK deb yuritiladi"
        # alias declaration (no pub-record signal) must be left alone --
        # not this fix's concern, and RE_CLAUSE never matches inside it anyway.
        ("Fuqarolik kodeksi (bundan buyon matnda FK deb yuritiladi) 99-moddasi",
         {}, [("article", "99", "single")]),
    ]
    for text, kwargs, expected in pub_paren_cases:
        got = [(c.target_kind, c.article, c.listing) for c in extract(text, **kwargs)]
        want = [(k, a, l) for k, a, l in expected]
        if got != want:
            failures += 1
            print(f"FAIL(pub_paren) {text[:64]!r}\n     got  {got}\n     want {want}")
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

    # "paragrif" spelling variant (real corpus text, row 46605, both its
    # occurrences -- found 2026-11-02, gold batch 17 gold_id 25; see
    # DAILY_REVIEW.md): must resolve to "section", same as the "paragraf"
    # spelling, not silently downgrade to a bare "chapter".
    paragrif_cases: list[tuple[str, dict, list[tuple]]] = [
        ("mazkur Kodeksning 65-bobining 1-paragrifi, “Firma nomlari”", {},
         [(65, 1)]),
        ("mazkur Kodeksning 65-bobi 1-paragrifi, “Firma nomlari”", {},
         [(65, 1)]),
    ]
    for text, kwargs, expected in paragrif_cases:
        got = [(c.struct_number, c.section_number) for c in extract(text, is_the_code=True, **kwargs)
               if c.target_kind in ("chapter", "section")]
        if got != expected:
            failures += 1
            print(f"FAIL(paragrif) {text[:64]!r}\n     got  {got}\n     want {expected}")

    # "§ N" section-mark notation (real corpus phrasing, row 41858, found
    # 2026-10-04, known_gap gold_id 324, swept 2026-11-15): semantically the
    # same as "9-bobining 2-paragrafi" but naming the section with the
    # symbol, not the word.
    section_mark_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Fuqarolik kodeksining 9-bobi § 2", {}, [(9, 2)]),
    ]
    for text, kwargs, expected in section_mark_cases:
        got = [(c.struct_number, c.section_number) for c in extract(text, **kwargs)
               if c.target_kind in ("chapter", "section")]
        if got != expected:
            failures += 1
            print(f"FAIL(section_mark) {text[:64]!r}\n     got  {got}\n     want {expected}")

    # A Roman-numeral chapter never got the same paragraf/section lookahead
    # the Arabic "bob" branch has always had (real corpus phrasing, row
    # 15441, found 2026-09-25, known_gap gold_id 123, swept 2026-11-15).
    roman_section_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Fuqarolik kodeksi IV bobining 2 paragrafi", {}, [("section", 4, 2)]),
        # a roman-numeral chapter LIST ("IV va V bobi") has no measured
        # corpus occurrence paired with a section lookahead -- must still
        # resolve as a bare chapter list, not attempt the lookahead at all.
        ("Fuqarolik kodeksi IV va V bobi", {}, [("chapter", 4, None), ("chapter", 5, None)]),
    ]
    for text, kwargs, expected in roman_section_cases:
        got = [(c.target_kind, c.struct_number, c.section_number) for c in extract(text, **kwargs)
               if c.target_kind in ("chapter", "section")]
        if got != expected:
            failures += 1
            print(f"FAIL(roman_section) {text[:64]!r}\n     got  {got}\n     want {expected}")

    # Arabic-digit "boʻlim" names a CHAPTER, not a roman-numeral Part (real
    # corpus phrasing, row 32903, found 2026-10-30, known_gap gold_id 618,
    # swept 2026-11-15).
    arabic_bolim_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Fuqarolik kodeksining 40-boʻlimi (“Transport ekspeditsiyasi”)", {},
         [("chapter", 40)]),
        # the roman-numeral Part form must still resolve as 'part', not be
        # swallowed by the new digit-only regex.
        ("Fuqarolik kodeksining V-boʻlimi.", {}, [("part", 5)]),
    ]
    for text, kwargs, expected in arabic_bolim_cases:
        got = [(c.target_kind, c.struct_number) for c in extract(text, **kwargs)
               if c.target_kind in ("chapter", "part")]
        if got != expected:
            failures += 1
            print(f"FAIL(arabic_bolim) {text[:64]!r}\n     got  {got}\n     want {expected}")

    # "hamda" with NOTHING before it already covered by the main `cases` list
    # above (row 24219 shape) -- this is the OTHER shape the 2026-09-15 note
    # originally worried about hypothetically ("hamda"-joined, nothing after
    # the second number but the unit word itself), confirmed fixed the same
    # way (gold_id 140, swept 2026-11-15).
    hamda_cases: list[tuple[str, dict, list[tuple]]] = [
        ("Fuqarolik kodeksining 14 hamda 20-moddasi", {},
         [("article", "14", "list"), ("article", "20", "list")]),
    ]
    for text, kwargs, expected in hamda_cases:
        got = [(c.target_kind, c.article, c.listing) for c in extract(text, **kwargs)
               if c.target_kind == "article"]
        if got != expected:
            failures += 1
            print(f"FAIL(hamda) {text[:64]!r}\n     got  {got}\n     want {expected}")

    total = (len(cases) + len(qism_cases) + len(stop_cases) + len(pub_paren_cases) + len(docid_cases)
             + len(section_comma_cases) + len(paragrif_cases) + len(section_mark_cases)
             + len(roman_section_cases) + len(arabic_bolim_cases) + len(hamda_cases))
    print(f"{total - failures}/{total} extractor self-tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(_selftest())
