# Messages capability acceptance scope

The 34.2.1 policy retains all 323 mandatory fields and all 183 runtime-required
fields from source contract fb5f16f11f3f66fce97a5eeb5f5a862ab71949ce.
The contract test fixes both canonical field-set hashes to prevent scope reduction.

283 mandatory fields have observations in real schema- and lifecycle-validated
producer streams. The other 40 remain Pending, with evidence requirements recorded
in each decision. Pending entries are release blockers; they are not owner-approved
exceptions. Full governance acceptance must fail until these entries are proved or
explicit exceptions are agreed. A simple passing scenario does not cover the full
runtime scope and must fail the strict runtime-coverage gate.

The recorded field observations concern the referenced integration checkpoints.
They do not replace acceptance of the final commit or the complete runtime matrix.
