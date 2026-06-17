#!/bin/bash
# RetroPie hook: καθαρίζει την κατάσταση όταν κλείνει το παιχνίδι.
# Το RetroPie το καλεί αυτόματα μόλις βγεις από ένα παιχνίδι.
# Χωρίς το αρχείο, το screen 2 δείχνει το aperture logo (idle).
#
# Εγκατάσταση: αντίγραψέ το ως
#   /opt/retropie/configs/all/runcommand-onend.sh
# και κάνε το εκτελέσιμο:  chmod +x runcommand-onend.sh

rm -f /tmp/game_status
