# RetroPie OLED Monitor

Stats on two 0.96" OLED displays (128x64, SSD1306) for a Raspberry Pi running RetroPie.

## Displays
- **Screen 1 - System stats** (`oled_stats.py`): uptime, CPU, temperature, RAM, disk, throttle. Boot sequence + Half-Life logo splash.
- **Screen 2 - Game stats** (`game_stats.py`): game, system/core, current session time (PLAY), total play time per game (TOTAL), clock. Aperture splash + aperture logo when no game is running.

Both logos appear with a pixel-reveal animation, at the same size (58x58).

## Flow (monitor.py)
1. **Screen 1: boot sequence** (screen 2 blank)
2. **Both: logo** with animation (Half-Life | Aperture), simultaneously
3. **Both: live stats**, simultaneously

## Files
| File | Description |
|------|-------------|
| `monitor.py` | **Main** - drives BOTH displays with a synchronized flow (for the Pi) |
| `oled_stats.py` | Screen 1 (system stats) - also standalone with `--emulate` |
| `game_stats.py` | Screen 2 (game stats) - also standalone with `--emulate` |
| `stats.py` | Terminal version (HDMI/large screen) - retro terminal style |
| `runcommand-onstart.sh` | RetroPie hook: writes `/tmp/game_status` when a game starts |
| `runcommand-onend.sh` | RetroPie hook: clears the state when a game exits |
| `retropie-oled-monitor.service` | systemd service for autostart at boot |
| `install.sh` | Step-by-step installer |
| `INSTALL.md` | Detailed installation instructions |

## Wiring (software I2C, 2 buses)
| | Screen 1 (system) | Screen 2 (game) |
|---|---|---|
| Bus | 3 | 4 |
| SDA | GPIO23 (pin 16) | GPIO22 (pin 15) |
| SCL | GPIO24 (pin 18) | GPIO27 (pin 13) |
| VCC | 3.3V (pin 17) | 3.3V (pin 17) |
| GND | pin 25 | pin 14 |

In `/boot/config.txt`:
```
dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24
dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27
```

## Install on the Raspberry Pi
```bash
cd ~ && git clone https://github.com/orestisns/retropie-oled-monitor.git
cd ~/retropie-oled-monitor
chmod +x install.sh
./install.sh
```
See [INSTALL.md](INSTALL.md) for full details. Then wire the displays and `sudo reboot`.

## Test on a PC (emulator, separately)
```bash
pip install luma.emulator pygame pillow psutil
python oled_stats.py --emulate
python game_stats.py --emulate
```

## Notes
- **FPS**: RetroArch does not expose the current FPS, so instead of it screen 2 shows **TOTAL play time** per game (kept in `playtimes.json`).
- Real current FPS would require patching/recompiling RetroArch or an LD_PRELOAD shim - out of scope.

## TODO
- [ ] Wiring + test on the real displays
- [ ] Buttons (optional)
- [ ] Live PLAYING/PAUSED via RetroArch `GET_STATUS` (optional)
