
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate
from qiskit.quantum_info import Statevector


# Each option is one possible water transfer.
OPTIONS = [
    {"route": "Tank A -> Clinic", "water": 20, "benefit": 40, "donor": "A", "receiver": "Clinic"},
    {"route": "Tank A -> Village", "water": 15, "benefit": 24, "donor": "A", "receiver": "Village"},
    {"route": "Tank B -> Clinic", "water": 15, "benefit": 33, "donor": "B", "receiver": "Clinic"},
    {"route": "Tank B -> Village", "water": 10, "benefit": 12, "donor": "B", "receiver": "Village"},
]

DONOR_CAPACITY = {"A": 25, "B": 20}
RECEIVER_NEED = {"Clinic": 25, "Village": 25}
PENALTY = 100.0


def _cost(bitstring):
    """Lower cost is better. Over-capacity choices receive penalties."""
    selected = [
        OPTIONS[i] for i, bit in enumerate(bitstring) if bit
    ]

    benefit = sum(item["benefit"] for item in selected)
    cost = -benefit

    for donor, capacity in DONOR_CAPACITY.items():
        total = sum(x["water"] for x in selected if x["donor"] == donor)
        cost += PENALTY * max(0, total - capacity) ** 2

    for receiver, need in RECEIVER_NEED.items():
        total = sum(x["water"] for x in selected if x["receiver"] == receiver)
        cost += PENALTY * max(0, total - need) ** 2

    return float(cost)


def solve_qaoa_demo(reps=1, maxiter=40):
    """Run a small QAOA circuit using Qiskit's local statevector simulator."""
    n = len(OPTIONS)
    energies = np.array([
        _cost([(state >> i) & 1 for i in range(n)])
        for state in range(2**n)
    ])

    def circuit(params):
        gammas = params[:reps]
        betas = params[reps:]
        qc = QuantumCircuit(n)
        qc.h(range(n))

        for gamma, beta in zip(gammas, betas):
            qc.append(DiagonalGate(np.exp(-1j * gamma * energies)), range(n))
            for qubit in range(n):
                qc.rx(2 * beta, qubit)

        return qc

    def expectation(params):
        state = Statevector.from_instruction(circuit(params))
        probabilities = np.abs(state.data) ** 2
        return float(np.dot(probabilities, energies))

    result = minimize(
        expectation,
        np.random.default_rng(7).uniform(0, np.pi, 2 * reps),
        method="COBYLA",
        options={"maxiter": maxiter},
    )

    state = Statevector.from_instruction(circuit(result.x))
    probabilities = np.abs(state.data) ** 2

    # Prefer feasible solutions; among them, choose the most probable.
    feasible = []
    for index, probability in enumerate(probabilities):
        bits = [(index >> i) & 1 for i in range(n)]
        chosen = [OPTIONS[i] for i, bit in enumerate(bits) if bit]
        if _cost(bits) < 0:
            feasible.append((probability, index, chosen))

    if feasible:
        _, index, chosen = max(feasible, key=lambda x: x[0])
    else:
        index = int(np.argmax(probabilities))
        chosen = [OPTIONS[i] for i in range(n) if (index >> i) & 1]

    return {
        "method": "QAOA (Qiskit statevector simulation)",
        "transfers": chosen,
        "water_l": sum(x["water"] for x in chosen),
        "benefit": sum(x["benefit"] for x in chosen),
        "objective": _cost([(index >> i) & 1 for i in range(n)]),
        "optimizer_expectation": float(result.fun),
        "optimizer_success": bool(result.success),
        "note": "Small illustrative demo; not a hardware quantum run.",
    }
