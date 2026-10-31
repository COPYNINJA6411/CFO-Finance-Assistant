"""Read-only SQL policy. Defense in depth: lexical policy plus database read-only identity recommended."""
import re
from dataclasses import dataclass

APPROVED_COLUMNS = {
    "fact_finance": {"market", "currency", "date", "region", "product", "segment", "revenue", "cost"},
}
DENIED = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|merge|exec(?:ute)?|grant|revoke|backup|restore|into|use)\b", re.I)

@dataclass
class SQLPolicyError(ValueError):
    message: str
    def __str__(self): return self.message

def validate_sql(sql: str, limit: int = 500, market: str | None = None) -> str:
    """Accept a single SELECT over the approved view/table, with an enforced row cap."""
    q = sql.strip().rstrip(";").strip()
    if not q or not re.match(r"(?is)^select\b", q): raise SQLPolicyError("Only a single SELECT statement is allowed.")
    if ";" in q: raise SQLPolicyError("Multiple SQL statements are not allowed.")
    if "--" in q or "/*" in q or "*/" in q: raise SQLPolicyError("SQL comments are not allowed.")
    if DENIED.search(q): raise SQLPolicyError("The query contains a blocked SQL operation or keyword.")
    if not re.search(r"(?i)\bfact_finance\b", q): raise SQLPolicyError("Query must use the approved fact_finance dataset.")
    if market is not None and market not in {"US","IN"}:
        raise SQLPolicyError("Unsupported market dataset.")
    # Restrict identifier references; aliases and SQL syntax are allowed, but unknown qualified fields are not.
    if re.search(r"(?i)\b(fact_finance|f)\.([A-Za-z_]\w*)", q):
        for _, col in re.findall(r"(?i)\b(fact_finance|f)\.([A-Za-z_]\w*)", q):
            if col.lower() not in APPROVED_COLUMNS["fact_finance"]: raise SQLPolicyError(f"Column '{col}' is not approved.")
    # Reject dangerous functions / system catalog access.
    if re.search(r"(?i)\b(openrowset|opendatasource|xp_cmdshell|sys\.|information_schema)\b", q): raise SQLPolicyError("System objects and external access are blocked.")
    try:
        import sqlglot
        from sqlglot import exp
        tree=sqlglot.parse_one(q, read="tsql")
        if not isinstance(tree, exp.Select): raise SQLPolicyError("Only a SELECT statement is allowed.")
        tables=list(tree.find_all(exp.Table))
        if not tables or any(t.name.lower()!="fact_finance" or (t.db and t.db.lower()!="dbo") for t in tables):
            raise SQLPolicyError("Only dbo.fact_finance is approved for access.")
        aliases={a.alias.lower() for a in tree.find_all(exp.Alias)}
        for col in tree.find_all(exp.Column):
            name=col.name.lower()
            if name=="*": raise SQLPolicyError("Wildcard column access is not allowed; select approved fields explicitly.")
            if name not in APPROVED_COLUMNS["fact_finance"] and name not in aliases:
                raise SQLPolicyError(f"Column '{col.name}' is not approved.")
        if any(not isinstance(star.parent,exp.Count) for star in tree.find_all(exp.Star)):
            raise SQLPolicyError("Wildcard column access is not allowed; select approved fields explicitly.")
        if market is not None:
            # Add the selected-market predicate as a top-level AND term. This remains
            # safe even if model SQL contains an OR expression that tries to broaden rows.
            def top_level_terms(node):
                if isinstance(node, exp.And): return top_level_terms(node.this)+top_level_terms(node.expression)
                return [node]
            where=tree.args.get("where")
            terms=top_level_terms(where.this) if where else []
            scoped=any(isinstance(term,exp.EQ) and isinstance(term.this,exp.Column)
                      and term.this.name.lower()=="market" and isinstance(term.expression,exp.Literal)
                      and term.expression.this.upper()==market for term in terms)
            if not scoped:
                predicate=exp.EQ(this=exp.column("market"),expression=exp.Literal.string(market))
                tree=tree.where(predicate,append=True)
            q=tree.sql(dialect="tsql")
    except ImportError:
        # The package is a required runtime dependency; this fallback preserves basic
        # policy if validation is imported in a minimal test environment.
        if market is not None: raise SQLPolicyError("Market scoping requires the sqlglot runtime dependency.")
        if re.search(r"(?i)select\s+\*",q): raise SQLPolicyError("Wildcard column access is not allowed.")
        if re.search(r"(?i)\b(from|join)\s+(?!dbo\.fact_finance\b)[\w.\[\]]+",q): raise SQLPolicyError("Only dbo.fact_finance is approved for access.")
    except SQLPolicyError:
        raise
    except Exception as exc:
        raise SQLPolicyError(f"SQL could not be parsed safely: {exc}") from exc
    top=re.search(r"(?i)\bTOP\s*(?:\(\s*(\d+)\s*\)|(\d+))(\s+PERCENT|\s+WITH\s+TIES)?",q)
    if top:
        amount_group=1 if top.group(1) is not None else 2
        if top.group(3): raise SQLPolicyError("TOP PERCENT and WITH TIES are not allowed.")
        if int(top.group(amount_group))>limit:
            q=q[:top.start(amount_group)]+str(limit)+q[top.end(amount_group):]
    else:
        if re.search(r"(?i)\b(limit|offset|fetch)\b",q): raise SQLPolicyError("Use a bounded TOP clause for SQL Server queries.")
        q = re.sub(r"(?i)^select\s+", f"SELECT TOP ({limit}) ", q, count=1)
    return q
