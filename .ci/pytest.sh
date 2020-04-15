#!/bin/sh -e
topdir="$(realpath "$(dirname "$0")/..")"
cd "$topdir"

../pmbootstrap/pmbootstrap.py work_migrate

pytest -vv -x --cov=bpo test -m "not sourcehut" "$@"
