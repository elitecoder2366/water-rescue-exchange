# Architecture

## Current prototype

```text
Editable demo field data
          |
          v
Streamlit interface (app.py)
          |
          v
Greedy recommendation logic (src/water_rescue.py)
          |
          v
Basic checks: authorization, volume, travel time/deadline
          |
          v
Recommendation table + rejected-candidate reasons
```

The prototype has no hardware connection. All data is supplied by the user in the dashboard.

## Later architecture (planned)

Sensors -> validated readings -> surplus/demand estimator -> feasible transfer generator
-> optimizer -> independent safety validator -> human approval -> gate controller
-> measured delivery reconciliation.

The optimizer must never directly command physical gates. A separate safety layer and manual override are required.
