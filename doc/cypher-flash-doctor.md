# Cypher Flash Doctor

_the hash speaks when the mask is quiet_

Cypher Flash Doctor is a read-only diagnostic tool for Bitaxe/AxeOS after a firmware flash. It helps users explain the most common reports:

- firmware and AxeOS version mismatch;
- high AxeOS response time / ping-like latency;
- high ASIC error rate;
- fallback pool usage;
- stale or rejected shares;
- weak Wi-Fi and high temperature.

It does not upload firmware, change settings, or require any account.

## Run Against A Device

```bash
python3 tools/cypher_flash_doctor.py --host 192.168.1.42
```

You can also use the local hostname if mDNS works:

```bash
python3 tools/cypher_flash_doctor.py --host bitaxe
```

## Save A Shareable Report

Markdown:

```bash
python3 tools/cypher_flash_doctor.py --host 192.168.1.42 --format markdown > bitaxe-report.md
```

JSON:

```bash
python3 tools/cypher_flash_doctor.py --host 192.168.1.42 --format json > bitaxe-report.json
```

## Offline Diagnosis

If someone sends only the `/api/system/info` JSON:

```bash
python3 tools/cypher_flash_doctor.py --from-json system-info.json
```

## Exit Codes

- `0`: OK or informational findings only
- `1`: warning findings
- `2`: critical findings
- `3`: could not read device info

## Flash Mismatch Fix

If the report says `VERSION_MISMATCH`, flash both binaries from the same release:

1. Upload `www.bin` to AxeOS OTAWWW.
2. Upload `esp-miner.bin` to firmware OTA.
3. Reboot after both uploads.

Do not mix a new firmware binary with an old AxeOS binary.

## Why This Exists

After a flash, users often blame the firmware for symptoms that come from mixed binaries, pool fallback, weak Wi-Fi, stale shares, or unstable tuning. This tool gives a repeatable diagnosis without asking users to identify themselves or share private accounts.
