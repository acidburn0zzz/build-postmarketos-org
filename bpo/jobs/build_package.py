# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import bpo.db
import bpo.helpers.job
import logging
import shlex


def run(arch, pkgname):
    """ Start a single package build job. """
    # Change status to building
    session = bpo.db.session()
    package = bpo.db.get_package(session, pkgname, arch)
    package.status = bpo.db.PackageStatus.building
    session.merge(package)
    session.commit()

    # FIXME: arch is None here for some reason
    arch = "x86_64"

    # Start job
    bpo.helpers.job.run("build_package", {
        # FIXME: use proper --mirror-pmOS parameters etc.
        "pmbootstrap build": """
            ./pmbootstrap.py build \
                --strict \
                --arch """ + shlex.quote(arch) + """ \
                """ + shlex.quote(pkgname) + """
            """,
            # FIXME: submit
    })

    # FIXME: write job id back to Packages


def abort(arch, pkgname):
    """ Stop a single package build job. """
    # FIXME
    logging.info("STUB")
