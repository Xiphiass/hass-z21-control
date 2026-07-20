# hass-z21-control

A [Home Assistant](https://www.home-assistant.io/) custom integration for
[Roco/Fleischmann **Z21**-compatible](https://www.z21.eu/) digital command
stations (e.g. ML-Train MZSpro). The integration is a **client** of exactly one
Z21, speaking the binary **Z21 LAN protocol** over UDP port 21105.

## Status

**v1 is monitor-only** (see [`CONTEXT.md`](CONTEXT.md)): it subscribes to the
command station's **System State** and exposes it as HA sensors and binary
sensors. No control (loco drive, turnouts, track power, CV programming) ships in
v1, though the design leaves room for it later (see
[ADR-0001](docs/adr/0001-symmetric-io-seam.md)).

### What exists today

| Layer | Module | State |
| --- | --- | --- |
| Pure protocol codec | `custom_components/z21/protocol.py` | ✅ Message builders + length-driven datagram parser. No `asyncio`, no socket, no HA imports. |
| Async UDP client | `custom_components/z21/client.py` | ✅ `asyncio.DatagramProtocol` endpoint wrapping the codec; `connect`/`send`/`subscribe`/`close`. Still HA-agnostic. |
| HA integration (config flow, coordinator, entities) | `custom_components/z21/` | ✅ UI config flow, DataUpdateCoordinator, and `sensor` / `binary_sensor` platforms. |

## Installation (HACS custom repository)

This integration is distributed as a **HACS custom repository** (it is not in
the default HACS store).

1. In Home Assistant, open **HACS → ⋮ (top-right) → Custom repositories**.
2. Add the repository URL `https://github.com/Xiphiass/hass-z21-control` with
   category **Integration**.
3. Install **Z21** from HACS, then **restart Home Assistant**.
4. Go to **Settings → Devices & services → Add integration**, search for
   **Z21**, and enter the command station's host IP (port is fixed at 21105).

Requires Home Assistant **2026.1.0** or newer.

## Architecture

The code is layered so each layer is independently testable and the reusable
parts carry no Home Assistant dependency:

```
protocol.py   pure codec — bytes <-> decoded datasets (no I/O)
    ▲
client.py     async UDP transport — one endpoint, symmetric send/receive seam
    ▲
(future)      HA config flow + coordinator + sensor/binary_sensor platforms
```

The client realizes the **symmetric I/O seam** of
[ADR-0001](docs/adr/0001-symmetric-io-seam.md):

- **Send path** — a general `send(header, payload)` primitive over the single UDP
  endpoint. v1's outbound messages (`request_serial_number`, `request_hwinfo`,
  `request_systemstate`, `set_broadcastflags`, `logoff`) are thin wrappers on it;
  future control commands are new wrappers on the same seam.
- **Receive path** — inbound datagrams are split (`protocol.split_datasets`),
  decoded by `Header` through `protocol.RECEIVE_DISPATCH`, and dispatched to
  handlers registered via `subscribe(handler)`. Adding a control-related inbound
  message later is a new dispatch entry plus a handler — no transport rework.

### `Z21Client` in brief

```python
from custom_components.z21.client import Z21Client

client = Z21Client("192.0.2.10")            # host only; port defaults to 21105
serial, hwinfo = await client.connect()      # round-trips serial + hwinfo with
                                             # bounded retries + backoff
unsubscribe = client.subscribe(lambda header, decoded: ...)
client.request_systemstate()                 # via the send(header, payload) seam
await client.close()                         # sends LAN_LOGOFF, tears down
```

`connect` correlates responses by header (the Z21 has no request IDs) using
one-shot futures, and re-sends its requests on each attempt so a single dropped
datagram against a reachable Z21 is recovered on retry. It raises `Z21Timeout`
once all attempts are exhausted.

## Development

Requires Python ≥ 3.11. The runtime has **zero dependencies** (pure-Python codec;
transport uses stdlib `asyncio`). The only dev dependency is `pytest`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -q
```

Tests run entirely against a **faked transport** — no physical Z21 and no real
socket — so the full suite is fast and hermetic.

## Documentation

- [`CONTEXT.md`](CONTEXT.md) — glossary / shared language for the domain.
- [`docs/adr/`](docs/adr/) — architecture decision records.

The codec implements the Z21 LAN protocol specification (v1.13); docstrings cite
its section numbers.
