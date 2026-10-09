```python
"""Small QUBO water-transfer demo.
Uses classical exhaustive search, NOT quantum hardware.
"""

from itertools import product


def solve_qubo_demo(fields, unit_liters=10):
    """Build and solve a small pairwise-conflict QUBO classically."""

    donors = []
    receivers = []

    for field in fields:
        available = float(field.get("available_water", 0))
        need = float(field.get("water_need", 0))

        if available > need:
            donors.append({
                "name": field.get("name", field.get("field_id", "Donor")),
                "surplus": available - need,
            })
        elif available < need:
            receivers.append({
                "name": field.get("name", field.get("field_id", "Receiver")),
                "deficit": need - available,
                "deadline": float(field.get("deadline_hours", 24)),
            })

    options = []

    for donor in donors:
        for receiver in receivers:
            amount = min(
                float(unit_liters),
                donor["surplus"],
                receiver["deficit"],
            )
            if amount > 0:
                # Earlier deadlines receive a higher priority.
                urgency = 1.0 / max(receiver["deadline"], 1.0)
                options.append({
                    "from": donor["name"],
                    "to": receiver["name"],
                    "liters": amount,
                    "benefit": amount * (1.0 + urgency),
                })

    # Keep enumeration small for this educational demo.
    options = options[:12]
    n = len(options)

    if n == 0:
        return {
            "method": "Classical exhaustive search over QUBO",
            "status": "No eligible transfer options",
            "transfers": [],
            "qubo_variables": 0,
            "best_energy": 0,
        }

    # QUBO energy: E(x) = sum(q_i*x_i) + sum(q_ij*x_i*x_j)
    # Lower energy is better. Pairwise conflicts get a penalty.
    penalty = 1000.0
    linear = [-item["benefit"] for item in options]
    conflicts = {}

    for i in range(n):
        for j in range(i + 1, n):
            a, b = options[i], options[j]

            same_donor = a["from"] == b["from"]
            same_receiver = a["to"] == b["to"]

            conflict = False

            if same_donor:
                donor = next(d for d in donors if d["name"] == a["from"])
                conflict |= a["liters"] + b["liters"] > donor["surplus"]

            if same_receiver:
                receiver = next(
                    r for r in receivers if r["name"] == a["to"]
                )
                conflict |= (
                    a["liters"] + b["liters"] > receiver["deficit"]
                )

            if conflict:
                conflicts[(i, j)] = penalty

    best_bits = None
    best_energy = float("inf")

    for bits in product((0, 1), repeat=n):
        energy = sum(linear[i] * bits[i] for i in range(n))

        for (i, j), weight in conflicts.items():
            energy += weight * bits[i] * bits[j]

        if energy < best_energy:
            best_energy = energy
            best_bits = bits

    chosen = [
        {**options[i]}
        for i, bit in enumerate(best_bits)
        if bit
    ]

    return {
        "method": "Classical exhaustive search over QUBO",
        "status": "Completed",
        "transfers": chosen,
        "qubo_variables": n,
        "best_energy": round(best_energy, 3),
        "quantum_hardware_used": False,
    }
```
