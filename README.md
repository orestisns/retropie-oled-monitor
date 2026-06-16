# RetroPie OLED Monitor

Stats σε δύο 0.96" OLED οθόνες (128x64, SSD1306) για Raspberry Pi με RetroPie.

## Οθόνες
- **Screen 1 — System stats** (`oled_stats.py`): uptime, CPU, θερμοκρασία, RAM, disk, throttle. Boot sequence + Half-Life logo splash.
- **Screen 2 — Game stats** (`game_stats.py`): παιχνίδι, σύστημα/core, χρόνος session (PLAY), συνολικός χρόνος ανά παιχνίδι (TOTAL), ώρα. Aperture splash + aperture logo όταν δεν τρέχει παιχνίδι.

Και τα δύο logos εμφανίζονται με pixel-reveal animation, στο ίδιο μέγεθος (58×58).

## Ροή (monitor.py)
1. **Screen 1: boot sequence** (η οθόνη 2 κενή)
2. **Και οι δύο: logo** με animation (Half-Life | Aperture), ταυτόχρονα
3. **Και οι δύο: live stats**, ταυτόχρονα

## Αρχεία
| Αρχείο | Περιγραφή |
|--------|-----------|
| `monitor.py` | **Κύριο** — οδηγεί ΚΑΙ τις δύο οθόνες με συγχρονισμένη ροή (για το Pi) |
| `oled_stats.py` | Screen 1 (system stats) — και standalone με `--emulate` |
| `game_stats.py` | Screen 2 (game stats) — και standalone με `--emulate` |
| `stats.py` | Terminal έκδοση (HDMI/μεγάλη οθόνη) — retro terminal στυλ |
| `runcommand-onstart.sh` | RetroPie hook: γράφει `/tmp/game_status` όταν ξεκινά παιχνίδι |
| `runcommand-onend.sh` | RetroPie hook: καθαρίζει την κατάσταση όταν κλείνει |
| `retropie-oled-monitor.service` | systemd service για autostart στο boot |
| `INSTALL.md` | Αναλυτικές οδηγίες εγκατάστασης |

## Καλωδίωση (software I2C, 2 buses)
| | Screen 1 (system) | Screen 2 (game) |
|---|---|---|
| Bus | 3 | 4 |
| SDA | GPIO23 (pin 16) | GPIO22 (pin 15) |
| SCL | GPIO24 (pin 18) | GPIO27 (pin 13) |
| VCC | 3.3V (pin 17) | 3.3V (pin 17) |
| GND | pin 25 | pin 14 |

Στο `/boot/config.txt`:
```
dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24
dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27
```

## Δοκιμή στο PC (emulator — ξεχωριστά)
```bash
pip install luma.emulator pygame pillow psutil
python oled_stats.py --emulate
python game_stats.py --emulate
```

## Στο Raspberry Pi
```bash
pip3 install luma.oled pillow psutil
python3 monitor.py
```
Πλήρης εγκατάσταση (I2C, hooks, autostart): βλ. [INSTALL.md](INSTALL.md).

## Σημειώσεις
- **FPS**: το RetroArch δεν εκθέτει τα τρέχοντα FPS, οπότε αντί γι' αυτά η οθόνη 2 δείχνει **TOTAL play time** ανά παιχνίδι (κρατιέται στο `playtimes.json`).
- Τα current FPS θα απαιτούσαν patch/recompile του RetroArch ή LD_PRELOAD shim — εκτός scope.

## TODO
- [ ] Καλωδίωση + δοκιμή στις πραγματικές οθόνες
- [ ] Κουμπιά (προαιρετικά)
- [ ] Live PLAYING/PAUSED μέσω RetroArch `GET_STATUS` (προαιρετικά)
