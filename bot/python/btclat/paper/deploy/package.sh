#!/usr/bin/env bash
# Build the paper-bot kit for an Ubuntu 24.04 arm64 t4g.small in eu-west-1 (AZ id euw1-az1).
#   bash btclat/paper/deploy/package.sh            -> dist/btclat-paper.tgz
# Runs NO AWS command. The launch commands below are printed for the user to run with the
# btclat-login profile (account <AWS_ACCOUNT>) after review; nothing here executes them.
# Cost: t4g.small $0.0184/h + IPv4 $0.005/h + 30 GB gp3 ~$2.4/month = ~$20/month (~$1.30 per 48 h run).
set -euo pipefail
cd "$(dirname "$0")/../../.."
OUT=dist/btclat-paper.tgz
mkdir -p dist
python3 - <<'PY'
import hashlib, json
from pathlib import Path
want = json.loads(Path("data/out/predict/prereg2.json").read_text())["models_sha256_16"]
for name, h in want.items():
    got = hashlib.sha256(Path("data/out/predict/models", name).read_bytes()).hexdigest()[:16]
    assert got == h, f"{name}: {got} != {h}"
print("model hashes match prereg2.json")
PY
tar czf "$OUT" --exclude=__pycache__ --exclude='*.pyc' \
  pyproject.toml btclat research \
  data/out/strategy/fair-pzm.json data/out/strategy/selection2.json \
  data/out/predict/prereg2.json data/out/predict/models/v1_L-40.pkl \
  data/out/predict/models/v1_L0.pkl data/out/predict/models/v1_L50.pkl
ls -l "$OUT"
cat <<'TXT'
To launch (review first; run by hand with the btclat-login profile):
  SUBNET=$(aws --profile btclat-login --region eu-west-1 ec2 describe-subnets \
    --filters Name=availability-zone-id,Values=euw1-az1 Name=default-for-az,Values=true \
    --query 'Subnets[0].SubnetId' --output text)
  AMI=$(aws --profile btclat-login --region eu-west-1 ssm get-parameter \
    --name /aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id \
    --query Parameter.Value --output text)
  aws --profile btclat-login --region eu-west-1 ec2 run-instances --image-id "$AMI" \
    --instance-type t4g.small --subnet-id "$SUBNET" --key-name <your-key> \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3}' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=btclat-paper}]'
  scp dist/btclat-paper.tgz ubuntu@<ip>:~ && ssh ubuntu@<ip> \
    'mkdir kit && tar xzf btclat-paper.tgz -C kit && sudo bash kit/btclat/paper/deploy/setup.sh'
  After 48 h: rsync -a ubuntu@<ip>:/opt/btclat/data/paper/ data/paper/ ;
  python3 -m btclat.paper.report --run dublin-<tag> --raw ; then terminate the instance.
TXT
