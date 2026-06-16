# RetroPie OLED Monitor

Stats σε δύο 0.96" OLED οθόνες (128x64, SSD1306) για Raspberry Pi με RetroPie.

## Οθόνες
- **Screen 1 — System stats** (`oled_stats.py`): uptime, CPU, θερμοκρασία, RAM, disk, throttle. Boot sequence + science (atom) splash.
- **Screen 2 — Game stats** (`game_stats.py`): παιχνίδι, σύστημα/core, play time, FPS, ώρα. Aperture splash + aperture logo όταν δεν τρέχει παιχνίδι.

## Αρχεία
| Αρχείο | Περιγραφή |
|--------|-----------|
| `stats.py` | Terminal έκδοση (μεγάλη οθόνη / HDMI) — retro terminal στυλ |
| `oled_stats.py` | Screen 1 για OLED (system stats) |
| `game_stats.py` | Screen 2 για OLED (game stats) |
| `runcommand-onstart.sh` | RetroPie hook: γράφει `/tmp/game_status` όταν ξεκινά παιχνίδι |
| `runcommand-onend.sh` | RetroPie hook: καθαρίζει την κατάσταση όταν κλείνει |

## Δοκιμή στο PC (emulator)
```bash
pip install luma.emulator pygame pillow psutil
python oled_stats.py --emulate
python game_stats.py --emulate
```

## Στο Raspberry Pi
```bash
pip3 install luma.oled pillow psutil
python3 oled_stats.py
python3 game_stats.py
```

Hooks → αντίγραψε στο `/opt/retropie/configs/all/` και `chmod +x`.

## TODO
- [ ] RetroArch FPS/status (network command)
- [ ] Ενοποιημένο `monitor.py` για δύο οθόνες ταυτόχρονα
- [ ] systemd services (autostart)
- [ ] Καθορισμός I2C διευθύνσεων (0x3C / 0x3D)
