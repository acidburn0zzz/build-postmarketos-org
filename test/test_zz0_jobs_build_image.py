# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Testing bpo/jobs/build_image.py """
import pytest

import bpo_test  # noqa
import bpo.config.const.images
import bpo.jobs.build_image


def build_image(monkeypatch):
    """ This function gets called by the two tests below, first with a stub and
        then without the stub. """
    monkeypatch.setattr(bpo.config.const.images, "images",
                        {"qemu-amd64": {
                            "branches": ["master"],
                            "branch_configs": {
                                "master": {
                                    "ui": ["none"],
                                    "installer": True,
                                    "kernels": ["virt"],
                                }
                            }
                        }})

    device = "qemu-amd64"
    branch = "master"
    ui = "none"

    with bpo_test.BPOServer(disable_pmos_mirror=False, fill_image_queue=True):
        monkeypatch.setattr(bpo.repo, "build", bpo_test.stop_server)

    bpo_test.assert_image(device, branch, ui, "published")


@pytest.mark.timeout(20)
def test_build_image_stub(monkeypatch):
    """ Do not run 'pmbootstrap install', just create a 1 MiB file with dd.
        This is much faster, and doesn't cause problems when running with
        gitlab CI (which would fail on 'modprobe loop' error). """

    def pmbootstrap_install_stub():
        arg_work = "$(pmbootstrap config work)"
        arg_work_rootfs = f"{arg_work}/chroot_native/home/pmos/rootfs"
        return f"""# pmbootstrap install stub from testsuite
                mkdir -p {arg_work_rootfs}
                dd \\
                    if=/dev/zero \\
                    of={arg_work_rootfs}/qemu-amd64.img \\
                    bs=1M \\
                    count=1

                echo pmbootstrap install"""

    monkeypatch.setattr(bpo.jobs.build_image, "get_pmbootstrap_install_cmd",
                        pmbootstrap_install_stub)
    build_image(monkeypatch)


@pytest.mark.skip_ci
@pytest.mark.timeout(300)
def test_build_image_SLOW_300s(monkeypatch):
    build_image(monkeypatch)
