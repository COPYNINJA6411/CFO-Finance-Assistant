"""Create SQL Server schema and seed reproducible sample data."""
import os, time
from sqlalchemy import create_engine, text
from app.data import sample_data, MARKETS

DDL = """
IF OBJECT_ID('dbo.fact_finance','U') IS NULL
CREATE TABLE dbo.fact_finance (
  id BIGINT IDENTITY(1,1) PRIMARY KEY,
  market NVARCHAR(2) NOT NULL CONSTRAINT DF_fact_finance_market DEFAULT 'US',
  currency NVARCHAR(3) NOT NULL CONSTRAINT DF_fact_finance_currency DEFAULT 'USD',
  [date] DATE NOT NULL, region NVARCHAR(40) NOT NULL,
  product NVARCHAR(80) NOT NULL, segment NVARCHAR(40) NOT NULL,
  revenue DECIMAL(18,2) NOT NULL, cost DECIMAL(18,2) NOT NULL,
  CONSTRAINT CK_fact_finance_nonnegative CHECK (revenue >= 0 AND cost >= 0)
);
IF COL_LENGTH('dbo.fact_finance','market') IS NULL
  ALTER TABLE dbo.fact_finance ADD market NVARCHAR(2) NOT NULL CONSTRAINT DF_fact_finance_market DEFAULT 'US' WITH VALUES;
IF COL_LENGTH('dbo.fact_finance','currency') IS NULL
  ALTER TABLE dbo.fact_finance ADD currency NVARCHAR(3) NOT NULL CONSTRAINT DF_fact_finance_currency DEFAULT 'USD' WITH VALUES;
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_fact_finance_market_date_region' AND object_id=OBJECT_ID('dbo.fact_finance'))
  CREATE INDEX IX_fact_finance_market_date_region ON dbo.fact_finance(market,[date],region);
"""

def main():
    url = os.getenv("DATABASE_URL")
    if not url: raise RuntimeError("Set DATABASE_URL before seeding SQL Server.")
    engine = create_engine(url, pool_pre_ping=True)
    for attempt in range(30):
      try:
        with engine.begin() as conn: conn.execute(text(DDL))
        break
      except Exception:
        if attempt == 29: raise
        time.sleep(2)
    for market,cfg in MARKETS.items():
      with engine.connect() as conn:
        existing = conn.execute(text("SELECT COUNT_BIG(*) FROM dbo.fact_finance WHERE market=:market"),{"market":market}).scalar_one()
      if existing:
        print(f"dbo.fact_finance already contains {existing:,} {market} rows; leaving them unchanged")
        continue
      df=sample_data(market)
      df.to_sql("fact_finance", engine, schema="dbo", if_exists="append", index=False, chunksize=500)
      print(f"Seeded {len(df):,} {cfg['name']} rows ({cfg['currency']}) into dbo.fact_finance")

if __name__ == "__main__": main()
