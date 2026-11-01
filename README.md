<div align="center">

# CFO Finance Assistant

### Agentic Text-to-SQL for finance teams

**Ask finance questions in plain English. Get read-only SQL, reconciled metrics, and a clear explanation grounded in reproducible data.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQL Server](https://img.shields.io/badge/Database-SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)](https://www.microsoft.com/sql-server)
[![LangGraph](https://img.shields.io/badge/Workflow-LangGraph-1C3C3C)](https://www.langchain.com/langgraph)
[![Docker Compose](https://img.shields.io/badge/Local%20stack-Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

**[Try it locally](#-quick-start) · [See the workflow](#-how-it-works) · [Review evaluation](#-evaluation)**

</div>

---

## At a glance

Finance teams need answers they can inspect. This project demonstrates a guarded natural-language-to-SQL workflow over a reproducible synthetic finance dataset. It makes the generated query, returned rows, metric reconciliation, and run details visible alongside the business-friendly answer.

Choose the **United States · USD** or **India · INR** dataset in the sidebar. They are generated independently; INR values are not converted from USD using an assumed exchange rate.

> **Illustrative data only:** this sample is synthetic and is not company reporting or financial advice. The South region has an intentional gross-margin change in Q2 2026 to make the root-cause example repeatable.

## ✨ What it demonstrates

- **Ask in plain English** about revenue, cost, gross profit, gross margin, region, product, or business segment.
- **Inspect the SQL** generated for a question and review the result rows and run metadata.
- **Explore a dashboard** with revenue and gross-margin KPIs, trends, and regional charts.
- **Switch between US/USD and India/INR** datasets without implying currency conversion.
- **Trace a margin movement** using period and product-level revenue and cost comparisons.
- **Use canonical financial definitions** so gross margin is computed from grouped totals, not by averaging percentages.
- **Run without an API key** in deterministic demo mode; configure OpenAI to enable model-generated SQL.

### Example questions

- What was the gross margin by region last quarter?
- Why did the South region's gross margin decrease?
- Which products generated the highest revenue?
- Compare revenue and expenses across regions.
- What were the top-performing business segments?

## 🖼️ Screenshots

<table>
  <tr>
    <td align="center"><strong>Finance dashboard</strong><br><img src="https://github.com/user-attachments/assets/e1353f25-646c-4bca-93cd-dd995c9b7880" alt="CFO Finance Assistant screenshot" width="100%"></td>
    <td align="center"><strong>Assistant and query results</strong><br><img src="https://github.com/user-attachments/assets/cb376ae7-c330-44cd-bfc3-676995098084" alt="CFO Finance Assistant screenshot" width="100%"></td>
  </tr>
  <tr>
    <td align="center" colspan="2"><strong>Generated SQL and run details</strong><br><img src="https://github.com/user-attachments/assets/dc4b8576-bcb0-4885-bd0c-28797881f02b" alt="CFO Finance Assistant screenshot" width="82%"></td>
  </tr>
</table>

## 🧭 How it works

```mermaid
flowchart LR
    U[Finance question] --> I[Understand intent and entities]
    I --> G[Generate SQL]
    G --> V[Validate read-only policy]
    V --> X[Execute via SQLAlchemy]
    X --> M[Reconcile canonical metrics]
    M --> A[Explain results with evidence]
    X --> L[Log executed SQL]
    A --> UI[Streamlit results, table, and chart]
