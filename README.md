```powershell
Copy-Item .env.example .env
```

Set a strong local `MSSQL_SA_PASSWORD` in `.env`, then update the password in `DATABASE_URL` to match it (URL-encode reserved characters in the password). `OPENAI_API_KEY` can remain blank for the deterministic demo. Start the app and SQL Server:

```powershell
docker compose up --build
```

Open **[http://localhost:8501](http://localhost:8501)**. To follow the app logs in another terminal:

```powershell
docker compose logs -f app
```

The first SQL Server startup and data seeding can take a few minutes. Stop the stack with `Ctrl+C` or `docker compose down`; the named SQL data volume is preserved when using `down`.

### Use a separate SQL Server

Set `DATABASE_URL` in `.env` to a reachable SQL Server connection string, then seed or migrate the finance table:

```powershell
python scripts/init_db.py
python -m streamlit run app/ui.py
```

The configured SQLAlchemy URL uses ODBC Driver 18. A suitable SQL Server ODBC driver must be installed for local Python runs.

## 💱 Financial definitions

| Metric | Definition |
| --- | --- |
| Revenue | Sum of `revenue` |
| Cost | Sum of `cost` |
| Gross profit | Revenue − cost |
| Gross margin | Gross profit ÷ revenue, formatted as a percentage |

For grouped results, gross margin is recomputed from the group's revenue and cost totals. Group percentages are not averaged. Fiscal periods use calendar quarters. Amounts are reported in the selected dataset's native currency.

The root-cause example compares South Q2 2026 with Q1 2026 and surfaces observed revenue, cost, and product contribution changes. It describes the data evidence and does not claim that a correlation proves business causation.

## 🛡️ Read-only query controls

- Only a single `SELECT` against the approved `dbo.fact_finance` dataset is allowed.
- DML/DDL statements, comments, multiple statements, system objects, and non-approved tables are rejected.
- Queries are scoped to the selected market, capped at 500 rows, and run with configured timeouts.
- Executed SQL is recorded in `finance_queries.log` (ignored by Git).
- Model-generated SQL passes through the same validation and execution path as deterministic templates.

These application checks are defense in depth. For any real database, use a dedicated SQL Server identity with **SELECT-only** permissions and appropriate network controls. Never point the demo at production financial data.

## 🧪 Evaluation

The repository includes a 40-question known-answer evaluation based on the synthetic fixture, plus ambiguous, out-of-scope, and unsafe-query checks. Run it to calculate observed execution rate, strict numeric accuracy, per-question values, and wall-clock latency:

```powershell
python -m app.evaluation
```

Results are written to `evaluation-results.json` when the command runs. The report does not include a prefilled score. Provider token usage is currently unavailable because the app does not expose token accounting from the selected API response. See [`evaluation-report.md`](evaluation-report.md) for measurement definitions and limitations.

Run the unit tests with:

```powershell
python -m pytest
```

The current suite is a starter evaluation harness. Add broader SQL equivalence checks, answer extraction scoring, and SQL Server integration coverage before using the project for operational reporting.

## ⚙️ Configuration

`.env.example` contains safe defaults and blank API-key configuration. Keep your local `.env` private; it is excluded by `.gitignore`.

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional key for model-generated SQL. Leave blank for deterministic templates. |
| `OPENAI_MODEL` | OpenAI model name used when model SQL generation is enabled. |
| `DATABASE_URL` | SQL Server URL; Docker Compose supplies the SQL Server service hostname. |
| `DEMO_MODE` | Enables the reproducible demo configuration. |
| `MSSQL_SA_PASSWORD` | Local SQL Server container password; set a strong private value in `.env`. |

## 🧰 Tech stack

| Area | Tools |
| --- | --- |
| Agent workflow | Python, LangGraph, Pydantic |
| SQL safety and execution | SQLGlot, SQLAlchemy, PyODBC |
| Database | SQL Server 2022; SQLite for deterministic demo mode |
| Interface and visualizations | Streamlit, Plotly, Pandas |
| Model provider | OpenAI API (optional for deterministic demo) |
| Packaging and tests | Docker Compose, Pytest |

## 📁 Project structure

```text
app/                 Agent, UI, data, metrics, SQL policy, and evaluation
scripts/             SQL Server initialization and sample-data seeding
tests/               SQL safety and synthetic data tests
docker-compose.yml   Local SQL Server and app services
evaluation-report.md Measurement definitions and current status
.env.example         Safe local configuration template
```

## ⚠️ Scope and limitations

- All bundled finance records are synthetic and illustrative.
- The two market datasets are independent samples; there is no currency conversion or FX analysis.
- Template-driven questions cover the showcased question families. Unsupported or ambiguous questions may not produce a result.
- Evaluation latency includes local execution and any enabled model call; it is not a production service-level measurement.
- The project is a portfolio demonstration, not a certified financial reporting system. Validate outputs and source data before making business decisions.

---

<div align="center">

**CFO Finance Assistant · Agentic Text-to-SQL**

Read-only by design. Reproducible by default. Transparent about its evidence.

</div>

## Screenshots
<img width="1917" height="872" alt="Screenshot 2026-10-31 060139" src="https://github.com/user-attachments/assets/e1353f25-646c-4bca-93cd-dd995c9b7880" />
<img width="1917" height="866" alt="Screenshot 2026-10-31 060218" src="https://github.com/user-attachments/assets/cb376ae7-c330-44cd-bfc3-676995098084" />
<img width="1906" height="872" alt="Screenshot 2026-10-31 062219" src="https://github.com/user-attachments/assets/dc4b8576-bcb0-4885-bd0c-28797881f02b" />

These screenshots were added to the GitHub repository by the project owner.
## Screenshots
<img width="1917" height="872" alt="Screenshot 2026-10-31 060139" src="https://github.com/user-attachments/assets/e1353f25-646c-4bca-93cd-dd995c9b7880" />
<img width="1917" height="866" alt="Screenshot 2026-10-31 060218" src="https://github.com/user-attachments/assets/cb376ae7-c330-44cd-bfc3-676995098084" />
<img width="1906" height="872" alt="Screenshot 2026-10-31 062219" src="https://github.com/user-attachments/assets/dc4b8576-bcb0-4885-bd0c-28797881f02b" />

These screenshots were added to the GitHub repository by the project owner.
