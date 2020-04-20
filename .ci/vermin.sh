#!/bin/sh -e
topdir="$(realpath "$(dirname "$0")/..")"

_vermin() {
	if ! vermin -q "$@" >/dev/null 2>&1; then
		vermin -vv "$@"
	fi
}

_vermin \
	-t=3.5- \
	--backport argparse \
	--backport configparser \
	--backport enum \
	$(ls -1 *.py) \
	$(find bpo -name '*.py') \
	$(find test -name '*.py') \
	helpers/bpo_package_status.py

echo "vermin check passed"
