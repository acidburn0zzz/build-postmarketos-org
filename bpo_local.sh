#!/bin/sh -ex

args="-t test/test_tokens.cfg"

# Fill DB with missing packages on first run
if ! [ -f "./bpo.db" ]; then
    args="$args --auto-get-repo-missing"
fi

./bpo.py $args local
