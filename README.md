<p align="center">
  <img src="custom_components/z21/brand/icon@2x.png" alt="Z21 icon" width="128">
</p>

<p align="center">
  <a href="https://github.com/Xiphiass/hass-z21-control/releases"><img src="https://img.shields.io/github/v/release/Xiphiass/hass-z21-control" alt="Release"></a>
  <a href="https://github.com/Xiphiass/hass-z21-control/actions/workflows/tests.yml"><img src="https://github.com/Xiphiass/hass-z21-control/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Xiphiass/hass-z21-control/actions/workflows/hassfest.yml"><img src="https://github.com/Xiphiass/hass-z21-control/actions/workflows/hassfest.yml/badge.svg" alt="hassfest"></a>
  <a href="https://hacs.xyz/docs/faq/custom_repositories/"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2026.8%2B-18BCF2?logo=homeassistant&logoColor=white" alt="Home Assistant 2026.8+">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Xiphiass/hass-z21-control" alt="License: MIT"></a>
</p>

# hass-z21-control

A [Home Assistant](https://www.home-assistant.io/) custom integration for
[Roco/Fleischmann **Z21**-compatible](https://www.z21.eu/) digital command
stations (e.g. ML-Train MZSpro). It talks to one Z21 over the binary **Z21 LAN
protocol** (UDP port 21105), with local push updates and no cloud or extra
dependencies.

## Features

- **Station monitoring**: track and programming current, temperature, supply
  and track voltage, plus the station's state flags (track power, emergency stop,
  short circuit, over-temperature, power lost, programming mode).
- **Station controls**: a track-power switch and a station-wide emergency stop.
- **Turnouts (Weichen)**: throw turnouts by function address, with live
  position feedback.
- **Locos**: up to 16 DCC locos, each with speed, direction, a per-loco
  emergency stop, and configurable decoder functions (F0–F31) as switches or
  momentary buttons.
- **Live feedback**: every entity follows what the Z21 reports, so changes
  made from a multiMaus, the Z21 app or another controller show up in Home
  Assistant too.
- **Availability**: if the Z21 goes quiet, entities turn `unavailable` instead
  of holding stale values, and the integration re-subscribes once the station
  is back.

UI available in English and German.

## Installation

The integration is distributed as a **HACS custom repository** (it is not in
the default HACS store). Requires Home Assistant **2026.8.0** or newer.

1. In Home Assistant, open **HACS → ⋮ (top-right) → Custom repositories**.
2. Add `https://github.com/Xiphiass/hass-z21-control` with category
   **Integration**.
3. Install **Z21** from HACS, then **restart Home Assistant**.
4. Go to **Settings → Devices & services → Add integration**, search for
   **Z21**, and enter the command station's IP address (the port is fixed at
   21105).

The integration checks that the Z21 answers before creating the entry, and
uses the station's serial number as its identity, so a changed IP address won't
create a duplicate.

## Configuration

The Z21 has no roster to query, so turnouts and locos are added by hand under
**Settings → Devices & services → Z21 → Configure**. The menu lets you manage
turnouts and locos; choose **Save and reload** to apply your changes.

### Turnouts

Each turnout has:

| Field | Meaning |
| --- | --- |
| **Name** | Friendly name for the switch entity (e.g. "Yard entry"). |
| **Function address (FAdr)** | The Z21 turnout address, `0`–`65534`. FAdr `0` is turnout #1 on a Roco multiMaus (the addressing is zero-based). |
| **Inverted** | Swaps the on/off ↔ output mapping. Off by default. |

The Z21 protocol only knows "output 1" and "output 2"; which physical direction
each one drives depends on how the decoder is wired. By default `off` = output 1
and `on` = output 2. If a turnout throws the wrong way, or you're driving an
accessory/lights decoder on a turnout address, enable **Inverted** instead of
rewiring.

> **Example.** Add a turnout named `Yard entry` at FAdr `12`. It appears as
> `switch.z21_<host>_yard_entry`. Turning it **on** throws it to output 2 and
> **off** back to output 1.

### Locos

Each loco has:

| Field | Meaning |
| --- | --- |
| **Name** | Name of the loco's device in Home Assistant. |
| **DCC address** | The loco address, `1`–`10239`. |
| **Speed steps** | The decoder's speed-step resolution: `14`, `28` or `128` (default; right for modern decoders). |

At most **16 locos** can be configured: the Z21 only sends live updates for 16
loco addresses per client. Locos are DCC only.

### Loco functions

Under **Manage locos → Manage loco functions**, pick a loco and add its decoder
functions. Each function has a **name**, a **function number** (`0`–`31`, `0` =
F0, usually the lights) and a **type**:

- **Switch**: latches the function on/off (lights, sound, smoke).
- **Button**: switches the function on briefly, about 1 s (horn, coupler).

## Entities

### Z21 device

**Sensors**

| Entity | Unit |
| --- | --- |
| Main track current | mA |
| Filtered main track current | mA |
| Programming track current | mA |
| Internal temperature | °C |
| Supply voltage | mV |
| Track voltage | mV |

**Binary sensors**

| Entity | On when |
| --- | --- |
| Track voltage off | Track power is switched off. |
| Emergency stop | An emergency stop is active. |
| Short circuit | A short circuit is detected. |
| Over-temperature | The command station is over temperature. |
| Power lost | The command station lost power. |
| Programming mode | The command station is in programming mode (diagnostic). |
| Locos in motion | Any configured loco reports a speed above 0 (only when locos are configured). |

**Controls**

| Entity | Type | Action |
| --- | --- | --- |
| Track power | `switch` | Turns track power on/off. Turning it on also clears an emergency stop and programming mode. |
| Emergency stop | `button` | Stops all locomotives immediately while leaving track power on. |
| *Turnout* (one per configured turnout) | `switch` | Throws the turnout between its two outputs. Shows *unknown* until the Z21 first reports its position. |

### Loco devices

Each configured loco is its own device, linked to the Z21 device:

| Entity | Type | Action |
| --- | --- | --- |
| Speed | `number` | Speed in raw decoder steps (0–14, 0–28 or 0–126, per the loco's speed steps). 0 is a normal stop. |
| Direction | `switch` | On = forward, off = reverse. |
| Emergency stop | `button` | Stops this loco immediately. |
| *Function* (one per configured function) | `switch` or `button` | Toggles or pulses the decoder function. |

Switches and speed are **non-optimistic**: after a command, the entity waits for
the Z21 to confirm the new state rather than assuming it.

## How it works

The integration logs on to the Z21, subscribes to its System State and
driving/switching broadcasts, and sends a keepalive every 30 s that also
re-asserts the subscriptions and re-polls each loco. If nothing arrives from the
Z21 for about 75 s, all entities go `unavailable`. On unload and on Home
Assistant shutdown it logs off from the Z21 cleanly.

The code is split into three layers, the lower two with no Home Assistant
dependency:

```
protocol.py   pure codec: bytes <-> decoded datasets (no I/O)
    ▲
client.py     async UDP client: one endpoint, send(header, payload) + header-keyed receive dispatch
    ▲
HA layer      config/options flow, coordinator, sensor/binary_sensor/switch/button/number platforms
```

See [ADR-0001](docs/adr/0001-symmetric-io-seam.md) for the I/O seam,
[ADR-0002](docs/adr/0002-control-feedback-via-system-state.md) for control
feedback and
[ADR-0003](docs/adr/0003-loco-drive-non-optimistic-subscription.md) for loco
drive. The codec follows the Z21 LAN protocol specification (v1.13); docstrings
cite its section numbers.

## Development

Requires Python ≥ 3.14.2. The runtime has **zero dependencies**.

```bash
python -m venv .venv && source .venv/bin/activate
pip install ".[dev]"          # plain install, not -e (see CLAUDE.md)
python -m pytest tests/ -q
```

Tests run against a **faked transport** (no physical Z21, no real socket), so
the suite is fast and hermetic.

## Documentation

- [`CONTEXT.md`](CONTEXT.md): glossary and shared language for the domain.
- [`docs/adr/`](docs/adr/): architecture decision records.

## License

[MIT](LICENSE)
