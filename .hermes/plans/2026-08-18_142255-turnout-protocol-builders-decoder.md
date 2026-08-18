# Turnout Protocol — Builders and Decoder

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add turnout message builders and decoder to the protocol layer (`protocol.py`) with full TDD coverage, so the codec can build and parse turnout datagrams per the Z21 LAN protocol spec (sections 5.1, 5.2, 5.3).

**Architecture:** Pure codec additions only — new builder functions, a new `TurnoutInfo` dataclass, and a new entry in `RECEIVE_DISPATCH`. No client-layer, HA-layer, or options-flow changes. This is strictly a Seam-0 (protocol) task.

**Tech Stack:** Python 3.11+, pytest, struct, dataclasses. Zero runtime dependencies.

---

## Background

Issue #26 ("Dynamic Turnout Support") is the parent feature. Issue #27 is this ticket: implement the protocol layer builders and decoder for turnout commands. After this, the codec can build and parse turnout datagrams, tested in isolation with exact byte verification.

### Protocol spec summary

**5.1 LAN_X_GET_TURNOUT_INFO** (poll request)
```
DataLen: 0x0008
Header:  0x0040
X-Header: 0x43
DB0: FAdr_MSB
DB1: FAdr_LSB
DB2: XOR-Byte
```
Total payload: 4 bytes (X-header + 2 address bytes + XOR).

**5.2 LAN_X_SET_TURNOUT** (switch command)
```
DataLen: 0x0009
Header:  0x0040
X-Header: 0x53
DB0: FAdr_MSB
DB1: FAdr_LSB
DB2: 1000A00P (4-bit field)
DB3: XOR-Byte
```
- A=0 → Deactivate output 1, A=1 → Activate output 2
- P=0 → Select output 1, P=1 → Select output 2
- Q=0 → Execute immediately, Q=1 → Queue mode (FW 1.24+)
- Function address = (FAdr_MSB << 8) + FAdr_LSB

**5.3 LAN_X_TURNOUT_INFO** (response/broadcast from Z21)
```
DataLen: 0x0009
Header:  0x0040
X-Header: 0x43
DB0: FAdr_MSB
DB1: FAdr_LSB
DB2: 000000ZZ (2-bit position field)
DB3: XOR-Byte
```
- ZZ=00 → Turnout not switched yet
- ZZ=01 → Position P=0 (output 1)
- ZZ=10 → Position P=1 (output 2)
- ZZ=11 → Invalid combination

### Existing code patterns

- Builders use `build_frame(header, payload)` for framing and `build_xbus(x_header, db)` for X-bus commands.
- `build_xbus` computes the XOR checkbyte automatically: XOR of X-header and all data bytes.
- Decoders are functions `_(payload: bytes) -> Dataclass | None` that return `None` for short payloads.
- `RECEIVE_DISPATCH` maps header ints to decoder functions.
- Tests verify exact outbound bytes against spec hex examples.

---

## Task 1: Add `HDR_TURNOUT_INFO` constant

**Objective:** Define the inbound header constant for `LAN_X_TURNOUT_INFO`.

**Files:**
- Modify: `custom_components/z21/protocol.py:37-38`

**Step 1: Add the constant**

Add below `HDR_SYSTEMSTATE_DATACHANGED = 0x84`:

```python
HDR_TURNOUT_INFO = 0x43  # LAN_X_TURNOUT_INFO (5.3)
```

Note: The X-header 0x43 is the payload byte, but the datagram header (LAN_X_TURNOUT_INFO) is `0x40` (HDR_X) with X-header 0x43 inside. Looking at the existing code, `HDR_TURNOUT_INFO` should be the datagram-level header that appears in `RECEIVE_DISPATCH`. In the existing code, `HDR_X = 0x40` is the datagram header for all X-bus commands, and individual X-headers (0x21, 0x80, 0x43, 0x53) are inside the payload.

Wait — let me re-check. Looking at the existing code:
- `HDR_X = 0x40` is used in `build_frame(HDR_X, ...)` for all X-bus commands
- The `_DISPATCH` table only has `HDR_SYSTEMSTATE_DATACHANGED: _decode_system_state`
- `RECEIVE_DISPATCH` has `HDR_SERIAL_NUMBER`, `HDR_HWINFO`, `HDR_SYSTEMSTATE_DATACHANGED`

The X-bus commands (track power, stop) don't have inbound responses decoded — they're fire-and-forget. But `LAN_X_TURNOUT_INFO` IS an inbound response/broadcast. The datagram header is still `0x40` (HDR_X), but the X-header inside is `0x43`.

So `RECEIVE_DISPATCH` needs to dispatch on `HDR_X` (0x40) and then the decoder needs to inspect the X-header byte inside the payload. OR we add a separate header constant and handle it specially.

Looking more carefully at the existing code: `RECEIVE_DISPATCH` maps headers to decoders. The `_DISPATCH` used by `parse_datagram` maps `HDR_SYSTEMSTATE_DATACHANGED` to the system state decoder. For X-bus inbound messages, the datagram header is `0x40` (HDR_X). The existing code does NOT decode X-bus responses yet.

For this task, I need to add a way to dispatch `LAN_X_TURNOUT_INFO`. The cleanest approach matching the existing architecture: add a new header constant and a new decoder entry. Since the datagram header for turnout info is `0x40` (HDR_X), and the existing `RECEIVE_DISPATCH` doesn't handle `HDR_X`, I'll add `HDR_TURNOUT_INFO = 0x43` as a semantic constant (the X-header value) and handle it in the dispatch.

Actually, re-reading the code more carefully: `parse_datagram` uses `_DISPATCH`, not `RECEIVE_DISPATCH`. `RECEIVE_DISPATCH` is a superset used by the async client's subscriber mechanism. The client's `connect()` uses one-shot futures keyed by header.

For the client layer (future work), the one-shot future correlation uses headers. For turnout info, the response header is `0x40` (HDR_X) with X-header `0x43` inside. The client's existing `connect()` pattern correlates by header — but for X-bus responses, the header is always `0x40`.

The simplest approach for now: define `HDR_TURNOUT_INFO = 0x43` as a semantic constant (matching the spec's naming), register a decoder in `_DISPATCH` keyed by `HDR_X` that inspects the X-header byte, and also add `HDR_TURNOUT_INFO` to `RECEIVE_DISPATCH` for the client's subscriber mechanism.

Hmm, that's getting complex. Let me look at how the client layer handles this...

Actually, for this task (protocol layer only), I should keep it simple:
1. Add `HDR_TURNOUT_INFO = 0x43` as a constant
2. Add a decoder that checks if the payload starts with X-header 0x43
3. Register it in `RECEIVE_DISPATCH` under `HDR_TURNOUT_INFO`
4. The `_DISPATCH` used by `parse_datagram` stays as-is (it only decodes SystemState)

Wait, but the acceptance criteria say "HDR_TURNOUT_INFO registered in RECEIVE_DISPATCH". So I just need it in `RECEIVE_DISPATCH`, not necessarily in `_DISPATCH`. The `_DISPATCH` is for `parse_datagram` which returns `list[SystemState]` — adding turnout info would change the return type. That's for a future task.

Let me re-read the acceptance criteria:
- `build_turnout_set(fadr, position, q=False)` produces correct bytes per spec 5.2
- `build_turnout_info_get(fadr)` produces correct bytes per spec 5.1
- `TurnoutInfo` dataclass decodes `LAN_X_TURNOUT_INFO` payload per spec 5.3
- `HDR_TURNOUT_INFO` registered in `RECEIVE_DISPATCH`
- All existing tests still pass

OK so:
1. Add `HDR_TURNOUT_INFO = 0x43` constant
2. Add `build_turnout_set()` and `build_turnout_info_get()` builders
3. Add `TurnoutInfo` dataclass and decoder
4. Add `HDR_TURNOUT_INFO: _decode_turnout_info` to `RECEIVE_DISPATCH`
5. All existing tests pass

`RECEIVE_DISPATCH` is a dict mapping header → decoder. Adding `HDR_TURNOUT_INFO` (0x43) → decoder is straightforward. The client layer will use this for one-shot future correlation and subscriber dispatch.

**Step 1: Add the constant**

Add after `HDR_SYSTEMSTATE_DATACHANGED = 0x84`:

```python
HDR_TURNOUT_INFO = 0x43  # LAN_X_TURNOUT_INFO (5.3)
```

**Step 2: Run existing tests**

```bash
python -m pytest tests/test_protocol.py -q
```

Expected: All existing tests pass (no regressions).

**Step 3: Commit**

```bash
git add custom_components/z21/protocol.py
git commit -m "chore: add HDR_TURNOUT_INFO constant"
```

---

## Task 2: Add `build_turnout_info_get()` builder

**Objective:** Build a `LAN_X_GET_TURNOUT_INFO` poll request for a given FAdr.

**Files:**
- Modify: `custom_components/z21/protocol.py` (add builder function)

**Step 1: Understand the exact bytes**

Per spec 5.1:
```
DataLen: 0x0008 (8 bytes total = 4 framing + 4 payload)
Header:  0x0040
Payload: X-Header(0x43) | FAdr_MSB | FAdr_LSB | XOR-Byte
```

XOR = 0x43 ^ FAdr_MSB ^ FAdr_LSB

For FAdr=4 (0x0004):
- X-Header = 0x43
- FAdr_MSB = 0x00, FAdr_LSB = 0x04
- XOR = 0x43 ^ 0x00 ^ 0x04 = 0x47
- Full payload: 43 00 04 47
- Full datagram: 08 00 40 00 43 00 04 47

**Step 2: Write the builder**

Add after `build_set_stop()`:

```python
def build_turnout_info_get(fadr: int) -> bytes:
    """LAN_X_GET_TURNOUT_INFO request (5.1).

    Polls the position of a turnout by its function address.
    ``fadr`` is the raw FAdr value (e.g. 0, 4, 9, ...).

    Example for FAdr=4::

        08 00 40 00 43 00 04 47

    """
    fadr_ms = (fadr >> 8) & 0xFF
    fadr_ls = fadr & 0xFF
    db = bytes((0x43, fadr_ms, fadr_ls))
    return build_xbus(0x43, db[1:])  # db[1:] = FAdr_MSB, FAdr_LSB
```

Wait — `build_xbus(x_header, db)` already prepends the X-header and computes XOR. So:

```python
def build_turnout_info_get(fadr: int) -> bytes:
    """LAN_X_GET_TURNOUT_INFO request (5.1)."""
    fadr_ms = (fadr >> 8) & 0xFF
    fadr_ls = fadr & 0xFF
    return build_xbus(0x43, bytes((fadr_ms, fadr_ls)))
```

This produces: `build_frame(0x40, 43 fadr_ms fadr_ls XOR)` where XOR = 0x43 ^ fadr_ms ^ fadr_ls.

For FAdr=4: `08 00 40 00 43 00 04 47` ✓

**Step 3: Write the test**

Add to `tests/test_protocol.py`:

```python
def test_turnout_info_get_fadr_4_exact_bytes():
    assert build_turnout_info_get(4) == bytes.fromhex("0800400043000447")


def test_turnout_info_get_fadr_0_exact_bytes():
    # FAdr=0: 43 00 00 XOR=0x43
    assert build_turnout_info_get(0) == bytes.fromhex("0800400043000043")


def test_turnout_info_get_fadr_65534_exact_bytes():
    # FAdr=65534 (0xFFFE): 43 FF FE XOR=0x43^0xFF^0xFE=0x43^0x01=0x42
    assert build_turnout_info_get(65534) == bytes.fromhex("0800400043FFFE42")
```

**Step 4: Run the test**

```bash
python -m pytest tests/test_protocol.py::test_turnout_info_get_fadr_4_exact_bytes -v
```

Expected: PASS

**Step 5: Run all tests**

```bash
python -m pytest tests/test_protocol.py -q
```

Expected: All tests pass.

**Step 6: Commit**

```bash
git add custom_components/z21/protocol.py tests/test_protocol.py
git commit -m "feat: add build_turnout_info_get() builder"
```

---

## Task 3: Add `build_turnout_set()` builder

**Objective:** Build a `LAN_X_SET_TURNOUT` command for a given FAdr, position, and queue mode.

**Files:**
- Modify: `custom_components/z21/protocol.py` (add builder function)

**Step 1: Understand the exact bytes**

Per spec 5.2:
```
DataLen: 0x0009 (9 bytes total = 4 framing + 5 payload)
Header:  0x0040
Payload: X-Header(0x53) | FAdr_MSB | FAdr_LSB | DB2(1000A00P) | XOR-Byte
```

DB2 = `1000A00P`:
- Bit 7 = 1 (always)
- Bit 6 = 0 (reserved)
- Bit 5 = 0 (reserved)
- Bit 4 = 0 (reserved)
- Bit 3 = A (0=deactivate, 1=activate)
- Bit 2 = 0 (reserved)
- Bit 1 = 0 (reserved)
- Bit 0 = P (0=output 1, 1=output 2)

So DB2 = `0b10000000 | (A << 3) | P` = `0x80 | (A << 3) | P`

XOR = 0x53 ^ FAdr_MSB ^ FAdr_LSB ^ DB2

For FAdr=4, position=1 (output 2), Q=0, A=1 (activate):
- DB2 = 0x80 | (1 << 3) | 1 = 0x80 | 8 | 1 = 0x89
- XOR = 0x53 ^ 0x00 ^ 0x04 ^ 0x89 = 0x53 ^ 0x04 ^ 0x89 = 0x57 ^ 0x89 = 0xDE
- Full datagram: 09 00 40 00 53 00 04 89 DE

For FAdr=4, position=0 (output 1), A=0 (deactivate):
- DB2 = 0x80 | (0 << 3) | 0 = 0x80
- XOR = 0x53 ^ 0x00 ^ 0x04 ^ 0x80 = 0x57 ^ 0x80 = 0xD7
- Full datagram: 09 00 40 00 53 00 04 80 D7

For Q=1, the Q bit is bit 7 of DB2... wait, let me re-read the spec:

```
1000A00P
Q=0 ... Execute command immediately
Q=1 ... From Z21 FW V1.24: Insert turnout command into the queue
```

Looking at the bit pattern `1000A00P`, the Q flag is NOT shown in this 8-bit field. Let me re-examine...

Actually, looking at the spec more carefully, the format shows:
```
X-Header DB0 DB1 DB2 XOR-Byte
0x53 FAdr_MSB FAdr_LSB 10Q0A00P XOR-Byte
```

So the byte is `10Q0A00P`:
- Bit 7 = 1 (always)
- Bit 6 = 0 (always)
- Bit 5 = Q (queue flag)
- Bit 4 = 0 (reserved)
- Bit 3 = A (activate/deactivate)
- Bit 2 = 0 (reserved)
- Bit 1 = 0 (reserved)
- Bit 0 = P (output select)

So DB2 = `0b10000000 | (Q << 5) | (A << 3) | P` = `0x80 | (Q << 5) | (A << 3) | P`

Wait, that doesn't match the spec text. Let me re-read:

```
1000A00P
A=0 ... Deactivate turnout output
A=1 ... Activate turnout output
P=0 ... Select output 1 of the turnout
P=1 ... Select output 2 of the turnout
Q=0 ... Execute command immediately
Q=1 ... From Z21 FW V1.24: Insert turnout command into the queue
```

The spec says `10Q0A00P` — so:
- Bit 7 = 1
- Bit 6 = 0
- Bit 5 = Q
- Bit 4 = 0
- Bit 3 = A
- Bit 2 = 0
- Bit 1 = 0
- Bit 0 = P

DB2 = (1 << 7) | (Q << 5) | (A << 3) | P

For activate, output 2, Q=0: DB2 = 0x80 | 0 | 0x08 | 1 = 0x89
For activate, output 2, Q=1: DB2 = 0x80 | 0x20 | 0x08 | 1 = 0xA9

The spec example confirms: "Activate turnout #5/A2 (4,0x89)" — position 1 (output 2), Q=0 → 0x89. And "Activate turnout #25 / A2 (24, 0xA9)" — position 1, Q=1 → 0xA9. 0x80 | 0x20 | 0x08 | 1 = 0xA9 ✓

**Step 2: Write the builder**

```python
def build_turnout_set(fadr: int, position: int, q: bool = False) -> bytes:
    """LAN_X_SET_TURNOUT command (5.2).

    Switches a turnout by its function address.

    Args:
        fadr: Raw function address (0–65534).
        position: 0 = output 1 (deactivate), 1 = output 2 (activate).
        q: If True, queue mode (Z21 FW 1.24+).

    Example for FAdr=4, position=1 (activate, output 2), Q=0::

        09 00 40 00 53 00 04 89 DE

    """
    fadr_ms = (fadr >> 8) & 0xFF
    fadr_ls = fadr & 0xFF
    a = 1 if position else 0
    q_bit = 1 if q else 0
    db2 = 0x80 | (q_bit << 5) | (a << 3) | position
    return build_xbus(0x53, bytes((fadr_ms, fadr_ls, db2)))
```

**Step 3: Write the tests**

```python
def test_turnout_set_activate_output2_exact_bytes():
    # FAdr=4, position=1 (output 2, activate), Q=0
    # DB2 = 0x80 | 0 | 8 | 1 = 0x89
    # XOR = 0x53 ^ 0x00 ^ 0x04 ^ 0x89 = 0xDE
    assert build_turnout_set(4, 1) == bytes.fromhex("0900400053000489DE")


def test_turnout_set_deactivate_output1_exact_bytes():
    # FAdr=4, position=0 (output 1, deactivate), Q=0
    # DB2 = 0x80 | 0 | 0 | 0 = 0x80
    # XOR = 0x53 ^ 0x00 ^ 0x04 ^ 0x80 = 0xD7
    assert build_turnout_set(4, 0) == bytes.fromhex("0900400053000480D7")


def test_turnout_set_queue_mode_exact_bytes():
    # FAdr=24, position=1, Q=1
    # DB2 = 0x80 | 0x20 | 0x08 | 1 = 0xA9
    # XOR = 0x53 ^ 0x00 ^ 0x18 ^ 0xA9 = 0x53 ^ 0x18 ^ 0xA9 = 0x4B ^ 0xA9 = 0xE2
    assert build_turnout_set(24, 1, q=True) == bytes.fromhex("09004000530018A9E2")


def test_turnout_set_fadr_0():
    # FAdr=0, position=1, Q=0
    # DB2 = 0x89, XOR = 0x53 ^ 0x00 ^ 0x00 ^ 0x89 = 0x53 ^ 0x89 = 0xDA
    assert build_turnout_set(0, 1) == bytes.fromhex("0900400053000089DA")
```

**Step 4: Run the tests**

```bash
python -m pytest tests/test_protocol.py -q -k turnout_set
```

Expected: All 4 tests pass.

**Step 5: Run all tests**

```bash
python -m pytest tests/test_protocol.py -q
```

Expected: All tests pass.

**Step 6: Commit**

```bash
git add custom_components/z21/protocol.py tests/test_protocol.py
git commit -m "feat: add build_turnout_set() builder"
```

---

## Task 4: Add `TurnoutInfo` dataclass and decoder

**Objective:** Define the `TurnoutInfo` dataclass and a decoder for `LAN_X_TURNOUT_INFO` responses.

**Files:**
- Modify: `custom_components/z21/protocol.py` (add dataclass and decoder function)

**Step 1: Define the dataclass**

Per spec 5.3, the payload is 4 bytes:
- DB0: FAdr_MSB
- DB1: FAdr_LSB
- DB2: 000000ZZ (position bits)
- DB3: XOR-Byte (not stored — just a check)

```python
@dataclass(frozen=True)
class TurnoutInfo:
    """Decoded LAN_X_TURNOUT_INFO response (5.3).

    ``position`` is 0 (output 1), 1 (output 2), or None (not switched yet / ZZ=00).
    ``invalid`` is True when ZZ=11 (invalid combination).
    """

    fadr: int  # raw function address
    position: int | None  # 0, 1, or None (not switched yet)
    invalid: bool  # True when ZZ=11
```

**Step 2: Write the decoder**

```python
def _decode_turnout_info(payload: bytes) -> TurnoutInfo | None:
    """Decode a turnout info payload; ``None`` if too short."""
    if len(payload) < 4:
        return None
    fadr_ms, fadr_ls, zz = struct.unpack_from("<BBB", payload, 0)
    fadr = (fadr_ms << 8) | fadr_ls
    zz_val = zz & 0x03  # lower 2 bits
    if zz_val == 0:
        position: int | None = None  # not switched yet
    elif zz_val == 1:
        position = 0  # P=0
    elif zz_val == 2:
        position = 1  # P=1
    else:
        position = None  # ZZ=11 is invalid
    return TurnoutInfo(fadr=fadr, position=position, invalid=zz_val == 3)
```

**Step 3: Write the tests**

```python
def test_turnout_info_decode_output1():
    # FAdr=4, ZZ=01 (position 0 / P=0)
    payload = bytes.fromhex("04000100")  # FAdr=4, ZZ=1, XOR=0x43^0x04^0x01=0x46 (but we just decode)
    # Actually: payload is just the data after the header, so:
    # FAdr_MSB=0x00, FAdr_LSB=0x04, ZZ=0x01, XOR=0x46
    info = _decode_turnout_info(bytes((0x00, 0x04, 0x01, 0x46)))
    assert info is not None
    assert info.fadr == 4
    assert info.position == 0
    assert info.invalid is False


def test_turnout_info_decode_output2():
    # FAdr=4, ZZ=10 (position 1 / P=1)
    info = _decode_turnout_info(bytes((0x00, 0x04, 0x02, 0x45)))
    assert info.fadr == 4
    assert info.position == 1
    assert info.invalid is False


def test_turnout_info_decode_not_switched():
    # ZZ=00 → position is None
    info = _decode_turnout_info(bytes((0x00, 0x04, 0x00, 0x47)))
    assert info.fadr == 4
    assert info.position is None
    assert info.invalid is False


def test_turnout_info_decode_invalid():
    # ZZ=11 → invalid=True
    info = _decode_turnout_info(bytes((0x00, 0x04, 0x03, 0x44)))
    assert info.fadr == 4
    assert info.position is None
    assert info.invalid is True


def test_turnout_info_decode_short_payload():
    assert _decode_turnout_info(b"\x00\x04\x01") is None
    assert _decode_turnout_info(b"") is None


def test_turnout_info_decode_fadr_65534():
    info = _decode_turnout_info(bytes((0xFF, 0xFE, 0x02, 0x41)))
    assert info.fadr == 65534
    assert info.position == 1
```

**Step 4: Run the tests**

```bash
python -m pytest tests/test_protocol.py -q -k "turnout_info_decode"
```

Expected: All tests pass.

**Step 5: Run all tests**

```bash
python -m pytest tests/test_protocol.py -q
```

Expected: All tests pass.

**Step 6: Commit**

```bash
git add custom_components/z21/protocol.py tests/test_protocol.py
git commit -m "feat: add TurnoutInfo dataclass and decoder"
```

---

## Task 5: Register `HDR_TURNOUT_INFO` in `RECEIVE_DISPATCH`

**Objective:** Add the turnout info header to the receive dispatch table.

**Files:**
- Modify: `custom_components/z21/protocol.py` (add to RECEIVE_DISPATCH)

**Step 1: Add the entry**

Add to `RECEIVE_DISPATCH`:

```python
RECEIVE_DISPATCH = {
    HDR_SERIAL_NUMBER: _decode_serial_number,
    HDR_HWINFO: _decode_hwinfo,
    HDR_SYSTEMSTATE_DATACHANGED: _decode_system_state,
    HDR_TURNOUT_INFO: _decode_turnout_info,
}
```

**Step 2: Write a test**

```python
def test_turnout_info_in_receive_dispatch():
    assert HDR_TURNOUT_INFO in RECEIVE_DISPATCH
    assert RECEIVE_DISPATCH[HDR_TURNOUT_INFO] is _decode_turnout_info
```

**Step 3: Run all tests**

```bash
python -m pytest tests/test_protocol.py -q
```

Expected: All tests pass.

**Step 4: Commit**

```bash
git add custom_components/z21/protocol.py tests/test_protocol.py
git commit -m "feat: register HDR_TURNOUT_INFO in RECEIVE_DISPATCH"
```

---

## Task 6: Final verification

**Objective:** Ensure all existing tests still pass and the new code is clean.

**Step 1: Run the full test suite**

```bash
python -m pytest tests/ -q
```

Expected: All tests pass (existing + new).

**Step 2: Verify no forbidden imports**

The existing test `test_codec_has_no_forbidden_imports` checks that `protocol.py` has no `import asyncio`, `import socket`, or `homeassistant`. Our changes don't add any imports beyond `struct` and `dataclass` which are already present.

**Step 3: Final commit (if not already committed incrementally)**

```bash
git add -A
git commit -m "feat: add turnout protocol builders and decoder (#27)"
```

---

## Files Likely to Change

| File | Change |
|------|--------|
| `custom_components/z21/protocol.py` | New constant `HDR_TURNOUT_INFO`, new builders `build_turnout_info_get()` and `build_turnout_set()`, new dataclass `TurnoutInfo`, new decoder `_decode_turnout_info()`, new entry in `RECEIVE_DISPATCH` |
| `tests/test_protocol.py` | New tests for all builders, decoder, and dispatch registration |

## Tests / Validation

- **Exact byte tests**: Each builder produces exact bytes matching the spec's hex examples.
- **Decoder tests**: `TurnoutInfo` correctly decodes all position values (0, 1, not switched, invalid) and edge cases (short payload, max FAdr).
- **Dispatch test**: `HDR_TURNOUT_INFO` is in `RECEIVE_DISPATCH` and maps to the correct decoder.
- **Regression**: All existing tests pass unchanged.
- **Seam guard**: No forbidden imports added to `protocol.py`.

## Risks, Tradeoffs, and Open Questions

1. **XOR checkbyte verification**: The tests verify exact output bytes, which inherently validates the XOR computation. No separate XOR test needed.

2. **`_DISPATCH` vs `RECEIVE_DISPATCH`**: `_DISPATCH` is used by `parse_datagram()` which returns `list[SystemState]`. We do NOT add turnout info to `_DISPATCH` because that would change the return type. `RECEIVE_DISPATCH` is for the client's subscriber mechanism and one-shot futures. This is intentional — `parse_datagram` is a v1-only entry point.

3. **Position mapping**: The spec uses ZZ=01 for P=0 and ZZ=10 for P=1. Our decoder maps ZZ=01 → position=0 (output 1) and ZZ=10 → position=1 (output 2). This matches the switch entity convention where `is_on=True` = output 2 (activate) and `is_on=False` = output 1 (deactivate).

4. **FAdr range**: The spec doesn't explicitly state a max FAdr, but it's a 16-bit value. We accept 0–65534 (65535 is reserved). Validation of the range will be done in the options flow (future task).

5. **No `_DISPATCH` entry for turnout info**: If someone calls `parse_datagram()` with a turnout info datagram, it will be silently skipped (not in `_DISPATCH`). This is correct for v1 — `parse_datagram` is a convenience function for SystemState-only use. The client layer's subscriber mechanism uses `RECEIVE_DISPATCH` instead.