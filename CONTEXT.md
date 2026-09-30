# Context / Glossary

The shared language for the Z21 Home Assistant integration. Terms only — no
implementation detail.

## Z21 (Command Station)

The physical Roco/Fleischmann Z21-compatible digital command station (e.g.
ML-Train MZSpro) on the local network. Speaks the **Z21 LAN protocol** over
UDP port 21105. The integration is a **client** of exactly one Z21.

## Z21 LAN protocol

The binary UDP request/response + broadcast protocol documented in
`z21-lan-protocol.md`. Every datagram is `DataLen (LE16) | Header (LE16) |
Data`. Multiple datasets may be packed in one UDP packet.

## System State

The command station's live snapshot, delivered in the `LAN_SYSTEMSTATE_DATACHANGED`
packet (Header `0x0084`, 16-byte payload). Contains two distinct kinds of data:

- **Electrical telemetry** — main-track current, filtered main current, prog-track
  current, internal temperature, supply voltage, track voltage. Continuously
  varying analog values.
- **Central State** — the `CentralState` / `CentralStateEx` bitmasks: discrete
  operational conditions (emergency stop, track voltage off, short circuit,
  programming mode active, over-temperature, power lost). This is the primary
  surface HA users automate on.

Note: "Central State" here means the bitmask fields specifically, NOT the whole
System State snapshot. Avoid using "central state" loosely for the snapshot.

## Broadcast subscription

A per-client (per IP+port) set of flags set via `LAN_SET_BROADCASTFLAGS` that
tells the Z21 which asynchronous broadcasts to push. Flags reset on every new
logon and must be re-sent after reconnect. v1 uses flag **`0x00000100`** — the
one that delivers `LAN_SYSTEMSTATE_DATACHANGED`. (Note: flag `0x00000001` is the
*driving & switching* group, NOT system state — a common mix-up.)

## Keepalive

A periodic `LAN_SYSTEMSTATE_GETDATA` request the integration sends on a fixed
interval. Serves two purposes: refreshes System State, and acts as a liveness
probe so a silently-dropped broadcast subscription is detected and recovered.

## Liveness / Availability

The Z21 is considered **alive** if *any* datagram (push broadcast or keepalive
response) has arrived within the **staleness window** (~2.5× the keepalive
interval). On silence past that window, all entities report `unavailable`
(greyed in HA) rather than holding stale values — automations must not fire on
stale data. On the first datagram after a silence, the integration re-sends
`LAN_SET_BROADCASTFLAGS` (flags reset on logoff/reconnect) before trusting the
push stream again.

## Entity surface (v1)

All entities belong to one HA **Device** representing the Z21.

Sensors (electrical telemetry): MainCurrent, FilteredMainCurrent, ProgCurrent
(device_class `current`, mA); Temperature (`temperature`, °C); SupplyVoltage,
VCCVoltage/track voltage (`voltage`, mV).

Binary sensors (from Central State bitmasks): track voltage off (`power`,
inverted), emergency stop / short circuit / over-temperature / power lost
(`problem`), programming-mode-active (diagnostic, no class). When locos are
configured, the station also carries a **locos in motion** binary sensor
(`moving`): on while any configured loco's reported speed is above 0.

Deliberately skipped in v1: the granular short-circuit-location bits
(`cseShortCircuitExternal`, `cseShortCircuitInternal`) and `cseRCN213` — the
general short-circuit bit covers the automatable case.

## Identity & lifecycle

The config flow takes the **host IP only** (port fixed at 21105). It validates
by round-tripping `LAN_GET_SERIAL_NUMBER` within a short timeout — a wrong IP
fails fast rather than creating a dead entry. The 32-bit serial becomes the
config-entry `unique_id` (survives IP changes, blocks duplicates). No
auto-discovery in v1 (Z21 has no mDNS/SSDP; UDP-broadcast probe deferred).

Logon to the Z21 is **implicit** on the first command sent. On HA teardown the
integration sends `LAN_LOGOFF` (`0x30`) for a clean disconnect.

## Domain

The HA integration identifier / `custom_components/` folder name is **`z21`**
(fallback `z21_lan` if it collides). It is a general Z21-compatible integration,
not ML-Train-specific — ML-Train MZSpro is one supported station among Roco Z21
compatibles.

## Distribution (HACS)

The integration is distributed as a **HACS custom repository**: users install it
by adding the repo URL under HACS → Custom repositories, not by searching the
default HACS store. Default-store inclusion is explicitly out of scope for now.

## Central controller controls

Station-wide power/stop commands — the first **control** surface, distinct from
per-loco/CV control (still out of scope). Turnout control ships separately (see
"Turnouts" below). Three Z21 LAN commands, all on the shared `0x40` X-bus header:

- **Track power** — `LAN_X_SET_TRACK_POWER_ON` (2.6) / `LAN_X_SET_TRACK_POWER_OFF`
  (2.5). Modeled as one HA **`switch`** (on = power on, off = power off).
  `TRACK_POWER_ON` also clears an active emergency stop and programming mode.
- **Emergency stop** — `LAN_X_SET_STOP` (2.13). Halts all locos but **leaves
  track voltage on** (distinct from track-power-off). Modeled as an HA
  **`button`** (momentary, stateless).

## Turnouts (Weichen)

User-configured accessory outputs addressed by **function address (FAdr)**, a
16-bit value `0`–`65534` (FAdr `0` = turnout #1 on a Roco multiMaus). The Z21 has
no turnout inventory to discover, so turnouts are added by hand through the
**options flow** (add/edit/delete), each becoming one HA **`switch`**.

- **Throw** — `LAN_X_SET_TURNOUT` (5.2): an Activate followed by a paired
  Deactivate (the client owns that timing). The protocol names only **output 1**
  and **output 2**, never "straight"/"branching" — the physical direction depends
  on decoder cabling the station can't know.
- **Position feedback** — `LAN_X_TURNOUT_INFO` (5.3), polled on setup and pushed
  on change. Switches are **non-optimistic** (per ADR-0002): state follows the
  reported position, so external throws (e.g. a multiMaus) are reflected.
- **on/off ↔ output** — by default `off` = output 1, `on` = output 2. A
  per-turnout **inverted** flag swaps this, for a decoder wired backwards or an
  accessory/lights decoder on a turnout address.

## Locos (Loco control)

User-configured locomotives addressed by **DCC loco address** (1–10239 usable).
The Z21 has no loco roster to discover, so locos are added by hand through the
**options flow**, alongside turnouts (add/edit/delete). Each loco is a HA
**Device** — a container for its drive entities today and its function entities
later. Per-loco config is `{id, name, address, speed_steps}`, with a stable `id`
independent of the address (so an address edit migrates the entities), and
`speed_steps` one of **14 / 28 / 128** (default 128), because the drive command
requires it and the Z21 stores it per address. **DCC only** — the integration
never sends `LAN_SET_LOCOMODE`.

- **Drive** — `LAN_X_SET_LOCO_DRIVE` (4.2): one command packing **speed and
  direction together** (DB3 `RVVVVVVV`). Because they are coupled, the
  coordinator holds each loco's last-known `(direction, speed)` and composes
  every command from it (see ADR-0003).
- **Speed steps** — 14 / 28 / 128, the DCC resolution stored per loco. Speed is
  exposed in **raw steps** (0–14 / 0–28 / 0–126), not percent, so the feedback
  echo round-trips without rounding.
- **Stop vs E-Stop** — speed **0** is a normal **Stop** (decelerate). A per-loco
  **E-Stop** (immediate) is a separate `button`. Both are still the drive command
  (`R0000000` / `R0000001`). Distinct from the station-wide emergency stop
  (`LAN_X_SET_STOP`, see "Central controller controls").
- **Loco feedback** — `LAN_X_LOCO_INFO` (4.4, X-Header `0xEF`), pushed when any
  client/handset changes a **subscribed** loco. Subscription is per loco via
  `LAN_X_GET_LOCO_INFO` (4.1) on the **driving & switching** broadcast group
  (flag `0x00000001`), capped at **16 addresses (FIFO)** per client — so the
  integration caps configured locos at 16. State is **non-optimistic**: entities
  follow the reported info, reflecting external control (ADR-0003).

### Loco entities

Each configured loco is one HA **Device** carrying three entities: a speed
**`number`** (0..step-max), a direction **`switch`** (on = forward), and an
emergency-stop **`button`** (per-loco E-Stop). Function buttons (F0–F31) are
deliberately deferred to a follow-up slice.

## Scope (v1)

v1 **monitors and controls the central station**: it subscribes to System State
and exposes it as HA sensors + binary sensors, ships the station-wide
central-controller controls (a track-power switch and an emergency-stop button;
see "Central controller controls" above), exposes user-configured turnouts
as switch entities (see "Turnouts" above), and exposes user-configured locos as
drive entities — a speed number, a direction switch, and an E-Stop button per
loco (see "Locos" above). Finer-grained control — loco **functions** (F0–F31),
CV programming — stays out of scope for this slice, though the design leaves room
for it later (see ADR-0001, the symmetric I/O seam, and ADR-0003).

Fixed behaviours (not user-configurable in v1): keepalive interval **30s**,
staleness window **2.5× keepalive (~75s)**, UDP port **21105**. Turnouts are
managed through an options flow; the connection itself is not reconfigurable.
