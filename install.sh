#!/usr/bin/env bash
#
# RetroPie OLED Monitor — installer
# Τρέχει κάθε βήμα ξεχωριστά, δείχνει τι κάνει και τυχόν σφάλματα.
#
# Χρήση (ΟΧΙ με sudo):
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

echo -e "${BOLD}RetroPie OLED Monitor — Installer${NC}"
echo "Φάκελος project: $SCRIPT_DIR"

# --- Έλεγχος: όχι ως root ---
if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    fail "Μην το τρέχεις με sudo. Τρέξε απλά: ./install.sh"
    exit 1
fi

# --- Βήμα 1: Πακέτα συστήματος ---
step "1/6  Ενημέρωση & πακέτα συστήματος"
info "sudo apt update + εγκατάσταση python3-pip, i2c-tools, libjpeg-dev, zlib1g-dev, git"
if sudo apt update && sudo apt install -y python3-pip i2c-tools libjpeg-dev zlib1g-dev git; then
    ok "Πακέτα εγκαταστάθηκαν"
else
    fail "Αποτυχία εγκατάστασης πακέτων (έλεγξε δίκτυο/apt)"
fi

# --- Βήμα 2: Ενεργοποίηση I2C ---
step "2/6  Ενεργοποίηση I2C"
if sudo raspi-config nonint do_i2c 0; then
    ok "I2C ενεργοποιήθηκε"
else
    warn "Δεν βρέθηκε raspi-config — παράλειψη (έλεγξε χειροκίνητα ότι το I2C είναι ON)"
fi

# --- Βήμα 3: Δύο software I2C buses στο config.txt ---
step "3/6  Δημιουργία software I2C buses (bus 3 & 4)"
CONFIG=/boot/firmware/config.txt
[ -f "$CONFIG" ] || CONFIG=/boot/config.txt
info "Αρχείο: $CONFIG"
if [ ! -f "$CONFIG" ]; then
    fail "Δεν βρέθηκε config.txt"
else
    L3="dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24"
    L4="dtoverlay=i2c-gpio,bus=4,i2c_gpio_sda=22,i2c_gpio_scl=27"
    if grep -q "i2c_gpio_sda=23" "$CONFIG"; then
        info "bus 3 υπάρχει ήδη — παράλειψη"
    else
        echo "$L3" | sudo tee -a "$CONFIG" >/dev/null && ok "Προστέθηκε bus 3 (GPIO23/24)"
    fi
    if grep -q "i2c_gpio_sda=22" "$CONFIG"; then
        info "bus 4 υπάρχει ήδη — παράλειψη"
    else
        echo "$L4" | sudo tee -a "$CONFIG" >/dev/null && ok "Προστέθηκε bus 4 (GPIO22/27)"
    fi
fi

# --- Βήμα 4: Python βιβλιοθήκες ---
step "4/6  Python βιβλιοθήκες (luma.oled, pillow, psutil)"
if pip3 install luma.oled pillow psutil; then
    ok "Εγκαταστάθηκαν"
elif pip3 install --break-system-packages luma.oled pillow psutil; then
    ok "Εγκαταστάθηκαν (--break-system-packages)"
else
    fail "Αποτυχία pip install"
fi

# --- Βήμα 5: runcommand hooks (game stats) ---
step "5/6  Εγκατάσταση RetroPie game hooks"
HOOKDIR=/opt/retropie/configs/all
if [ ! -d "$HOOKDIR" ]; then
    fail "Δεν βρέθηκε $HOOKDIR — δεν φαίνεται να είναι RetroPie"
else
    if sudo cp "$SCRIPT_DIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onstart.sh" \
       && sudo cp "$SCRIPT_DIR/runcommand-onend.sh" "$HOOKDIR/runcommand-onend.sh" \
       && sudo chmod +x "$HOOKDIR/runcommand-onstart.sh" "$HOOKDIR/runcommand-onend.sh"; then
        ok "Hooks εγκαταστάθηκαν στο $HOOKDIR"
    else
        fail "Αποτυχία αντιγραφής hooks"
    fi
fi

# --- Βήμα 6: systemd autostart ---
step "6/6  Autostart (systemd service)"
SVC=/etc/systemd/system/retropie-oled-monitor.service
if sudo cp "$SCRIPT_DIR/retropie-oled-monitor.service" "$SVC" \
   && sudo sed -i "s|/home/pi/retropie-oled-monitor|$SCRIPT_DIR|g; s|^User=pi|User=$USER|" "$SVC" \
   && sudo systemctl daemon-reload \
   && sudo systemctl enable retropie-oled-monitor.service; then
    ok "Service εγκαταστάθηκε & ενεργοποιήθηκε (User=$USER, dir=$SCRIPT_DIR)"
else
    fail "Αποτυχία εγκατάστασης service"
fi

# --- Σύνοψη ---
echo
echo -e "${BOLD}==================== ΣΥΝΟΨΗ ====================${NC}"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}Όλα τα βήματα ολοκληρώθηκαν.${NC} (warnings: $WARN_COUNT)"
else
    echo -e "${RED}Ολοκληρώθηκε με $FAIL_COUNT σφάλμα(τα)${NC} και $WARN_COUNT warning(s) — δες παραπάνω."
fi
echo
echo "Επόμενα βήματα:"
echo "  1) Καλωδίωσε τις 2 οθόνες (βλ. README)"
echo "  2) Κάνε επανεκκίνηση:   sudo reboot"
echo "  3) Μετά το reboot έλεγξε:"
echo "       ls /dev/i2c-3 /dev/i2c-4"
echo "       i2cdetect -y 3   (πρέπει να δείξει 3c)"
echo "       i2cdetect -y 4   (πρέπει να δείξει 3c)"
echo "       systemctl status retropie-oled-monitor.service"
echo
