#!/usr/bin/env python3
"""
RetroPie OLED Monitor — οδηγεί ΚΑΙ τις δύο οθόνες ταυτόχρονα.

  Οθόνη 1 (system) -> I2C bus 3  (GPIO23/24)
  Οθόνη 2 (game)   -> I2C bus 4  (GPIO22/27)

Κάθε οθόνη τρέχει σε δικό της thread (boot -> splash -> live).

Τρέξιμο στο Pi:
    python3 monitor.py

(Για δοκιμή ξεχωριστά στο PC χρησιμοποίησε oled_stats.py / game_stats.py
 με --emulate — ο emulator δεν ανοίγει δύο παράθυρα ταυτόχρονα.)
"""
import threading
from PIL import ImageFont

from oled_stats import get_device, run as run_system
from game_stats import run as run_game


def main():
    font = ImageFont.load_default()
    dev_system = get_device(port=3)      # /dev/i2c-3
    dev_game = get_device(port=4)        # /dev/i2c-4

    threads = [
        threading.Thread(target=run_system, args=(dev_system, font), daemon=True),
        threading.Thread(target=run_game, args=(dev_game, font), daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
