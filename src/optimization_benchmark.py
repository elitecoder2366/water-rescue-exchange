"""Compare QAOA simulation with simple classical baselines on the same toy problem."""
from itertools import product
from time import perf_counter

from src.quantum_optimizer import OPTIONS, _cost, solve_qaoa_demo


def _bits_to_transfers(bits):
    return [OPTIONS[i] for i, bit in enumerate(bits) if bit]


def _feasible(bits):
    chosen = _bits_to_transfers(bits)
    for donor, capacity in {"A": 25, "B": 20}.items():
        if sum(x["water"] for x in chosen if x["donor"] == donor) > capacity:
            return False
    for receiver, need in {"Clinic": 25, "Village": 25}.items():
        if sum(x["water"] for x in chosen if x["receiver"] == receiver) > need:
            return False
    return True


def _result_row(method, bits, runtime_s):
    chosen = _bits_to_transfers(bits)
    return {
        "Method": method,
        "Selected transfers": len(chosen),
        "Water moved (L)": sum(x["water"] for x in chosen),
        "Benefit score": sum(x["benefit"] for x in chosen),
        "Objective (lower is better)": _cost(bits),
        "Feasible": _feasible(bits),
        "Runtime (seconds)": round(runtime_s, 6),
        "Transfers": ", ".join(x["route"] for x in chosen) or "None",
    }


def run_optimization_comparison():
    """Run greedy, exhaustive classical optimum, and QAOA simulation."""
    n = len(OPTIONS)

    # Greedy baseline: rank by benefit per litre, accepting only feasible additions.
    start = perf_counter()
    greedy_bits = [0] * n
    for i in sorted(range(n), key=lambda j: OPTIONS[j]["benefit"] / OPTIONS[j]["water"], reverse=True):
        candidate = greedy_bits.copy()
        candidate[i] = 1
        if _feasible(candidate):
            greedy_bits = candidate
    greedy_time = perf_counter() - start

    # Exact classical baseline: enumerate every bitstring and keep the best feasible one.
    start = perf_counter()
    feasible_states = []
    for bits in product([0, 1], repeat=n):
        bits = list(bits)
        if _feasible(bits):
            feasible_states.append(( _cost(bits), bits))
    exact_cost, exact_bits = min(feasible_states, key=lambda item: item[0])
    exact_time = perf_counter() - start

    # QAOA is stochastic/approximate; report the selected candidate and measured runtime.
    start = perf_counter()
    qaoa = solve_qaoa_demo()
    qaoa_time = perf_counter() - start
    qaoa_bits = [0] * n
    selected_routes = {item["route"] for item in qaoa["transfers"]}
    for i, item in enumerate(OPTIONS):
        qaoa_bits[i] = int(item["route"] in selected_routes)

    rows = [
        _result_row("Greedy classical baseline", greedy_bits, greedy_time),
        _result_row("Exact classical search (optimal)", exact_bits, exact_time),
        _result_row("QAOA statevector simulation", qaoa_bits, qaoa_time),
    ]
    return {
        "results": rows,
        "exact_objective": exact_cost,
        "note": (
            "All methods use the same four-option toy objective and capacity constraints. "
            "Exact search is the classical optimum for this small instance. Runtime is a "
            "single local measurement and is not a general performance benchmark. QAOA runs "
            "on a classical statevector simulator, not physical quantum hardware."
        ),
    }
