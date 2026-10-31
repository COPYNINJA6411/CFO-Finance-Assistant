"""Streamlit CFO workspace: finance overview, chat, and transparent query evidence."""
from datetime import datetime
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from app.agent import ask
from app.data import sample_data, MARKETS
from app.currency import currency_symbol, format_compact
from app.metrics import DEFINITIONS

load_dotenv()
st.set_page_config(page_title="CFO Finance Assistant", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--ink:#edf4fb;--muted:#93a4b8;--line:rgba(148,173,195,.15);--panel:#111d2b;--panel2:#152436;--teal:#52d6c5;--blue:#79adff}
.stApp{background:radial-gradient(ellipse at 82% -10%,rgba(30,94,116,.22),transparent 36%),#0b1420;color:var(--ink)}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:#0d1926;border-right:1px solid var(--line)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#aebdd0;font-size:.88rem}
.block-container{max-width:1500px;padding:2rem 2.2rem 5rem}
.eyebrow{color:var(--teal);font-size:.69rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;margin-bottom:.55rem}
.page-title{font-family:Manrope,sans-serif;color:#f4f8fc;font-size:2rem;font-weight:800;letter-spacing:-.045em;margin:0;line-height:1.18}
.page-subtitle{color:#97aabd;font-size:.94rem;margin:.45rem 0 0}
.status-chip{display:inline-flex;align-items:center;gap:.48rem;border:1px solid var(--line);border-radius:999px;padding:.48rem .78rem;background:rgba(17,29,43,.8);color:#c5d3e0;font-size:.77rem;white-space:nowrap}
.status-dot{width:.48rem;height:.48rem;border-radius:50%;background:var(--teal);box-shadow:0 0 12px rgba(82,214,197,.5)}
.section-label{font-family:Manrope,sans-serif;color:#eaf1f8;font-size:1.06rem;font-weight:700;margin:.3rem 0 .8rem}
.section-hint{color:var(--muted);font-size:.81rem;margin-top:-.55rem;margin-bottom:.8rem}
.metric-card{height:130px;background:linear-gradient(145deg,rgba(22,39,57,.96),rgba(16,29,44,.96));border:1px solid var(--line);border-radius:15px;padding:17px 19px;box-shadow:0 12px 28px rgba(0,0,0,.12)}
.metric-top{display:flex;justify-content:space-between;align-items:center;color:#a9b9ca;font-size:.78rem;font-weight:600}
.metric-icon{display:grid;place-items:center;width:30px;height:30px;border-radius:9px;background:rgba(82,214,197,.1);color:var(--teal);font-size:1rem}
.metric-value{font-family:Manrope,sans-serif;font-size:1.62rem;font-weight:800;letter-spacing:-.04em;color:#f2f7fc;margin-top:9px;line-height:1.2}
.metric-note{font-size:.72rem;color:#7f93a8;margin-top:5px}
.panel-head{font-family:Manrope,sans-serif;font-size:.92rem;font-weight:700;color:#e9f1f8;margin:.15rem 0 .1rem}
.panel-note{font-size:.74rem;color:#8397ab;margin-bottom:.35rem}
.prompt-caption{color:#93a7bb;font-size:.8rem;margin-bottom:.5rem}
.assistant-box{border:1px solid var(--line);background:linear-gradient(145deg,rgba(18,32,48,.92),rgba(14,25,38,.92));border-radius:15px;padding:1rem 1.1rem;margin:.55rem 0 1rem}
.answer-label{font-size:.69rem;text-transform:uppercase;letter-spacing:.12em;font-weight:700;color:var(--teal);margin-bottom:.45rem}
.audit-pill{display:inline-block;padding:.24rem .53rem;border-radius:999px;background:rgba(82,214,197,.1);color:#7ce4d5;font-size:.7rem;font-weight:700}
div[data-testid="stChatMessage"]{border:1px solid var(--line);background:rgba(17,29,43,.75);border-radius:14px;padding:.75rem 1rem;margin:.55rem 0}
div[data-testid="stChatInput"]{border-color:rgba(121,173,255,.38)!important;background:#111d2b!important;border-radius:13px!important}
div[data-testid="stButton"]>button{border-radius:10px;border-color:var(--line);background:rgba(18,32,48,.88);color:#dce7f2;transition:all .16s ease}
div[data-testid="stButton"]>button:hover{border-color:rgba(82,214,197,.6);color:#fff;background:#172a3b}
hr{border-color:var(--line)!important}
@media(max-width:900px){.block-container{padding:1.2rem 1rem 4rem}.page-title{font-size:1.65rem}.metric-card{height:120px;padding:14px}}
</style>
""",unsafe_allow_html=True)

SUGGESTIONS=[
    ("◉  Regional margins", "What was the gross margin by region last quarter?"),
    ("↗  Margin drivers", "Why did the South region's gross margin decrease?"),
    ("▥  Product revenue", "Which products generated the highest revenue?"),
    ("⇄  Revenue vs cost", "Compare revenue and expenses across regions."),
    ("◆  Segments", "What were the top-performing business segments?"),
]

def money_short(value, market):
    return format_compact(value,market)

def metric_card(label, value, note, icon):
    st.markdown(f'<div class="metric-card"><div class="metric-top"><span>{label}</span><span class="metric-icon">{icon}</span></div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',unsafe_allow_html=True)

def render_result(item):
    with st.container(border=True):
        status="✓ Reconciled" if item.get("reconciled") else "! Review figures"
        item_market=item.get("market","US")
        st.markdown(f'<div class="answer-label">FINANCE ASSISTANT · {MARKETS[item_market]["currency"]} &nbsp; <span class="audit-pill">{status}</span></div>',unsafe_allow_html=True)
        st.markdown(item.get("answer",""))
        if item.get("sql") or item.get("rows"):
            result_tab,sql_tab,details_tab=st.tabs(["Results", "Generated SQL", "Run details"])
            with result_tab:
                if item.get("rows"):
                    result=pd.DataFrame(item["rows"])
                    currency_suffix=MARKETS[item_market]["currency"]
                    display_names={name:f"{name.replace('_',' ').title()} ({currency_suffix})" for name in ("revenue","cost","expenses","gross_profit","current_revenue","current_cost","previous_revenue","previous_cost","revenue_change","cost_change")}
                    st.dataframe(result.rename(columns=display_names),use_container_width=True,hide_index=True,height=min(360,45+35*len(result)))
                    numeric=[c for c in result.columns if pd.api.types.is_numeric_dtype(result[c]) and c not in ("gross_margin_pct",)]
                    labels=[c for c in result.columns if c not in numeric and c not in ("gross_margin_pct",)]
                    if numeric and labels:
                        preferred=next((c for c in numeric if "margin" in c.lower()),None)
                        if preferred and "pct" not in preferred.lower():
                            chart_data=result.copy(); chart_data[preferred]=chart_data[preferred]*100
                            fig=px.bar(chart_data,x=labels[0],y=preferred,color_discrete_sequence=["#52d6c5"])
                            fig.update_yaxes(title="Margin (%)",ticksuffix="%")
                        else:
                            fig=px.bar(result,x=labels[0],y=numeric[0],color_discrete_sequence=["#52d6c5"])
                            fig.update_yaxes(title=numeric[0].replace("_"," ").title())
                        fig.update_layout(template="plotly_dark",height=300,margin=dict(l=8,r=8,t=12,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=False,font=dict(family="DM Sans",color="#c4d1df"))
                        if any(token in numeric[0].lower() for token in ("revenue","cost","expense","profit")):
                            fig.update_yaxes(tickprefix=currency_symbol(item_market))
                        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                else:
                    st.info("No result rows were returned.")
            with sql_tab:
                st.code(item.get("sql","No SQL generated"),language="sql")
                st.caption("Read-only query · approved finance dataset")
            with details_tab:
                a,b,c=st.columns(3)
                a.metric("Source",item.get("source","—"))
                b.metric("Response time",f"{item.get('latency_ms','—')} ms")
                c.metric("Reconciliation","Passed" if item.get("reconciled") else "Review")

with st.sidebar:
    st.markdown("<div class='eyebrow'>CFO WORKSPACE</div>",unsafe_allow_html=True)
    st.markdown("### 📊 Finance Assistant")
    mode="SQL Server" if os.getenv("DATABASE_URL") else "Sample data"
    market=st.selectbox("Active dataset",options=list(MARKETS),format_func=lambda code:f"{MARKETS[code]['name']} · {MARKETS[code]['currency']}",key="active_market")
    currency=MARKETS[market]["currency"]
    market_name=MARKETS[market]["name"]
    st.markdown(f'<div class="status-chip"><span class="status-dot"></span>{mode} · {currency}</div>',unsafe_allow_html=True)
    st.markdown("")
    if st.button("＋  New conversation",use_container_width=True):
        st.session_state.history=[]
        st.session_state.pending_question=None
        st.rerun()
    with st.expander("Metric definitions",expanded=False):
        st.caption(DEFINITIONS)
    with st.expander("Query history",expanded=bool(st.session_state.get("history"))):
        history=st.session_state.get("history",[])
        if history:
            for i,item in enumerate(reversed(history),1):
                st.caption(f"{i:02d}  ·  {item['question']}")
        else:
            st.caption("Questions you ask will be listed here.")
    st.markdown("---")
    st.caption(f"{market_name} synthetic dataset · 2024–2026\n\nValues are generated independently in {currency}, not converted using an FX rate. Illustrative only.")

data=sample_data(market)
revenue=int(data.revenue.sum()); gross_profit=int((data.revenue-data.cost).sum()); gross_margin=gross_profit/revenue

header_left,header_right=st.columns([3.5,1.2])
with header_left:
    st.markdown('<div class="eyebrow">FINANCE INTELLIGENCE</div><h1 class="page-title">CFO Finance Assistant</h1><p class="page-subtitle">A clear view of performance, with answers grounded in your finance data.</p>',unsafe_allow_html=True)
with header_right:
    st.markdown(f'<div style="text-align:right"><span class="status-chip"><span class="status-dot"></span>{market_name} · {currency}</span><br><span style="color:#8499ae;font-size:.72rem">SYNTHETIC DATA · {currency}</span></div>',unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)
k1,k2,k3,k4=st.columns(4,gap="medium")
with k1: metric_card("Total revenue",money_short(revenue,market),f"All sample periods · {currency}","↗")
with k2: metric_card("Gross profit",money_short(gross_profit,market),f"Revenue less cost · {currency}","＋")
with k3: metric_card("Gross margin",f"{gross_margin:.1%}","Gross profit ÷ revenue","◌")
with k4: metric_card("Transactions",f"{len(data):,}","Synthetic finance records","▤")

st.markdown("<div style='height:1.4rem'></div><div class='section-label'>Performance overview</div><div class='section-hint'>Explore the sample dataset before asking a question.</div>",unsafe_allow_html=True)
chart_left,chart_right=st.columns([1.65,1],gap="large")
monthly=data.assign(month=data["date"].dt.to_period("M").dt.to_timestamp()).groupby("month",as_index=False).agg(revenue=("revenue","sum"),cost=("cost","sum"))
monthly["gross_profit"]=monthly.revenue-monthly.cost
monthly["revenue_display"]=monthly.revenue/(10_000_000 if market=="IN" else 1_000_000)
revenue_unit="Cr" if market=="IN" else "M"
region=data.groupby("region",as_index=False).agg(revenue=("revenue","sum"),cost=("cost","sum"))
region["gross_margin"]=(region.revenue-region.cost)/region.revenue
with chart_left:
    st.markdown(f'<div class="panel-head">Monthly revenue</div><div class="panel-note">{market_name} · monthly totals · {currency}</div>',unsafe_allow_html=True)
    fig=px.area(monthly,x="month",y="revenue_display",custom_data=["revenue"],color_discrete_sequence=["#52d6c5"])
    fig.update_traces(line=dict(width=2.5),fillcolor="rgba(82,214,197,.14)",hovertemplate=f"%{{x|%b %Y}}<br>{currency_symbol(market)}%{{customdata[0]:,.0f}}<extra></extra>")
    fig.update_layout(template="plotly_dark",height=275,margin=dict(l=4,r=8,t=8,b=4),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=False,font=dict(family="DM Sans",color="#9eb0c2"),xaxis_title=None,yaxis_title=None)
    fig.update_yaxes(tickprefix=currency_symbol(market),ticksuffix=revenue_unit,tickformat=".1f",gridcolor="rgba(148,173,195,.1)")
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
with chart_right:
    st.markdown('<div class="panel-head">Regional gross margin</div><div class="panel-note">Recomputed from regional totals</div>',unsafe_allow_html=True)
    fig=px.bar(region.sort_values("gross_margin"),x="gross_margin",y="region",orientation="h",color_discrete_sequence=["#79adff"],text=region.sort_values("gross_margin").gross_margin.map(lambda x:f"{x:.1%}"))
    fig.update_traces(textposition="outside",cliponaxis=False,hovertemplate="%{y}<br>%{x:.1%}<extra></extra>")
    fig.update_layout(template="plotly_dark",height=275,margin=dict(l=4,r=28,t=8,b=4),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=False,font=dict(family="DM Sans",color="#c4d1df"),xaxis_title=None,yaxis_title=None)
    fig.update_xaxes(tickformat=".0%",range=[0,.85],gridcolor="rgba(148,173,195,.1)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

st.markdown("<div style='height:.7rem'></div><div class='section-label'>Ask your finance assistant</div><div class='prompt-caption'>Start with a question, or choose a prompt to run it instantly.</div>",unsafe_allow_html=True)
prompt_cols=st.columns(5,gap="small")
for col,(label,prompt) in zip(prompt_cols,SUGGESTIONS):
    with col:
        if st.button(label,use_container_width=True,key="prompt_"+label):
            st.session_state.pending_question=prompt
            st.rerun()

if "history" not in st.session_state: st.session_state.history=[]
if "pending_question" not in st.session_state: st.session_state.pending_question=None
for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant",avatar="📊"):
        render_result(item)

typed_question=st.chat_input("Ask about revenue, gross margin, a region, product, or business segment…",key="finance_question")
question=st.session_state.pending_question or typed_question
if question:
    st.session_state.pending_question=None
    with st.spinner("Checking the finance data and preparing your answer…"):
        try:
            result=ask(question,market)
        except Exception as exc:
            result={"answer":f"I couldn’t complete that question: {exc}","sql":None,"rows":[],"source":"Assistant","latency_ms":0,"reconciled":False}
    result["question"]=question
    result["market"]=market
    result["asked_at"]=datetime.now().strftime("%H:%M")
    st.session_state.history.append(result)
    st.rerun()
