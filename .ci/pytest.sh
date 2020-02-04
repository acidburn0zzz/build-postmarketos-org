#!/bin/sh -e
topdir="$(realpath "$(dirname "$0")/..")"
cd "$topdir"
pytest -vv -x --cov=bpo test -m "not sourcehut" "$@"
