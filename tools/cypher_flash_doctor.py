#!/usr/bin/env python3
"""
Cypher Flash Doctor for Bitaxe / AxeOS.

Diagnoses the common post-flash failures users report:
- firmware and AxeOS version mismatch;
- high response time / ping-like latency;
- high ASIC hash error percentage;
- fallback pool usage;
- rejected/stale shares;
- weak Wi-Fi and thermal pressure.

The tool is read-only by default. It never uploads firmware or changes settings.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"ok": 0, "info": 1, "warn": 2, "critical": 3}


@dataclass
class Finding:
    severity: str
    code: str
    title: str
    detail: str
    action: str


def normalize_host(host: str) -> str:
    host = host.strip()
    if not host:
        raise ValueError("empty host")
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host.rstrip("/")


def fetch_json(host: str, path: str, timeout: float) -> dict[str, Any]:
    url = f"{normalize_host(host)}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not return a JSON object")
    return payload


def number(data: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = data.get(key, default)
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def text(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if value is None:
        return default
    return str(value)


def boolish(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def add(
    findings: list[Finding],
    severity: str,
    code: str,
    title: str,
    detail: str,
    action: str,
) -> None:
    findings.append(Finding(severity, code, title, detail, action))


def rejection_summary(info: dict[str, Any]) -> tuple[int, str]:
    reasons = info.get("sharesRejectedReasons") or []
    if not isinstance(reasons, list):
        return 0, ""

    rows: list[tuple[int, str]] = []
    total = 0
    for reason in reasons:
        if not isinstance(reason, dict):
            continue
        count = int(number(reason, "count", 0))
        message = text(reason, "message", "unknown")
        total += count
        rows.append((count, message))

    rows.sort(reverse=True)
    summary = ", ".join(f"{count}x {message}" for count, message in rows[:3])
    return total, summary


def diagnose(info: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []

    firmware = text(info, "version", "Unknown")
    axeos = text(info, "axeOSVersion", "Unknown")
    asic = text(info, "ASICModel", "Unknown")
    board = text(info, "boardVersion", "Unknown")

    if firmware != "Unknown" and axeos != "Unknown" and firmware != axeos:
        add(
            findings,
            "critical",
            "VERSION_MISMATCH",
            "Firmware and AxeOS were flashed from different builds",
            f"Firmware is {firmware}, AxeOS is {axeos}. AxeOS shows this exact mismatch warning after mixed OTA uploads.",
            "Flash both files from the same release: first www.bin through OTAWWW, then esp-miner.bin through OTA. Reboot after both uploads.",
        )

    if boolish(info, "isUsingFallbackStratum"):
        add(
            findings,
            "warn",
            "FALLBACK_POOL",
            "Device is mining on fallback pool",
            "Share stats reset and users often read this as a firmware failure, but it normally means the primary pool could not stay connected.",
            "Check Pool settings: URL, port, TLS flag, worker name, password, and suggested difficulty. Temporarily disable fallback while debugging.",
        )

    if boolish(info, "miningPaused"):
        add(
            findings,
            "warn",
            "MINING_PAUSED",
            "Mining is paused",
            "The device is reachable but not actively hashing.",
            "Resume mining from AxeOS or POST /api/system/resume after confirming settings.",
        )

    if boolish(info, "power_fault"):
        add(
            findings,
            "critical",
            "POWER_FAULT",
            "Power fault is active",
            "A power fault can cause low hashrate, high errors, unstable pool traffic, or restarts.",
            "Check PSU rating, USB-C/PCIe wiring, voltage sag, and board connectors before tuning frequency or voltage.",
        )

    response_time = number(info, "responseTime", 0)
    if response_time >= 1000:
        add(
            findings,
            "critical",
            "HIGH_RESPONSE_TIME",
            "Very high AxeOS response time",
            f"responseTime is {response_time:.0f} ms. This matches the 1000+ ms complaints after flash.",
            "Move the miner closer to Wi-Fi, use 2.4 GHz with a clean channel, reduce AP congestion, and avoid judging firmware until responseTime is stable below 300 ms.",
        )
    elif response_time >= 500:
        add(
            findings,
            "warn",
            "HIGH_RESPONSE_TIME",
            "High AxeOS response time",
            f"responseTime is {response_time:.0f} ms.",
            "Fix Wi-Fi/pool latency before changing ASIC frequency. High latency often creates stale/rejected shares.",
        )

    wifi = number(info, "wifiRSSI", 0)
    if wifi and wifi <= -85:
        add(
            findings,
            "critical",
            "WEAK_WIFI",
            "Wi-Fi signal is extremely weak",
            f"wifiRSSI is {wifi:.0f} dBm.",
            "Improve antenna placement or access point distance. Target better than -70 dBm for stable mining.",
        )
    elif wifi and wifi <= -75:
        add(
            findings,
            "warn",
            "WEAK_WIFI",
            "Wi-Fi signal is weak",
            f"wifiRSSI is {wifi:.0f} dBm.",
            "Expect ping spikes and stale shares until the signal improves.",
        )

    error_percentage = number(info, "errorPercentage", 0)
    if error_percentage >= 5:
        add(
            findings,
            "critical",
            "HIGH_ASIC_ERROR",
            "ASIC hash error rate is very high",
            f"errorPercentage is {error_percentage:.2f}%.",
            "Lower frequency one step or raise core voltage one safe step, then wait 10 minutes. Check cooling and PSU before pushing autotune.",
        )
    elif error_percentage >= 1:
        add(
            findings,
            "warn",
            "HIGH_ASIC_ERROR",
            "ASIC hash error rate is elevated",
            f"errorPercentage is {error_percentage:.2f}%.",
            "Let the miner warm up for 10 minutes. If it persists, reduce frequency or increase voltage slightly within board limits.",
        )

    temp = max(number(info, "temp", 0), number(info, "temp2", 0))
    if temp >= 78:
        add(
            findings,
            "critical",
            "HOT_ASIC",
            "ASIC temperature is too high",
            f"ASIC temperature is {temp:.1f} C.",
            "Increase cooling and lower frequency/voltage. Do not chase hashrate until temperature is controlled.",
        )
    elif temp >= 72:
        add(
            findings,
            "warn",
            "HOT_ASIC",
            "ASIC temperature is high",
            f"ASIC temperature is {temp:.1f} C.",
            "Improve airflow. High temperature can explain rising error rate and lower efficiency.",
        )

    accepted = number(info, "sharesAccepted", 0)
    rejected = number(info, "sharesRejected", 0)
    total_rejections, rejection_reasons = rejection_summary(info)
    if rejected > 0 and accepted + rejected > 0:
        rejected_pct = (rejected / (accepted + rejected)) * 100
        severity = "critical" if rejected_pct >= 10 else "warn" if rejected_pct >= 2 else "info"
        add(
            findings,
            severity,
            "SHARE_REJECTIONS",
            "Rejected shares detected",
            f"{rejected:.0f} rejected of {accepted + rejected:.0f} total shares ({rejected_pct:.2f}%). Reasons: {rejection_reasons or 'not reported'}.",
            "If reasons mention stale/job-not-found, fix pool latency and difficulty first. If errors rise with rejections, tune ASIC frequency/voltage.",
        )
    elif total_rejections > 0:
        add(
            findings,
            "warn",
            "SHARE_REJECTIONS",
            "Rejected share reasons were reported",
            f"Reasons: {rejection_reasons}.",
            "Check pool configuration and latency.",
        )

    expected = number(info, "expectedHashrate", 0)
    actual_10m = number(info, "hashRate_10m", 0)
    uptime = number(info, "uptimeSeconds", 0)
    if expected > 0 and actual_10m > 0 and uptime >= 600:
        ratio = actual_10m / expected
        if ratio < 0.70:
            add(
                findings,
                "critical",
                "LOW_HASHRATE",
                "Hashrate is far below expected",
                f"10m average is {actual_10m:.0f} Gh/s vs expected {expected:.0f} Gh/s ({ratio:.0%}).",
                "Check ASIC detection, power, cooling, and pool connection. Do not increase clocks until error and power faults are clear.",
            )
        elif ratio < 0.85:
            add(
                findings,
                "warn",
                "LOW_HASHRATE",
                "Hashrate is below expected",
                f"10m average is {actual_10m:.0f} Gh/s vs expected {expected:.0f} Gh/s ({ratio:.0%}).",
                "Let autotune settle and inspect errors/temperature. If stable, tune gradually.",
            )

    if not findings:
        add(
            findings,
            "ok",
            "HEALTHY",
            "No obvious post-flash issue detected",
            f"{asic} board {board} reports firmware {firmware} / AxeOS {axeos}.",
            "Keep both binaries from the same release for future updates and monitor 10m hashrate after changes.",
        )

    return findings


def worst_severity(findings: list[Finding]) -> str:
    return max(findings, key=lambda item: SEVERITY_ORDER[item.severity]).severity


def print_text(info: dict[str, Any], findings: list[Finding]) -> None:
    firmware = text(info, "version", "Unknown")
    axeos = text(info, "axeOSVersion", "Unknown")
    asic = text(info, "ASICModel", "Unknown")
    board = text(info, "boardVersion", "Unknown")
    host = text(info, "hostname", "Bitaxe")

    print("Cypher Flash Doctor")
    print("_the hash speaks when the mask is quiet_")
    print()
    print(f"Device: {host} | ASIC: {asic} | Board: {board}")
    print(f"Firmware: {firmware} | AxeOS: {axeos}")
    print(
        "Metrics: "
        f"responseTime={number(info, 'responseTime', 0):.0f}ms, "
        f"error={number(info, 'errorPercentage', 0):.2f}%, "
        f"temp={max(number(info, 'temp', 0), number(info, 'temp2', 0)):.1f}C, "
        f"wifiRSSI={number(info, 'wifiRSSI', 0):.0f}dBm"
    )
    print()

    for item in findings:
        label = item.severity.upper()
        print(f"[{label}] {item.code}: {item.title}")
        print(f"  Detail: {item.detail}")
        print(f"  Action: {item.action}")
        print()

    print(f"Overall: {worst_severity(findings).upper()}")


def print_markdown(info: dict[str, Any], findings: list[Finding]) -> None:
    print("# Cypher Flash Doctor Report")
    print()
    print("_the hash speaks when the mask is quiet_")
    print()
    print("| Field | Value |")
    print("| --- | --- |")
    for key in ("hostname", "ASICModel", "boardVersion", "version", "axeOSVersion", "responseTime", "errorPercentage", "temp", "temp2", "wifiRSSI"):
        print(f"| {key} | {info.get(key, 'Unknown')} |")
    print()
    print(f"Overall: **{worst_severity(findings).upper()}**")
    print()
    for item in findings:
        print(f"## {item.severity.upper()} - {item.code}")
        print()
        print(item.title)
        print()
        print(f"Detail: {item.detail}")
        print()
        print(f"Action: {item.action}")
        print()


def output_json(info: dict[str, Any], findings: list[Finding]) -> None:
    print(
        json.dumps(
            {
                "generatedAt": int(time.time()),
                "overall": worst_severity(findings),
                "device": {
                    "hostname": info.get("hostname"),
                    "asic": info.get("ASICModel"),
                    "boardVersion": info.get("boardVersion"),
                    "firmware": info.get("version"),
                    "axeOS": info.get("axeOSVersion"),
                },
                "findings": [item.__dict__ for item in findings],
            },
            indent=2,
            sort_keys=True,
        )
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Bitaxe/AxeOS post-flash diagnostic tool."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--host", help="Bitaxe host or IP, for example 192.168.1.42")
    source.add_argument("--from-json", help="Read a saved /api/system/info JSON file")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds")
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="Output format",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        if args.from_json:
            info = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
            if not isinstance(info, dict):
                raise ValueError("--from-json must contain a JSON object")
        else:
            info = fetch_json(args.host, "/api/system/info", args.timeout)
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"Cypher Flash Doctor could not read device info: {exc}", file=sys.stderr)
        print("Check the IP address, Wi-Fi, and that AxeOS is reachable at /api/system/info.", file=sys.stderr)
        return 3

    findings = diagnose(info)
    if args.format == "json":
        output_json(info, findings)
    elif args.format == "markdown":
        print_markdown(info, findings)
    else:
        print_text(info, findings)

    severity = worst_severity(findings)
    if severity == "critical":
        return 2
    if severity == "warn":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
