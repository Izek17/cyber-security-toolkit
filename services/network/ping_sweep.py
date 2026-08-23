"""
ping_sweep.py

Core host-discovery logic for the Ping Sweeper tool.
This module ONLY contains the ping logic. No Flask code here yet.
"""

import subprocess
import platform
import re
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---- Safety limits (do not remove) ----
MAX_HOSTS = 20              # max number of IPs allowed in one sweep
MAX_TIMEOUT_SECONDS = 5     # max timeout a user can request, in seconds
MAX_CONCURRENT_PINGS = 10   # max number of pings running at the same time


class PingSweepError(Exception):
    """Raised when user input fails validation."""
    pass


def validate_ip_range(start_ip: str, end_ip: str, timeout: float):
    """
    Checks that start_ip, end_ip, and timeout are all valid and safe.
    Raises PingSweepError with a clear message if not.
    Returns (start_addr, end_addr) as ipaddress.IPv4Address objects.
    """
    try:
        start = ipaddress.IPv4Address(start_ip)
    except ValueError:
        raise PingSweepError(f"Invalid start IP address: {start_ip}")

    try:
        end = ipaddress.IPv4Address(end_ip)
    except ValueError:
        raise PingSweepError(f"Invalid end IP address: {end_ip}")

    if int(start) > int(end):
        raise PingSweepError("start_ip must be less than or equal to end_ip")

    host_count = int(end) - int(start) + 1
    if host_count > MAX_HOSTS:
        raise PingSweepError(
            f"Range too large: {host_count} hosts requested, "
            f"maximum allowed is {MAX_HOSTS}"
        )

    if not (0 < timeout <= MAX_TIMEOUT_SECONDS):
        raise PingSweepError(
            f"Timeout must be greater than 0 and at most {MAX_TIMEOUT_SECONDS} seconds"
        )

    return start, end


def _extract_response_time(ping_output: str):
    """
    Pulls the response time (in ms) out of ping.exe's text output.
    Example line: 'Reply from 127.0.0.1: bytes=32 time<1ms TTL=64'
    """
    match = re.search(r"time[=<]([\d.]+)\s*ms", ping_output, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def ping_host(ip: str, timeout: float) -> dict:
    """
    Pings a single IP address using the OS's own ping command.
    Returns a dict: {ip, status, response_time}
    status is one of: "reachable", "unreachable", "error"
    """
    timeout_ms = int(timeout * 1000)
    is_windows = platform.system().lower() == "windows"

    if is_windows:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, int(timeout))), ip]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 1  # extra safety margin so Python never hangs
        )
        output = result.stdout

        if result.returncode == 0 and ("ttl=" in output.lower()):
            response_time = _extract_response_time(output)
            return {"ip": ip, "status": "reachable", "response_time": response_time}
        else:
            return {"ip": ip, "status": "unreachable", "response_time": None}

    except subprocess.TimeoutExpired:
        return {"ip": ip, "status": "unreachable", "response_time": None}
    except Exception:
        return {"ip": ip, "status": "error", "response_time": None}


def ping_sweep(start_ip: str, end_ip: str, timeout: float = 1.0) -> list:
    """
    Main entry point. Validates input, then pings every IP in the
    range concurrently (bounded), and returns a sorted list of results.
    """
    start, end = validate_ip_range(start_ip, end_ip, timeout)

    ip_list = [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]

    results = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PINGS) as executor:
        future_to_ip = {executor.submit(ping_host, ip, timeout): ip for ip in ip_list}
        for future in as_completed(future_to_ip):
            results.append(future.result())

    # Sort results by IP order so output is predictable
    results.sort(key=lambda r: ipaddress.IPv4Address(r["ip"]))
    return results