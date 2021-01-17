# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import re

# Regular expressions for resulting dir and file names
pattern_dir = re.compile("^[0-9]{8}-[0-9]{4}$")
pattern_file = re.compile(
        "^[0-9]{8}-[0-9]{4}-postmarketOS-[a-z0-9._+-]+\\.img\\.xz$")

# Default password for regular (non-installer) images
password = "147147"

# Branches to build images for, can be overridden per device in 'images' below
branches_default = ["master"]

# Build configuration, can be overridden per device/branch in 'images' below
branch_config_default = {
    # Schedule a new image each {date-interval} days, start at {date-start}.
    "date-interval": 7,
    "date-start": "2020-12-29",

    # User interfaces to build. At least one UI must be set for each device,
    # otherwise no image for that device will be built.
    "ui": [
        "phosh",
        "plasma-mobile",
    ],

    # Build images with the on-device installer. If set to False, build one
    # image without the installer. If set to True, build another image, which
    # wraps the first image with the installer.
    "installer": False,

    # To create additional images with other kernels selected, override this
    # variable. For qemu-amd64, this could be ["virt", "lts"].
    # https://postmarketos.org/multiple-kernels
    "kernels": [""],

    # How many images (image directories) to keep of one branch:device:ui
    # combination. Older images will get deleted to free up space.
    "keep": 3
}

# For each image you add here, make sure there is a proper wiki redirect for
# https://wiki.postmarketos.org/wiki/<codename>. That is what will show up in
# the generated readme.html!
images = {
    "bq-paella": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "motorola-harpia": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "nokia-n900": {
        "branch_configs": {
            "all": {
                "ui": [
                    "i3wm",
                ],
            },
         },
    },
    "pine64-pinephone": {
        "branches": [
            "master",
            "v20.05",
        ],
        "branch_configs": {
            "all": {
                "ui": [
                    "phosh",
                    "plasma-mobile",
                    "sxmo",
                ],
                "installer": True,
            },
            "v20.05": {
                "ui": [
                    "phosh",
                ],
                # Needs postmarketos-ondev 0.3.x or higher backported
                "installer": False,
            },
        },
    },
    "pine64-pinetab": {
        "branch_configs": {
            "all": {
                "installer": True,
                "kernels": [
                    "allwinner",
                    "allwinner-dev",
                ],
            },
        },
    },
    "purism-librem5": {
        "branch_configs": {
            "all": {
                "installer": True,
            },
        },
    },
    "samsung-a3ulte": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "samsung-a5lte": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "samsung-a5ulte": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "samsung-serranovelte": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
    "wileyfox-crackling": {
        "branch_configs": {
            "all": {
                "kernels": [
                    "mainline-modem",
                ],
            },
        },
    },
}
