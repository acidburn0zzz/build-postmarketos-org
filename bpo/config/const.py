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
