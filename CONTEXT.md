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
(`problem`), programming-mode-active (diagnostic, no class).

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

## Scope (v1)

v1 is **monitor-only**: it subscribes to System State and exposes it as HA
sensors + binary sensors. No control (loco drive, turnouts, track power,
CV programming) ships in v1, though the design leaves room for it later (see
ADR-0001, the symmetric I/O seam).

Fixed behaviours (not user-configurable in v1): keepalive interval **30s**,
staleness window **2.5× keepalive (~75s)**, UDP port **21105**. No options flow.
