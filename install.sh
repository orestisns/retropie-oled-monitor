#!/usr/bin/env bash
#
# RetroPie OLED Monitor - installer (no apt, EOL-friendly)
# Runs each step in order. Stops immediately if a step fails.
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
warn()  { echo -e "    ${YEL}[WARN]${NC} $1"; }
fail()  { echo -e "    ${RED}[ERROR]${NC} $1"; echo; echo -e "${RED}${BOLD}Installation aborted.${NC}"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BOLD}RetroPie OLED Monitor - Installer${NC}"
echo "Project folder: $SCRIPT_DIR"

# --- Check: not as root ---
if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    fail "Do not run with sudo. Just run: ./install.sh"
fi

# --- Step 1: Enable I2C ---
step "1/5  Enable I2C"
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_i2c 0 && ok "I2C enabled" || warn "raspi-config returned an error (ok under QEMU)"
else
    warn "raspi-config not found - make sure I2C is enabled manually"
fi

# --- Step 2: Two software I2C buses in config.txt ---
step "2/5  Create software I2C buses (bus 3 & 4)"
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
info "File: $CONFIG"
[ -f "$CONFIG" ] || fail "config.txt not found"
if grep -q "i2c_gpio_sda=23" "$CONFIG"; then
    info "bus 3 already present - skipped"
else
    echo "dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24" | sudo tee -a "$CONFIG" >/dev/null \
        && ok "Added bus 3 (GPIO23/24)" || fail "Could not write to $CONFIG"
fi
if grep -q "i2c_gpio_sda=22" "$CONFIG"; then
    info "bus 4 already present - skipped"
else
    echo "dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27" | sudo tee -a "$CONFIG" >/dev/null \
        && ok "Added bus 4 (GPIO22/27)" || fail "Could not write to $CONFIG"
fi

# --- Step 3: Ensure pip (no apt) ---
step "3/5  Ensure pip is available"
if python3 -m pip --version >/dev/null 2>&1; then
    ok "pip already present: $(python3 -m pip --version)"
else
    info "Bootstrapping pip via ensurepip..."
    python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    if ! python3 -m pip --version >/dev/null 2>&1; then
        info "ensurepip unavailable - trying get-pip (version-matched for EOL Python)..."
        PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "https://bootstrap.pypa.io/pip/$PYV/get-pip.py" -o /tmp/get-pip.py \
              || curl -fsSL "https://bootstrap.pypa.io/get-pip.py" -o /tmp/get-pip.py
        else
            wget -qO /tmp/get-pip.py "https://bootstrap.pypa.io/pip/$PYV/get-pip.py" \
              || wget -qO /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py"
        fi
        python3 /tmp/get-pip.py --user >/dev/null 2>&1 || true
    fi
    python3 -m pip --version >/dev/null 2>&1 \
        && ok "pip installed: $(python3 -m pip --version)" \
        || fail "Could not install pip (check internet connection)"
fi

# --- Step 4: Python libraries ---
step "4/5  Python libraries (luma.oled, pillow, psutil)"
info "Prebuilt wheels from piwheels; pillow<10 for Python 3.7 (Buster)"
PIPW="--extra-index-url https://www.piwheels.org/simple"
python3 -m pip install --user --prefer-binary --no-cache-dir $PIPW "pillow<10" luma.oled psutil \
    || fail "pip install failed - if on QEMU/EOL, try the apt backup: ./install-apt.sh"
python3 -c "import PIL, psutil, luma.oled" >/dev/null 2>&1 \
    && ok "Python libraries installed & importable" \
    || fail "Installed but not importable - check pip output above"

# --- Step 5: hooks + autostart ---
step "5/5  Install hooks + autostart"
HOOKDIR=/opt/retropie/configs/all
[ -d "$HOOKDIR" ] || fail "$HOOKDIR not found - does not look like RetroPie"
sudo cp "$SCRIPT_DIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onstart.sh" \
  && sudo cp "$SCRIPT_DIR/runcommand-onend.sh" "$HOOKDIR/runcommand-onend.sh" \
  && sudo chmod +x "$HOOKDIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onend.sh" \
  && ok "Game hooks installed in $HOOKDIR" || fail "Failed to copy hooks"

SVC=/etc/systemd/system/retropie-oled-monitor.service
sudo cp "$SCRIPT_DIR/retropie-oled-monitor.service" "$SVC" \
  && sudo sed -i "s|/home/pi/retropie-oled-monitor|$SCRIPT_DIR|g; s|^User=pi|User=$USER|" "$SVC" \
  && sudo systemctl daemon-reload \
  && sudo systemctl enable retropie-oled-monitor.service >/dev/null 2>&1 \
  && ok "Service installed & enabled (User=$USER)" || fail "Failed to install service"

# --- Success (reached only if every step passed) ---
echo
echo -e "${GREEN}${BOLD}Installation successful.${NC}"
echo
echo -e "Now reboot:   ${BOLD}sudo reboot${NC}"
echo "After reboot, check that everything is up:"
echo "    ls /dev/i2c-3 /dev/i2c-4"
echo "    systemctl status retropie-oled-monitor.service"
echo
