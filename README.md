# Water Rescue Exchange 💧

**A prototype for deadline-aware irrigation water reallocation.**

Water Rescue Exchange explores a practical question: when one field has water it can safely spare, can that water be redirected to another field that needs it more urgently?

This first version is intentionally small. It uses editable demo data and a simple urgency-first greedy rule to recommend transfers that pass basic checks.

## What works in this version

- Editable sample data for four fields
- Donor surplus and recipient unmet-need inputs
- Basic transfer authorization checks
- Simplified route-volume limit
- Deadline-versus-travel-time check
- Transfer recommendation table and rejected-transfer explanations
- Unit tests for basic behavior

## What is not implemented yet

- Live sensors or real-time canal data
- Real hydraulic modelling or a calibrated canal network
- Farmer accounts or legal water-rights integration
- QAOA or any quantum solver
- Physical gate control

All included values are illustrative. The app is not intended to make real irrigation decisions.

## Run locally

Install Python 3.10 or newer, open a terminal in this folder, and run:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install dependencies and start the app:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Run tests:

```bash
python -m pytest -q
```

## Project layout

```text
app.py                  Streamlit interface
src/water_rescue.py     Basic transfer recommendation logic
tests/                  Unit tests
docs/                   Design notes and references
```

## Planned work

1. Improve donor surplus estimation using remaining crop needs and safety reserves.
2. Model shared canal segments and time-dependent capacity.
3. Compare the greedy rule with a classical optimization solver.
4. Formulate a small constrained transfer problem for an experimental QAOA comparison.
5. Add sensor integration only after simulation and safety tests work.

## Why compare against classical methods?

A quantum-inspired or quantum solver should not be assumed to outperform a classical method. Any QAOA experiment will be compared on the same test cases against a classical baseline, with feasibility and runtime reported.

## References

See [`docs/references.md`](docs/references.md) for related repositories and research starting points.

## Safety note

This is an educational prototype. Any real transfer would require farmer consent, applicable allocation permissions, measured physical availability, hydraulic validation, and independent safety checks.
