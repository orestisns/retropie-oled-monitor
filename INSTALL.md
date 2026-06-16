# Εγκατάσταση (Software) στο Raspberry Pi / RetroPie

> Η καλωδίωση των οθονών γίνεται ξεχωριστά. Εδώ μόνο το software.

## 1. Ενημέρωση συστήματος
```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Ενεργοποίηση I2C
```bash
sudo raspi-config
```
→ Interface Options → I2C → Yes → Finish

## 3. Δημιουργία των δύο software I2C buses
```bash
sudo nano /boot/config.txt      # ή /boot/firmware/config.txt
```
Στο τέλος του αρχείου πρόσθεσε:
```
dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24
dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27
```
- bus 3 → Οθόνη 1 (system)  | GPIO23 (SDA), GPIO24 (SCL)
- bus 4 → Οθόνη 2 (game)    | GPIO22 (SDA), GPIO27 (SCL)

## 4. Πακέτα συστήματος
```bash
sudo apt install -y python3-pip i2c-tools libjpeg-dev zlib1g-dev git
```

## 5. Reboot
```bash
sudo reboot
```

## 6. Έλεγχος buses
```bash
ls /dev/i2c-*            # πρέπει να υπάρχουν i2c-3 και i2c-4
i2cdetect -y 3           # -> 3c (αν είναι συνδεδεμένη η οθόνη 1)
i2cdetect -y 4           # -> 3c (αν είναι συνδεδεμένη η οθόνη 2)
```

## 7. Κατέβασμα project
```bash
cd ~
git clone https://github.com/orestisns/retropie-oled-monitor.git
cd retropie-oled-monitor
```

## 8. Python βιβλιοθήκες
```bash
pip3 install luma.oled pillow psutil
# αν βγει "externally-managed-environment":
# pip3 install --break-system-packages luma.oled pillow psutil
```

## 9. runcommand hooks (game stats)
```bash
cp runcommand-onstart.sh /opt/retropie/configs/all/runcommand-onstart.sh
cp runcommand-onend.sh   /opt/retropie/configs/all/runcommand-onend.sh
chmod +x /opt/retropie/configs/all/runcommand-onstart.sh
chmod +x /opt/retropie/configs/all/runcommand-onend.sh
```
> Αν υπάρχουν ήδη, πρόσθεσε το περιεχόμενο αντί να τα αντικαταστήσεις.

## 10. Δοκιμή
```bash
cd ~/retropie-oled-monitor
python3 monitor.py
```
Σταμάτημα: Ctrl+C

---

## 11. Autostart στο boot (systemd)
Αντίγραψε το service αρχείο και ενεργοποίησέ το:
```bash
sudo cp ~/retropie-oled-monitor/retropie-oled-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable retropie-oled-monitor.service
sudo systemctl start retropie-oled-monitor.service
```
Έλεγχος / διαχείριση:
```bash
systemctl status retropie-oled-monitor.service   # κατάσταση
journalctl -u retropie-oled-monitor.service -f   # logs ζωντανά
sudo systemctl restart retropie-oled-monitor.service
sudo systemctl stop retropie-oled-monitor.service
sudo systemctl disable retropie-oled-monitor.service   # να μη ξεκινά στο boot
```

> Σημείωση: το service τρέχει ως χρήστης `pi` από τον φάκελο `/home/pi/retropie-oled-monitor`.
> Αν ο χρήστης/φάκελός σου είναι διαφορετικός, διόρθωσε το `.service` αρχείο.
