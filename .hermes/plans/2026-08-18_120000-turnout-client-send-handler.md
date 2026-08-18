# Turnout Client — Send Methods and Broadcast Handler

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add `set_turnout()` and `request_turnout_info()` send methods to `Z21Client`, plus broadcast handler support for `LAN_X_TURNOUT_INFO` datagrams.

**Architecture:** Two new client methods wrapping existing protocol builders. `request_turnout_info` uses the existing one-shot future pattern (like `request_serial_number`). Broadcast delivery already works via `subscribe()` — no new registry needed, just a convenience helper.

**Tech Stack:** Python 3.11+, asyncio, pytest. Zero runtime dependencies.

---

## Task 1: Add `set_turnout()` send method to `Z21Client`

**Objective:** Expose `build_turnout_set` through a client method that sends the framed datagram.

**Files:**
- Modify: `custom_components/z21/client.py:198-204` (after `emergency_stop`)
- Test: `tests/test_client.py`

**Step 1: Write failing test**

```python
def test_set_turnout_fadr_4_position_1():
    c = Z21Client("192.0.2.10")
    t = FakeTransport()
    c._attach_transport(t)
    c.set_turnout(4, 1)
    assert t.sent == [protocol.build_turnout_set(4, 1)]


def test_set_turnout_with_q_bit():
    c = Z21Client("192.0.2.10")
    t = FakeTransport()
    c._attach_transport(t)
    c.set_turnout(4, 1, q=True)
    assert t.sent == [protocol.build_turnout_set(4, 1, q=True)]


def test_set_turnout_without_transport_raises():
    c = Z21Client("192.0.2.10")
    with pytest.raises(RuntimeError):
        c.set_turnout(0, 0)
```

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_client.py::test_set_turnout_fadr_4_position_1 -v`
Expected: FAIL — "method not defined" or "no such test"

**Step 3: Write minimal implementation**

Add to `client.py` after `emergency_stop()` (around line 200):

```python
def set_turnout(self, fadr: int, position: int, q: bool = False) -> None:
    """Send LAN_X_SET_TURNOUT (5.2)."""
    self._transport_send(protocol.build_turnout_set(fadr, position, q))
```

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_client.py -k "set_turnout" -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add custom_components/z21/client.py tests/test_client.py
git commit -m "feat: add set_turnout() send method"
```

---

## Task 2: Add `request_turnout_info()` method with one-shot future

**Objective:** Poll turnout position — creates a pending future, sends the request, returns the future.

**Files:**
- Modify: `custom_components/z21/client.py` (after `request_systemstate`, around line 183)
- Test: `tests/test_client.py`

**Step 1: Write failing test**

```python
def test_request_turnout_info_returns_future():
    async def scenario():
        c = Z21Client("192.0.2.10")
        t = FakeTransport()
        c._attach_transport(t)

        def responder(header, client):
            if header == protocol.HDR_TURNOUT_INFO:
                payload = struct.pack("<BBB", 0x00, 0x04, 0x08)
                client._on_datagram(
                    protocol.build_frame(protocol.HDR_TURNOUT_INFO, payload)
                )

        c._attach_transport(RespondingTransport(c, responder))
        fut = c.request_turnout_info(4)
        result = await asyncio.wait_for(fut, timeout=0.5)
        return result

    info = run(scenario())
    assert isinstance(info, protocol.TurnoutInfo)
    assert info.fadr == 4
    assert info.position == 1


def test_request_turnout_info_without_transport_raises():
    c = Z21Client("192.0.2.10")
    with pytest.raises(RuntimeError):
        c.request_turnout_info(0)
```

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_client.py::test_request_turnout_info_returns_future -v`
Expected: FAIL — "method not defined"

**Step 3: Write minimal implementation**

Add after `request_systemstate()` (around line 183):

```python
def request_turnout_info(self, fadr: int) -> asyncio.Future:
    """Send LAN_X_GET_TURNOUT_INFO (5.1) and return a Future for the response."""
    loop = self._loop or asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    self._pending[protocol.HDR_TURNOUT_INFO] = fut
    self.send(protocol.HDR_TURNOUT_INFO_GET if hasattr(protocol, 'HDR_TURNOUT_INFO_GET') else protocol.build_turnout_info_get(fadr))
    return fut
```

Wait — `build_turnout_info_get` is already in protocol.py. The send method needs to call it. Let me fix:

```python
def request_turnout_info(self, fadr: int) -> asyncio.Future:
    """Send LAN_X_GET_TURNOUT_INFO (5.1) and return a Future for the response."""
    loop = self._loop or asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    self._pending[protocol.HDR_TURNOUT_INFO] = fut
    self.send(protocol.HDR_TURNOUT_INFO_GET if hasattr(protocol, 'HDR_TURNOUT_INFO_GET') else ...)
    return fut
```

Hmm, looking at the protocol, `build_turnout_info_get(fadr)` returns a full frame. But `send()` expects `(header, payload)` and wraps it. The existing `request_serial_number` calls `self.send(protocol.HDR_SERIAL_NUMBER)` which just sends the header with empty payload, and `build_get_serial_number()` does the framing.

But `build_turnout_info_get(fadr)` already returns a complete frame. So the client method should use `_transport_send` directly, like `set_track_power_on`:

```python
def request_turnout_info(self, fadr: int) -> asyncio.Future:
    """Send LAN_X_GET_TURNOUT_INFO (5.1) and return a Future for the response."""
    loop = self._loop or asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    self._pending[protocol.HDR_TURNOUT_INFO] = fut
    self._transport_send(protocol.build_turnout_info_get(fadr))
    return fut
```

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_client.py -k "request_turnout_info" -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add custom_components/z21/client.py tests/test_client.py
git commit -m "feat: add request_turnout_info() with one-shot future"
```

---

## Task 3: Add convenience helper for turnout broadcast handlers

**Objective:** The existing `subscribe()` already routes all decoded datagrams to handlers. The issue asks for a "broadcast handler registry" — this is already provided by `subscribe()`. Add a convenience method `subscribe_turnout_info(handler)` that wraps the existing subscribe pattern for clarity.

Actually, re-reading the acceptance criteria: "Broadcast `LAN_X_TURNOUT_INFO` datagrams dispatched to registered handlers". This is already working — `_on_datagram` already calls all subscribers for every decoded datagram. Let me verify this works for turnout info.

**Files:**
- Test: `tests/test_client.py`

**Step 1: Write test verifying turnout info broadcasts reach subscribers**

```python
def test_turnout_info_broadcast_reaches_subscriber():
    c = Z21Client("192.0.2.10")
    received: list[tuple[int, object]] = []
    unsub = c.subscribe(lambda h, d: received.append((h, d)))

    turnout_payload = struct.pack("<BBB", 0x00, 0x04, 0x08)
    c._on_datagram(protocol.build_frame(protocol.HDR_TURNOUT_INFO, turnout_payload))

    assert len(received) == 1
    header, decoded = received[0]
    assert header == protocol.HDR_TURNOUT_INFO
    assert isinstance(decoded, protocol.TurnoutInfo)
    assert decoded.fadr == 4
    assert decoded.position == 1

    unsub()
    c._on_datagram(protocol.build_frame(protocol.HDR_TURNOUT_INFO, turnout_payload))
    assert len(received) == 1  # no further delivery after unsubscribe
```

**Step 2: Run test to verify pass**

Run: `python3 -m pytest tests/test_client.py::test_turnout_info_broadcast_reaches_subscriber -v`
Expected: PASS — the existing subscribe mechanism already handles this.

**Step 3: Commit**

```bash
git add tests/test_client.py
git commit -m "test: verify turnout info broadcast delivery via subscribe()"
```

---

## Task 4: Run full test suite to confirm no regressions

**Objective:** All existing tests must still pass.

**Files:**
- Run: `python3 -m pytest tests/test_protocol.py tests/test_client.py -q`

**Step 1: Run full suite**

Run: `python3 -m pytest tests/test_protocol.py tests/test_client.py -q`
Expected: All 67+ tests pass (67 original + 6 new = 73)

**Step 2: Fix any regressions**

If any existing test fails, diagnose and fix. The protocol layer should be untouched.

---

## Files likely to change

| File | Action | Reason |
| --- | --- | --- |
| `custom_components/z21/client.py` | Modify | Add `set_turnout()` and `request_turnout_info()` methods |
| `tests/test_client.py` | Modify | Add tests for both new methods and broadcast delivery |
| `custom_components/z21/protocol.py` | No change | Builders and decoder already exist from issue #27 |

---

## Tests / validation

- `test_set_turnout_fadr_4_position_1` — sends correct frame
- `test_set_turnout_with_q_bit` — Q mode flag
- `test_set_turnout_without_transport_raises` — RuntimeError guard
- `test_request_turnout_info_returns_future` — Future resolves on response
- `test_request_turnout_info_without_transport_raises` — RuntimeError guard
- `test_turnout_info_broadcast_reaches_subscriber` — subscribe() delivers decoded TurnoutInfo
- `python3 -m pytest tests/test_protocol.py tests/test_client.py -q` — all 73 pass

---

## Risks, tradeoffs, and open questions

- **No new broadcast registry needed:** The existing `subscribe()` pattern already routes all decoded datagrams by header. The acceptance criterion "broadcast handler registry" is satisfied by `subscribe()`. If the user wants a typed convenience wrapper (e.g. `subscribe_turnout_info(handler)`), that's a minor addition but not required by the AC.
- **`HDR_TURNOUT_INFO` reuse:** `request_turnout_info` uses the same header for pending lookup as broadcast delivery. This is fine — the one-shot future is cleared immediately after `set_result()`, and subsequent broadcasts go to subscribers only.
- **Protocol layer untouched:** No changes to `protocol.py` — all builders/decoders already exist from issue #27.
- **Open question:** Should `request_turnout_info` accept a timeout parameter like `connect()`? The issue doesn't specify one. The returned Future can be awaited with `asyncio.wait_for(fut, timeout=...)` by the caller. Keeping it simple for now.