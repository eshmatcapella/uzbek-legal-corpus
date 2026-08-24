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

*(none yet — first session picks one from the backlog below)*

---

## Backlog

### Extractor recall/precision
- **Build the gold set.** ~50 articles, hand-verified ground truth for
  citation extraction (which acts realize them, at what confidence). No gold
  set exists yet — `citation_extractor.py`'s 22 self-tests check surface-form
  parsing, not corpus-wide recall. Creative angle worth trying: don't sample
  gold-set articles uniformly — sample where the extractor's own signals
  disagree (e.g. an article cited via `cross_references` but never via
  `article_text`, or vice versa) so the gold set concentrates on the
  extractor's actual blind spots instead of confirming what it already gets
  right.
- **Measure recall against a second independent signal.** The parquet's
  `cross_references` field is LexUZ's own curated citation list. Where it
  names an article the extractor's `article_text` pass missed entirely, that
  is a free recall check with no manual annotation required — run this before
  building the gold set by hand, it may cut the gold-set size needed.
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

*(entries go here, newest first, once the first session runs)*
