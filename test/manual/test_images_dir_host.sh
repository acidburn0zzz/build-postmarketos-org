#!/bin/sh -e
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
topdir="$(realpath "$(dirname "$0")/../..")"

cd "$topdir"
mkdir -p _images _html_out

cd _html_out
python3 -m http.server --bind 127.0.0.1 8990 &

cd ../_images
python3 -m http.server --bind 127.0.0.1 8991 &

sleep 0.3
echo
echo "* http://127.0.0.1:8990 (build.postmarketos.org)"
echo "* http://127.0.0.1:8991 (images.postmarketos.org/bpo)"
echo
echo "Run test_images_dir_gen.sh to generate new HTML files."
echo "Hit return to stop."
read foo

kill %1 %2
