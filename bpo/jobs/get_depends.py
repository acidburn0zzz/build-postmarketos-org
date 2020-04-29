# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import shlex

import bpo.helpers.job


def run(branch):
    tasks = collections.OrderedDict()
    mirror_final = bpo.config.args.mirror
    if mirror_final:
        mirror_final += "/" + branch

    for arch in bpo.config.const.architectures:
        tasks[branch + "_" + arch] = """
            export ARCH=""" + shlex.quote(arch) + """
            export JSON="depends.$ARCH.json"

            ./pmbootstrap/pmbootstrap.py \\
                --aports=$PWD/pmaports \\
                -mp """ + shlex.quote(mirror_final) + """ \\
                repo_missing --built --arch "$ARCH" \\
                > "$JSON"
            cat "$JSON"
            """

    tasks["submit"] = """
        export BPO_API_ENDPOINT="get-depends"
        export BPO_ARCH=""
        export BPO_BRANCH=""" + shlex.quote(branch) + """
        export BPO_PAYLOAD_FILES="$(ls -1 depends.*.json)"
        export BPO_PAYLOAD_IS_JSON="0"
        export BPO_PKGNAME=""
        export BPO_VERSION=""

        # Always run submit.py with exec, because when running locally, the
        # current_task.sh script can change before submit.py completes!
        exec build.postmarketos.org/helpers/submit.py
        """

    note = "Parse packages and dependencies from pmaports.git"
    bpo.helpers.job.run("get_depends", note, tasks, branch)
