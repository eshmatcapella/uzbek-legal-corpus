# Daily review log

Purpose: a standing, self-directed R&D cadence for this project. Each entry is
one day's session. The brief is deliberately open — invent the approach, don't
just run a checklist. Multi-day threads are normal and expected; a thread stays
"active" until it resolves, not until a calendar day ends.

How to use this file each session:
1. Read "Active threads" below. Continue one if it's mid-flight.
2. Otherwise pull the next-highest-value item from "Backlog" (rotate across
   the three focus areas rather than draining one), or invent a new angle the
   backlog hasn't captured yet — the backlog is a floor, not a ceiling.
3. Do real work: write code, run it against corpus.duckdb, measure the result.
   A day that ends in "I looked into X" without a number, a commit, or a
   concrete artifact is a day that didn't happen.
4. Run `python verify_transfer.py` before closing out — it must stay green.
5. Append a dated entry to "Log" (below Active threads), update Active threads
   and Backlog to reflect new state, and commit with a message describing
   what changed and why.

---

## Active threads

- **Extractor recall, beyond the core forms.** 2026-09-03 measured 0 real
  misses for the article-level ("N-modda") and chapter/section-level
  ("N-bob[ining M-paragrafi]") surface forms, corpus-wide (see Log entry and
  `measure_extractor_recall.py`). Not yet covered by the same method: qism
  ("N-moddasining Mchi qismida") and band ("N-moddasining M-bandiga") forms,
  the FK-alias form, and the "ushbu/shu Kodeks" self-reference form — those
  need their own naive detectors (a qism/band naive regex is trickier since
  the ordinal-word list makes a dumb regex noisier than the modda/bob case).
  Working hypothesis: recall stays this good across the board, since all
  forms share the same anchor+window scanning logic and only the tail
  pattern differs — but that is not yet measured, so it stays a hypothesis.
  Next step: extend `measure_extractor_recall.py` with a qism/band naive
  checker (build the naive regex from `citation_extractor.ORDINALS` rather
  than hand-rolling one) and self-reference coverage restricted to
  doc_id IN (-111189, -180552). If that also comes back near-zero misses,
  the gold-set backlog item can shrink to precision only (does the extractor
  ever *misattribute* a correctly-found number — wrong target doc, wrong
  qism) rather than recall, which would be a real scope reduction worth
  writing up.

---

## Backlog

### Extractor recall/precision
- **Build the gold set.** ~50 articles, hand-verified ground truth for
  citation extraction (which acts realize them, at what confidence). No gold
  set exists yet — `citation_extractor.py`'s 22 self-tests check surface-form
  parsing, not corpus-wide recall. 2026-09-03 found the "sample where signals
  disagree" angle (below) doesn't apply cleanly — the two source fields
  disagree by design, not by extractor error — so lean on precision misses
  instead once the recall extension in Active threads finishes: sample from
  citations the extractor found but where `dst_ambiguous` or `dst_dangling`
  is true, since that's where a wrong resolution is most likely.
- ~~Measure recall against a second independent signal (`cross_references`
  vs `article_text` on the same row).~~ **Tried 2026-09-03, hypothesis
  falsified**: 4249/4272 (99.5%) of cross_references-sourced Civil Code
  article citations have no matching article_text citation on the same row —
  but manual inspection of samples shows this is because `cross_references`
  is LexUZ editorial commentary pointing at topically related provisions in
  OTHER acts (e.g. a Water Code article's footnote citing an unrelated Civil
  Code contract-law article), not a restatement of what article_text says.
  The two fields are independently informative, not redundant, so agreement
  between them isn't a validity signal. Superseded by the naive-regex method
  in the Log entry below, which found the real recall gap (zero, for the
  forms it covers).
- **Qism-level (article-part) recall.** 522 edges already carry a `dst_qism`
  attribute but the grain stays article-level per the original scope
  decision. Worth a measurement pass: how often does citing at the qism level
  change which stage/institution the citation should attach to?

### Data currency
- **175/885 repeal items still unresolved** (`repeal_clause` table, see
  `build_links.py`'s repeal-detection block). Sampled failures are acts
  where the quoted title in the repeal clause doesn't exact-match
  `act.doc_title` after normalisation — truncated titles, embedded quote
  marks, or paraphrased titles. Next step: fuzzy match (edit distance or
  token-set match) on (date, title) pairs that fail exact match, with a
  confidence-scored `match_method` so weak matches stay visibly weak rather
  than silently wrong.
- **Amendment chains, not just repeals.** An act can *amend* another without
  repealing it (redlines specific articles). No detection exists for this at
  all yet — only whole-act repeal. Worth inventing a detector for "kiritilsin"
  / "oʻzgartirish kiritilsin" style amendment clauses, at least at the
  citing-act level, so `v_act_currency` can distinguish "superseded" from
  "amended but still partly in force."
- **Propagate currency into the LLC dossier's implementing-acts list** (and
  eventually the general explorer) as a first-class filter rather than a
  toggle buried in an expander — currency should probably gate what counts as
  "implements" by default.

### Cleanup
- **Retire superseded prototypes**, once confirmed dead:
  `hierarchy_engine.py` (f-string SQL, empty `okoz_to_fk_map`, superseded by
  `build_okoz.py`+`app_hierarchy.py`), `app_deep.py` (superseded by
  `app_hierarchy.py`), `app.py` (earliest Streamlit prototype, superseded).
  Confirm nothing imports them before deleting.
- **`test_transfer_e2e.py`** (956 lines, unittest-based, covers "AC1-AC3")
  predates `verify_transfer.py`'s AC1-AC7 and may now be fully redundant —
  or may cover cases verify_transfer.py dropped. Diff their actual coverage
  before deciding: merge anything unique into verify_transfer.py, then retire
  the rest rather than keeping two acceptance suites that can drift apart.
- **One-off exploration scripts** (`analyze_civil_code.py`, `analyze_fk.py`,
  `analyze_fk_deep.py`, `find_civil_code.py`) were scratch queries from the
  original orchestrator run, not part of the maintained pipeline. Either
  fold anything still-useful into a proper diagnostic script or delete.
- **`hierarchy_engine.py`'s f-string SQL** is a live SQL-injection pattern if
  anything ever calls it with user input — even if the file is slated for
  deletion, flag/fix it first in case deletion gets deprioritized.

---

## Log

### 2026-09-03 — first session: extractor recall, measured corpus-wide

Picked the highest-value Extractor recall/precision item: no gold set exists,
and the backlog's proposed shortcut (compare `article_text` vs
`cross_references` extractions on the same row) looked cheap to try before
committing to hand-annotation. Also had to `pip install duckdb pyarrow` and
`apt-get install git-lfs` + `git lfs pull` first — the parquet ships as a
163MB LFS object and neither LFS nor the Python deps were present in this
fresh clone; without pulling it, `articles/train-00000-of-00001.parquet` is
just a 134-byte pointer file, invisible to any read against the raw layer.

**Tried the cross_references-vs-article_text idea, measured it, and it
failed.** Built the comparison directly from the already-computed
`link_edge` table (build_links.py already runs the extractor separately over
both fields, tagged by `source_field` — no new extraction needed). Result:
4249/4272 (99.5%) of cross_references-sourced Civil Code article citations
have no matching article_text citation on the same row. Manually inspected
4 of these (rows 1073, 1390, 1759, 1764) by reading the raw parquet text: in
every case cross_references correctly points at a real, unrelated provision
in another law (a defense-procurement act's LexUZ footnote pointing at Civil
Code arts 457-458 on contracts; a Water Code article pointing at a Land Code
article) that the citing article's own body text never mentions. This is
LexUZ editorial commentary adding related-reading pointers, not restating
what the act says — so "article_text missed it" is the wrong description;
the two fields are structurally independent, and their disagreement rate
says nothing about extractor recall. Recorded as a falsified hypothesis in
the backlog rather than silently dropped, since another day (or another
resumed session) could otherwise re-try the same dead end.

**Built a working recall check instead, and it passed clean.** Wrote
`measure_extractor_recall.py`: an independent, deliberately dumber "naive"
detector (`\d+-modda`, `\d+-bob`, both scoped by the extractor's own
RE_STOP/RE_STOP_ABBR boundaries so a same-window "FPK 75-moddasi" doesn't
get flagged) run against every "Fuqarolik kodeksi" anchor occurrence across
the full 54,173-row raw corpus (10,348 candidate rows contain "kodeks" or
"FK"), then checked that every naive hit is accounted for by some citation
the real extractor returned in the same window. Result: **0 real misses**,
both for article-level citations (1321 anchor windows, 1469 naive numbers vs
3147 extracted — extractor finds more because it correctly expands lists
and ranges the naive regex can't) and chapter/section-level citations (238
windows, 243 naive vs 256 extracted). Two apparent misses during
development turned out to be bugs in the naive checker itself (not
excluding "IPK 107-moddasi" / "FPK 274-275-moddalari" — other codes'
abbreviations — and not counting the extractor's `section` target kind
alongside `chapter`), both fixed before the final run; the script's
docstring records why. This is a real, corpus-scale validation that the
22 self-tests didn't provide before.

**Decision:** don't build the ~50-article gold set yet — recall on the two
most common surface forms (article and chapter/section citations, which
together are the overwhelming majority of the 6827 edges) is empirically
excellent, so hand-annotation effort is better spent on precision
(misattribution: wrong target doc/article for a correctly-found number) once
the remaining surface forms (qism, band, FK-alias, self-reference) are
checked the same way — see Active threads. No pipeline code changed; this
was pure measurement, so `verify_transfer.py` was not expected to move and
stayed green (45+ checks pass, same INFO-level findings as before).

*(earlier entries go here, newest first, once more sessions run)*
