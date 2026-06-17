# Εγκατάσταση στο RetroPie (όλα με εντολές terminal)

> Αποκλειστικά για **RetroPie** (Raspberry Pi). Όλα γίνονται γράφοντας εντολές —
> χωρίς χειροκίνητο editing αρχείων. Η καλωδίωση των οθονών γίνεται ξεχωριστά (βλ. README).

## Αυτόματο script (προτεινόμενο)
Δείχνει κάθε βήμα ξεχωριστά + πληροφορίες/σφάλματα:
```bash
cd ~ && git clone https://github.com/orestisns/retropie-oled-monitor.git
cd ~/retropie-oled-monitor
chmod +x install.sh
./install.sh
```
Μετά: καλωδίωσε τις οθόνες και `sudo reboot`.

---

## Ή χειροκίνητα (copy-paste όλα μαζί)

```bash
# 1) Ενημέρωση + πακέτα συστήματος
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-pip i2c-tools libjpeg-dev zlib1g-dev git

# 2) Ενεργοποίηση I2C (χωρίς μενού)
sudo raspi-config nonint do_i2c 0

# 3) Δημιουργία των 2 software I2C buses στο config.txt
CONFIG=/boot/firmware/config.txt; [ -f "$CONFIG" ] || CONFIG=/boot/config.txt
grep -q "i2c_gpio_sda=23" "$CONFIG" || echo "dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24" | sudo tee -a "$CONFIG"
grep -q "i2c_gpio_sda=22" "$CONFIG" || echo "dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27" | sudo tee -a "$CONFIG"

# 4) Κατέβασμα project
cd ~ && git clone https://github.com/orestisns/retropie-oled-monitor.git
cd ~/retropie-oled-monitor

# 5) Python βιβλιοθήκες
pip3 install luma.oled pillow psutil || pip3 install --break-system-packages luma.oled pillow psutil

# 6) Εγκατάσταση game hooks (για το screen 2)
sudo cp runcommand-onstart.sh /opt/retropie/configs/all/runcommand-onstart.sh
sudo cp runcommand-onend.sh   /opt/retropie/configs/all/runcommand-onend.sh
sudo chmod +x /opt/retropie/configs/all/runcommand-onstart.sh /opt/retropie/configs/all/runcommand-onend.sh

# 7) Εγκατάσταση autostart (systemd) — προσαρμογή στον χρήστη σου
sudo cp retropie-oled-monitor.service /etc/systemd/system/
sudo sed -i "s|/home/pi/retropie-oled-monitor|$HOME/retropie-oled-monitor|g; s|^User=pi|User=$USER|" /etc/systemd/system/retropie-oled-monitor.service
sudo systemctl daemon-reload
sudo systemctl enable retropie-oled-monitor.service

# 8) Επανεκκίνηση
sudo reboot
```

## Έλεγχος μετά το reboot
```bash
# Υπάρχουν τα 2 buses;
ls /dev/i2c-3 /dev/i2c-4

# Ανιχνεύονται οι οθόνες; (πρέπει να δείξει 3c)
i2cdetect -y 3
i2cdetect -y 4

# Τρέχει το service;
systemctl status retropie-oled-monitor.service
```

## Χρήσιμες εντολές διαχείρισης
```bash
# Logs ζωντανά (debug)
journalctl -u retropie-oled-monitor.service -f

# Restart / Stop
sudo systemctl restart retropie-oled-monitor.service
sudo systemctl stop retropie-oled-monitor.service

# Χειροκίνητη εκτέλεση (αφού κάνεις stop το service)
cd ~/retropie-oled-monitor && python3 monitor.py
```

## Ενημέρωση σε νέα έκδοση
```bash
cd ~/retropie-oled-monitor
git pull
sudo systemctl restart retropie-oled-monitor.service
```

---

### Σημειώσεις
- Αν το βήμα 6 βγάλει «No such file or directory», ο φάκελος `/opt/retropie/configs/all/` δεν υπάρχει — δεν είναι σωστό RetroPie image.
- Αν οι οθόνες δεν ανιχνεύονται (`i2cdetect` δεν δείχνει `3c`), έλεγξε καλωδίωση + ότι μπήκαν οι 2 γραμμές στο config.txt.
- Το service τρέχει ως ο χρήστης σου (το βήμα 7 το προσαρμόζει αυτόματα).
