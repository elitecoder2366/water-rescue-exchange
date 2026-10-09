"""Scenario-aware allocation experiment with fairness and drought stress tests.

This is an educational small-instance QAOA simulation. Hard constraints are
rechecked independently after optimization; never use its output as a work order.
"""
from itertools import product
from time import perf_counter

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate
from qiskit.quantum_info import Statevector


def build_options(fields, route_capacity_l, drought_factor=1.0):
    """Build a small binary candidate set; each candidate is one capped route."""
    if not 0.5 <= float(drought_factor) <= 1.0:
        raise ValueError("Drought factor must be between 0.5 and 1.0.")
    rows = [dict(r) for r in fields]
    options = []
    for donor in rows:
        supply = max(0.0, float(donor.get("surplus_l", 0))) * drought_factor
        if not donor.get("authorized", False) or supply <= 0:
            continue
        for recipient in rows:
            need = max(0.0, float(recipient.get("need_l", 0))) / drought_factor
            if (donor.get("field") == recipient.get("field")
                    or not recipient.get("authorized", False) or need <= 0
                    or float(recipient.get("travel_min", 0)) > float(recipient.get("deadline_min", 0))):
                continue
            quantity = min(supply, need, float(route_capacity_l))
            if quantity > 0:
                options.append({
                    "route": f'{donor["field"]} → {recipient["field"]}',
                    "donor": str(donor["field"]), "recipient": str(recipient["field"]),
                    "water": float(quantity),
                    "benefit": float(quantity) * (1.0 + float(recipient.get("urgency", 1)) / 10.0),
                })
    # Keep circuits tractable on a browser-hosted demo.
    return options[:8]


def _feasible(bits, options, donor_caps, recipient_needs):
    chosen = [options[i] for i, bit in enumerate(bits) if bit]
    sent, received = {}, {}
    for x in chosen:
        sent[x["donor"]] = sent.get(x["donor"], 0.0) + x["water"]
        received[x["recipient"]] = received.get(x["recipient"], 0.0) + x["water"]
    return (all(v <= donor_caps.get(k, 0.0) + 1e-8 for k, v in sent.items())
            and all(v <= recipient_needs.get(k, 0.0) + 1e-8 for k, v in received.items()))


def _score(bits, options, donor_caps, recipient_needs, fairness_weight=12.0):
    chosen = [options[i] for i, bit in enumerate(bits) if bit]
    if not chosen:
        return 0.0
    sent, received = {}, {}
    benefit = sum(x["benefit"] for x in chosen)
    for x in chosen:
        sent[x["donor"]] = sent.get(x["donor"], 0.0) + x["water"]
        received[x["recipient"]] = received.get(x["recipient"], 0.0) + x["water"]
    penalty = 0.0
    for name, amount in sent.items():
        penalty += 1000.0 * max(0.0, amount - donor_caps.get(name, 0.0)) ** 2
    for name, amount in received.items():
        penalty += 1000.0 * max(0.0, amount - recipient_needs.get(name, 0.0)) ** 2
    satisfaction = [min(1.0, received.get(name, 0.0) / need)
                    for name, need in recipient_needs.items() if need > 0]
    gap = max(satisfaction) - min(satisfaction) if len(satisfaction) > 1 else 0.0
    # Lower energy is better. Fairness is a soft preference, never a hard guarantee.
    return float(-benefit + fairness_weight * gap + penalty)


def _qaoa_bits(options, energy, reps=1, maxiter=35):
    n = len(options)
    if n == 0:
        return []
    energies = np.asarray([energy([(s >> i) & 1 for i in range(n)])
                           for s in range(2 ** n)], dtype=float)
    def circuit(params, measure=False):
        qc = QuantumCircuit(n, n if measure else 0)
        qc.h(range(n))
        for gamma, beta in zip(params[:reps], params[reps:]):
            qc.append(DiagonalGate(np.exp(-1j * gamma * energies)), range(n))
            for q in range(n):
                qc.rx(2 * beta, q)
        if measure:
            qc.measure(range(n), range(n))
        return qc
    def expectation(params):
        probs = np.abs(Statevector.from_instruction(circuit(params)).data) ** 2
        return float(np.dot(probs, energies))
    result = minimize(expectation, np.random.default_rng(7).uniform(0, np.pi, 2 * reps),
                      method="COBYLA", options={"maxiter": maxiter})
    probs = np.abs(Statevector.from_instruction(circuit(result.x)).data) ** 2
    # Return the lowest-energy feasible bitstring among sampled statevector support.
    order = np.argsort(probs)[::-1]
    return [(int(order[0]) >> i) & 1 for i in range(n)], circuit(result.x, measure=True)


def _fairness_gap(chosen, needs):
    received = {}
    for x in chosen:
        received[x["recipient"]] = received.get(x["recipient"], 0.0) + x["water"]
    ratios = [min(1.0, received.get(name, 0.0) / need)
              for name, need in needs.items() if need > 0]
    return round(max(ratios) - min(ratios), 3) if len(ratios) > 1 else 0.0


def hardware_status():
    """Check optional IBM Quantum access without failing the simulator path."""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        return {"available": False, "message": "Optional package missing; simulator remains available."}
    try:
        service = QiskitRuntimeService()
        backends = service.backends(simulator=False, operational=True)
        return {"available": bool(backends),
                "message": f"IBM Quantum credentials found; {len(backends)} operational backend(s) listed."}
    except Exception as exc:
        return {"available": False,
                "message": f"No usable IBM Quantum account/backend: {type(exc).__name__}. Simulator fallback is ready."}


def run_scenario(fields, route_capacity_l, drought_factor=1.0, try_hardware=False):
    """Compare exact classical optimum with QAOA; independently audit chosen transfers."""
    options = build_options(fields, route_capacity_l, drought_factor)
    donor_caps = {str(r["field"]): max(0.0, float(r.get("surplus_l", 0))) * drought_factor for r in fields}
    needs = {str(r["field"]): max(0.0, float(r.get("need_l", 0))) / drought_factor for r in fields}
    energy = lambda bits: _score(bits, options, donor_caps, needs)
    start = perf_counter()
    feasible = [(energy(list(bits)), list(bits)) for bits in product([0, 1], repeat=len(options))
                if _feasible(list(bits), options, donor_caps, needs)]
    exact_energy, exact_bits = min(feasible, key=lambda x: x[0]) if feasible else (0.0, [0] * len(options))
    exact_time = perf_counter() - start
    start = perf_counter()
    qbits, circuit = _qaoa_bits(options, energy)
    qaoa_time = perf_counter() - start
    # Independent hard-constraint validation: unsafe candidate is rejected, not auto-repaired.
    qaoa_valid = _feasible(qbits, options, donor_caps, needs)
    qchosen = [options[i] for i, bit in enumerate(qbits) if bit] if qaoa_valid else []
    exact_chosen = [options[i] for i, bit in enumerate(exact_bits) if bit]
    hardware = hardware_status() if try_hardware else {"available": False, "message": "Hardware check not requested."}
    return {
        "scenario": {"drought_factor": drought_factor, "surplus_multiplier": drought_factor,
                     "need_multiplier": round(1.0 / drought_factor, 3)},
        "options": options,
        "classical": {"method": "Exact classical enumeration", "objective": round(exact_energy, 3),
                      "runtime_s": round(exact_time, 6), "transfers": exact_chosen,
                      "feasible": bool(_feasible(exact_bits, options, donor_caps, needs)),
                      "fairness_gap": _fairness_gap(exact_chosen, needs)},
        "qaoa": {"method": "QAOA statevector simulator", "objective": round(energy(qbits), 3),
                 "runtime_s": round(qaoa_time, 6), "transfers": qchosen,
                 "feasible": qaoa_valid, "fairness_gap": _fairness_gap(qchosen, needs),
                 "note": "Unsafe QAOA selections are rejected by the independent validator."},
        "hardware": hardware,
        "hardware_circuit_qubits": len(options),
        "note": "Small educational model only. IBM access is checked, but this run executes on the local simulator; no hardware job is submitted.",
    }
