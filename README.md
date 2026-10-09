# 💧 Water Rescue Exchange

**Smarter Water Distribution • Stronger Communities • A Safer Tomorrow**

Water Rescue Exchange is a prototype water-allocation platform designed to help communities manage water shortages and emergency situations. It uses supply and demand data to suggest possible transfers from areas with surplus water to areas facing shortages, and includes an educational QAOA optimization demo using Qiskit's local simulator.

[![Hackathon Project](https://img.shields.io/badge/Project-Hackathon-12345A)](https://github.com/elitecoder2366/water-rescue-exchange)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://water-rescue-exchange-cqti59sqcvw7zyto6fa65h.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Quantum_Demo-Qiskit-6929C4)](https://www.ibm.com/quantum/qiskit)

## 📌 Problem Statement

Water scarcity and uneven distribution can create serious challenges, especially during emergencies. Different locations may have different water supplies and demand levels, making it difficult to decide where available water should go.

Water Rescue Exchange explores how a simple data-driven application can help users review water availability and identify potential transfer recommendations.

## 💡 Our Solution

- **Water allocation dashboard:** Enter or review water supply and demand information.
- **Transfer recommendations:** Suggest potential transfers from surplus areas to areas with shortages.
- **QAOA demo:** Demonstrate a simplified optimization example using Qiskit's local quantum simulator.
- **Classical baseline comparison:** Compare a greedy baseline, exact classical search, and QAOA simulation on the same small illustrative problem; view objective scores, feasibility, selected transfers, and one-run runtime.
- **Scenario testing:** Check normal, high-demand, zero-supply, and insufficient-water situations.
- **Accessible interface:** A Streamlit app makes the prototype easy to try.

## ✨ Key Features

### 💧 Water Allocation Dashboard
Review water supply and demand values and view suggested water transfers.

### ⚛️ QAOA Optimization Demo
Explore a small example of the Quantum Approximate Optimization Algorithm (QAOA). The demo runs in software using a local simulator; it does **not** use a physical quantum computer.

### 🧪 Multiple Scenarios
Try different supply and demand situations to see how the prototype responds. Verify outputs before using them for any real operational decision.

### 📊 Classical vs QAOA Comparison
Run the benchmark from the app to compare greedy selection, exact classical search (the optimum for this small instance), and QAOA statevector simulation using the same toy objective and capacity limits. Results include water moved, benefit score, objective value, feasibility, selected transfers, and a single measured runtime. You can export the table as CSV.

**Interpretation:** The exact classical search is the reference optimum for this small problem. QAOA is approximate and may not match it. Runtime from a single small simulation is illustrative, not a general performance benchmark, and this demo makes no claim of quantum advantage.

### 🖥️ Simple User Interface
Built with Streamlit for an interactive, browser-based experience.

## 🧰 Tech Stack

- Python
- Streamlit
- Pandas
- Qiskit
- SciPy
- NumPy
- Pytest

## 🚀 Live Demo

Try the deployed application:

**https://water-rescue-exchange-cqti59sqcvw7zyto6fa65h.streamlit.app/**

## 🛠️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/elitecoder2366/water-rescue-exchange.git
cd water-rescue-exchange
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the app

```bash
streamlit run app.py
```

Streamlit will print a local URL in your terminal; open it in your browser.

## 📁 Project Structure

```text
water-rescue-exchange/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── runtime.txt               # Python runtime version for deployment
├── src/
│   ├── water_rescue.py       # Water-allocation logic
│   ├── quantum_optimizer.py  # QAOA demo using Qiskit\n│   └── optimization_benchmark.py # Classical baselines vs QAOA comparison
├── tests/
│   └── test_water_rescue.py  # Tests for allocation logic
└── README.md                 # Project documentation
```

## ⚛️ QAOA Demo: What It Does (and Doesn't Do)

The Quantum Approximate Optimization Algorithm (QAOA) is a hybrid quantum-classical optimization approach. In this project, Qiskit simulates a small quantum circuit locally, while a classical optimizer adjusts parameters to search for a candidate solution to a simplified example.

- **Simulator only:** No physical quantum hardware is used.
- **Illustrative example:** The demo uses a simplified problem and should not be treated as a complete optimizer for real-world water distribution.
- **No proven quantum advantage:** This project does not claim that QAOA is faster or better than classical optimization.
- **Further validation needed:** A real deployment would require realistic data, operational constraints, fairness and safety checks, and expert evaluation.

## 🧪 Testing

If the project includes the test dependencies, run:

```bash
pytest
```

Review the test results and manually try several scenarios in the app before presenting the prototype.

## ⚠️ Limitations and Responsible Use

This is an educational and hackathon prototype, not a production emergency-response system. Recommendations should be validated against real-world conditions and reviewed by relevant water-management experts before any operational use.

## 🌍 Future Improvements

- Integrate reliable, up-to-date water supply and demand data.
- Add geographic maps and validated transport constraints.
- Include fairness, priority, and emergency constraints in allocation.
- Compare optimization results against classical baselines (a small demo benchmark is now included).
- Evaluate whether QAOA offers any practical benefit on appropriately sized benchmark problems.

## 👥 Project

**Repository:** https://github.com/elitecoder2366/water-rescue-exchange  
**Live app:** https://water-rescue-exchange-cqti59sqcvw7zyto6fa65h.streamlit.app/

---

**💙 Save Water • Save Lives**
