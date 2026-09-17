"""Shared test configuration.

``hermesAgent`` validates its required configuration at *import time*, so the
values are injected during collection — before any test module is imported — via
``pytest_configure``. ``setdefault`` preserves any values already exported from
the shell.
"""

import os


def pytest_configure(config):
    os.environ.setdefault("HERMES_BASE_URL", "http://127.0.0.1:8642")
    os.environ.setdefault("API_SERVER_KEY", "test-api-key")
    os.environ.setdefault("HERMES_MODEL", "hermes-agent")
    os.environ.setdefault("HERMES_TIMEOUT", "600")
