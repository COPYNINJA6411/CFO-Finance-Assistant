import pytest
from app.security import validate_sql, SQLPolicyError

def test_select_is_capped():
    assert "TOP (500)" in validate_sql("SELECT region FROM dbo.fact_finance")

@pytest.mark.parametrize("sql",["DELETE FROM dbo.fact_finance", "SELECT * FROM dbo.fact_finance; DROP TABLE x", "SELECT * FROM dbo.other", "SELECT f.secret FROM dbo.fact_finance f", "SELECT * FROM dbo.fact_finance -- comment", "SELECT * FROM dbo.fact_finance WHERE x=1; SELECT 2"])
def test_rejected_sql(sql):
    with pytest.raises(SQLPolicyError): validate_sql(sql)

def test_approved_column_query():
    assert "gross_profit" in validate_sql("SELECT SUM(revenue)-SUM(cost) gross_profit FROM dbo.fact_finance")

def test_top_limit_is_clamped():
    assert "TOP (500)" in validate_sql("SELECT TOP (999999) region FROM dbo.fact_finance")

def test_selected_market_must_be_scoped():
    scoped=validate_sql("SELECT region FROM dbo.fact_finance",market="IN")
    assert "market = 'IN'" in scoped

def test_market_scope_cannot_be_bypassed_by_or():
    scoped=validate_sql("SELECT region FROM dbo.fact_finance WHERE market = 'US' OR region = 'West'",market="IN")
    assert "market = 'IN'" in scoped
    assert "OR" in scoped.upper()

@pytest.mark.parametrize("sql",["SELECT TOP (5) PERCENT revenue FROM dbo.fact_finance", "SELECT revenue FROM dbo.fact_finance OFFSET 2 ROWS", "SELECT * FROM dbo.fact_finance"])
def test_unbounded_or_wildcard_patterns_rejected(sql):
    with pytest.raises(SQLPolicyError): validate_sql(sql)
