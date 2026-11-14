#!/usr/bin/env bash
# Self-terminating EC2 latency probes (USER RUNS THIS; it rents machines, the agent never does).
#
# Launches one t4g.micro per target AZ (Tokyo apne1-az1/az2/az4, Dublin euw1-az1, London
# euw2-az1), each runs latency/infra/binance_probe.py (120 s) and http_probe.py (20 rounds)
# plus the Polymarket geoblock check, prints the results to its serial console and powers
# off; shutdown behaviour "terminate" deletes it. Hard cap: every instance shuts down after
# 30 min even if a step hangs. No key pair, no inbound rules, IMDSv2 only. Read-only probes:
# nothing is ever posted to Polymarket or Binance.
#
# Cost (on-demand, 2026-10-10 price maps): t4g.micro $0.0092-0.0108/h + public IPv4 $0.005/h +
# 8 GB gp3, 5 instances x <= 0.5 h  =>  about $0.05 in total. Needs a default VPC per region.
#
#   aws login                                   # refresh credentials first (free)
#   bash latency/infra/aws_probe.sh launch --yes
#   bash latency/infra/aws_probe.sh collect    # ~15 min later: saves data/out/infra/aws/*.txt
#   bash latency/infra/aws_probe.sh cleanup    # terminates any probe still running
set -euo pipefail
cd "$(dirname "$0")/../.."
TAG=btclat-infra-probe
TARGETS="ap-northeast-1:apne1-az1 ap-northeast-1:apne1-az2 ap-northeast-1:apne1-az4 eu-west-1:euw1-az1 eu-west-2:euw2-az1"
AMI="resolve:ssm:/aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id"
OUT=data/out/infra/aws
STATE=$OUT/instances.txt

userdata() {
  local bp hp
  bp=$(base64 -w0 latency/infra/binance_probe.py)
  hp=$(base64 -w0 latency/infra/http_probe.py)
  cat <<EOF
#!/bin/bash
exec > >(tee -a /dev/console) 2>&1
shutdown -h +30
echo "server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4" > /etc/chrony/sources.d/aws.sources
chronyc reload sources || true
apt-get update -qq && apt-get install -y -qq python3-venv >/dev/null
python3 -m venv /opt/v && /opt/v/bin/pip install -q websockets 'httpx[http2]' numpy
mkdir -p /opt/p/latency/infra /opt/p/data/out/infra && cd /opt/p
echo $bp | base64 -d > latency/infra/binance_probe.py
echo $hp | base64 -d > latency/infra/http_probe.py
sleep 20; chronyc tracking | sed 's/^/CHRONY /'
TOKEN=\$(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')
echo "AZID \$(curl -s -H "X-aws-ec2-metadata-token: \$TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone-id)"
echo "GEOBLOCK \$(curl -s https://polymarket.com/api/geoblock)"
/opt/v/bin/python latency/infra/binance_probe.py 120 | tr -d '\n ' | sed 's/^/BINANCE /'; echo
/opt/v/bin/python latency/infra/http_probe.py 20 | tr -d '\n ' | sed 's/^/CLOB /'; echo
echo INFRA-PROBE-DONE
shutdown -h now
EOF
}

launch() {
  [[ "${1:-}" == "--yes" ]] || { echo "rents 5 small EC2 instances (~\$0.05 total); rerun with --yes"; exit 1; }
  mkdir -p "$OUT"; : > "$STATE"
  local ud; ud=$(mktemp); userdata > "$ud"
  for t in $TARGETS; do
    local region=${t%%:*} azid=${t##*:} subnet id
    subnet=$(aws ec2 describe-subnets --region "$region" \
      --filters Name=default-for-az,Values=true Name=availability-zone-id,Values="$azid" \
      --query 'Subnets[0].SubnetId' --output text)
    [[ "$subnet" == "None" ]] && { echo "no default subnet in $azid, skipped"; continue; }
    id=$(aws ec2 run-instances --region "$region" --image-id "$AMI" --instance-type t4g.micro \
      --subnet-id "$subnet" --associate-public-ip-address --user-data "file://$ud" \
      --instance-initiated-shutdown-behavior terminate \
      --metadata-options HttpTokens=required,HttpEndpoint=enabled \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG-$azid}]" \
      --query 'Instances[0].InstanceId' --output text)
    echo "$region $azid $id" | tee -a "$STATE"
  done
  rm -f "$ud"
  echo "launched; run 'collect' in ~15 min"
}

collect() {
  while read -r region azid id; do
    aws ec2 get-console-output --region "$region" --instance-id "$id" --latest --output text \
      > "$OUT/$azid.txt" || true
    if grep -q INFRA-PROBE-DONE "$OUT/$azid.txt"; then echo "$azid done"; else echo "$azid not finished"; fi
  done < "$STATE"
}

cleanup() {
  for region in ap-northeast-1 eu-west-1 eu-west-2; do
    ids=$(aws ec2 describe-instances --region "$region" \
      --filters "Name=tag:Name,Values=$TAG-*" Name=instance-state-name,Values=pending,running,stopping,stopped \
      --query 'Reservations[].Instances[].InstanceId' --output text)
    [[ -n "$ids" ]] && aws ec2 terminate-instances --region "$region" --instance-ids $ids >/dev/null \
      && echo "terminated $ids in $region" || echo "nothing running in $region"
  done
}

case "${1:-}" in
  launch) launch "${2:-}" ;;
  collect) collect ;;
  cleanup) cleanup ;;
  *) sed -n '2,19p' "$0" ;;
esac
