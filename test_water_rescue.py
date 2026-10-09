import pytest
from src.water_rescue import demo_fields, recommend_transfers


def test_demo_data_has_four_fields():
    assert len(demo_fields()) == 4


def test_transfers_do_not_exceed_donor_surplus_or_recipient_need():
    fields = demo_fields()
    recs, _ = recommend_transfers(fields, route_capacity_l=20)
    assert sum(r["quantity_l"] for r in recs) <= 40
    assert all(r["quantity_l"] <= 20 for r in recs)


def test_late_recipient_is_not_selected():
    fields = demo_fields()
    recs, _ = recommend_transfers(fields, route_capacity_l=20)
    assert not any(r["recipient"] == "Field D" for r in recs)


def test_zero_capacity_rejected():
    with pytest.raises(ValueError):
        recommend_transfers(demo_fields(), route_capacity_l=0)
