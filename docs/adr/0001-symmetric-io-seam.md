# 1. Symmetric send/receive seam in the client library

Date: 2026-07-20

## Status

Accepted

## Context

v1 of the Z21 Home Assistant integration is monitor-only: it subscribes to
System State broadcasts and exposes them as sensors and binary sensors. It sends
almost nothing outbound (broadcast-flags, keepalive, serial/hwinfo queries).

However, the project intends to add **control** later (loco drive, functions,
turnouts, track power, CV programming). Control is a large, stateful surface that
deserves its own design pass and is explicitly out of scope for v1.

The question was how much control-readiness to bake into the v1 transport core.
Three options were considered:

- **(a) Minimal** — build v1 clean with no control-specific abstractions; rely
  on general good structure to make control "possible later."
- **(b) Symmetric I/O seam** — give the HA-agnostic client library a first-class,
  general `send(header, payload)` primitive and a header-keyed receive dispatch
  table now, but ship no control entities.
- **(c) Speculative scaffolding** — add placeholder command modules, a loco
  registry, and control platform stubs ahead of a real control spec.

## Decision

Adopt **(b)**. The client library exposes a symmetric seam:

- **Send path**: a general `send(header, payload)` primitive over the single UDP
  endpoint. v1's outbound messages are built on it; future control commands are
  new message builders on the same primitive.
- **Receive path**: a length-driven parser that splits combined datagrams and
  dispatches on `Header` through a table. Adding a control-related inbound
  message (e.g. `LAN_X_LOCO_INFO`) is a new dispatch entry plus a parser.

Ship **no** control entities, command builders, or registries in v1.

## Consequences

- Adding control later is additive — new message builders, new parsers, new
  entity platforms — with no rework of the transport core (the one expensive
  refactor is avoided).
- The receive-side dispatch table is needed anyway for a robust parser that
  ignores unknown/unsubscribed headers, so the seam costs little over (a).
- We deliberately reject (c): the control model (loco addressing, state
  reconciliation, DCC speed-step encoding) has real design decisions that should
  be grilled when control is scoped, not guessed at now (YAGNI).
- The seam is an internal shape of the client library, not a public contract; it
  can still evolve when the control design forces changes.
