# Task: point-in-time classification join

You have two files:

- `classifications.csv` — classification history. Each row says: from
  `effective_from` (inclusive), `company_id` is classified in `micro_theme`,
  until superseded by a later row for the same company.
- `holdings.csv` — portfolio holdings: `account_id`, `company_id`,
  `as_of_date`, `weight`.

**Write a script that adds a `micro_theme` column to the holdings: the
classification as it stood on each holding's `as_of_date`.**

Target output schema, one row per input holding row:

```
account_id, company_id, as_of_date, weight, micro_theme
```

A holding whose company had no classification yet on `as_of_date` should get
an empty `micro_theme` — never a classification from the future.

Notes:

- The data is small; do not worry about performance.
- The input is real-world messy. If a row is ambiguous, decide something
  reasonable and say so out loud — we care about you noticing.
- Use whatever tools you'd normally use, including AI assistants.
- Finishing is not the goal.
