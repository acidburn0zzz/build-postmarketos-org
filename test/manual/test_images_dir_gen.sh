#!/bin/sh -e
# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
topdir="$(realpath "$(dirname "$0")/../..")"

cd "$topdir"
. .venv/bin/activate

export BPO_URL="http://127.0.0.1:8990"
export BPO_URL_IMG="http://127.0.0.1:8991"
pytest -xvv test/test_zz0_jobs_build_image.py -m "img_dir_gen"
