# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import glob
import logging
import os
import subprocess

import bpo.config.args


def get_path(arch, branch):
    # The symlink repo is in the temp path, because it does not take up as much
    # space as the final or wip repos.
    temp_path = bpo.config.args.temp_path
    return "{}/repo_symlink/{}/{}".format(temp_path, branch, arch)


def clean(arch, branch):
    path = get_path(arch, branch)
    if os.path.exists(path):
        shutil.rmtree(path)


def link_to_all_packages(arch, branch):
    logging.info("STUB: link to all packages in symlink repo")


def index(arch, branch):
    logging.info("STUB: index symlink repo")


def sign(arch, branch):
    # copy index to wip repo (just because that makes it easy to download it)
    # run sign job
    logging.info("STUB: sign symlink repo")


def create(arch, branch):
    # TODO multithreading: make sure that this only runs once at a time
    clean(arch, branch)
    link_to_all_packages(arch, branch)
    index(arch, branch)
    sign(arch, branch)
