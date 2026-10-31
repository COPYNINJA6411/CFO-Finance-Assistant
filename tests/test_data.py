from app.data import sample_data

def test_seed_is_deterministic():
    a,b=sample_data(),sample_data()
    assert len(a)==len(b)==2160
    assert a.equals(b)

def test_south_margin_deteriorates_q2_2026():
    df=sample_data(); df["q"]=df.date.dt.quarter
    south=df[df.region=="South"]
    q1=south[(south.date.dt.year==2026)&(south.q==1)]
    q2=south[(south.date.dt.year==2026)&(south.q==2)]
    assert (q2.revenue.sum()-q2.cost.sum())/q2.revenue.sum() < (q1.revenue.sum()-q1.cost.sum())/q1.revenue.sum()

def test_india_dataset_is_separate_and_native_inr():
    from app.data import sample_data
    us=sample_data("US"); india=sample_data("IN")
    assert len(india)==len(us)==2160
    assert set(india.currency)=={"INR"} and set(india.market)=={"IN"}
    assert set(us.currency)=={"USD"} and set(us.market)=={"US"}
    assert not india.revenue.equals(us.revenue)

def test_indian_currency_uses_lakh_and_crore_formatting():
    from app.currency import format_amount, format_compact
    assert format_amount(12_345_678,"IN")=="₹1,23,45,678"
    assert format_compact(12_345_678,"IN")=="₹1.2Cr"
