# Cypher Bitaxe Flash Support

This fork is experimental. Most support requests are not mining algorithm
problems; they are usually flash bundle, AxeOS, pool, or network problems.

Use this page when a friend says:

- `Firmware and AxeOS versions do not match`
- AxeOS shows fallback pool warnings
- ping is high
- stale shares are high
- error rate is high
- hashrate is unstable after flashing
- the wrong `esp-miner.bin` or `www.bin` may have been uploaded

## Before Asking For Help

Collect this information:

- Bitaxe model
- ASIC chip: BM1366, BM1368, or BM1370
- firmware version shown in AxeOS
- AxeOS version shown in AxeOS
- dashboard screenshot
- pool URL and worker format
- ping
- stale share percentage
- error rate
- ASIC temperature
- hashrate after at least 10 minutes
- exact files flashed: `esp-miner.bin`, `www.bin`, or `esp-miner-factory.bin`

## Fast Checks

1. If AxeOS warns that firmware and AxeOS versions do not match, update both
   files from the same release or build:

   - `esp-miner.bin`
   - `www.bin`

2. Do not mix official AxeOS assets with an experimental firmware build unless
   the release notes explicitly say it is supported.

3. If AxeOS loads but looks broken, upload `www.bin` again before changing pool
   or ASIC settings.

4. If the miner boots but mining is unstable, leave voltage/frequency
   conservative until pool, ping, stale shares, and error rate are understood.

5. If the device does not boot or the UI is unreachable, use the factory image
   over USB:

   ```text
   esp-miner-factory.bin
   ```

## Paid Remote Support

For remote help, open a support request here:

```text
https://github.com/0xjc65eth/bitaxe-flash-doctor/issues/new?template=bitaxe-support.yml
```

BTC payment / tips:

```text
35gjAoadgQxrNc1Kx6QiSLx7wCCXRnRFkM
```

No seed phrases. No private keys. No custody. No exchange logins.

## Support Tool

Use Bitaxe Flash Doctor to inspect local firmware bundles before sharing or
flashing:

```text
https://github.com/0xjc65eth/bitaxe-flash-doctor
```

It helps create:

- SHA-256 checksums
- firmware manifests
- flash checklists
- version-string inspection notes

> verify first. flash second.
