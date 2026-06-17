#!/usr/bin/env bash
#
# RetroPie OLED Monitor - installer
# Runs each step separately, showing what it does and any errors.
#
# Usage (NOT with sudo):
#   cd ~/retropie-oled-monitor
#   chmod +x install.sh
#   ./install.sh
#
set -u

GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; CYA='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

step()  { echo; echo -e "${CYA}${BOLD}==> $1${NC}"; }
info()  { echo -e "    $1"; }
ok()    { echo -e "    ${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "    ${YEL}[WARN]${NC} $1"; WARN_COUNT=$((WARN_COUNT+1)); }
fail()  { echo -e "    ${RED}[ERROR]${NC} $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }

WARN_COUNT=0
FAIL_COUNT=0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BOLD}RetroPie OLED Monitor - Installer${NC}"
echo "Project folder: $SCRIPT_DIR"

# --- Check: not as root ---
if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    fail "Do not run with sudo. Just run: ./install.sh"
    exit 1
fi

# --- Step 1: System packages ---
step "1/6  System update & packages"
info "sudo apt update + install python3-pip, i2c-tools, libjpeg-dev, zlib1g-dev, git"
if sudo apt update && sudo apt install -y python3-pip i2c-tools libjpeg-dev zlib1g-dev git; then
    ok "Packages installed"
else
    fail "Package installation failed (check network/apt)"
fi

# --- Step 2: Enable I2C ---
step "2/6  Enable I2C"
if sudo raspi-config nonint do_i2c 0; then
    ok "I2C enabled"
else
    warn "raspi-config not found - skipped (make sure I2C is ON manually)"
fi

# --- Step 3: Two software I2C buses in config.txt ---
step "3/6  Create software I2C buses (bus 3 & 4)"
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
info "File: $CONFIG"
if [ ! -f "$CONFIG" ]; then
    fail "config.txt not found"
else
    L3="dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24"
    L4="dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27"
    if grep -q "i2c_gpio_sda=23" "$CONFIG"; then
        info "bus 3 already present - skipped"
    else
        echo "$L3" | sudo tee -a "$CONFIG" >/dev/null && ok "Added bus 3 (GPIO23/24)"
    fi
    if grep -q "i2c_gpio_sda=22" "$CONFIG"; then
        info "bus 4 already present - skipped"
    else
        echo "$L4" | sudo tee -a "$CONFIG" >/dev/null && ok "Added bus 4 (GPIO22/27)"
    fi
fi

# --- Step 4: Python libraries ---
step "4/6  Python libraries (luma.oled, pillow, psutil)"
if pip3 install luma.oled pillow psutil; then
    ok "Installed"
elif pip3 install --break-system-packages luma.oled pillow psutil; then
    ok "Installed (--break-system-packages)"
else
    fail "pip install failed"
fi

# --- Step 5: runcommand hooks (game stats) ---
step "5/6  Install RetroPie game hooks"
HOOKDIR=/opt/retropie/configs/all
if [ ! -d "$HOOKDIR" ]; then
    fail "$HOOKDIR not found - does not look like RetroPie"
else
    if sudo cp "$SCRIPT_DIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onstart.sh" \
       && sudo cp "$SCRIPT_DIR/runcommand-onend.sh" "$HOOKDIR/runcommand-onend.sh" \
       && sudo chmod +x "$HOOKDIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onend.sh"; then
        ok "Hooks installed in $HOOKDIR"
    else
        fail "Failed to copy hooks"
    fi
fi

# --- Step 6: systemd autostart ---
step "6/6  Autostart (systemd service)"
SVC=/etc/systemd/system/retropie-oled-monitor.service
if sudo cp "$SCRIPT_DIR/retropie-oled-monitor.service" "$SVC" \
   && sudo sed -i "s|/home/pi/retropie-oled-monitor|$SCRIPT_DIR|g; s|^User=pi|User=$USER|" "$SVC" \
   && sudo systemctl daemon-reload \
   && sudo systemctl enable retropie-oled-monitor.service; then
    ok "Service installed & enabled (User=$USER, dir=$SCRIPT_DIR)"
else
    fail "Failed to install service"
fi

# --- Summary ---
echo
echo -e "${BOLD}==================== SUMMARY ====================${NC}"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}All steps completed.${NC} (warnings: $WARN_COUNT)"
else
    echo -e "${RED}Completed with $FAIL_COUNT error(s)${NC} and $WARN_COUNT warning(s) - see above."
fi
echo
echo "Next steps:"
echo "  1) Wire the 2 displays (see README)"
echo "  2) Reboot:   sudo reboot"
echo "  3) After reboot, verify:"
echo "       ls /dev/i2c-3 /dev/i2c-4"
echo "       i2cdetect -y 3   (should show 3c)"
echo "       i2cdetect -y 4   (should show 3c)"
echo "       systemctl status retropie-oled-monitor.service"
echo
