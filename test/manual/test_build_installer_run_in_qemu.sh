#!/bin/sh -e
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
topdir="$(realpath "$(dirname "$0")/../..")"
work="$(pmbootstrap config work)"
rootfs_xz="$work"/chroot_native/home/pmos/rootfs/qemu-amd64.img.xz

cd "$topdir"
. .venv/bin/activate

set -x
pytest -xvv test/test_zz0_jobs_build_image.py -k 'test_build_image_SLOW_'
sudo cp _temp/local_job/out/*-installer.img.xz "$rootfs_xz"
sudo unxz "$rootfs_xz"
DISPLAY=:0 pmbootstrap qemu
