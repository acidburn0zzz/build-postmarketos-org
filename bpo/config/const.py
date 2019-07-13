# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

# Various configuration options, that the user shouldn't need to change (just
# like pmb/config/__init__.py).
import os

# Directory containing bpo.py and the bpo module
top_dir = os.path.normpath(os.path.realpath(__file__) + "/../../..")

architectures = ["x86_64"]
