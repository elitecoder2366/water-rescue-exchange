"""Simple, testable logic for the Water Rescue Exchange demo."""

def demo_fields():
    """Return illustrative field data. These are not measured farm values."""
    return [
        {
            "field": "Field A",
            "surplus_l": 40.0,
            "need_l": 0.0,
            "urgency": 1,
            "travel_min": 0,
            "deadline_min": 60,
            "authorized": True,
        },
        {
            "field": "Field B",
            "surplus_l": 0.0,
            "need_l": 25.0,
            "urgency": 10,
            "travel_min": 5,
            "deadline_min": 20,
            "authorized": True,
        },
        {
            "field": "Field C",
            "surplus_l": 0.0,
            "need_l": 20.0,
            "urgency": 6,
            "travel_min": 10,
            "deadline_min": 30,
            "authorized": True,
        },
        {
            "field": "Field D",
            "surplus_l": 0.0,
            "need_l": 15.0,
            "urgency": 3,
            "travel_min": 25,
            "deadline_min": 15,
            "authorized": True,
        },
    ]


def recommend_transfers(fields, route_capacity_l):
    """
    Greedy demo allocator. It prioritizes recipients by urgency, then deadline.
    Returns (accepted_transfers, rejected_candidates).
    """
    if route_capacity_l <= 0:
        raise ValueError("Route capacity must be greater than zero.")

    by_id = {row["field"]: dict(row) for row in fields}
    donors = {
        name: max(0.0, float(row["surplus_l"]))
        for name, row in by_id.items()
        if float(row["surplus_l"]) > 0
    }
    recipients = [
        dict(row) for row in fields if float(row["need_l"]) > 0
    ]
    recipients.sort(
        key=lambda row: (-int(row["urgency"]), int(row["deadline_min"]))
    )

    accepted = []
    rejected = []

    for recipient in recipients:
        remaining_need = max(0.0, float(recipient["need_l"]))
        for donor_name in list(donors):
            if remaining_need <= 0:
                break
            available = donors[donor_name]
            if available <= 0:
                continue
            if donor_name == recipient["field"]:
                continue

            reason = None
            if not bool(recipient.get("authorized", False)):
                reason = "Recipient transfer not authorized"
            elif float(recipient["travel_min"]) > float(recipient["deadline_min"]):
                reason = "Estimated arrival misses recipient deadline"
            elif not bool(by_id[donor_name].get("authorized", False)):
                reason = "Donor transfer not authorized"

            if reason:
                rejected.append({
                    "donor": donor_name,
                    "recipient": recipient["field"],
                    "reason": reason,
                })
                continue

            quantity = min(available, remaining_need, float(route_capacity_l))
            if quantity <= 0:
                continue

            accepted.append({
                "donor": donor_name,
                "recipient": recipient["field"],
                "quantity_l": quantity,
                "urgency": int(recipient["urgency"]),
                "travel_min": float(recipient["travel_min"]),
                "deadline_min": float(recipient["deadline_min"]),
                "status": "Passed basic demo checks",
            })
            donors[donor_name] -= quantity
            remaining_need -= quantity

    return accepted, rejected
