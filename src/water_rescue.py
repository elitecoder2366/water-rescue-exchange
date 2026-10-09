"""Simple, testable logic for the Water Rescue Exchange demo."""


def demo_fields():
    """Return illustrative field data. These are not measured farm values."""
    return [
        {"field": "Field A", "surplus_l": 40.0, "need_l": 0.0, "urgency": 1, "travel_min": 0, "deadline_min": 60, "authorized": True},
        {"field": "Field B", "surplus_l": 0.0, "need_l": 25.0, "urgency": 10, "travel_min": 5, "deadline_min": 20, "authorized": True},
        {"field": "Field C", "surplus_l": 0.0, "need_l": 20.0, "urgency": 6, "travel_min": 10, "deadline_min": 30, "authorized": True},
        {"field": "Field D", "surplus_l": 0.0, "need_l": 15.0, "urgency": 3, "travel_min": 25, "deadline_min": 15, "authorized": True},
    ]


def audit_allocation(fields, transfers):
    """Return prototype safety checks and simple fairness indicators; not a certification."""
    by_id = {row["field"]: row for row in fields}
    delivered = {name: 0.0 for name in by_id}
    violations = []
    for transfer in transfers:
        donor = transfer.get("donor")
        recipient = transfer.get("recipient")
        quantity = float(transfer.get("quantity_l", 0))
        if donor not in by_id or recipient not in by_id:
            violations.append("Transfer references an unknown field.")
            continue
        if donor == recipient:
            violations.append(f"{donor}: self-transfer is not allowed.")
        if quantity <= 0:
            violations.append(f"{donor} → {recipient}: transfer quantity must be positive.")
        if quantity > float(by_id[donor].get("surplus_l", 0)):
            violations.append(f"{donor}: transfer exceeds the listed safe surplus.")
        if not bool(by_id[donor].get("authorized", False)) or not bool(by_id[recipient].get("authorized", False)):
            violations.append(f"{donor} → {recipient}: authorization is missing.")
        if float(by_id[recipient].get("travel_min", 0)) > float(by_id[recipient].get("deadline_min", 0)):
            violations.append(f"{recipient}: estimated arrival misses the deadline.")
        if quantity > 0 and recipient in delivered:
            delivered[recipient] += quantity

    needs = {name: max(0.0, float(row.get("need_l", 0))) for name, row in by_id.items()}
    satisfaction = [
        min(1.0, delivered[name] / need) if need > 0 else None
        for name, need in needs.items()
    ]
    measured = [value for value in satisfaction if value is not None]
    fairness_gap = (max(measured) - min(measured)) if measured else 0.0
    return {
        "checks_passed": not violations,
        "violations": violations,
        "delivered_l": delivered,
        "need_satisfaction": satisfaction,
        "fairness_gap": round(fairness_gap, 3),
        "note": "Prototype audit only. This is not a production-grade safety, fairness, legal, or hydraulic validation.",
    }


def build_simulated_control_plan(transfers):
    """Create a non-actuating preview; never sends commands to physical equipment."""
    return [
        {
            "step": i + 1,
            "simulated_action": "PREVIEW ONLY — do not execute automatically",
            "donor": row.get("donor", "Unknown"),
            "recipient": row.get("recipient", "Unknown"),
            "quantity_l": float(row.get("quantity_l", 0)),
            "status": "Not sent to any pump, gate, PLC, or IoT device",
        }
        for i, row in enumerate(transfers)
    ]


def recommend_transfers(fields, route_capacity_l):
    """
    Greedy demo allocator. Prioritizes recipients by urgency, then deadline.
    Returns (accepted_transfers, rejected_candidates).
    """
    if route_capacity_l <= 0:
        raise ValueError("Route capacity must be greater than zero.")

    by_id = {row["field"]: dict(row) for row in fields}
    for row in fields:
        if float(row.get("surplus_l", 0)) < 0 or float(row.get("need_l", 0)) < 0:
            raise ValueError("Surplus and need must be zero or greater.")
        if not 1 <= int(row.get("urgency", 1)) <= 10:
            raise ValueError("Urgency must be between 1 and 10.")
        if float(row.get("travel_min", 0)) < 0 or float(row.get("deadline_min", 0)) < 0:
            raise ValueError("Travel time and deadline must be zero or greater.")

    donors = {
        name: max(0.0, float(row["surplus_l"]))
        for name, row in by_id.items()
        if float(row["surplus_l"]) > 0
    }
    recipients = [dict(row) for row in fields if float(row["need_l"]) > 0]
    recipients.sort(key=lambda row: (-int(row["urgency"]), int(row["deadline_min"])))

    accepted = []
    rejected = []
    for recipient in recipients:
        remaining_need = max(0.0, float(recipient["need_l"]))
        for donor_name in list(donors):
            if remaining_need <= 0:
                break
            available = donors[donor_name]
            if available <= 0 or donor_name == recipient["field"]:
                continue

            reason = None
            if not bool(recipient.get("authorized", False)):
                reason = "Recipient transfer not authorized"
            elif float(recipient["travel_min"]) > float(recipient["deadline_min"]):
                reason = "Estimated arrival misses recipient deadline"
            elif not bool(by_id[donor_name].get("authorized", False)):
                reason = "Donor transfer not authorized"

            if reason:
                rejected.append({"donor": donor_name, "recipient": recipient["field"], "reason": reason})
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
                "status": "Passed basic demo checks — human review still required",
            })
            donors[donor_name] -= quantity
            remaining_need -= quantity

    return accepted, rejected
