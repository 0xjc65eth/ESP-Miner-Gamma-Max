# Flash Cypher Gamma Max

Cypher Gamma Max is experimental ESP-Miner firmware for Bitaxe devices using
BM1368 or BM1370 ASICs.

Supported targets:

- BM1368: Supra and SupraHex style devices.
- BM1370: Gamma, GammaDuo, and GammaTurbo style devices.

Do not flash this on unrelated hardware. If you are unsure which ASIC your
Bitaxe uses, open AxeOS and check the device information first.

## What to Download

For a normal update from AxeOS, download these two files from a successful
GitHub Actions build or release:

- `esp-miner.bin`: firmware application.
- `www.bin`: AxeOS web interface.

For a full USB recovery/factory flash, use:

- `esp-miner-factory.bin`: merged factory image.

The safest path for most users is OTA from AxeOS using `esp-miner.bin` and
`www.bin`.

## Option 1: Flash from AxeOS

Use this if your Bitaxe already boots and you can open AxeOS in a browser.

1. Open your Bitaxe in a browser:

   ```text
   http://bitaxe
   ```

   or:

   ```text
   http://YOUR-BITAXE-IP
   ```

2. Go to the update/OTA area in AxeOS.

3. Upload `esp-miner.bin` as the firmware update.

4. Wait for the Bitaxe to reboot.

5. Open AxeOS again.

6. Upload `www.bin` as the web interface update.

7. Reboot once more if AxeOS asks for it.

8. Confirm the fork is active by opening:

   ```text
   http://YOUR-BITAXE-IP/api/system/info
   ```

   Look for:

   ```json
   "predictiveEfficiency": {
     "forkName": "Cypher Gamma Max",
     "forkCodename": "CYPHER-GAMMA-MAX",
     "creator": "0xjc65eth",
     "creatorTag": "CYPHER-0xJC65ETH"
   }
   ```

## Option 2: Flash by USB with Bitaxetool

Use this if the device is new, stuck, or AxeOS is not reachable.

Install Bitaxetool:

```bash
pip install bitaxetool==0.6.1
```

Connect the Bitaxe:

1. Power the Bitaxe with its normal power supply.
2. Connect USB from the Bitaxe to your computer.
3. Flash the factory image:

```bash
bitaxetool --firmware ./esp-miner-factory.bin
```

After flashing:

1. Wait until the tool finishes.
2. Press RESET on the Bitaxe if it does not reboot.
3. Complete the normal AxeOS setup.
4. Open `/api/system/info` and verify the Cypher identity fields shown above.

## Option 3: Flash by Browser with Espressif Web Tool

Use this if you prefer not to install Python tools.

1. Open Chrome or Edge.
2. Go to:

   ```text
   https://espressif.github.io/esptool-js/
   ```

3. Power the Bitaxe normally and connect USB.
4. Click `Connect`.
5. Select the serial port.
6. Set the flash address to:

   ```text
   0x0
   ```

7. Choose `esp-miner-factory.bin`.
8. Click `Program`.
9. Wait until the console says the operation is finished.
10. Reset the Bitaxe.

## How to Build the Files Yourself

If there are no downloadable binaries yet, build them with GitHub Actions:

1. Open the repository:

   ```text
   https://github.com/0xjc65eth/ESP-Miner-Gamma-Max
   ```

2. Go to `Actions`.
3. Open `Build Firmware`.
4. Click `Run workflow`.
5. Wait for the build to finish.
6. Download the build artifacts:

   - `esp-miner.bin`
   - `www.bin`
   - `esp-miner-factory.bin`

## Running the Ollama Agent After Flashing

The Ollama agent does not run inside the ESP32. Run it on a computer in the
same network as the Bitaxe:

```bash
python3 tools/bitaxe_ollama_research_agent.py \
  --bitaxe-url http://YOUR-BITAXE-IP \
  --ollama-url http://127.0.0.1:11434 \
  --model llama3.1 \
  --auto-research \
  --authority safe \
  --apply
```

Use `--authority experimental` only on supervised test hardware.

## Recovery Notes

- If AxeOS looks broken after an update, open:

  ```text
  http://YOUR-BITAXE-IP/recovery
  ```

- If the device does not boot correctly, flash `esp-miner-factory.bin` by USB.
- If you flashed the wrong device type, re-flash an official ESP-Miner factory
  image that matches your Bitaxe hardware, then update again carefully.
