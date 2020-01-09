# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import shlex

import bpo.helpers.job


def run():
    tasks = collections.OrderedDict()
    for branch in bpo.config.const.branches:
        mirror_final = bpo.config.args.mirror
        if mirror_final:
            mirror_final += "/" + branch

        # FIXME: checkout proper pmaports branch (currently always master)
        for arch in bpo.config.const.architectures:
            tasks["repo_" + branch + "_" + arch] = """
                export BRANCH=""" + shlex.quote(branch) + """
                export ARCH=""" + shlex.quote(arch) + """
                export JSON="depends.$BRANCH.$ARCH.json"

                ./pmbootstrap/pmbootstrap.py \\
                    -mp """ + shlex.quote(mirror_final) + """ \\
                    repo_missing --arch "$ARCH" \\
                    > "$JSON"
                cat "$JSON"
                """

    tasks["submit"] = """
        export BPO_API_ENDPOINT="get-depends"
        export BPO_ARCH=""
        export BPO_BRANCH=""
        export BPO_PAYLOAD_FILES="$(ls -1 depends.*.*.json)"
        export BPO_PAYLOAD_IS_JSON="0"
        export BPO_PKGNAME=""
        export BPO_VERSION=""

        # Always run submit.py with exec, because when running locally, the
        # current_task.sh script can change before submit.py completes!
        exec pmaports/.build.postmarketos.org/submit.py
        """

    note = "Parse packages and dependencies from pmaports.git"
    bpo.helpers.job.run("get_depends", note, tasks)
