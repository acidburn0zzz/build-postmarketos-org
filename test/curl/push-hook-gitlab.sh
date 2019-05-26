#!/bin/sh -e

port="5000"
if [ -n "$1" ]; then
    port="$1"
fi

# Load the test token with: ./bpo.py -t test/test_tokens.cfg
token="iptTdfRNwSvg8ycZqiEdNhMqGalvsgvSXp91SIk2dukG74BNVu"

set -x
curl \
    -d '
{
    "object_kind":"push",
    "checkout_sha": "deadbeef",
    "commits": [
        {
            "id": "5e9e102a00e58541ed91164de15fd209af628b42",
            "message": "main\/postmarketos-ui-phosh: clean-up\n",
            "timestamp": "2019-05-25T16:23:30Z",
            "url": "https:\/\/gitlab.com\/postmarketOS\/pmaports\/commit\/5e9e102a00e58541ed91164de15fd209af628b42",
            "author": {
                "name": "Bart Ribbers",
                "email": "redacted@localhost"
            },
            "added": [],
            "modified": [
                "main\/postmarketos-ui-phosh\/APKBUILD"
            ],
            "removed": []
        }
    ]
}' \
    -H "Content-Type: application/json" \
    -H "X-Gitlab-Token: $token" \
    "http://localhost:$port/api/push-hook/gitlab"
