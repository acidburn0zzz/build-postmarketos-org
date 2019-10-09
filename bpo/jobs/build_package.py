# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import bpo.db
import bpo.helpers.job

import collections
import fnmatch
import logging
import os
import shlex


def do_build_strict(pkgname):
    """ Check if --strict should be supplied to "pmbootstrap build". Usually
        we want to use it every time, but in order to work around bugs we may
        need to disable it for certain packages. For example:
        https://gitlab.alpinelinux.org/alpine/apk-tools/issues/10649 """
    for pattern in bpo.config.const.no_build_strict:
        if fnmatch.fnmatch(pkgname, pattern):
            return False
    return True


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

    strict_arg = "--strict" if do_build_strict(pkgname) else ""

    # Start job
    job_id = bpo.helpers.job.run("build_package", collections.OrderedDict([
        ("install_pubkey", """
            echo -n '""" + pubkey + """' \
                > pmbootstrap/pmb/data/keys/wip.rsa.pub
            """),
        # FIXME: checkout branch
        ("pmbootstrap_build", """
            ./pmbootstrap/pmbootstrap.py \\
                """ + mirrors + """ \\
                --details-to-stdout \\
                build \\
                --no-depends \\
                """ + strict_arg + """ \\
                --arch """ + shlex.quote(arch) + """ \\
                """ + shlex.quote(pkgname) + """
            """),
        ("submit", """
            export BPO_API_ENDPOINT="build-package"
            export BPO_ARCH=""" + shlex.quote(arch) + """
            export BPO_BRANCH=""" + shlex.quote(branch) + """
            export BPO_PAYLOAD_FILES="$(ls -1 "$(pmbootstrap/pmbootstrap.py \\
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
    bpo.db.set_package_status(session, package, bpo.db.PackageStatus.building,
                              job_id)


def abort(package):
    """ Stop a single package build job.
        :param package: bpo.db.Package object """
    # FIXME
    logging.info("STUB")
