# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

# Various configuration options, that the user shouldn't need to change (just
# like pmb/config/__init__.py).
import os

# Directory containing bpo.py and the bpo module
top_dir = os.path.normpath(os.path.realpath(__file__) + "/../../..")

# Keypair for signing the APKINDEX of the WIP repository will be stored here
repo_wip_keys = top_dir + "/_repo_wip_keys"

architectures = ["x86_64"]

# Which pmaports.git branches will be built. The idea is to add branches based
# on Alpine's aports.git branches at some point (v3.10, v3.9, ...).
branches = ["master"]

# How many build jobs can run in parallel (across all arches)
max_parallel_build_jobs = 1

# UID that is used for building packages with pmbootstrap (same as
# chroot_user_id in pmb/config/__init__.py)
pmbootstrap_chroot_uid_user = "12345"

# The final repository location, where published and properly signed packages
# can be found.
# TODO: this becomes http://postmarketos.brixit.nl/postmarketos when running
# productively!
primary_mirror = "http://postmarketos.brixit.nl"
