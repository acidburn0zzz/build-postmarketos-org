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
        arg_work_boot = f"{arg_work}/chroot_rootfs_qemu-amd64/boot"
        arg_work_rootfs = f"{arg_work}/chroot_native/home/pmos/rootfs"

        # "true" is where we let the printf password pipe end
        return f"""true # pmbootstrap install stub from testsuite
                rootfs="{arg_work_rootfs}/qemu-amd64.img"
                bootimg="{arg_work_boot}/boot.img-qemu-amd64"

                mkdir -p {arg_work_rootfs} {arg_work_boot}
                dd \\
                    if=/dev/zero \\
                    of="$rootfs" \\
                    bs=1M \\
                    count=1

                # Pretent to have a boot.img too, to test that code path
                cp -v "$rootfs" "$bootimg"

                echo pmbootstrap install"""

    monkeypatch.setattr(bpo.jobs.build_image, "get_pmbootstrap_install_cmd",
                        pmbootstrap_install_stub)
    build_image(monkeypatch)


@pytest.mark.timeout(20)
def test_build_image_stub_split_boot_root(monkeypatch):
    """ Like test_build_image_stub_split, but emulate pmbootstrap generating
        split -boot and -root partitions, as it would do with
        deviceinfo_flasher="fastboot-bootpart". See also: pmb!1871 """

    def pmbootstrap_install_stub():
        arg_work = "$(pmbootstrap config work)"
        arg_work_rootfs = f"{arg_work}/chroot_native/home/pmos/rootfs"

        # "true" is where we let the printf password pipe end
        return f"""true # pmbootstrap install stub from testsuite
                rootfs_root_part="{arg_work_rootfs}/qemu-amd64-root.img"
                rootfs_boot_part="{arg_work_rootfs}/qemu-amd64-boot.img"

                mkdir -p {arg_work_rootfs}
                dd \\
                    if=/dev/zero \\
                    of="$rootfs_root_part" \\
                    bs=1M \\
                    count=1

                cp -v "$rootfs_root_part" "$rootfs_boot_part"

                echo pmbootstrap install"""

    monkeypatch.setattr(bpo.jobs.build_image, "get_pmbootstrap_install_cmd",
                        pmbootstrap_install_stub)
    build_image(monkeypatch)


# Run with: test/manual/test_build_installer_run_in_qemu.sh
@pytest.mark.skip_ci
@pytest.mark.timeout(300)
def test_build_image_SLOW_300s(monkeypatch):
    build_image(monkeypatch)
