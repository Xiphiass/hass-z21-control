# 3. Loco drive: non-optimistic via per-loco subscription, coupled speed+direction

Date: 2026-09-28

## Status

Accepted

## Context

Loco drive control adds the first **per-loco** surface: a speed `number`, a
direction `switch`, and an emergency-stop `button` per configured loco, each on
its own HA Device. It extends the non-optimistic philosophy of ADR-0002 (control
state follows the Z21, not the last command) but cannot reuse its mechanism, and
it carries two protocol constraints that shape the code in surprising ways:

1. **Speed and direction are one command.** `LAN_X_SET_LOCO_DRIVE` (§4.2) packs
   both into DB3 (`RVVVVVVV`) — you cannot set speed without also asserting a
   direction, or vice versa.
2. **Feedback is per-loco and capped.** Unlike track power / turnouts (whose
   state rides the System State broadcast), loco state arrives as
   `LAN_X_LOCO_INFO` (§4.4, X-Header `0xEF`) and only for addresses the client
   has **subscribed** to via `LAN_X_GET_LOCO_INFO` (§4.1). Subscription is capped
   at **16 addresses (FIFO)** per client; a 17th silently evicts the oldest.

## Decision

- **Non-optimistic, feedback-driven.** On setup and on recovery-from-silence the
  coordinator subscribes to every configured loco with `LAN_X_GET_LOCO_INFO`
  (mirroring `_discover_turnouts`). A new `_decode_loco_info` decoder surfaces
  address, direction, speed (raw steps), and speed-step mode under a logical
  `HDR_LOCO_INFO`; all three entities derive their state from it. Function bits
  (DB4–DB8) are intentionally left unparsed until functions ship.
- **Compose from last-known state.** Because the wire couples speed+direction,
  the coordinator holds the last reported `(direction, speed)` per address and
  the client's `set_loco_drive` composes each command from it. When no feedback
  has arrived yet, it defaults to **forward, speed 0** and sends anyway — the
  subscription poll corrects the entities within a datagram or two, so the loco
  never feels unresponsive on first use.
- **Two distinct halts.** Speed `number` at 0 sends normal **Stop**
  (`R0000000`); the per-loco `button` sends **E-Stop** (`R0000001`), both via the
  same drive command preserving the last-known direction. This is separate from
  the station-wide `LAN_X_SET_STOP` (ADR-0002).
- **Hard cap at 16 configured locos.** The options flow refuses a 17th loco
  rather than let the Z21 silently evict a subscription.
- **Raw speed steps, per-loco step mode.** The `number` max is the loco's
  configured step count (14 / 28 / 126); the codec handles all three encodings.
  DCC only — `LAN_SET_LOCOMODE` is never sent (the drive command works
  regardless of stored format, and addresses ≥256 are DCC automatically).
- **Direction flip is faithful.** Flipping direction while moving sends the new
  direction at the current speed — no implicit stop. Stop-first is left to HA
  automations, matching how the Z21's own handsets behave.

## Consequences

- The `0x40` inbound demux that ADR-0002 deferred is now built out: `decode_xbus`
  gains a second `_XBUS_DISPATCH` entry (`0xEF` → `HDR_LOCO_INFO`), exactly the
  additive shape ADR-0001 anticipated.
- External control (a multiMaus / another app moving a subscribed loco) is
  reflected in HA, consistent with turnouts and track power.
- The 16-loco cap is a real product limit; >16 locos would need a future
  rotating-subscription or polling-fallback design, out of scope here.
- A configured step mode that disagrees with the mode the Z21 reports in
  feedback can yield a reported step above the slider max; the entity clamps and
  logs rather than raising.
- On the send side, every drive command is sent in the step mode the Z21
  **last reported** for that address (`LAN_X_LOCO_INFO` DB2), not the configured
  one. §4.2 stores the command's `S` nibble as that address's mode, so a
  speed change in the configured mode (the slider's, default 128) rewrites a
  handset's 14/28-step loco into 128 and the decoder ignores the new speed —
  direction and E-Stop still worked, because they re-encoded the speed the Z21
  already had. An explicit slider speed is a raw step in the configured mode
  and is **rescaled** into the reported mode before encoding; an omitted speed
  (direction flip, E-Stop) is already in the reported mode and is sent as-is.
  The rescale keeps the step's position in the drivable range, rounded, and
  never rounds a moving loco down to Stop. Before any feedback the configured
  mode is used. The configured mode remains the slider's range and the record
  of what the decoder supports; it is no longer forced onto the wire (#55).
