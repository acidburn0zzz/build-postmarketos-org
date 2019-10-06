#!/bin/sh -e
topdir="$(realpath "$(dirname "$0")/..")"

flake8 \
	*.py \
	$(find bpo -name "*.py") \
	$(find test -name "*.py")

echo "flake8 check passed"
