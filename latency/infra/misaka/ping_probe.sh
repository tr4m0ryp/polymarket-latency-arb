#!/usr/bin/env bash
# Misaka route probe: from AWS Tokyo apne1-az4, Dublin euw1-az1 and London euw2-az1, ping every
# Misaka speedtest IPv4 (targets.txt: region tier ip) and mtr the key European/Tokyo ones, to find
# which Misaka sites sit closest to our boxes and whether AWS Tokyo traffic to Misaka Europe rides
# Misaka's backbone. 3 x t4g.micro, self-terminating, ~$0.02. Read-only pings.
#   AWS_PROFILE=btclat-login bash latency/infra/misaka/ping_probe.sh launch|collect
set -euo pipefail
cd "$(dirname "$0")/../../.."
TAG=btclat-misaka-probe OUT=data/out/infra/misaka STATE=data/out/infra/misaka/instances.txt
AMI="resolve:ssm:/aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id"
TARGETS="ap-northeast-1:apne1-az4 eu-west-1:euw1-az1 eu-west-2:euw2-az1"
TRACE="NRT04 LON05 DUB02 AMS02 FRA13 STO02 MOW01 KHV01 HKG12"

userdata() {
  local t; t=$(base64 -w0 latency/infra/misaka/targets.txt)
  cat <<EOT
#!/bin/bash
exec > >(tee -a /dev/console) 2>&1
shutdown -h +25
apt-get install -y -qq mtr-tiny >/dev/null 2>&1 || true
echo $t | base64 -d > /tmp/t.txt
while read -r reg tier ip; do
  ( r=\$(ping -n -c 20 -i 0.2 -W 2 -q \$ip | tail -2 | tr '\n' ' '); echo "MPING \$reg \$tier \$ip \$r" ) &
done < /tmp/t.txt
wait
for reg in $TRACE; do
  ip=\$(awk -v r=\$reg '\$1==r{print \$3; exit}' /tmp/t.txt)
  mtr -n -r -c 5 -w \$ip 2>/dev/null | awk -v r=\$reg 'NR>2{print "MTR", r, \$2, \$6}'
done
echo MISAKA-PROBE-DONE
sleep 60; shutdown -h now
EOT
}

launch() {
  mkdir -p "$OUT"; : > "$STATE"; local ud; ud=$(mktemp); userdata > "$ud"
  for t in $TARGETS; do
    local region=${t%%:*} azid=${t##*:} subnet id
    subnet=$(aws ec2 describe-subnets --region "$region" --filters Name=default-for-az,Values=true \
      Name=availability-zone-id,Values="$azid" --query 'Subnets[0].SubnetId' --output text)
    id=$(aws ec2 run-instances --region "$region" --image-id "$AMI" --instance-type t4g.micro \
      --subnet-id "$subnet" --associate-public-ip-address --user-data "file://$ud" \
      --instance-initiated-shutdown-behavior terminate --metadata-options HttpTokens=required,HttpEndpoint=enabled \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG-$azid}]" \
      --query 'Instances[0].InstanceId' --output text)
    echo "$region $azid $id" | tee -a "$STATE"
  done
  rm -f "$ud"
}

collect() {
  while read -r region azid id; do
    aws ec2 get-console-output --region "$region" --instance-id "$id" --latest --output text > "$OUT/$azid.txt" || true
    grep -q MISAKA-PROBE-DONE "$OUT/$azid.txt" && echo "$azid done" || echo "$azid not finished"
  done < "$STATE"
}

"${1:-}"
