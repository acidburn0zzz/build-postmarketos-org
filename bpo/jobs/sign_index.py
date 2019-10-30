# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import collections
import shlex

import bpo.config.const
import bpo.helpers.job


def run(arch, branch):
    web_path = arch + "/APKINDEX-symlink-repo.tar.gz"
    local_path = branch + "/" + web_path
    uid = bpo.config.const.pmbootstrap_chroot_uid_user
    rsa = bpo.config.const.final_repo_key_name

    bpo.helpers.job.run("sign_index", collections.OrderedDict([
        ("download_unsigned_index", """
            if [ -n "$BPO_WIP_REPO_PATH" ]; then
                cp "$BPO_WIP_REPO_PATH"/""" + shlex.quote(local_path) + """ \\
                    APKINDEX.tar.gz
            else
                wget "$BPO_WIP_REPO_URL"/""" + shlex.quote(web_path) + """ \\
                    -O APKINDEX.tar.gz
            fi
            """),
        ("sign", """
            ./pmbootstrap/pmbootstrap.py build_init
            work_dir="$(./pmbootstrap/pmbootstrap.py -q config work)"
            chroot_target="$work_dir/chroot_native/home/pmos/"
            sudo cp APKINDEX.tar.gz "$chroot_target"
            sudo cp .final.rsa "$chroot_target"/""" + shlex.quote(rsa) + """
            sudo chown -R """ + shlex.quote(uid) + """ "$chroot_target"
            ./pmbootstrap/pmbootstrap.py \\
                --details-to-stdout \\
                chroot --user -- \\
                    abuild-sign \\
                        -k /home/pmos/""" + shlex.quote(rsa) + """ \\
                        /home/pmos/APKINDEX.tar.gz
            sudo mv "$chroot_target/APKINDEX.tar.gz" .
        """),
        ("upload", """
            export BPO_API_ENDPOINT="sign-index"
            export BPO_ARCH=""" + shlex.quote(arch) + """
            export BPO_BRANCH=""" + shlex.quote(branch) + """
            export BPO_PAYLOAD_FILES="APKINDEX.tar.gz"
            export BPO_PAYLOAD_IS_JSON="0"
            export BPO_PKGNAME=""
            export BPO_VERSION=""

            # Always run submit.py with exec, because when running locally, the
            # current_task.sh script can change before submit.py completes!
            exec pmaports/.build.postmarketos.org/submit.py
        """),
    ]), branch, arch)
