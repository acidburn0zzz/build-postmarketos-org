#!/bin/sh -e
DIR="$(dirname "$0")"

port="5000"
if [ -n "$1" ]; then
    port="$1"
fi

arch="x86_64"
push_id="1"
# Load the test token with: ./bpo.py -t test/test_tokens.cfg
token="5tJ7sPJQ4fLSf0JoS81KSpUwoGMmbWk5Km0OJiAHWF2PM2cO7i"

set -x
curl \
    -d "$(cat "$DIR/../payload/job-callback-get-repo-missing.json")" \
    -H "Content-Type: application/json" \
    -H "X-BPO-Arch: $arch" \
    -H "X-BPO-Push-Id: $push_id" \
    -H "X-BPO-Token: $token" \
    "http://localhost:$port/api/job-callback/get-repo-missing"
