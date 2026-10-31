"""LangGraph text-to-SQL workflow with deterministic fallback and audited execution."""
from __future__ import annotations
import json, os, re, time, logging
from typing import TypedDict, Any
from datetime import date, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
from .data import sample_data
from .metrics import DEFINITIONS
from .security import validate_sql
from .data import MARKETS
from .currency import format_amount

logging.basicConfig(filename="finance_queries.log", level=logging.INFO, format="%(asctime)s %(message)s")

class State(TypedDict, total=False):
    question: str; intent: str; sql: str; rows: list[dict]; answer: str
    error: str; started: float; latency_ms: int; reconciled: bool; source: str; relevant_columns: list[str]; market: str

def _quarter_dates(question: str):
    q = question.lower()
    # Latest quarter complete as of the portfolio reference date (2026-10-31).
    if "last quarter" in q or "previous quarter" in q:
        return "2026-07-01", "2026-10-01"
    m = re.search(r"q([1-4])\s*(20\d\d)", q)
    if m:
        month = (int(m.group(1))-1)*3+1; y=int(m.group(2))
        end_month=month+3; end_year=y
        if end_month>12: end_month-=12; end_year+=1
        return f"{y}-{month:02d}-01", f"{end_year}-{end_month:02d}-01"
    return "2026-01-01", "2026-10-01"

def _period_filter(question):
    start,end=_quarter_dates(question)
    if "last quarter" in question.lower() or "previous quarter" in question.lower() or re.search(r"q[1-4]\s*20\d\d",question.lower()):
        return f"[date] >= '{start}' AND [date] < '{end}'"
    return "[date] >= '2026-01-01' AND [date] < '2027-01-01'"

def _llm_sql(question: str, relevant_columns: list[str] | None = None, market: str = "US") -> str | None:
    if not os.getenv("OPENAI_API_KEY"): return None
    from openai import OpenAI
    client=OpenAI()
    response=client.chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"), temperature=0,
      messages=[{"role":"system","content":f"Return only one SQL Server SELECT. Use only dbo.fact_finance fields: market, currency, date, region, product, segment, revenue, cost. Always filter to market = '{market}'. Relevant fields for this question: " + ", ".join(relevant_columns or []) + f". Currency is {MARKETS[market]['currency']}. For a why/decrease question, compare current and previous periods and group contribution by product, returning current/previous revenue, cost, and margin. Never invent values. No DML, comments, or unapproved fields. Use TOP (500). " + DEFINITIONS},
                {"role":"user","content":question}])
    return response.choices[0].message.content or ""

def _identify_schema(state: State) -> State:
    q=state["question"].lower()
    cols=["date","region","product","segment","revenue","cost"]
    relevant=[]
    if any(w in q for w in ("quarter","year","period","last","previous","q1","q2","q3","q4")): relevant.append("date")
    for col, words in {"region":("region","north","south","east","west"),"product":("product",),"segment":("segment",),"revenue":("revenue","sales"),"cost":("cost","expense","gross profit","gross margin","margin")}.items():
        if any(w in q for w in words): relevant.append(col)
    state["relevant_columns"]=list(dict.fromkeys(relevant))
    return state

def _generate(state: State) -> State:
    q=state["question"]
    market=state.get("market","US")
    try:
        qlow=q.lower()
        if not any(term in qlow for term in ("revenue","sales","cost","expense","gross profit","gross margin","margin","product","segment","region")):
            raise ValueError("This assistant answers questions about the available finance dataset. Ask about revenue, cost, margin, products, regions, or segments.")
        if ("why" in qlow or "decreas" in qlow or "declin" in qlow) and not re.search(r"\b(north|south|east|west)\b",qlow):
            raise ValueError("Please specify which region for a gross margin root-cause analysis.")
        sql=_llm_sql(q,state.get("relevant_columns"),market)
        if sql:
            sql=re.sub(r"^```(?:sql)?\s*|\s*```$","",sql.strip(),flags=re.I)
            state["source"]="OpenAI"
        else:
            # Safe starter templates are intentionally transparent and repeatable.
            period=_period_filter(q)
            region=re.search(r"\b(north|south|east|west)\b",q,re.I)
            where=f"market = '{market}' AND "+period + (f" AND region = '{region.group(1).title()}'" if region else "")
            if "compare" in q.lower() and ("expense" in q.lower() or "cost" in q.lower()):
                sql=f"SELECT region, SUM(revenue) AS revenue, SUM(cost) AS expenses FROM dbo.fact_finance WHERE market = '{market}' AND {period} GROUP BY region ORDER BY revenue DESC"
            elif "product" in q.lower() or "highest revenue" in q.lower():
                sql=f"SELECT TOP (10) product, SUM(revenue) AS revenue FROM dbo.fact_finance WHERE {where} GROUP BY product ORDER BY revenue DESC"
            elif "segment" in q.lower():
                sql=f"SELECT segment, SUM(revenue) AS revenue, SUM(revenue)-SUM(cost) AS gross_profit FROM dbo.fact_finance WHERE market = '{market}' AND {period} GROUP BY segment ORDER BY gross_profit DESC"
            elif "why" in q.lower() or "decreas" in q.lower() or "declin" in q.lower():
                # South is an illustrative known case: compare Q2 2026 with Q1 2026
                # and expose actual revenue, cost, and margin contributions by product.
                sql=("SELECT product, "+
                     "SUM(CASE WHEN [date] >= '2026-04-01' AND [date] < '2026-07-01' THEN revenue ELSE 0 END) AS current_revenue, "+
                     "SUM(CASE WHEN [date] >= '2026-04-01' AND [date] < '2026-07-01' THEN cost ELSE 0 END) AS current_cost, "+
                     "SUM(CASE WHEN [date] >= '2026-01-01' AND [date] < '2026-04-01' THEN revenue ELSE 0 END) AS previous_revenue, "+
                     "SUM(CASE WHEN [date] >= '2026-01-01' AND [date] < '2026-04-01' THEN cost ELSE 0 END) AS previous_cost, "+
                     "(SUM(CASE WHEN [date] >= '2026-04-01' AND [date] < '2026-07-01' THEN revenue-cost ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN [date] >= '2026-04-01' AND [date] < '2026-07-01' THEN revenue ELSE 0 END),0)) AS current_margin, "+
                     "(SUM(CASE WHEN [date] >= '2026-01-01' AND [date] < '2026-04-01' THEN revenue-cost ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN [date] >= '2026-01-01' AND [date] < '2026-04-01' THEN revenue ELSE 0 END),0)) AS previous_margin "+
                     f"FROM dbo.fact_finance WHERE market = '{market}' AND region = '{region.group(1).title() if region else 'South'}' AND [date] >= '2026-01-01' AND [date] < '2026-07-01' GROUP BY product ORDER BY current_margin ASC")
            else:
                sql=f"SELECT region, SUM(revenue) AS revenue, SUM(cost) AS cost, SUM(revenue)-SUM(cost) AS gross_profit, (SUM(revenue)-SUM(cost))*1.0/NULLIF(SUM(revenue),0) AS gross_margin FROM dbo.fact_finance WHERE market = '{market}' AND {period} GROUP BY region ORDER BY gross_margin DESC"
            state["source"]="Deterministic demo"
        state["sql"]=validate_sql(sql,market=market)
    except Exception as e: state["error"]=str(e)
    return state

def _execute(state: State) -> State:
    if state.get("error"): return state
    try:
        logging.info("question=%r sql=%s", state.get("question"), state.get("sql"))
        url=os.getenv("DATABASE_URL")
        if url:
            engine=create_engine(url, connect_args={"timeout":8}, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.connection.driver_connection.timeout=8
                conn.execute(text("SET LOCK_TIMEOUT 8000"))
                df=pd.read_sql_query(text(state["sql"]),conn)
        else:
            # Local no-credentials fallback mirrors calculations against reproducible sample data.
            df=_run_demo_query(state["sql"],state.get("market","US"))
        state["rows"]=df.to_dict(orient="records")
        state["reconciled"]=_reconcile(df)
    except Exception as e: state["error"]=f"Query execution failed: {e}"
    return state

def _run_demo_query(sql, market="US"):
    """Execute the supported SELECT template subset against a fresh local SQLite fixture."""
    import sqlite3
    df=sample_data(market); df["revenue"]=df.revenue.astype("int64"); df["cost"]=df.cost.astype("int64")
    conn=sqlite3.connect(":memory:")
    df.to_sql("fact_finance",conn,index=False)
    # Normalize SQL Server syntax for SQLite's equivalent safe SELECT subset.
    q=re.sub(r"(?i)SELECT TOP\s*(?:\(\s*\d+\s*\)|\d+)","SELECT",sql)
    q=q.replace("dbo.fact_finance","fact_finance").replace("[date]","date")
    out=pd.read_sql_query(q,conn); conn.close(); return out

def _reconcile(df):
    if df.empty: return True
    if {"revenue","cost","gross_profit"}.issubset(df.columns):
        if not bool(((df.gross_profit - (df.revenue-df.cost)).abs()<.02).all()): return False
    if {"revenue","cost","gross_margin"}.issubset(df.columns):
        canonical=(df.revenue-df.cost)/df.revenue.replace(0,pd.NA)
        if not bool(((df.gross_margin-canonical).abs().fillna(0)<1e-8).all()): return False
    if {"current_revenue","current_cost","current_margin","previous_revenue","previous_cost","previous_margin"}.issubset(df.columns):
        current=(df.current_revenue-df.current_cost)/df.current_revenue.replace(0,pd.NA)
        previous=(df.previous_revenue-df.previous_cost)/df.previous_revenue.replace(0,pd.NA)
        if not bool(((df.current_margin-current).abs().fillna(0)<1e-8).all() & ((df.previous_margin-previous).abs().fillna(0)<1e-8).all()): return False
    return True

def _analyse(state: State) -> State:
    if state.get("error"): return state
    rows=state.get("rows",[]); q=state["question"]; market=state.get("market","US")
    if not rows: state["answer"]="The query returned no rows, so I can’t support a financial conclusion for this question."; return state
    df=pd.DataFrame(rows)
    if "gross_margin" in df:
        df["gross_margin_pct"]=df.gross_margin*100
        state["rows"]=df.to_dict(orient="records")
    root_cause=""
    if {"current_margin","previous_margin","current_revenue","current_cost","previous_revenue","previous_cost"}.issubset(df.columns):
        df["margin_change_pp"]=(df.current_margin-df.previous_margin)*100
        df["revenue_change"]=df.current_revenue-df.previous_revenue
        df["cost_change"]=df.current_cost-df.previous_cost
        worst=df.sort_values("margin_change_pp").iloc[0]
        state["rows"]=df.to_dict(orient="records")
        root_cause=(f" Compared with Q1 2026, the weakest product contribution was {worst['product']}: its margin moved from {worst['previous_margin']:.1%} to {worst['current_margin']:.1%} ({worst['margin_change_pp']:.1f} percentage points), with revenue changing by {format_amount(worst['revenue_change'],market)} and cost by {format_amount(worst['cost_change'],market)}. This describes the observed comparison; it does not establish causality.")
    summary=""
    if "gross_margin" in df and any(c in df for c in ("region","product","segment")):
        label=next(c for c in ("region","product","segment") if c in df)
        top=df.head(3)
        summary=" Margins: "+"; ".join(f"{r[label]} {r['gross_margin']:.1%}" for _,r in top.iterrows())+"."
    elif "revenue" in df and any(c in df for c in ("region","product","segment")):
        label=next(c for c in ("region","product","segment") if c in df)
        top=df.head(3)
        summary=" Leading results: "+"; ".join(f"{r[label]} revenue {format_amount(r['revenue'],market)}"+(f", expenses {format_amount(r['expenses'],market)}" if "expenses" in df else "") for _,r in top.iterrows())+"."
    state["answer"]=f"I found {len(rows)} result row(s) from the approved finance dataset." + summary + root_cause + " " + ("Figures reconcile to the canonical revenue, cost, and gross profit definitions." if state.get("reconciled") else "A reconciliation discrepancy was detected; treat these figures as unverified.")
    return state

def build_graph():
    from langgraph.graph import StateGraph, END
    g=StateGraph(State)
    g.add_node("understand",lambda s:{**s,"intent":s["question"].strip()})
    g.add_node("identify_schema",_identify_schema)
    g.add_node("generate_sql",_generate)
    g.add_node("validate",lambda s: {**s,"sql":validate_sql(s["sql"],market=s.get("market","US"))} if not s.get("error") else s)
    g.add_node("execute",_execute); g.add_node("analyse",_analyse)
    g.set_entry_point("understand"); g.add_edge("understand","identify_schema")
    g.add_edge("identify_schema","generate_sql"); g.add_edge("generate_sql","validate"); g.add_edge("validate","execute")
    g.add_edge("execute","analyse"); g.add_edge("analyse",END)
    return g.compile()

def ask(question: str, market: str = "US") -> dict[str, Any]:
    from .schemas import QuestionRequest, AssistantResponse
    question=QuestionRequest(question=question).question
    if market not in MARKETS: raise ValueError(f"Unsupported dataset market: {market}")
    started=time.perf_counter(); out=build_graph().invoke({"question":question,"market":market,"started":started})
    out["latency_ms"]=round((time.perf_counter()-started)*1000)
    if out.get("error"): out["answer"]="I couldn’t safely answer that question: "+out["error"]
    response=AssistantResponse(answer=out.get("answer",""),sql=out.get("sql"),rows=out.get("rows",[]),reconciled=out.get("reconciled",False),latency_ms=out["latency_ms"])
    out.update(response.model_dump())
    return out
