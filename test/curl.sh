#!/bin/sh -e

port="5000"
if [ -n "$1" ]; then
    port="$1"
fi

# Load the test token with: ./bpo.py -t test/test_tokens.cfg
token="iptTdfRNwSvg8ycZqiEdNhMqGalvsgvSXp91SIk2dukG74BNVu"

set -x
curl \
    -d '{"object_kind":"push", "checkout_sha": "deadbeef","commits":["a","b"]}' \
    -H "Content-Type: application/json" \
    -H "X-Gitlab-Token: $token" \
    "http://localhost:$port/api/push-hook/gitlab"
