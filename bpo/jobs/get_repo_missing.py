# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import shlex

import bpo.helpers.job


def run_arch_branch(arch, branch):
    mirror_final = bpo.config.args.mirror + "/" + branch + "/" + arch

    bpo.helpers.job.run("get_repo_missing", collections.OrderedDict([
        ("pmbootstrap repo_missing", """
            ./pmbootstrap/pmbootstrap.py \
                --mirror-pmOS """ + shlex.quote(mirror_final) + """ \
                repo_missing > repo_missing.json
            """),
        # NOTE: the branch is already defined through the push_id in the
        # database. But let's write it out explicitly to make debugging easier.
        ("submit", """
            export BPO_API_ENDPOINT="get-repo-missing"
            export BPO_ARCH=""" + shlex.quote(arch) + """
            export BPO_BRANCH=""" + shlex.quote(branch) + """
            export BPO_PAYLOAD_FILES="repo_missing.json"
            export BPO_PAYLOAD_IS_JSON="1"
            export BPO_PKGNAME=""
            export BPO_VERSION=""

            # Always run submit.py with exec, because when running locally, the
            # current_task.sh script can change before submit.py completes!
            exec pmaports/.build.postmarketos.org/submit.py
            """),
    ]), branch, arch)


def run():
    for branch in bpo.config.const.branches:
        for arch in bpo.config.const.architectures:
            run_arch_branch(arch, branch)
