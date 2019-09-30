# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os
import subprocess

import bpo.config.const


def get_path(arch, branch):
    return "{}/{}/{}".format(bpo.config.args.repo_final_path, branch, arch)
