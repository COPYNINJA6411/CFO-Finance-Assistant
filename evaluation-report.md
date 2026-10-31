# Evaluation report

## Status

The 40-question evaluation suite has **not been run**, so no execution accuracy, numerical accuracy, mean latency, or API token usage is claimed here. The project unit tests were run under Python 3.12: **18 passed**. Deterministic SQLite smoke checks also returned four reconciled regional rows for the gross-margin question in both the USD and INR datasets. SQL Server integration and a refreshed browser screenshot have not been verified here.

## Reproduction

Install the project and run `python -m app.evaluation`. The script creates a deterministic fixture, executes 40 known-answer natural-language questions, writes individual expected and observed values plus computed summary metrics to `evaluation-results.json`, and exercises ambiguous, out-of-scope, and unsafe SQL cases. Then run `pytest` for unit tests. For integration evidence, start Docker Compose, let the database seed, and rerun the evaluation with `DATABASE_URL` pointing at SQL Server.

## Measurement definitions

- **SQL execution rate:** questions returning a numeric result divided by known-answer questions.
- **Numerical accuracy:** results within $0.02 of fixture-derived gold values divided by known-answer questions.
- **Latency:** observed wall-clock milliseconds per question; report mean in the generated JSON.
- **API usage:** the current app does not report provider tokens. Provider token accounting must be added for the selected API before a usage result is reported.

The demo evaluation uses SQLite over the same deterministic generated rows; SQL Server mode should be evaluated separately before operational use.
