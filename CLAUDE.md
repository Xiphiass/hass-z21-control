Guidance for AI agents working in this repo. Human-facing overview lives in
[`README.md`](README.md); domain vocabulary in [`CONTEXT.md`](CONTEXT.md).

## What this is

A Home Assistant custom integration for Roco/Fleischmann **Z21**-compatible
command stations, speaking the Z21 LAN protocol over UDP port 21105. **v1 is
monitor-only** (System State → sensors/binary sensors); no control ships in v1.

## Architecture

Three layers, each independently testable. The lower two carry **no Home
Assistant dependency** — keep it that way:

- `custom_components/z21/protocol.py` — **pure codec**. Message builders and a
  length-driven datagram parser. No `asyncio`, no `socket`, no `homeassistant`
  imports (a test enforces this).
- `custom_components/z21/client.py` — **async UDP client**. An
  `asyncio.DatagramProtocol` endpoint wrapping the codec; `connect` / `send` /
  `subscribe` / `close`. Still HA-agnostic (no `socket`/`homeassistant` imports —
  a test enforces this; `asyncio` is allowed).
- HA integration (config flow, coordinator, entity platforms) — **not built
  yet**.

Both layers honor the **symmetric I/O seam** of
[`docs/adr/0001-symmetric-io-seam.md`](docs/adr/0001-symmetric-io-seam.md): a
general `send(header, payload)` primitive on the send side, and a header-keyed
`RECEIVE_DISPATCH` table on the receive side. Adding a message is additive — a
new builder and/or a new dispatch entry + decoder — not a transport rewrite.

## Conventions

- **Zero runtime dependencies.** Pure-Python codec; transport uses stdlib
  `asyncio`. Do not add runtime deps. Dev-only dep is `pytest`.
- **Tests use a faked transport** — no physical Z21, no real socket. Mirror the
  existing style in `tests/`: plain `pytest` functions, `from __future__ import
  annotations`, local byte-builder helpers, `asyncio.run(...)` for coroutines
  (no `pytest-asyncio`).
- **Codec changes stay additive** and behavior-preserving: existing
  `tests/test_protocol.py` must stay green.
- Wire-format work follows the Z21 LAN protocol spec (v1.13) and cites section
  numbers in docstrings, as the existing code does.
- Use the vocabulary defined in [`CONTEXT.md`](CONTEXT.md); flag conflicts with
  an ADR rather than silently overriding it.

## Commands

```bash
python -m pytest tests/ -q        # full suite (fast, hermetic)
```

## Agent skills

### Issue tracker

Issues live in GitHub Issues at siemens.ghe.com (via the `gh` CLI); external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Domain docs

See `docs/agents/domain.md`.