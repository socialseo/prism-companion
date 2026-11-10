#!/bin/zsh
cd "$(dirname "$0")"
echo 'Apri http://localhost:8765 nel browser.'
echo 'Per altri dispositivi usa http://IP-DEL-MAC:8765 sulla stessa rete Wi-Fi.'
echo 'Lascia questa finestra aperta. Ctrl+C per fermare il server.'
python3 server.py --host 0.0.0.0
