# Optimization model — planned

The current implementation is a greedy baseline, not an optimization solver.

For each donor field i, estimate safe surplus U_i. For each recipient j, estimate unmet demand N_j. A transfer option a has donor i(a), recipient j(a), quantity q_a, travel time t_a, and benefit b_a based on urgency and delivery timing.

A future binary decision variable x_a indicates whether transfer option a is selected.

Example objective:

Maximize total urgency-weighted useful water delivered:

    maximize sum_a b_a * q_a * x_a

Subject to:

- Sum of outgoing transfer quantities from donor i <= U_i
- Sum of incoming quantities to recipient j <= N_j
- Flow on every shared canal segment and time slot <= its capacity
- Transfer is authorized and arrives before the deadline
- x_a is binary

This model must be extended for shared routes, time slots, crop-specific stress, and real hydraulic constraints before it can represent a real canal network.

QAOA is a planned experiment only. A future QUBO formulation will need explicit constraint encodings and comparison with classical optimization.
