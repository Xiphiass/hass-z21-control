"""Shared pytest fixtures for the Z21 test suite.

Only the HA-coupled config-flow tests use these. The pure ``test_protocol`` /
``test_client`` suites never import Home Assistant and are unaffected by the
autouse fixture below (it is a no-op for them beyond enabling the pttcc plugin).
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let HA load the in-tree ``custom_components/z21`` integration in tests."""
    yield
