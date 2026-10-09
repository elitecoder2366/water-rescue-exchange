from src.quantum_allocation import build_options, run_scenario


def sample_fields():
    return [
        {"field": "Donor", "surplus_l": 12, "need_l": 0, "urgency": 1,
         "travel_min": 0, "deadline_min": 60, "authorized": True},
        {"field": "Farm A", "surplus_l": 0, "need_l": 8, "urgency": 9,
         "travel_min": 5, "deadline_min": 20, "authorized": True},
        {"field": "Farm B", "surplus_l": 0, "need_l": 8, "urgency": 4,
         "travel_min": 4, "deadline_min": 20, "authorized": True},
    ]


def test_drought_scenario_builds_candidates():
    normal = build_options(sample_fields(), 10, 1.0)
    drought = build_options(sample_fields(), 10, 0.5)
    assert normal
    assert drought
    assert all(option["water"] > 0 for option in drought)


def test_scenario_keeps_classical_baseline_and_validation_fields():
    result = run_scenario(sample_fields(), 10, drought_factor=0.8)
    assert result["classical"]["method"] == "Exact classical enumeration"
    assert "feasible" in result["classical"]
    assert "feasible" in result["qaoa"]
    assert "fairness_gap" in result["qaoa"]
    assert result["hardware"]["available"] is False
