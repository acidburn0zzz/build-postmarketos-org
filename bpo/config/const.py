# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

# Various configuration options, that the user shouldn't need to change (just
# like pmb/config/__init__.py).
import os

# Directory containing bpo.py and the bpo module
top_dir = os.path.normpath(os.path.realpath(__file__) + "/../../..")

# Keypair for signing the APKINDEX of the WIP repository will be stored here
repo_wip_keys = top_dir + "/_repo_wip_keys"

architectures = ["x86_64", "armhf", "aarch64", "armv7", "x86"]

# Which pmaports.git branches will be built (e.g. "master", "v20.05", ...)
branches = ["master"]

# Omit the --strict argument for pmbootstrap build for these packages (fnmatch)
# gcc*-*: https://gitlab.alpinelinux.org/alpine/apk-tools/issues/10649
#         (fix is merged to abuild master, not yet in latest abuild release)
no_build_strict = ["gcc*-*"]

# How many build jobs can run in parallel (across all arches)
max_parallel_build_jobs = 1

# Automatically retry build (sometimes builds fail due to network errors, so
# just retry a few times to make it more robust) (#58)
retry_count_max = 2

# UID that is used for building packages with pmbootstrap (same as
# chroot_user_id in pmb/config/__init__.py)
pmbootstrap_chroot_uid_user = "12345"

# Seconds after which a build gets aborted by pmbootstrap if the commands ran
# by the APKBUILD stopped writing any output. Usually we get nowhere near the
# timeout without having anything written to stdout/stderr. However, linking
# big binaries may come close to the timeout. Especially during cross
# compilation, because we currently don't run the linker natively (could be
# possible though, see pmaports#233).
pmbootstrap_timeout = 900

# Values for the tokens in test/test_tokens.cfg
test_tokens = {"push_hook_gitlab": "iptTdfRNwSvg8ycZqiEdNhMqGalvsgvSXp91SIk2du"
                                   "kG74BNVu",
               "job_callback": "5tJ7sPJQ4fLSf0JoS81KSpUwoGMmbWk5Km0OJiAHWF2PM2"
                               "cO7i"}

# abuild-sign embeds this key name into the APKINDEX. The name of the .pub file
# in pmbootstrap.git's pmb/data/keys dir must match it.
final_repo_key_name = "build.postmarketos.org.rsa"
