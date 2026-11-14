#!/usr/bin/env bash
# Relay probe: Tokyo apne1-az4 forwards Binance perp updates over UDP to Dublin and London,
# which also read Binance directly; each receiver compares both paths per update id.
# 3 x t4g.micro, self-terminating (30 min cap), ~$0.03. Read-only: nothing is sent to any venue.
#   AWS_PROFILE=btclat-login bash latency/infra/relay/probe.sh launch
#   AWS_PROFILE=btclat-login bash latency/infra/relay/probe.sh collect   # ~12 min later
#   AWS_PROFILE=btclat-login bash latency/infra/relay/probe.sh cleanup
set -euo pipefail
cd "$(dirname "$0")/../../.."
TAG=btclat-relay-probe PORT=9700 SECS=300
AMI="resolve:ssm:/aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id"
OUT=data/out/infra/relay STATE=data/out/infra/relay/instances.txt

userdata() {  # $1 = command line run at START
  local f e s r
  f=$(base64 -w0 latency/infra/relay/feed.py); s=$(base64 -w0 latency/infra/relay/sender.py)
  r=$(base64 -w0 latency/infra/relay/receiver.py)
  cat <<EOT
#!/bin/bash
exec > >(tee -a /dev/console) 2>&1
shutdown -h +30
echo "server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4" > /etc/chrony/sources.d/aws.sources
chronyc reload sources || true
apt-get update -qq && apt-get install -y -qq python3-venv >/dev/null
python3 -m venv /opt/v && /opt/v/bin/pip install -q websockets numpy
mkdir -p /opt/r && cd /opt/r
echo $f | base64 -d > feed.py; echo $s | base64 -d > sender.py; echo $r | base64 -d > receiver.py
chronyc tracking | sed 's/^/CHRONY /'
while [ \$(date +%s) -lt $START ]; do sleep 1; done
/opt/v/bin/python $1
echo RELAY-PROBE-DONE
shutdown -h now
EOT
}

launch_one() {  # region azid cmd [sg] -> instance id
  local region=$1 azid=$2 cmd=$3 sg=${4:-} subnet ud extra=()
  subnet=$(aws ec2 describe-subnets --region "$region" --filters Name=default-for-az,Values=true \
    Name=availability-zone-id,Values="$azid" --query 'Subnets[0].SubnetId' --output text)
  ud=$(mktemp); userdata "$cmd" > "$ud"
  [[ -n "$sg" ]] && extra=(--security-group-ids "$sg")
  aws ec2 run-instances --region "$region" --image-id "$AMI" --instance-type t4g.micro \
    --subnet-id "$subnet" --associate-public-ip-address --user-data "file://$ud" "${extra[@]}" \
    --instance-initiated-shutdown-behavior terminate \
    --metadata-options HttpTokens=required,HttpEndpoint=enabled \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG-$azid}]" \
    --query 'Instances[0].InstanceId' --output text
  rm -f "$ud"
}

udp_sg() {  # region -> sg id allowing UDP PORT inbound (default SG rules kept for outbound)
  local region=$1 vpc sg
  vpc=$(aws ec2 describe-vpcs --region "$region" --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)
  sg=$(aws ec2 describe-security-groups --region "$region" --filters Name=group-name,Values=$TAG \
    Name=vpc-id,Values="$vpc" --query 'SecurityGroups[0].GroupId' --output text)
  if [[ "$sg" == "None" ]]; then
    sg=$(aws ec2 create-security-group --region "$region" --group-name $TAG --vpc-id "$vpc" \
      --description "relay probe UDP in" --query GroupId --output text)
    aws ec2 authorize-security-group-ingress --region "$region" --group-id "$sg" \
      --protocol udp --port $PORT --cidr 0.0.0.0/0 >/dev/null
  fi
  echo "$sg"
}

launch() {
  mkdir -p "$OUT"; : > "$STATE"
  START=$(( $(date +%s) + 420 ))
  local ips=() id ip
  for t in eu-west-1:euw1-az1 eu-west-2:euw2-az1; do
    local region=${t%%:*} azid=${t##*:}
    id=$(launch_one "$region" "$azid" "receiver.py $SECS $PORT" "$(udp_sg "$region")")
    aws ec2 wait instance-running --region "$region" --instance-ids "$id"
    ip=$(aws ec2 describe-instances --region "$region" --instance-ids "$id" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    ips+=("$ip:$PORT"); echo "$region $azid $id" | tee -a "$STATE"
  done
  id=$(launch_one ap-northeast-1 apne1-az4 "sender.py $((SECS + 5)) ${ips[*]}")
  echo "ap-northeast-1 apne1-az4 $id" | tee -a "$STATE"
  echo "measuring from $(date -u -d @$START +%T) UTC for ${SECS}s; collect after $(date -u -d @$((START + SECS + 60)) +%T)"
}

collect() {
  while read -r region azid id; do
    aws ec2 get-console-output --region "$region" --instance-id "$id" --latest --output text > "$OUT/$azid.txt" || true
    grep -q RELAY-PROBE-DONE "$OUT/$azid.txt" && echo "$azid done" || echo "$azid not finished"
  done < "$STATE"
}

cleanup() {
  for region in ap-northeast-1 eu-west-1 eu-west-2; do
    ids=$(aws ec2 describe-instances --region "$region" --filters "Name=tag:Name,Values=$TAG-*" \
      Name=instance-state-name,Values=pending,running,stopping,stopped \
      --query 'Reservations[].Instances[].InstanceId' --output text)
    [[ -n "$ids" ]] && aws ec2 terminate-instances --region "$region" --instance-ids $ids >/dev/null && echo "terminated $ids"
    if [[ "$region" != ap-northeast-1 ]]; then
      sg=$(aws ec2 describe-security-groups --region "$region" --filters Name=group-name,Values=$TAG \
        --query 'SecurityGroups[0].GroupId' --output text)
      [[ "$sg" != "None" ]] && aws ec2 delete-security-group --region "$region" --group-id "$sg" 2>/dev/null \
        && echo "deleted $sg" || true
    fi
  done
}

"${1:-}"
