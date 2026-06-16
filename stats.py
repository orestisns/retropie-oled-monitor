#!/usr/bin/env python3
import os, sys, time, subprocess, psutil

# ---- ANSI χρώματα ----
GREEN  = "\033[32m"
BRIGHT = GREEN          # ίδιο πράσινο παντού (όχι ξεχωριστό φωτεινό)
AMBER  = "\033[33m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def enable_ansi_windows():
    # Ενεργοποίηση VT100 χρωμάτων στο Windows terminal
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def cpu_temp():
    # Δουλεύει στο Raspberry Pi· στα Windows επιστρέφει None
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(out.strip().replace("temp=", "").replace("'C", ""))
    except Exception:
        pass
    try:
        temps = psutil.sensors_temperatures()
        for entries in temps.values():
            if entries:
                return float(entries[0].current)
    except Exception:
        pass
    return None

EMU_NAMES = (
    "retroarch", "ppsspp", "dolphin", "pcsx", "mupen64plus", "reicast",
    "redream", "mame", "scummvm", "drastic", "duckstation", "vice",
    "mednafen", "snes9x", "fbneo", "fceux", "yabause", "hatari",
)

def emulation_running():
    # True αν τρέχει κάποιος γνωστός emulator αυτή τη στιγμή
    try:
        for p in psutil.process_iter(["name"]):
            n = (p.info["name"] or "").lower()
            if any(e in n for e in EMU_NAMES):
                return True
    except Exception:
        pass
    return False

def uptime_str():
    # Πόση ώρα δουλεύει το σύστημα
    try:
        secs = int(time.time() - psutil.boot_time())
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        d, h = divmod(h, 24)
        if d:
            return f"{d}d {h:02d}:{m:02d}:{s:02d}"
        return f"{h:02d}:{m:02d}:{s:02d}"
    except Exception:
        return "N/A"

def throttled_status():
    # Επιστρέφει (κείμενο, χρώμα). Μόνο στο Raspberry Pi (vcgencmd).
    try:
        out = subprocess.check_output(["vcgencmd", "get_throttled"]).decode()
        val = int(out.strip().split("=")[1], 16)
    except Exception:
        return "N/A", GREEN
    if val == 0:
        return "OK", BRIGHT
    flags = []
    if val & 0x1:
        flags.append("UNDER-VOLTAGE")
    if val & 0x2:
        flags.append("FREQ CAPPED")
    if val & 0x4:
        flags.append("THROTTLED")
    if val & 0x8:
        flags.append("TEMP LIMIT")
    if not flags:  # μόνο "has occurred" bits (παλιότερο συμβάν)
        flags.append("PAST EVENT")
    return ", ".join(flags), RED

def bar(percent, width=36):
    percent = max(0.0, min(100.0, percent))
    filled = int(round(width * percent / 100.0))
    # χρώμα ανάλογα με το πόσο γεμάτο
    color = BRIGHT if percent < 60 else (AMBER if percent < 85 else RED)
    return f"{color}[{'|' * filled}{' ' * (width - filled)}]{RESET}"

BANNER = r"""
                 =/;;/-
                +:    //
               /;      /;
              -X        H.
.//;;;:;;-,   X=        :+   .-;:=;:;%;.
M-       ,=;;;#:,      ,:#;;:=,       ,@
:%           :%.=/++++/=.$=           %=
 ,%;         %/:+/;,,/++:+/         ;+.
   ,+/.    ,;@+,        ,%H;,    ,/+,
      ;+;;/= @.  .H##X   -X :///+;
      ;+=;;;.@,  .XM@$.  =X.//;=%/.
   ,;:      :@%=        =$H:     .+%-
 ,%=         %;-///==///-//         =%,
;+           :%-;;;;;;;;-X-           +:
@-      .-;;;;M-        =M/;;;-.      -X
 :;;::;;-.    %-        :+    ,-;;-;:==
              ,X        H.
               ;/      %=
                //    +;
                 ,////,
"""

def type_out(text, delay=0.02, color=GREEN):
    # Τυπώνει το κείμενο γράμμα-γράμμα (εφέ πληκτρολόγησης)
    sys.stdout.write(color)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET + "\n")
    sys.stdout.flush()

SPIN_DELAY = 0.18  # ίδια ταχύτητα περιστροφής spinner παντού

def boot_step(line, type_delay=0.03, think_cycles=3, think_delay=SPIN_DELAY):
    # Τυπώνει τη γραμμή, δείχνει spinner "σκέψης", μετά γράφει το OK/PASSED
    split = line.rindex(" ") + 1
    prefix, result = line[:split], line[split:]
    sys.stdout.write(GREEN)
    for ch in prefix:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(type_delay)
    frames = "|/-\\"
    for i in range(think_cycles * len(frames)):
        sys.stdout.write(frames[i % len(frames)])
        sys.stdout.flush()
        time.sleep(think_delay)
        sys.stdout.write("\b")
        sys.stdout.flush()
    sys.stdout.write(result + RESET + "\n")
    sys.stdout.flush()

def boot_sequence():
    clear_screen()
    print()
    type_out("  RETROPIE MONITOR  ::  TERMINAL BOOT", 0.04, BRIGHT)
    time.sleep(0.6)
    type_out("  -----------------------------------", 0.015)
    time.sleep(0.5)
    # (γραμμή, think_cycles) — ίδια ταχύτητα, διαφορετικός αριθμός περιστροφών
    boot_lines = [
        ("  > INITIALIZING SYSTEM ..................... OK", 3),
        ("  > LOADING RETROPIE MONITOR v1.2 ........... OK", 2),
        ("  > MOUNTING DRIVES ......................... OK", 1),
        ("  > READING CPU SENSORS ..................... OK", 3),
        ("  > READING MEMORY BANKS .................... OK", 2),
    ]
    for ln, cyc in boot_lines:
        boot_step(ln, think_cycles=cyc)
        time.sleep(0.4)

    # --- Βήμα ραδιενέργειας με προειδοποίηση που αναβοσβήνει ---
    prefix = "  > MEASURING RADIATION LEVELS .............. "
    sys.stdout.write(GREEN)
    for ch in prefix:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(0.03)
    # spinner "loading" αντί για στατική παύση
    frames = "|/-\\"
    for i in range(9):
        sys.stdout.write(frames[i % len(frames)])
        sys.stdout.flush()
        time.sleep(SPIN_DELAY)
        sys.stdout.write("\b")
        sys.stdout.flush()
    time.sleep(2.0)  # παύση μετά το spinner, πριν αρχίσει να αναβοσβήνει
    warn = "ABOVE NORMAL LEVELS!"
    for _ in range(2):
        sys.stdout.write(RED + warn + RESET)
        sys.stdout.flush()
        time.sleep(0.8)
        sys.stdout.write("\b" * len(warn) + " " * len(warn) + "\b" * len(warn))
        sys.stdout.flush()
        time.sleep(0.6)
    sys.stdout.write(GREEN + "PASSED" + RESET + "\n")
    sys.stdout.flush()
    time.sleep(0.4)

    boot_lines2 = [
        ("  > RUNNING SELF-TEST ....................... PASSED", 3),
        ("  > ESTABLISHING UPLINK ..................... OK", 1),
    ]
    for ln, cyc in boot_lines2:
        boot_step(ln, think_cycles=cyc)
        time.sleep(0.4)
    print()
    type_out("  SYSTEM READY. STARTING MONITOR", 0.06, BRIGHT)
    for _ in range(3):
        sys.stdout.write(BRIGHT + " ." + RESET)
        sys.stdout.flush()
        time.sleep(0.8)
    time.sleep(1.0)

def splash_logo(seconds=1.5):
    # Boot screen: το σύμβολο εμφανίζεται γραμμή-γραμμή
    clear_screen()
    print()
    art = BANNER.strip("\n").split("\n")
    for l in art:
        print(GREEN + l + RESET)
        sys.stdout.flush()
        time.sleep(0.06)
    print()
    print(GREEN + "     R E T R O P I E   M O N I T O R" + RESET)
    print(GREEN + "        // SYSTEM ONLINE  v1.2 //" + RESET)
    time.sleep(seconds)

def main():
    enable_ansi_windows()
    boot_sequence()
    splash_logo()
    disk_path = "C:\\" if os.name == "nt" else "/"
    psutil.cpu_percent(interval=None)  # προετοιμασία μέτρησης
    line = "=" * 69

    first = True
    while True:
        cpu  = psutil.cpu_percent(interval=None)
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage(disk_path)
        temp = cpu_temp()
        temp_pct = (temp / 80.0 * 100.0) if temp is not None else 0.0
        temp_str = f"{temp:.1f}°C" if temp is not None else " N/A "

        frame = []
        frame.append(GREEN + line)
        frame.append(" RETROPIE MONITOR v1.2")
        frame.append(line + RESET)
        frame.append("")
        frame.append(GREEN + "  SYSTEM STATS")
        frame.append("  " + "=" * 67 + RESET)
        thr_txt, thr_col = throttled_status()
        frame.append(f"{GREEN}   CPU usage : {cpu:5.1f} %       {bar(cpu)}{RESET}")
        frame.append(f"{GREEN}   CPU temp  : {temp_str:>6}        {bar(temp_pct)}{RESET}")
        frame.append(f"{GREEN}   Throttle  : {thr_col}{thr_txt}{RESET}")
        frame.append(f"{GREEN}   RAM       : {mem.percent:5.1f} %       {bar(mem.percent)} "
                     f"{GREEN}{mem.used//1024//1024}/{mem.total//1024//1024} MB{RESET}")
        frame.append(f"{GREEN}   Disk      : {disk.percent:5.1f} %       {bar(disk.percent)}{RESET}")
        frame.append(f"{GREEN}   Uptime    : {uptime_str()}{RESET}")
        frame.append("")
        emu = emulation_running()
        emu_txt = f"{GREEN}RUNNING{GREEN}" if emu else f"{RED}OFF{GREEN}"
        frame.append(GREEN + line)
        frame.append(" STATUS: ONLINE")
        frame.append(f"{GREEN} EMULATION: {emu_txt}")
        frame.append(line + RESET)

        clear_screen()
        if first:
            # Εμφάνιση σελίδας σταδιακά, από πάνω προς τα κάτω
            for row in frame:
                print(row)
                sys.stdout.flush()
                time.sleep(0.06)
            first = False
        else:
            print("\n".join(frame))
        time.sleep(1)

if __name__ == "__main__":
    main()
