# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import shlex

import bpo.helpers.job


def run(push, arch):
    """ :param push: bpo.db.Push object """
    bpo.helpers.job.run("get_depends", collections.OrderedDict([
        # FIXME: checkout right pmaports.git branch (and somehow deal with it
        # when running locally, we don't want to change the branch then)
        ("pmbootstrap repo_missing", """
            ./pmbootstrap/pmbootstrap.py \
                --mirror-pmOS """ + shlex.quote(bpo.config.args.mirror) + """ \
                repo_missing > repo_missing.json
            """),
        # NOTE: the branch is already defined through the push_id in the
        # database. But let's write it out explicitly to make debugging easier.
        ("submit", """
            export BPO_API_ENDPOINT="get-repo-missing"
            export BPO_ARCH=""" + shlex.quote(arch) + """
            export BPO_BRANCH=""" + shlex.quote(push.branch) + """
            export BPO_PAYLOAD_FILES="repo_missing.json"
            export BPO_PAYLOAD_IS_JSON="1"
            export BPO_PKGNAME=""
            export BPO_PUSH_ID=""" + shlex.quote(str(push.id)) + """
            export BPO_VERSION=""

            # Always run submit.py with exec, because when running locally, the
            # current_task.sh script can change before submit.py completes!
            exec pmaports/.build.postmarketos.org/submit.py
            """),
    ]))
