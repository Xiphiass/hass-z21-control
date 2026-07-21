# 2. Control feedback via System State, not command broadcasts

Date: 2026-07-21

## Status

Accepted

## Context

The first **control** surface adds the station-wide power/stop triad —
`LAN_X_SET_TRACK_POWER_ON` (2.6), `LAN_X_SET_TRACK_POWER_OFF` (2.5), and
`LAN_X_SET_STOP` (2.13) — exposed as a track-power `switch` and an
emergency-stop `button`.

Each of these commands has a dedicated Z21 confirmation broadcast
(`LAN_X_BC_TRACK_POWER_ON`/`OFF`, `LAN_X_BC_STOPPED`, plus
`LAN_X_STATUS_CHANGED`). But those broadcasts:

- arrive only on the **driving & switching** broadcast group (flag
  `0x00000001`), which the integration deliberately does **not** subscribe to
  (v1 subscribes to System State only, flag `0x00000100`), and
- share the inbound X-bus header `0x40`, so consuming them would require
  sub-header demultiplexing (`0x61`, `0x62`, `0x81`, …) on the receive seam,
  which today is a flat header-keyed dispatch.

Crucially, the *effects* of all three commands are already visible in the
System State broadcast the integration does consume: `csTrackVoltageOff` and
`csEmergencyStop` are decoded fields the binary sensors already read.

The question: does control feedback come from each command's own confirmation
broadcast, or from the System State we already have?

## Decision

Feedback comes from **System State**. The control layer is send-only:

- The track-power `switch` derives `is_on` from `not track_voltage_off` in
  `coordinator.data` — non-optimistic, no `assumed_state`.
- The emergency-stop `button` is fire-and-forget; the existing `emergency_stop`
  binary sensor is its feedback.
- Commands are fire-once over UDP: no retry, no reconciliation loop.
- No second broadcast subscription and no `0x40` inbound demultiplexing are
  added.

## Consequences

- System State stays the single source of truth for station condition, and
  external changes (a multiMaus operator, a short circuit) are reflected the
  same way for control state as for the monitor sensors.
- We give up per-command ACKs. A silently-dropped command surfaces honestly:
  the switch never leaves its confirmed position, and the user retries. This is
  consistent with the other fire-and-forget sends (broadcast flags, keepalive).
- Feedback latency is bounded by the System State push (typically sub-second, as
  the Z21 pushes on power changes) and at worst the 30 s keepalive.
- When per-loco control arrives it will *need* the `0x40` inbound demux (for
  `LAN_X_LOCO_INFO`); building it now would be speculative (ADR-0001 YAGNI). This
  ADR can be revisited then if explicit ACKs prove worthwhile.
