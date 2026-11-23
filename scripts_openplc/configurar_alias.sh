#!/bin/bash
# Agrega al servidor una IP virtual por placa (alias en la tarjeta de red de la red de laboratorio).
# El editor identifica cada runtime por la IP de origen de su respuesta de descubrimiento, asi que cada placa
# necesita su propia IP en el servidor. Hay que ejecutarlo como administrador (sudo) cada vez que arranca el servidor,
# o ponerlo en la configuracion de red del sistema.
# Uso: sudo ./configurar_alias.sh <interfaz> <ip1>/<mascara> [<ip2>/<mascara> ...]
#      sudo ./configurar_alias.sh enp1s0f1 10.42.0.201/24 10.42.0.202/24
set -e
IF="$1"; shift
[ -n "$IF" ] && [ $# -gt 0 ] || { sed -n '2,9p' "$0"; exit 2; }
for a in "$@"; do ip addr add "$a" dev "$IF" 2>/dev/null || echo "ya existe o no se pudo: $a"; done
ip -br addr show "$IF"
