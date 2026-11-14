#!/usr/bin/env bash
# Route probe from a Misaka NRT04 (Tokyo) VM: is Misaka's own Tokyo -> London/Dublin path
# faster than AWS Tokyo -> Dublin (~101 ms one way)? Waits for the order, then measures
#   ICMP to Misaka LON05/DUB02/AMS02/FRA13 speedtest IPs (inside-Misaka route),
#   TCP connect to AWS eu-west-1/eu-west-2 endpoints and Binance (handoff cost),
#   mtr to London and Dublin (does the path cross the US or Russia?).
# Usage: bash latency/infra/misaka/nrt_probe.sh
set -euo pipefail
KEY=$(cat ~/.config/btclat/misaka_key)
SSHKEY=~/.config/btclat/misaka_nrt
API=https://app.misaka.io/api
OUT=data/out/infra/misaka/nrt04_route.txt

ip=""
until [ -n "$ip" ]; do
  ip=$(curl -s -H "Authorization: Token $KEY" $API/mc2/instances/ |
    python3 -c "import json,sys
print(next((i['access_ipv4'] for i in json.load(sys.stdin)['results']
  if i['node']['region']=='NRT04' and i['state']=='active' and i.get('access_ipv4')),''))" 2>/dev/null || true)
  [ -n "$ip" ] || sleep 60
done
echo "instance ip $ip"
SSH="ssh -i $SSHKEY -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 root@$ip"
until $SSH true 2>/dev/null; do sleep 20; done

$SSH 'bash -s' > "$OUT" <<'EOF'
export DEBIAN_FRONTEND=noninteractive
apt-get -qq update >/dev/null && apt-get -qq install -y mtr-tiny curl >/dev/null
date -u +%FT%TZ
for t in "LON05 45.142.244.202" "DUB02 45.150.240.129" "AMS02 45.11.106.130" "FRA13 194.45.101.132"; do
  set -- $t; echo "PING $1 $(ping -c 50 -i 0.2 -q $2 | tail -1)"; done
tcp() { curl -s -o /dev/null -w "%{time_connect}" "https://$1/" 2>/dev/null; }
for h in fstream.binance.com stream.binance.com ec2.eu-west-1.amazonaws.com ec2.eu-west-2.amazonaws.com clob.polymarket.com; do
  v=""; for i in 1 2 3 4 5; do v="$v $(tcp $h)"; done; echo "TCP $h$v"; done
for t in "LON05 45.142.244.202" "DUB02 45.150.240.129" "EUW1 ec2.eu-west-1.amazonaws.com"; do
  set -- $t; echo "MTR $1"; mtr -n -r -c 20 -w $2; done
EOF
cat "$OUT"
