# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import bpo.db
import bpo.helpers.job

import collections
import logging
import os
import shlex


def run(arch, pkgname, branch):
    """ Start a single package build job. """
    # Load package from db
    session = bpo.db.session()
    package = bpo.db.get_package(session, pkgname, arch, branch)

    # Read WIP repo pub key
    with open(bpo.config.const.repo_wip_keys + "/wip.rsa.pub", "r") as handle:
        pubkey = handle.read()

    # Set mirror args (either primary mirror, or WIP + primary)
    wip_path = "{}/{}/{}/APKINDEX.tar.gz".format(bpo.config.args.repo_wip_path,
                                                 branch, arch)
    mirror_final = bpo.config.args.mirror + "/" + branch + "/" + arch
    mirrors = "--mirror-pmOS " + shlex.quote(mirror_final)
    if os.path.exists(wip_path):
        mirrors = '$BPO_WIP_REPO_ARG ' + mirrors

    # Start job
    job_id = bpo.helpers.job.run("build_package", collections.OrderedDict([
        ("install wip.rsa.pub", """
            echo -n '""" + pubkey + """' \
                > pmbootstrap/pmb/data/keys/wip.rsa.pub
            """),
        # FIXME: checkout branch
        ("pmbootstrap build", """
            ./pmbootstrap/pmbootstrap.py \
                """ + mirrors + """ \
                --details-to-stdout \
                build \
                --no-depends \
                --strict \
                --arch """ + shlex.quote(arch) + """ \
                """ + shlex.quote(pkgname) + """
            """),
        ("submit", """
            export BPO_API_ENDPOINT="build-package"
            export BPO_ARCH=""" + shlex.quote(arch) + """
            export BPO_BRANCH=""" + shlex.quote(branch) + """
            export BPO_PAYLOAD_FILES="$(ls -1 "$(./pmbootstrap/pmbootstrap.py \
                -q config work)/packages/$BPO_ARCH/"*.apk)"
            export BPO_PAYLOAD_IS_JSON="0"
            export BPO_PKGNAME=""" + shlex.quote(pkgname) + """
            export BPO_VERSION=""" + shlex.quote(package.version) + """

            # Always run submit.py with exec, because when running locally, the
            # current_task.sh script can change before submit.py completes!
            exec pmaports/.build.postmarketos.org/submit.py
            """)
    ]), branch, arch, pkgname, package.version)

    # Change status to building and save job_id
    package.status = bpo.db.PackageStatus.building
    package.job_id = job_id
    session.merge(package)
    session.commit()


def abort(package):
    """ Stop a single package build job.
        :param package: bpo.db.Package object """
    # FIXME
    logging.info("STUB")
