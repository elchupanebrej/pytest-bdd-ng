# Messages capability acceptance scope

The 34.2.1 policy retains all 323 mandatory fields and all 183 runtime-required
fields from source contract fb5f16f11f3f66fce97a5eeb5f5a862ab71949ce.
The contract test fixes both canonical field-set hashes to prevent scope reduction.

All 494 current-schema fields, including both original scopes, were observed in a
single real producer stream at 0380725582437830e38262ca5aeff473d066fc38. Each decision
references its field evidence, stream hash and line. The profile includes combined
step arguments, source hooks, attachments, collection and runtime errors, and
controlled CI environment inputs. CI metadata presence does not prove a cloud CI run.

These observations establish field presence. They do not establish complete semantic
parity or replace acceptance of the final commit and the complete runtime matrix.
No owner exceptions were inferred. A simple passing scenario still lacks observations
for the full runtime scope and must fail the strict runtime-coverage gate. Implemented
fields without observations in a supplied report remain release blockers.
