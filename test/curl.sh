#!/bin/sh -e

port="1338"
if [ -n "$1" ]; then
    port="$1"
fi

# This is a test token, replace with your own one
set -x
curl \
    -d '{"object_kind":"push", "checkout_sha": "deadbeef","commits":["a","b"]}' \
    -H "Content-Type: application/json" \
    -H "X-Gitlab-Token: rewDBfdzYqV6rWRcL0gkypDgPs3nXYr2ARHlTvwtV7gfgtQBIe" \
    "http://localhost:$port/api/push_hook/gitlab"
