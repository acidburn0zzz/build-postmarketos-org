#!/bin/sh -ex

USER="put-your-username-here"

args=""

# Fill DB with missing packages on first run
if ! [ -f "./bpo.db" ]; then
    args="$args --auto-get-depends"
fi

./bpo.py $args sourcehut --user "$USER"
