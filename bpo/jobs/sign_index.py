# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import shlex

import bpo.config.const
import bpo.helpers.job


def run(arch, branch):
    unsigned = "{}/{}/APKINDEX-symlink-repo.tar.gz".format(branch, arch)
    uid = bpo.config.const.pmbootstrap_chroot_uid_user

    bpo.helpers.job.run("sign_index", {
        "download unsigned index": """
            if [ -n "$BPO_WIP_REPO_PATH" ]; then
                cp "$BPO_WIP_REPO_PATH"/""" + shlex.quote(unsigned) + """ \
                    APKINDEX.tar.gz
            else
                wget "$BPO_WIP_REPO_URL"/""" + shlex.quote(unsigned) + """ \
                    -O APKINDEX.tar.gz
            fi
            """,
        "sign": """
            ./pmbootstrap/pmbootstrap.py build_init
            work_dir="$(./pmbootstrap/pmbootstrap.py -q config work)"
            chroot_target="$work_dir/chroot_native/home/pmos/APKINDEX.tar.gz"
            sudo cp APKINDEX.tar.gz "$chroot_target"
            sudo chown """ + shlex.quote(uid) + """ "$chroot_target"
            ./pmbootstrap/pmbootstrap.py chroot --user -- \
                abuild-sign /home/pmos/APKINDEX.tar.gz
            sudo mv "$chroot_target" APKINDEX.tar.gz
        """,
        "upload": """
            echo "stub: upload"
        """,
    })
