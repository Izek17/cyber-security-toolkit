"""
test_ping_sweep.py

Tests for ping_sweep.py — covers validation logic and ping behavior
using mocks (so tests don't depend on real network conditions),
plus one real localhost test.
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess

from ping_sweep import (
    ping_sweep,
    validate_ip_range,
    ping_host,
    PingSweepError,
    MAX_HOSTS,
)


# ---------- Validation tests ----------

def test_valid_range_passes_validation():
    start, end = validate_ip_range("192.168.1.1", "192.168.1.5", 1)
    assert str(start) == "192.168.1.1"
    assert str(end) == "192.168.1.5"


def test_invalid_start_ip_raises_error():
    with pytest.raises(PingSweepError, match="Invalid start IP"):
        validate_ip_range("999.999.999.999", "192.168.1.5", 1)


def test_invalid_end_ip_raises_error():
    with pytest.raises(PingSweepError, match="Invalid end IP"):
        validate_ip_range("192.168.1.1", "not-an-ip", 1)


def test_reversed_range_raises_error():
    with pytest.raises(PingSweepError, match="less than or equal to"):
        validate_ip_range("192.168.1.10", "192.168.1.1", 1)


def test_range_exceeding_max_raises_error():
    # MAX_HOSTS is 20, so this range of 50 hosts should fail
    with pytest.raises(PingSweepError, match="Range too large"):
        validate_ip_range("10.0.0.1", "10.0.0.50", 1)


def test_timeout_out_of_bounds_raises_error():
    with pytest.raises(PingSweepError, match="Timeout must be"):
        validate_ip_range("127.0.0.1", "127.0.0.1", 999)


# ---------- ping_host behavior tests (mocked, no real network needed) ----------

def test_ping_host_reachable(monkeypatch):
    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "Reply from 127.0.0.1: bytes=32 time<1ms TTL=64"

    with patch("subprocess.run", return_value=fake_result):
        result = ping_host("127.0.0.1", 1)

    assert result["ip"] == "127.0.0.1"
    assert result["status"] == "reachable"


def test_ping_host_unreachable(monkeypatch):
    fake_result = MagicMock()
    fake_result.returncode = 1
    fake_result.stdout = "Request timed out."

    with patch("subprocess.run", return_value=fake_result):
        result = ping_host("192.168.1.250", 1)

    assert result["status"] == "unreachable"
    assert result["response_time"] is None


def test_ping_host_timeout_handled():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ping", timeout=1)):
        result = ping_host("192.168.1.251", 1)

    assert result["status"] == "unreachable"
    assert result["response_time"] is None


# ---------- Real integration test (localhost only — always safe) ----------

def test_ping_sweep_localhost_real():
    """
    Real test using localhost — this doesn't touch any other network
    and is always safe/authorized to run.
    """
    results = ping_sweep("127.0.0.1", "127.0.0.1", timeout=1)
    assert len(results) == 1
    assert results[0]["ip"] == "127.0.0.1"
    assert results[0]["status"] == "reachable"