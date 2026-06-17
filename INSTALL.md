# Install on RetroPie (all via terminal commands)

> For **RetroPie** (Raspberry Pi) only. Everything is done by typing commands -
> no manual file editing. The display wiring is done separately (see README).

## Automatic script (recommended)
Shows each step separately + info/errors:
```bash
cd ~ && git clone https://github.com/orestisns/retropie-oled-monitor.git
cd ~/retropie-oled-monitor
chmod +x install.sh
./install.sh
```
Then: wire the displays and `sudo reboot`.

---

## Or manually (copy-paste all at once)

```bash
# 1) Update + system packages
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-pip i2c-tools libjpeg-dev zlib1g-dev git

# 2) Enable I2C (no menu)
sudo raspi-config nonint do_i2c 0

# 3) Create the 2 software I2C buses in config.txt
CONFIG=/boot/firmware/config.txt; [ -f "$CONFIG" ] || CONFIG=/boot/config.txt
grep -q "i2c_gpio_sda=23" "$CONFIG" || echo "dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24" | sudo tee -a "$CONFIG"
grep -q "i2c_gpio_sda=22" "$CONFIG" || echo "dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27" | sudo tee -a "$CONFIG"

# 4) Download the project
cd ~ && git clone https://github.com/orestisns/retropie-oled-monitor.git
cd ~/retropie-oled-monitor

# 5) Python libraries
pip3 install luma.oled pillow psutil || pip3 install --break-system-packages luma.oled pillow psutil

# 6) Install game hooks (for screen 2)
sudo cp runcommand-onstart.sh /opt/retropie/configs/all/runcommand-onstart.sh
sudo cp runcommand-onend.sh   /opt/retropie/configs/all/runcommand-onend.sh
sudo chmod +x /opt/retropie/configs/all/runcommand-onstart.sh /opt/retropie/configs/all/runcommand-onend.sh

# 7) Install autostart (systemd) - adapt to your user
sudo cp retropie-oled-monitor.service /etc/systemd/system/
sudo sed -i "s|/home/pi/retropie-oled-monitor|$HOME/retropie-oled-monitor|g; s|^User=pi|User=$USER|" /etc/systemd/system/retropie-oled-monitor.service
sudo systemctl daemon-reload
sudo systemctl enable retropie-oled-monitor.service

# 8) Reboot
sudo reboot
```

## Check after reboot
```bash
# Do the 2 buses exist?
ls /dev/i2c-3 /dev/i2c-4

# Are the displays detected? (should show 3c)
i2cdetect -y 3
i2cdetect -y 4

# Is the service running?
systemctl status retropie-oled-monitor.service
```

## Useful management commands
```bash
# Live logs (debug)
journalctl -u retropie-oled-monitor.service -f

# Restart / Stop
sudo systemctl restart retropie-oled-monitor.service
sudo systemctl stop retropie-oled-monitor.service

# Run manually (after stopping the service)
cd ~/retropie-oled-monitor && python3 monitor.py
```

## Update to a new version
```bash
cd ~/retropie-oled-monitor
git pull
sudo systemctl restart retropie-oled-monitor.service
```

---

### Notes
- If step 6 gives "No such file or directory", the folder `/opt/retropie/configs/all/` does not exist - it is not a proper RetroPie image.
- If the displays are not detected (`i2cdetect` does not show `3c`), check the wiring + that the 2 lines were added to config.txt.
- The service runs as your user (step 7 adapts it automatically).
