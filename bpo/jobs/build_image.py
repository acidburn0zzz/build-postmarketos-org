# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import collections
import shlex

import bpo.db
import bpo.ui
import bpo.helpers.job
import bpo.images
import bpo.images.config


def get_pmbootstrap_install_cmd():
    """ pmbootstrap install command for image building. This is a separate
        function, so we can override it with a stub in a test. """
    arg_mirror_alpine = shlex.quote(bpo.config.const.mirror_alpine)
    arg_mirror_pmos = shlex.quote(f"{bpo.config.args.mirror}/")

    return f"""pmbootstrap \\
                -m {arg_mirror_alpine} \\
                -mp {arg_mirror_pmos} \\
                --details-to-stdout \\
                install \\
                --no-local-pkgs"""


def run(device, branch, ui):
    """ Start a single image build job. """
    # Put the pkgver from this package into the image name
    ui_apkbuild = f"main/postmarketos-ui-{ui}/APKBUILD"
    if ui == "none":
        ui_apkbuild = "main/postmarketos-base/APKBUILD"

    # Shell arguments
    arg_branch = shlex.quote(branch)
    arg_device = shlex.quote(device)
    arg_pass = shlex.quote(bpo.config.const.images.password)
    arg_pmos_ver = shlex.quote(bpo.images.pmos_ver(branch))
    arg_ui = shlex.quote(ui)
    arg_ui_apkbuild = shlex.quote(ui_apkbuild)
    arg_work = "$(pmbootstrap config work)"
    arg_work_boot = f"{arg_work}/chroot_rootfs_{arg_device}/boot"
    arg_work_rootfs = f"{arg_work}/chroot_native/home/pmos/rootfs"

    # Task: img_prepare (generate image prefix, configure pmb, create tmpdir)
    tasks = collections.OrderedDict()
    tasks["img_prepare"] = f"""
        IMG_DATE="$(date +%Y%m%d-%H%M)"
        echo "$IMG_DATE" > img-date

        # Image prefix format:
        # <YYYYMMDD-HHMM>-postmarketOS-<PMOS VER>-<UI>-<UI VER>-<DEVICE>
        UI_VERSION=$(grep "^pkgver=" "$(pmbootstrap config aports \\
            )"/{arg_ui_apkbuild} | cut -d= -f2)
        IMG_PREFIX="$IMG_DATE"-postmarketOS-{arg_pmos_ver}-{arg_ui}
        IMG_PREFIX="$IMG_PREFIX"-"$UI_VERSION"-{arg_device}
        echo "$IMG_PREFIX" > img-prefix

        pmbootstrap config ui {arg_ui}
        pmbootstrap config device {arg_device}

        mkdir out
    """

    pmbootstrap_install = get_pmbootstrap_install_cmd()

    # Iterate over kernels to generate the images, with zap in-between
    branch_cfg = bpo.images.config.get_branch_config(device, branch)
    for kernel in branch_cfg["kernels"]:
        # Task and image name, add kernel suffix if having multiple kernels
        task_name = "img"
        arg_img_prefix = "$(cat img-prefix)"
        if kernel:
            task_name += f"_{kernel}".replace("-", "_")
            arg_img_prefix += shlex.quote(f"-{kernel}")

        # Task: img (non-installer image)
        arg_kernel = shlex.quote(kernel)
        tasks[task_name] = f"""
            IMG_PREFIX={arg_img_prefix}

            pmbootstrap config kernel {arg_kernel}
            pmbootstrap -q -y zap -p

            printf "%s\\n%s\\n" {arg_pass} {arg_pass} | {pmbootstrap_install}

            if [ -e {arg_work_rootfs}/{arg_device}.img ]; then
                sudo mv {arg_work_rootfs}/{arg_device}.img \\
                        "out/$IMG_PREFIX.img"
            else
                # Boot and root partitions in separate files (pmbootstrap!1871)
                # Name the second file -bootpart.img instead of -boot.img to
                # avoid confusion with Android boot.img files.
                sudo mv {arg_work_rootfs}/{arg_device}-root.img \\
                        "out/$IMG_PREFIX.img"
                sudo mv {arg_work_rootfs}/{arg_device}-boot.img \\
                        "out/$IMG_PREFIX-bootpart.img"
            fi
            ls -lh out
        """

        # Task: img_bootimg
        # For Android devices, postmarketos-mkinitfs generates a boot.img
        # inside the rootfs img (above). Make it available as separate file, to
        # make flashing easier. 'boot.img-*', because the kernel name is
        # appended (e.g. boot.img-postmarketos-qcom-msm8916).
        tasks[f"{task_name}_bootimg"] = f"""
            IMG_PREFIX={arg_img_prefix}

            for i in {arg_work_boot}/boot.img-*; do
                if [ -e "$i" ]; then
                    sudo mv "$i" "out/$IMG_PREFIX-boot.img"
                fi
            done

            ls -lh out
        """

        # Task: img_installer (wrap installer around previous image)
        if not branch_cfg["installer"]:
            continue
        task_name += "_installer"
        tasks[task_name] = f"""
            IMG_PREFIX={arg_img_prefix}

            pmbootstrap -q -y zap -p

            {pmbootstrap_install} \\
                --ondev \\
                --no-rootfs \\
                --cp "out/$IMG_PREFIX.img":/var/lib/rootfs.img

            if [ -e {arg_work_rootfs}/{arg_device}.img ]; then
                sudo mv {arg_work_rootfs}/{arg_device}.img \\
                    "out/$IMG_PREFIX-installer.img"
            else
                # Boot and root partitions in separate files (pmbootstrap!1871)
                # Move the root partition to -installer.img and ignore the boot
                # partition (it's the same as the -bootpart.img saved in the
                # img task above).
                sudo mv {arg_work_rootfs}/{arg_device}-root.img \\
                    "out/$IMG_PREFIX-installer.img"
            fi
            ls -lh out
        """

    tasks["compress"] = """
            sudo chown "$(id -u):$(id -g)" out/*.img

            for i in out/*.img; do
                xz -0 -T0 "$i"
            done

            ls -lh out
    """

    tasks["checksums"] = """
            cd out
            sha512sum *
    """

    tasks["submit"] = f"""
            export BPO_API_ENDPOINT="build-image"
            export BPO_ARCH=""
            export BPO_BRANCH={arg_branch}
            export BPO_DEVICE={arg_device}
            export BPO_UI={arg_ui}
            export BPO_PAYLOAD_FILES="$(find out -type f)"
            export BPO_PAYLOAD_IS_JSON="0"
            export BPO_PKGNAME=""
            export BPO_VERSION="$(cat img-date)"

            # Always run submit.py with exec, because when running locally, the
            # current_task.sh script can change before submit.py completes!
            exec build.postmarketos.org/helpers/submit.py
    """

    # Submit to job service
    note = f"Build image: `{branch}:{device}:{ui}`"
    job_id = bpo.helpers.job.run("build_image", note, tasks, branch,
                                 device=device, ui=ui)

    # Update DB and UI
    session = bpo.db.session()
    image = bpo.db.get_image(session, branch, device, ui)
    if image.status == bpo.db.ImageStatus.failed:
        image.retry_count += 1
    bpo.db.set_image_status(session, image, bpo.db.ImageStatus.building,
                            job_id)
    bpo.ui.update(session)
