# Lab 1 quality checks

From the repository root, run:

```bash
python lab01_release/qa.py
```

Or run `python qa.py` from the lab directory. No installation, API key, or
network access is needed for the current implementation. Exit code 0 means
all checks passed; exit code 1 means a check failed. Each failure names the
stage and explains the assertion. To focus on one stage:

```bash
python lab01_release/qa.py FetchChecks
python lab01_release/qa.py ScoreChecks
python lab01_release/qa.py WorkflowConfigurationChecks
```

The script exercises the real fetching and scoring functions. It checks a
small controlled review file, the actual dataset, known numeric answers,
food/service weighting, repeated reviews, and printed decimal precision.
Temporary data is removed automatically; the lab dataset is unchanged.

For workflow checks, a recording substitute replaces AutoGen. It records
agents, registered functions, and the sequential chat configuration. These
checks target this lab's current three-stage architecture; update them if
you intentionally change conversation patterns. They do not execute tools
through AutoGen or prove that an LLM extracts correct scores.

After offline checks pass, validate a live run separately:

1. Run one restaurant query and inspect the actual tool result, not only the
   suggested call. Confirm the restaurant and fetched reviews are correct.
2. Compare the analyzer's scores with a few manually scored reviews. There
   must be one food/service pair per review, in order, with integers 1–5.
3. Confirm the final calculation executes and prints three decimal places.
4. Run the supplied `test.py` with request pacing appropriate to your quota.
   A 429 is a blocked run, not evidence of an incorrect restaurant score.

Passing offline QA does not mean the public tests passed. Live tests also
check model interpretation and the real AutoGen conversation behavior.
